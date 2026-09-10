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


def read_pdf_pages(path: Path) -> tuple[list[str], str]:
    try:
        import fitz  # type: ignore
        with fitz.open(path) as document:
            return [page.get_text("text") for page in document], "PyMuPDF"
    except ImportError:
        try:
            from pypdf import PdfReader  # type: ignore
        except ImportError as exc:
            raise RuntimeError("PDF extraction requires PyMuPDF or pypdf") from exc
        return [page.extract_text() or "" for page in PdfReader(path).pages], "pypdf"


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
        pages, meta["pdf_extractor"] = read_pdf_pages(path)
        meta["pages"] = len(pages)
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


def audit(path: Path, identity_terms: list[str], *, full_draft: bool = False,
          body_start_page: int | None = None, body_end_page: int | None = None,
          target_body_pages: tuple[int, int] | None = None) -> dict:
    if (body_start_page is None) != (body_end_page is None):
        raise ValueError("Provide both body-start-page and body-end-page.")
    if body_start_page is not None:
        if path.suffix.lower() != ".pdf":
            raise ValueError("Physical body-page ranges require a rendered PDF.")
        if body_start_page < 1 or body_end_page < body_start_page:
            raise ValueError("Body pages must be positive, inclusive and ordered.")
    if target_body_pages is not None:
        if len(target_body_pages) != 2 or target_body_pages[0] < 1 or target_body_pages[1] < target_body_pages[0]:
            raise ValueError("Target body range must have two positive ordered values.")
    text, meta = read_text(path)
    normalized = compact(text)
    findings: list[dict] = []
    length_diagnostics: dict = {}
    if full_draft or body_start_page is not None or target_body_pages is not None:
        length_diagnostics = {
            "target_body_pages": list(target_body_pages) if target_body_pages else None,
            "page_numbering": "one-based physical PDF pages, inclusive",
            "body_pages": None,
            "status": "unmeasured",
        }
        if body_start_page is None:
            add(findings, "draft_length", "manual",
                "未提供已核对的正文页范围；不将PDF总页数当成正文篇幅。")
        else:
            pages, _ = read_pdf_pages(path)
            if body_end_page > len(pages):
                raise ValueError("Body-page range exceeds PDF page count.")
            body = "\n".join(pages[body_start_page - 1:body_end_page])
            count = body_end_page - body_start_page + 1
            length_diagnostics.update({
                "body_start_page": body_start_page,
                "body_end_page": body_end_page,
                "body_pages": count,
                "body_characters_compact": len(compact(body)),
                "body_han_characters": len(re.findall(r"[\u4e00-\u9fff]", body)),
                "status": "measured_without_target",
            })
            if target_body_pages:
                low, high = target_body_pages
                status = "below_target" if count < low else "above_target" if count > high else "within_target"
                length_diagnostics["status"] = status
                if status != "within_target":
                    add(findings, "draft_length", "recommended",
                        "正文篇幅偏离工作目标；检查论证展开、未利用证据及排版。工作目标不是全国硬性规则，不得靠凑页数或缩小字号修复。",
                        {"actual": count, "target": [low, high], "status": status})
        if full_draft:
            add(findings, "draft_depth", "manual",
                "完整成稿仍需逐问检查推导、求解与选择依据、结果解释和验证；结构齐全或页数达标不能证明论证充分。请记录正文位置及未利用证据去向。")

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
        "length_diagnostics": length_diagnostics,
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
    parser.add_argument("--full-draft", action="store_true", help="Request depth and length review diagnostics, not a quality certification")
    parser.add_argument("--body-start-page", type=int, help="Verified first body page, one-based physical PDF page")
    parser.add_argument("--body-end-page", type=int, help="Verified last body page, inclusive; use the planned counting convention")
    parser.add_argument("--target-body-pages", nargs=2, type=int, metavar=("MIN", "MAX"), help="Working body-page range, not an official rule")
    args = parser.parse_args()
    if not args.manuscript.is_file():
        parser.error(f"File not found: {args.manuscript}")
    try:
        result = audit(args.manuscript, args.identity_term, full_draft=args.full_draft,
                       body_start_page=args.body_start_page, body_end_page=args.body_end_page,
                       target_body_pages=tuple(args.target_body_pages) if args.target_body_pages else None)
    except ValueError as exc:
        parser.error(str(exc))
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    sys.stdout.buffer.write((payload + "\n").encode("utf-8"))
    return 1 if result["summary"]["finding_counts"].get("hard_violation", 0) else 0


if __name__ == "__main__":
    raise SystemExit(main())
