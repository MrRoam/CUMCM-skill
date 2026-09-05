#!/usr/bin/env python3
"""Run a conservative, reproducible content audit on a CUMCM manuscript."""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET


def read_text(path: Path) -> tuple[str, dict]:
    suffix = path.suffix.lower()
    meta: dict[str, object] = {"file": str(path.resolve()), "type": suffix}
    if suffix in {".md", ".txt", ".tex", ".csv"}:
        for encoding in ("utf-8-sig", "utf-8", "gb18030"):
            try:
                return path.read_text(encoding=encoding), meta
            except UnicodeDecodeError:
                continue
        raise ValueError("Unable to decode text file")
    if suffix == ".docx":
        with zipfile.ZipFile(path) as archive:
            root = ET.fromstring(archive.read("word/document.xml"))
        namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        paragraphs = []
        for paragraph in root.findall(".//w:p", namespace):
            value = "".join(node.text or "" for node in paragraph.findall(".//w:t", namespace)).strip()
            if value:
                paragraphs.append(value)
        meta["paragraphs_extracted"] = len(paragraphs)
        return "\n\n".join(paragraphs), meta
    if suffix == ".pdf":
        try:
            import fitz  # type: ignore
            with fitz.open(path) as document:
                pages = [page.get_text("text") for page in document]
                meta["pages"] = len(document)
            meta["pdf_extractor"] = "PyMuPDF"
        except ImportError:
            try:
                from pypdf import PdfReader  # type: ignore
            except ImportError as exc:
                raise RuntimeError("PDF extraction requires PyMuPDF or pypdf") from exc
            reader = PdfReader(path)
            pages = [page.extract_text() or "" for page in reader.pages]
            meta["pages"] = len(reader.pages)
            meta["pdf_extractor"] = "pypdf"
        meta["first_page_text"] = pages[0][:5000] if pages else ""
        return "\n\n".join(pages), meta
    raise ValueError(f"Unsupported file type: {suffix}")


def compact(value: str) -> str:
    return re.sub(r"\s+", "", value)


def add(findings: list[dict], category: str, severity: str, message: str, evidence: object = None) -> None:
    finding = {"category": category, "severity": severity, "message": message}
    if evidence not in (None, "", []):
        finding["evidence"] = evidence
    findings.append(finding)


def exact_duplicate_paragraphs(text: str) -> list[dict]:
    paragraphs = [compact(item) for item in re.split(r"\n\s*\n", text)]
    paragraphs = [item for item in paragraphs if len(item) >= 45 and not item.startswith(("#", "|"))]
    counts = Counter(paragraphs)
    return [
        {"count": count, "preview": paragraph[:120]}
        for paragraph, count in counts.most_common()
        if count > 1
    ][:20]


