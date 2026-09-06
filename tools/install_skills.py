#!/usr/bin/env python3
"""从本地 Git 的完整 commit 安装 Skill；默认只预览，--apply 才写入。

install/update/verify --repo REPO --revision FULL_SHA --skill NAME --dest SKILLS
update 只接受原版本的后继提交，旧目录保留在 skills 根旁的备份目录；不覆盖人工改动。
仅用标准库和本机 git，无网络；导出提交中的字节，不包含未提交工作区改动。
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import uuid
from urllib.parse import unquote, urlsplit

RECEIPT = '.skill-install.json'
MAX_BYTES = 32 * 1024 * 1024


class InstallError(Exception):
    pass


def git(repo, *args):
    result = subprocess.run(['git', '-C', str(repo)] + list(args),
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        raise InstallError(result.stderr.decode('utf-8', 'replace').strip())
    return result.stdout


def checked_path(path):
    """拒绝路径任一已有分量的 symlink 或 Windows reparse point（含 junction）。"""
    path = Path(os.path.abspath(str(path)))
    for part in [path] + list(path.parents):
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise InstallError('拒绝符号链接或 junction: ' + str(part))
    return path


def safe_relative(name):
    path = PurePosixPath(name)
    reserved = {'CON', 'PRN', 'AUX', 'NUL'} | {
        prefix + str(i) for prefix in ('COM', 'LPT') for i in range(1, 10)}
    if not name or path.is_absolute() or '\\' in name or str(path) != name:
        raise InstallError('不安全的相对路径: ' + name)
    for part in path.parts:
        if (part in ('.', '..') or part.rstrip(' .') != part or
                re.search(r'[<>:"|?*\x00-\x1f]', part) or
                part.split('.')[0].upper() in reserved):
            raise InstallError('不兼容的文件名: ' + name)
    return path


def check_links(files):
    # 检查 Markdown 显式链接；自然语言/运行时拼接路径不可能静态穷举。
    for name, payload in files.items():
        if not name.lower().endswith('.md'):
            continue
        body = payload.decode('utf-8-sig')
        links = re.findall(r'\]\((<[^>]+>|[^\s)]+)', body)
        links += re.findall(r'^\s*\[[^\]]+\]:\s*(<[^>]+>|\S+)', body, re.M)
        for raw in links:
            link = raw.strip('<>')
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = unquote(parsed.path)
            if target.startswith('/'):
                raise InstallError('Skill 引用了安装目录外的绝对路径: ' + target)
            parts = list(PurePosixPath(name).parent.parts)
            for part in target.split('/'):
                if part == '..':
                    if not parts:
                        raise InstallError('相对引用越出 Skill: ' + target)
                    parts.pop()
                elif part not in ('', '.'):
                    parts.append(part)
            resolved = '/'.join(parts)
            if resolved and resolved not in files and not any(
                    f.startswith(resolved + '/') for f in files):
                raise InstallError('提交中缺少引用资源: {} -> {}'.format(name, target))


def snapshot(repo, revision, skill):
    if not re.fullmatch(r'[0-9a-fA-F]{40}|[0-9a-fA-F]{64}', revision):
        raise InstallError('--revision 必须为完整 commit SHA，不能使用 main/HEAD/短 SHA')
    repo = checked_path(repo)
    root = git(repo, 'rev-parse', '--show-toplevel').decode('utf-8').strip()
    if Path(root).resolve() != repo.resolve():
        raise InstallError('--repo 必须指向 Git 工作区根目录')
    commit = git(repo, 'rev-parse', '--verify', revision + '^{commit}').decode().strip()
    skill_path = safe_relative(skill)
    name = skill_path.name
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', name):
        raise InstallError('Skill 目录名须为小写字母、数字和连字符')
    rows = git(repo, 'ls-tree', '-rz', '-l', commit, '--', skill + '/')
    files, modes, folded, total = {}, {}, set(), 0
    for row in rows.split(b'\0'):
        if not row:
            continue
        meta, path_bytes = row.split(b'\t', 1)
        mode, kind, oid, size = meta.split()
        path = path_bytes.decode('utf-8')
        rel = path[len(skill) + 1:]
        safe_relative(rel)
        if rel.casefold() in folded or rel.casefold() == RECEIPT.casefold():
            raise InstallError('大小写重名或安装记录文件冲突: ' + rel)
        folded.add(rel.casefold())
        if kind != b'blob' or mode not in (b'100644', b'100755'):
            raise InstallError('Skill 不支持 symlink/submodule: ' + path)
        total += int(size)
        if total > MAX_BYTES:
            raise InstallError('单个 Skill 超过 32 MiB，本工具拒绝隐式大包安装')
        files[rel] = git(repo, 'cat-file', 'blob', oid.decode())
        modes[rel] = mode.decode()
    if 'SKILL.md' not in files:
        raise InstallError('该 commit 中不存在 Skill/SKILL.md: ' + skill)
    entry = files['SKILL.md'].decode('utf-8-sig')
    front = re.match(r'^---\s*\n(.*?)\n---(?:\s*\n|$)', entry, re.S)
    if not front or not all(re.search(r'^' + key + r':\s*\S', front[1], re.M)
                            for key in ('name', 'description')):
        raise InstallError('SKILL.md 缺少 name/description YAML frontmatter')
    check_links(files)
    receipt = {'format': 1, 'commit': commit, 'skill': skill,
               'files': {p: hashlib.sha256(b).hexdigest() for p, b in files.items()},
               'modes': modes}
    dirty = git(repo, 'status', '--porcelain', '--untracked-files=normal', '--', skill)
    return files, receipt, bool(dirty)


def inventory(directory):
    directory = checked_path(directory)
    if not directory.is_dir():
        raise InstallError('安装位置不是目录: ' + str(directory))
    files = {}
    for parent, dirs, names in os.walk(str(directory), followlinks=False):
        for name in dirs + names:
            checked_path(Path(parent) / name)
        for name in names:
            path = Path(parent) / name
            if not path.is_file():
                raise InstallError('安装目录包含非普通文件: ' + str(path))
            rel = path.relative_to(directory).as_posix()
            if rel != RECEIPT:
                files[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return files


def installed(directory):
    files = inventory(directory)
    receipt_path = directory / RECEIPT
    if not receipt_path.is_file():
        raise InstallError('已有同名目录但无安装记录，不覆盖: ' + str(directory))
    try:
        receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    except (ValueError, UnicodeError) as exc:
        raise InstallError('安装记录损坏: ' + str(exc))
    if receipt.get('format') != 1 or receipt.get('files') != files:
        raise InstallError('安装内容已修改/缺失/新增；请另选目录或人工处理: ' + str(directory))
    return receipt


def operate(action, repo, revision, skills, dest, apply=False):
    if not skills or len({PurePosixPath(s).name.casefold() for s in skills}) != len(skills):
        raise InstallError('至少选一个 Skill，且安装目录名不能重复')
    dest = checked_path(dest)
    if dest.exists() and not dest.is_dir():
        raise InstallError('目标根不是目录')
    plans = []
    for skill in skills:
        files, receipt, dirty = snapshot(repo, revision, skill)
        target = checked_path(dest / PurePosixPath(skill).name)
        if target.exists():
            old = installed(target)
            if old.get('skill') != skill:
                raise InstallError('同名目录属于另一个 Skill')
            if action == 'install':
                raise InstallError('已安装；更新请显式使用 update')
            if action == 'verify' and old != receipt:
                raise InstallError('安装记录与指定 commit 不一致')
            if action == 'update':
                # 旧安装记录也用 Git 对象复核，不能只信本地 receipt。
                _, trusted_old, _ = snapshot(repo, old.get('commit', ''), skill)
                if old != trusted_old:
                    raise InstallError('旧安装记录与原 commit 不一致')
                git(repo, 'merge-base', '--is-ancestor', old['commit'], receipt['commit'])
        elif action != 'install':
            raise InstallError('未安装: ' + str(target))
        plans.append((target, files, receipt, dirty))
    report = {'action': action, 'applied': bool(apply and action != 'verify'), 'skills': [
        {'target': str(t), 'commit': r['commit'], 'files': len(f),
         'bytes': sum(map(len, f.values())), 'working_tree_ignored': d}
        for t, f, r, d in plans]}
    if not apply or action == 'verify':
        return report
    dest.mkdir(parents=True, exist_ok=True)
    checked_path(dest)
    lock = dest / '.skill-install.lock'
    # 同时安装者不相互覆盖；中断遗留的锁需人工检查后处理。
    try:
        handle = lock.open('x', encoding='utf-8')
    except FileExistsError:
        raise InstallError('安装锁已存在，可能有运行或中断待处理: ' + str(lock))
    try:
        with handle:
            handle.write(str(os.getpid()))
        # 锁内重新核验，避免预览和写入之间的一般并发变化。
        operate(action, repo, revision, skills, dest, apply=False)
        for target, files, receipt, dirty in plans:
            if action == 'update' and installed(target) == receipt:
                report['skills'][skills.index(receipt['skill'])]['unchanged'] = True
                continue
            token = uuid.uuid4().hex
            stage = checked_path(dest / ('.skill-stage-' + token))
            stage.mkdir()
            for name, data in files.items():
                path = stage.joinpath(*PurePosixPath(name).parts)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
                if os.name != 'nt' and receipt['modes'][name] == '100755':
                    path.chmod(0o755)
            (stage / RECEIPT).write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            backup = None
            if action == 'update':
                installed(target)
                # 备份放在 skills 根之外，避免被发现为第二份可用 Skill。
                backups = checked_path(dest.parent / ('.' + dest.name + '-backups'))
                backups.mkdir(exist_ok=True)
                backup = backups / (target.name + '-' + token)
                target.rename(backup)
            try:
                if target.exists():
                    raise InstallError('写入前目标已出现，不覆盖: ' + str(target))
                stage.rename(target)
            except Exception:
                if backup is not None and not target.exists():
                    backup.rename(target)
                raise
            if backup is not None:
                report['skills'][skills.index(receipt['skill'])]['backup'] = str(backup)
    finally:
        lock.unlink()
    return report


def main(argv=None):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['install', 'update', 'verify'])
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--skill', required=True, action='append', dest='skills')
    parser.add_argument('--dest', required=True, type=Path,
                        help='明确的 skills 根目录，例如 项目/.agents/skills 或个人 skills 路径')
    parser.add_argument('--apply', action='store_true', help='写入安装/更新；默认仅检查和预览')
    args = parser.parse_args(argv)
    try:
        report = operate(args.action, args.repo, args.revision, args.skills, args.dest, args.apply)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except (InstallError, OSError, UnicodeError, ValueError) as exc:
        print('失败: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
