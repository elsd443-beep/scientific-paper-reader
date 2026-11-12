#!/usr/bin/env python3
"""
Phase 1 Token-Efficient Triage Script for Scientific Papers.

Extracts ONLY the high-signal structural elements needed for Phase 1:
1. Title & Metadata (first page top lines)
2. Abstract
3. Section Headings (IMRAD skeleton)
4. Conclusion / Summary section
5. Figure & Table Captions (e.g., "Figure 1:", "Fig. 1.", "Table 1:")
6. Parsed Markdown Tables (via pdfplumber, zero vision tokens)
7. Selective low-DPI page rendering ONLY for pages with figures (--render-figures)

Usage:
  python3 scripts/phase1_triage.py paper.pdf --output-dir ./triage_out
  python3 scripts/phase1_triage.py paper.pdf --output-dir ./triage_out --render-figures --dpi 120
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


def extract_text_pages(pdf_path: str):
    """Extract text and tables per page using pdfplumber (with pypdf fallback)."""
    pages_data = []
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            for idx, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                raw_tables = page.extract_tables() or []
                md_tables = []
                for tbl in raw_tables:
                    cleaned = [
                        [(cell or "").replace("\n", " ").strip() for cell in row]
                        for row in tbl
                        if row and any(cell and str(cell).strip() for cell in row)
                    ]
                    if len(cleaned) >= 2:
                        header = "| " + " | ".join(cleaned[0]) + " |"
                        sep = "| " + " | ".join(["---"] * len(cleaned[0])) + " |"
                        body = "\n".join(
                            "| " + " | ".join(r[: len(cleaned[0])]) + " |"
                            for r in cleaned[1:15]
                        )
                        md_tables.append(f"{header}\n{sep}\n{body}")
                has_images = bool(getattr(page, "images", []))
                pages_data.append(
                    {
                        "page": idx,
                        "text": text,
                        "tables_markdown": md_tables,
                        "image_count": len(getattr(page, "images", [])),
                        "has_images": has_images,
                    }
                )
        return pages_data
    except ImportError:
        pass

    from pypdf import PdfReader
    reader = PdfReader(pdf_path)
    for idx, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages_data.append(
            {
                "page": idx,
                "text": text,
                "tables_markdown": [],
                "image_count": len(getattr(page, "images", [])),
                "has_images": bool(getattr(page, "images", [])),
            }
        )
    return pages_data


def parse_phase1_elements(pages_data):
    """Extract Title, Abstract, Headings, Captions, and Conclusions with minimal tokens."""
    full_text_by_page = {p["page"]: p["text"] for p in pages_data}
    first_page_lines = [
        line.strip()
        for line in pages_data[0]["text"].splitlines()
        if line.strip()
    ] if pages_data else []

    title_candidates = first_page_lines[:8]

    # Extract Abstract
    first_two_pages = "\n".join(p["text"] for p in pages_data[:2])
    abstract_match = re.search(
        r"(?is)\b(?:abstract|summary)\b[:\s\n]*(.+?)(?=\n\s*(?:1\.?\s+)?(?:introduction|background|keywords|key\s+words)\b)",
        first_two_pages,
    )
    abstract_text = (
        abstract_match.group(1).strip()
        if abstract_match
        else "\n".join(first_page_lines[:25])
    )

    # Extract Conclusion (typically on last 2-3 pages)
    last_pages_text = "\n".join(p["text"] for p in pages_data[-3:])
    conclusion_match = re.search(
        r"(?is)\b(?:conclusions?|summary|concluding\s+remarks)\b[:\s\n]*(.+?)(?=\n\s*(?:references|bibliography|acknowledg(?:e)?ments|funding|conflict\s+of\s+interest)\b|$)",
        last_pages_text,
    )
    conclusion_text = (
        conclusion_match.group(1).strip()[:2000]
        if conclusion_match
        else last_pages_text[-1500:].strip()
    )

    # Extract Section Headings, Figure Captions, and Table Captions
    headings = []
    figure_captions = []
    table_captions = []
    figure_pages = set()
    table_pages = set()

    heading_pattern = re.compile(
        r"^(?:[1-9](?:\.[0-9]+)*\.?\s+)?(?:ABSTRACT|INTRODUCTION|BACKGROUND|MATERIALS\s+AND\s+METHODS|METHODS|METHODOLOGY|EXPERIMENTAL|RESULTS|DISCUSSION|RESULTS\s+AND\s+DISCUSSION|CONCLUSIONS?|LIMITATIONS|REFERENCES)\b.*",
        re.IGNORECASE,
    )
    fig_pattern = re.compile(
        r"^(?:Figure|Fig\.?|Scheme)\s*\d+[A-Za-z0-9\-]*[\.:\s].+",
        re.IGNORECASE,
    )
    tbl_pattern = re.compile(
        r"^(?:Table|Tbl\.?)\s*\d+[A-Za-z0-9\-]*[\.:\s].+",
        re.IGNORECASE,
    )

    for p in pages_data:
        pno = p["page"]
        lines = [line.strip() for line in p["text"].splitlines() if line.strip()]
        for i, line in enumerate(lines):
            if len(line) < 90 and heading_pattern.match(line):
                headings.append({"page": pno, "heading": line})
            if fig_pattern.match(line):
                caption_block = " ".join(lines[i : min(i + 4, len(lines))])
                figure_captions.append({"page": pno, "caption": caption_block[:500]})
                figure_pages.add(pno)
            if tbl_pattern.match(line):
                caption_block = " ".join(lines[i : min(i + 3, len(lines))])
                table_captions.append({"page": pno, "caption": caption_block[:500]})
                table_pages.add(pno)
        if p["has_images"]:
            figure_pages.add(pno)
        if p["tables_markdown"]:
            table_pages.add(pno)

    extracted_tables = [
        {"page": p["page"], "tables": p["tables_markdown"]}
        for p in pages_data
        if p["tables_markdown"]
    ]

    return {
        "total_pages": len(pages_data),
        "title_header_lines": title_candidates,
        "abstract": abstract_text[:2500],
        "section_headings": headings,
        "figure_captions": figure_captions,
        "table_captions": table_captions,
        "extracted_markdown_tables": extracted_tables,
        "figure_pages": sorted(figure_pages),
        "table_pages": sorted(table_pages),
        "conclusion": conclusion_text,
    }


def render_selected_pages(pdf_path: str, pages_to_render, out_dir: Path, dpi: int = 120):
    """Render ONLY specific figure pages at low DPI to save vision tokens."""
    rendered_files = []
    if not pages_to_render:
        return rendered_files

    try:
        import pypdfium2 as pdfium
        doc = pdfium.PdfDocument(pdf_path)
        scale = dpi / 72.0
        for pno in pages_to_render:
            if 1 <= pno <= len(doc):
                page = doc[pno - 1]
                bitmap = page.render(scale=scale)
                pil_image = bitmap.to_pil()
                out_file = out_dir / f"figure_page_{pno:02d}.png"
                pil_image.save(out_file, optimize=True)
                rendered_files.append(str(out_file.resolve()))
        return rendered_files
    except ImportError:
        pass

    try:
        from pdf2image import convert_from_path
        for pno in pages_to_render:
            imgs = convert_from_path(
                pdf_path, dpi=dpi, first_page=pno, last_page=pno
            )
            if imgs:
                out_file = out_dir / f"figure_page_{pno:02d}.png"
                imgs[0].save(out_file, optimize=True)
                rendered_files.append(str(out_file.resolve()))
    except Exception as exc:
        print(f"Warning: could not render figure pages: {exc}", file=sys.stderr)

    return rendered_files


def main():
    parser = argparse.ArgumentParser(
        description="Token-efficient Phase 1 triage for scientific PDFs."
    )
    parser.add_argument("pdf_path", help="Path to the scientific article PDF")
    parser.add_argument(
        "--output-dir",
        default="./triage_out",
        help="Directory to write triage_summary.json and optional figure renders",
    )
    parser.add_argument(
        "--render-figures",
        action="store_true",
        help="Render only pages containing figures at low DPI",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=120,
        help="DPI for selective figure page rendering (default: 120)",
    )
    parser.add_argument(
        "--pages",
        type=str,
        default="",
        help="Comma-separated page numbers to render (overrides auto-detected figure pages)",
    )
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    pages_data = extract_text_pages(args.pdf_path)
    summary = parse_phase1_elements(pages_data)

    if args.render_figures:
        if args.pages.strip():
            target_pages = [
                int(x.strip()) for x in args.pages.split(",") if x.strip().isdigit()
            ]
        else:
            target_pages = summary["figure_pages"]
        summary["rendered_figure_files"] = render_selected_pages(
            args.pdf_path, target_pages, out_dir, dpi=args.dpi
        )
    else:
        summary["rendered_figure_files"] = []

    json_path = out_dir / "triage_summary.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"Phase 1 triage saved to: {json_path.resolve()}")
    print(f"Total pages: {summary['total_pages']}")
    print(f"Detected figure pages: {summary['figure_pages']}")
    print(f"Detected table pages: {summary['table_pages']}")
    print(f"Figure captions found: {len(summary['figure_captions'])}")
    print(f"Table captions found: {len(summary['table_captions'])}")
    if summary["rendered_figure_files"]:
        print("Rendered figure pages:")
        for rf in summary["rendered_figure_files"]:
            print(f"  - {rf}")


if __name__ == "__main__":
    main()