def audit(path: Path, identity_terms: list[str]) -> dict:
    text, meta = read_text(path)
    normalized = compact(text)
    findings: list[dict] = []

    if not re.search(r"摘\s*要", text):
        add(findings, "structure", "manual", "未检出摘要标记；请确认提取或结构。")
    if not re.search(r"关\s*键[词字]", text):
        add(findings, "structure", "manual", "未检出关键词标记。")
    if re.search(r"(^|\n)\s*(目\s*录|contents)\s*($|\n)", text, re.I):
        add(findings, "official_format", "hard_violation", "检出目录标题；2026 全国规范要求正文不要目录。")

    expected_modules = {
        "assumptions": r"假\s*设",
        "symbols": r"符\s*号|变\s*量\s*说\s*明",
        "validation": r"检\s*验|灵\s*敏\s*度|敏\s*感\s*性|稳\s*健\s*性|误\s*差\s*分\s*析",
        "evaluation": r"模型.{0,3}(评价|优点|缺点|推广|改进)",
        "references": r"参\s*考\s*文\s*献",
        "appendix": r"附\s*录",
        "ai_declaration": r"AI\s*工具使用声明|人工智能工具使用声明",
    }
    module_presence = {name: bool(re.search(pattern, text, re.I)) for name, pattern in expected_modules.items()}
    for name in ("validation", "references", "ai_declaration"):
        if not module_presence[name]:
            add(findings, "structure", "manual", f"未检出 {name}；请根据当年规则和论文内容确认。")

    placeholder_patterns = [
        r"TODO", r"TBD", r"待补(?:充|写|算|图)?", r"待核验", r"待确认", r"XX+", r"\?\?+",
        r"【\s*(?:简要用途|待填写|填写|补充|作者确认)[^】]*】",
    ]
    placeholders = []
    for pattern in placeholder_patterns:
        placeholders.extend(match.group(0) for match in re.finditer(pattern, text, re.I))
    if placeholders:
        add(findings, "completeness", "manual", "检出未完成占位符。", sorted(set(placeholders))[:30])

    identity_hits = []
    for term in identity_terms:
        if term and term.lower() in text.lower():
            identity_hits.append(term)
    generic_identity = re.findall(r"[^\n]{0,12}(?:大学|学院|指导教师|参赛队员|姓名|学号)[^\n]{0,24}", text)
    if identity_hits:
        add(findings, "anonymity", "hard_violation", "检出用户指定的身份信息。", identity_hits)
    if generic_identity:
        add(findings, "anonymity", "manual", "检出可能的身份信息；需人工排除正文中的普通语义。", generic_identity[:20])

    duplicates = exact_duplicate_paragraphs(text)
    if duplicates:
        add(findings, "redundancy", "recommended", "检出完全重复的长段落。", duplicates)

    figure_captions = re.findall(r"(?:^|\n)\s*图\s*\d+(?:[-.]\d+)?[^\n]{0,100}", text)
    table_captions = re.findall(r"(?:^|\n)\s*表\s*\d+(?:[-.]\d+)?[^\n]{0,100}", text)
    figure_callouts = re.findall(r"(?:见|如|由)?图\s*\d+(?:[-.]\d+)?", text)
    table_callouts = re.findall(r"(?:见|如|由)?表\s*\d+(?:[-.]\d+)?", text)
    if figure_captions and not figure_callouts:
        add(findings, "cross_reference", "recommended", "检出图题但未稳定检出正文图引用。")
    if table_captions and not table_callouts:
        add(findings, "cross_reference", "recommended", "检出表题但未稳定检出正文表引用。")

    inline_citations = re.findall(r"\[\s*\d+(?:\s*[-,，]\s*\d+)*\s*\]", text)
    reference_entries = re.findall(r"(?:^|\n)\s*\[\s*\d+\s*\]", text)
    if inline_citations and not module_presence["references"]:
        add(findings, "citation", "hard_violation", "检出文内数字引用但未检出参考文献标题。")

    if re.search(r"使用了?AI工具", normalized, re.I) and "AI工具使用详情.pdf" not in text:
        add(findings, "ai_disclosure", "manual", "论文似乎声明使用 AI；请确认支撑材料包含 AI工具使用详情.pdf。")

    severity_counts = Counter(item["severity"] for item in findings)
    return {
        "metadata": meta,
        "summary": {
            "characters_compact": len(normalized),
            "modules": module_presence,
            "figure_captions": len(figure_captions),
            "table_captions": len(table_captions),
            "inline_citations": len(inline_citations),
            "reference_entries": len(reference_entries),
            "finding_counts": dict(severity_counts),
        },
        "findings": findings,
        "limitations": [
            "Text checks cannot prove formula correctness, page geometry, visual readability, or factual validity.",
            "Regex matches may miss variant wording or flag ordinary uses of identity-related words.",
            "Render and visually inspect final PDF pages before delivery.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manuscript", type=Path)
    parser.add_argument("--identity-term", action="append", default=[], help="Exact identity term to flag; repeatable")
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    args = parser.parse_args()
    if not args.manuscript.is_file():
        parser.error(f"File not found: {args.manuscript}")
    result = audit(args.manuscript, args.identity_term)
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    sys.stdout.buffer.write((payload + "\n").encode("utf-8"))
    return 1 if result["summary"]["finding_counts"].get("hard_violation", 0) else 0


if __name__ == "__main__":
    raise SystemExit(main())
