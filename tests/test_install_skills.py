"""隔离的真实 Git/文件系统测试；临时目录始终位于 tests/.tmp。"""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'tools/install_skills.py'
TEMP_ROOT = ROOT / 'tests/.tmp'
spec = importlib.util.spec_from_file_location('install_skills', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        mod.checked_path(TEMP_ROOT)
        TEMP_ROOT.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='安装器验证-', dir=str(TEMP_ROOT))
        self.addCleanup(self.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / '中文源'
        self.repo.mkdir()
        self.git('init', '-q', '-b', 'not-main')
        self.git('config', 'user.name', 'Local test')
        self.git('config', 'user.email', 'test@invalid.local')
        self.git('config', 'core.autocrlf', 'false')
        self.skill = self.repo / 'sample-skill'
        (self.skill / 'references').mkdir(parents=True)
        (self.skill / 'SKILL.md').write_text(
            '---\nname: sample-skill\ndescription: 用于隔离测试\n---\n'
            '[参考](references/说明.md)\n', encoding='utf-8')
        (self.skill / 'references/说明.md').write_text('已提交内容\n', encoding='utf-8')
        self.first = self.commit()
        self.dest = self.base / '安装目标/.agents/skills'

    def cleanup(self):
        # Python 3.8 TemporaryDirectory 不会自动去掉 Windows Git 对象的只读位。
        mod.checked_path(TEMP_ROOT)
        if self.base.resolve().parent != TEMP_ROOT or not self.base.name.startswith('安装器验证-'):
            raise RuntimeError('测试清理路径越界')
        for parent, dirs, files in os.walk(str(self.base), followlinks=False):
            for name in files:
                path = Path(parent) / name
                mod.checked_path(path)
                path.chmod(0o600)
        self.temp.cleanup()

    def git(self, *args):
        return mod.git(self.repo, *args).decode('utf-8').strip()

    def commit(self):
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')
        return self.git('rev-parse', 'HEAD')

    def op(self, action='install', revision=None, apply=False, **kw):
        return mod.operate(action, self.repo, revision or self.first,
                           ['sample-skill'], kw.get('dest', self.dest), apply)

    def test_preview_no_write_and_fixed_commit_ignores_dirty_source(self):
        (self.skill / 'references/说明.md').write_text('未提交，不应安装', encoding='utf-8')
        report = self.op()
        self.assertFalse(self.dest.exists())
        self.assertTrue(report['skills'][0]['working_tree_ignored'])
        self.op(apply=True)
        actual = self.dest / 'sample-skill/references/说明.md'
        self.assertEqual(actual.read_text(encoding='utf-8'), '已提交内容\n')
        self.op('verify')

    def test_update_requires_explicit_command_and_keeps_backup(self):
        self.op(apply=True)
        (self.skill / 'references/说明.md').write_text('第二版', encoding='utf-8')
        second = self.commit()
        with self.assertRaises(mod.InstallError):
            self.op(revision=second, apply=True)
        report = self.op('update', second, apply=True)
        backup = Path(report['skills'][0]['backup'])
        self.assertEqual((backup / 'references/说明.md').read_text(encoding='utf-8'), '已提交内容\n')
        self.op('verify', second)
        with self.assertRaises(mod.InstallError):
            self.op('update', self.first, apply=True)
        self.op('verify', second)

    def test_manual_changes_block_update_and_verify(self):
        self.op(apply=True)
        path = self.dest / 'sample-skill/references/说明.md'
        path.write_text('人工修改', encoding='utf-8')
        for command in ('update', 'verify'):
            with self.assertRaises(mod.InstallError):
                self.op(command, apply=True)
        self.assertEqual(path.read_text(encoding='utf-8'), '人工修改')

    def test_extra_file_and_missing_file_detected(self):
        self.op(apply=True)
        extra = self.dest / 'sample-skill/笔记.txt'
        extra.write_text('保留', encoding='utf-8')
        with self.assertRaises(mod.InstallError):
            self.op('verify')
        extra.unlink()
        (self.dest / 'sample-skill/references/说明.md').unlink()
        with self.assertRaises(mod.InstallError):
            self.op('verify')

    def test_unmanaged_same_name_not_overwritten(self):
        target = self.dest / 'sample-skill'
        target.mkdir(parents=True)
        (target / '保留.txt').write_text('人工安装', encoding='utf-8')
        with self.assertRaises(mod.InstallError):
            self.op(apply=True)
        self.assertTrue((target / '保留.txt').exists())

    def test_missing_reference_rejected_without_write(self):
        (self.skill / 'SKILL.md').write_text(
            '---\nname: sample-skill\ndescription: test\n---\n[遗漏](references/missing.md)', encoding='utf-8')
        bad = self.commit()
        with self.assertRaises(mod.InstallError):
            self.op(revision=bad, apply=True)
        self.assertFalse(self.dest.exists())

    def test_refuses_ref_names_and_non_repo_archive(self):
        for revision in ('HEAD', 'not-main', self.first[:8]):
            with self.assertRaises(mod.InstallError):
                self.op(revision=revision)
        with self.assertRaises(mod.InstallError):
            mod.snapshot(self.base, self.first, 'sample-skill')

    def test_receipt_tampering_cannot_bless_modified_file(self):
        self.op(apply=True)
        target = self.dest / 'sample-skill'
        (target / 'SKILL.md').write_text('伪造', encoding='utf-8')
        path = target / mod.RECEIPT
        receipt = json.loads(path.read_text(encoding='utf-8'))
        receipt['files'] = mod.inventory(target)
        path.write_text(json.dumps(receipt), encoding='utf-8')
        with self.assertRaises(mod.InstallError):
            self.op('verify')
        with self.assertRaises(mod.InstallError):
            self.op('update', apply=True)

    def test_git_symlink_rejected_without_following(self):
        process = subprocess.run(['git', '-C', str(self.repo), 'hash-object', '-w', '--stdin'],
                                 input=b'../../outside', stdout=subprocess.PIPE, check=True)
        oid = process.stdout.decode().strip()
        self.git('update-index', '--add', '--cacheinfo', '120000,' + oid + ',sample-skill/link')
        self.git('commit', '-qm', 'symlink fixture')
        with self.assertRaises(mod.InstallError):
            self.op(revision=self.git('rev-parse', 'HEAD'), apply=True)
        self.assertFalse(self.dest.exists())

    def test_destination_junction_or_symlink_rejected(self):
        real = self.base / '真实目录'
        real.mkdir()
        link = self.base / '跳转目录'
        if os.name == 'nt':
            command = "New-Item -ItemType Junction -Path '{}' -Target '{}' | Out-Null".format(
                str(link).replace("'", "''"), str(real).replace("'", "''"))
            result = subprocess.run(['powershell', '-NoProfile', '-Command', command],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode:
                self.skipTest('当前环境不可创建 junction')
        else:
            link.symlink_to(real, target_is_directory=True)
        try:
            with self.assertRaises(mod.InstallError):
                self.op(dest=link / 'skills', apply=True)
            self.assertEqual(list(real.iterdir()), [])
        finally:
            if os.name == 'nt':
                os.rmdir(str(link))
            else:
                link.unlink()


if __name__ == '__main__':
    unittest.main(verbosity=2)
