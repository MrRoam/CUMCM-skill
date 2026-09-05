#!/usr/bin/env python3
"""Audit basic CUMCM electronic-paper and support-archive invariants."""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


LIMIT = 20 * 1024 * 1024
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def finding(items: list[dict], check: str, status: str, detail: str, evidence: object = None) -> None:
    item = {"check": check, "status": status, "detail": detail}
    if evidence not in (None, "", []):
        item["evidence"] = evidence
    items.append(item)


def pdf_metadata(path: Path) -> dict:
    try:
        import fitz  # type: ignore
        with fitz.open(path) as document:
            pages = [page.get_text("text") for page in document]
            count = len(document)
        extractor = "PyMuPDF"
    except ImportError:
        try:
            from pypdf import PdfReader  # type: ignore
        except ImportError as exc:
            raise RuntimeError("PDF checks require PyMuPDF or pypdf") from exc
        reader = PdfReader(path)
        pages = [page.extract_text() or "" for page in reader.pages]
        count = len(reader.pages)
        extractor = "pypdf"
    return {
        "pages": count,
        "first_page": pages[0] if pages else "",
        "text": "\n".join(pages),
        "extractor": extractor,
    }


def docx_metadata(path: Path) -> dict:
    namespace = {"w": W_NS}
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    text = "\n".join(
        "".join(node.text or "" for node in paragraph.findall(".//w:t", namespace))
        for paragraph in root.findall(".//w:p", namespace)
    )
    sections = []
    for section in root.findall(".//w:sectPr", namespace):
        size = section.find("w:pgSz", namespace)
        margin = section.find("w:pgMar", namespace)
        sections.append(
            {
                "width_twips": int(size.get(f"{{{W_NS}}}w", "0")) if size is not None else None,
                "height_twips": int(size.get(f"{{{W_NS}}}h", "0")) if size is not None else None,
                "margins_twips": {
                    key: int(margin.get(f"{{{W_NS}}}{key}", "0")) if margin is not None else None
                    for key in ("top", "right", "bottom", "left")
                },
            }
        )
    return {"text": text, "first_page": text[:5000], "sections": sections}


def inspect_archive(path: Path, identity_terms: list[str]) -> dict:
    result: dict[str, object] = {"file": str(path.resolve()), "size_bytes": path.stat().st_size}
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
        result["entries"] = names
        result["identity_filename_hits"] = [
            name for name in names if any(term.lower() in name.lower() for term in identity_terms if term)
        ]
        result["has_ai_details_pdf"] = any(Path(name).name == "AI工具使用详情.pdf" for name in names)
    else:
        result["entries"] = None
        result["has_ai_details_pdf"] = None
    return result


def audit(paper: Path, support: Path | None, identity_terms: list[str]) -> dict:
    findings: list[dict] = []
    suffix = paper.suffix.lower()
    finding(findings, "paper_format", "pass" if suffix in {".pdf", ".docx"} else "fail", "电子论文应为单独的 PDF 或 Word 文件。", suffix)
    finding(findings, "paper_size", "pass" if paper.stat().st_size <= LIMIT else "fail", "电子论文不得超过 20 MB。", paper.stat().st_size)

    meta: dict = {}
    if suffix == ".pdf":
        meta = pdf_metadata(paper)
    elif suffix == ".docx":
        meta = docx_metadata(paper)

    first_page = str(meta.get("first_page", ""))
    all_text = str(meta.get("text", ""))
    if meta:
        finding(findings, "electronic_first_page", "fail" if re.search(r"承诺书|编号专用页", first_page) else "pass", "电子版第一页不得包含承诺书或编号专用页。")
        finding(findings, "abstract_first_page", "pass" if re.search(r"摘\s*要", first_page) else "manual", "电子版第一页应为摘要专用页。")
        finding(findings, "no_toc", "fail" if re.search(r"(^|\n)\s*目\s*录\s*($|\n)", all_text) else "pass", "正文不得设置目录。")

    if suffix == ".docx":
        for index, section in enumerate(meta.get("sections", []), start=1):
            width = section.get("width_twips")
            height = section.get("height_twips")
            a4 = width is not None and height is not None and abs(min(width, height) - 11906) <= 120 and abs(max(width, height) - 16838) <= 120
            finding(findings, f"section_{index}_a4", "pass" if a4 else "manual", "页面应为 A4；横向 A4 也允许，但需人工确认用途。", {"width": width, "height": height})
            margins = section.get("margins_twips", {})
            too_small = [key for key, value in margins.items() if value is not None and value < 1417]
            finding(findings, f"section_{index}_margins", "fail" if too_small else "pass", "四边页边距均应至少 2.5 cm。", margins)

    identity_hits = [term for term in identity_terms if term and term.lower() in all_text.lower()]
    if identity_hits:
        finding(findings, "paper_anonymity", "fail", "论文中检出用户指定身份词。", identity_hits)
    else:
        finding(findings, "paper_anonymity", "manual", "需继续检查图片、元数据、路径、代码注释和未提供的身份词。")

    archive_meta = None
    if support:
        archive_meta = inspect_archive(support, identity_terms)
        finding(findings, "support_format", "pass" if support.suffix.lower() in {".zip", ".rar"} else "fail", "支撑材料应为一个 ZIP 或 RAR。", support.suffix.lower())
        finding(findings, "support_size", "pass" if support.stat().st_size <= LIMIT else "fail", "支撑材料不得超过 20 MB。", support.stat().st_size)
        if archive_meta.get("identity_filename_hits"):
            finding(findings, "support_anonymity", "fail", "支撑材料文件名检出身份词。", archive_meta["identity_filename_hits"])
        if re.search(r"使用了?AI工具", re.sub(r"\s+", "", all_text), re.I):
            has_details = archive_meta.get("has_ai_details_pdf")
            finding(findings, "ai_details", "pass" if has_details is True else "manual", "使用 AI 时支撑材料应包含 AI工具使用详情.pdf。", has_details)
    else:
        finding(findings, "support_material", "manual", "未提供支撑材料；如确实没有，附录须写明“本论文没有支撑材料”。")

    if all_text:
        finding(findings, "appendix_file_list", "manual", "需将附录文件清单与实际支撑材料逐项比对。")
        finding(findings, "body_page_limit", "manual", "正文不超过 30 页；附录不限页。自动脚本不能可靠判定所有变体的正文边界。", meta.get("pages"))
        finding(findings, "render_review", "manual", "仍需逐页渲染检查页码、溢出、乱码、缺图、题注分离及灰度可读性。")

    statuses = {status: sum(item["status"] == status for item in findings) for status in ("pass", "fail", "manual")}
    return {
        "paper": str(paper.resolve()),
        "support": str(support.resolve()) if support else None,
        "paper_metadata": {key: value for key, value in meta.items() if key not in {"text", "first_page"}},
        "support_metadata": archive_meta,
        "status_counts": statuses,
        "findings": findings,
        "rules_version": "CUMCM national 2026 baseline; recheck current national/regional/school notices",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paper", type=Path)
    parser.add_argument("--support", type=Path)
    parser.add_argument("--identity-term", action="append", default=[])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.paper.is_file():
        parser.error(f"Paper not found: {args.paper}")
    if args.support and not args.support.is_file():
        parser.error(f"Support archive not found: {args.support}")
    result = audit(args.paper, args.support, args.identity_term)
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    sys.stdout.buffer.write((payload + "\n").encode("utf-8"))
    return 1 if result["status_counts"]["fail"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
