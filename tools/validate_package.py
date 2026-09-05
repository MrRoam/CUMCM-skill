from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents" / "skills" / "cumcm-formatting"


def fail(message: str) -> None:
    raise ValueError(message)


def validate_frontmatter() -> None:
    path = SKILL / "SKILL.md"
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        fail("SKILL.md 缺少有效 YAML frontmatter")
    frontmatter = match.group(1)
    name = re.search(r"(?m)^name:\s*[\"']?([^\n\"']+)", frontmatter)
    description = re.search(r"(?m)^description:\s*(.+)$", frontmatter)
    if not name or name.group(1).strip() != SKILL.name:
        fail("Skill 名称与目录名不一致")
    if not description or len(description.group(1).strip()) < 40:
        fail("Skill description 缺失或过短")


def validate_json() -> None:
    for path in SKILL.rglob("*.json"):
        with path.open("r", encoding="utf-8") as handle:
            json.load(handle)


def validate_python() -> None:
    for path in SKILL.rglob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def validate_markdown_links() -> None:
    pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    missing: list[str] = []
    for path in ROOT.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        for target in pattern.findall(text):
            clean = target.strip().split("#", 1)[0]
            if not clean or re.match(r"^[a-z]+://", clean, re.IGNORECASE):
                continue
            candidate = (path.parent / clean).resolve()
            if not candidate.exists():
                missing.append(f"{path.relative_to(ROOT)} -> {target}")
    if missing:
        fail("发现失效的本地 Markdown 链接:\n" + "\n".join(missing))


def validate_required_files() -> None:
    required = [
        "SKILL.md",
        "agents/openai.yaml",
        "references/official-format.md",
        "references/writing-and-review.md",
        "references/assumptions-and-validation.md",
        "references/visuals.md",
        "references/evidence-boundaries.md",
        "references/workflow-and-routing.md",
        "scripts/audit_manuscript.py",
        "scripts/audit_submission.py",
        "assets/visual-style-tokens.json",
        "evals/evals.json",
    ]
    missing = [item for item in required if not (SKILL / item).is_file()]
    if missing:
        fail("缺少必要文件: " + ", ".join(missing))


def validate_placeholders() -> None:
    patterns = ("TODO", "TBD", "PLACEHOLDER", "REPLACE_ME")
    findings: list[str] = []
    for path in SKILL.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".md", ".yaml", ".json"}:
            continue
        text = path.read_text(encoding="utf-8")
        for marker in patterns:
            if marker in text:
                findings.append(f"{path.relative_to(ROOT)}: {marker}")
    if findings:
        fail("发现未完成占位符:\n" + "\n".join(findings))


def main() -> int:
    checks = (
        validate_required_files,
        validate_frontmatter,
        validate_json,
        validate_python,
        validate_markdown_links,
        validate_placeholders,
    )
    try:
        for check in checks:
            check()
    except (OSError, SyntaxError, ValueError, json.JSONDecodeError) as exc:
        print(f"VALIDATION FAILED: {exc}", file=sys.stderr)
        return 1
    count = sum(1 for path in SKILL.rglob("*") if path.is_file())
    print(f"VALIDATION PASSED: cumcm-formatting ({count} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
