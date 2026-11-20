#!/usr/bin/env python3
"""
Phase 1 Token-Efficient Triage Script for Scientific Papers.

Extracts ONLY the high-signal structural elements needed for Phase 1:
1. Title & Metadata (first page top lines)
2. Abstract
3. Section Headings (IMRAD skeleton)
4. Conclusion section (searched across the whole paper, not just the last pages)
5. Figure & Table Captions (e.g., "Figure 1:", "Fig. 1.", "Table 1:")
6. Parsed Markdown Tables (via pdfplumber, zero vision tokens)
7. Figure-page detection for embedded images AND vector graphics (most charts)
8. Selective low-DPI page rendering ONLY for pages with figures (--render-figures)
9. Optional per-section text files for a targeted Phase 2 read (--sections)

Two-column layouts are detected per page and read column by column so that
captions and headings are not interleaved across columns.

Usage:
  python3 scripts/phase1_triage.py paper.pdf --output-dir ./triage_out
  python3 scripts/phase1_triage.py paper.pdf --output-dir ./triage_out --render-figures --dpi 120
  python3 scripts/phase1_triage.py paper.pdf --output-dir ./triage_out --sections methods,results
  python3 scripts/phase1_triage.py paper.pdf --output-dir ./triage_out --sections all
"""

import argparse
import json
import re
import sys
from pathlib import Path

# A page is treated as containing a figure when it has at least this many
# vector drawing objects (curves + rectangles). Plain text pages and simple
# table rules usually stay well below this; plotted charts exceed it easily.
VECTOR_FIGURE_THRESHOLD = 25

# Canonical section names -> heading regex (matched against a whole, short line).
SECTION_PATTERNS = [
    ("abstract", r"abstract|summary"),
    ("introduction", r"introduction|background"),
    ("methods", r"materials\s+and\s+methods|methods?|methodology|experimental(?:\s+procedures)?|study\s+design"),
    ("results", r"results(?:\s+and\s+discussion)?"),
    ("discussion", r"discussion"),
    ("conclusions", r"conclusions?|concluding\s+remarks"),
    ("limitations", r"limitations"),
    ("acknowledgements", r"acknowledg(?:e)?ments?"),
    ("references", r"references|bibliography|literature\s+cited"),
    ("other", r"funding|declarations|author\s+contributions|competing\s+interests|conflicts?\s+of\s+interest|data\s+availability|additional\s+files?|supplementary\s+(?:material|information)"),
]
_NUM_PREFIX = r"(?:[1-9]\d?(?:\.\d+)*\.?\s+|[IVX]+\.\s+)?"
HEADING_LINE = re.compile(
    r"^\s*" + _NUM_PREFIX + r"(" + "|".join(p for _, p in SECTION_PATTERNS) + r")\s*:?\s*$",
    re.IGNORECASE,
)


def _section_name(heading_text: str) -> str:
    text = re.sub(r"^\s*" + _NUM_PREFIX, "", heading_text).strip().rstrip(":").strip()
    for name, pat in SECTION_PATTERNS:
        if re.fullmatch(pat, text, re.IGNORECASE):
            return name
    return "other"


def _page_text_by_columns(page) -> str:
    """Read a pdfplumber page column by column when it looks two-column."""
    width = float(page.width)
    try:
        words = page.extract_words(keep_blank_chars=False, use_text_flow=False)
    except Exception:
        words = []
    if len(words) >= 60:
        mid = width / 2.0
        gutter_lo, gutter_hi = mid - width * 0.04, mid + width * 0.04
        crossing = sum(1 for w in words if w["x0"] < gutter_lo and w["x1"] > gutter_hi)
        left = sum(1 for w in words if w["x1"] <= mid)
        right = sum(1 for w in words if w["x0"] >= mid)
        # Two columns: few words span the gutter and both halves carry text.
        if crossing <= len(words) * 0.08 and left >= len(words) * 0.25 and right >= len(words) * 0.25:
            height = float(page.height)
            # Full-width block at the top (title, authors, single-column abstract) is read
            # first; everything below it is read left column, then right column.
            spanning_bottoms = [
                w["bottom"] for w in words
                if w["x0"] < gutter_lo and w["x1"] > gutter_hi and w["bottom"] < height * 0.45
            ]
            header_bottom = max(spanning_bottoms) + 1 if spanning_bottoms else 0
            parts = []
            if header_bottom:
                parts.append(page.crop((0, 0, width, header_bottom)).extract_text() or "")
            parts.append(page.crop((0, header_bottom, mid, height)).extract_text() or "")
            parts.append(page.crop((mid, header_bottom, width, height)).extract_text() or "")
            return "\n".join(p for p in parts if p)
    return page.extract_text() or ""


def extract_text_pages(pdf_path: str):
    """Extract text, tables and figure signals per page (pdfplumber, pypdf fallback)."""
    pages_data = []
    try:
        import pdfplumber
    except ImportError:
        pdfplumber = None

    if pdfplumber is not None:
        with pdfplumber.open(pdf_path) as pdf:
            for idx, page in enumerate(pdf.pages, start=1):
                text = _page_text_by_columns(page)
                try:
                    raw_tables = page.extract_tables() or []
                except Exception:
                    raw_tables = []
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
                image_count = len(getattr(page, "images", []) or [])
                vector_count = len(getattr(page, "curves", []) or []) + len(getattr(page, "rects", []) or [])
                pages_data.append(
                    {
                        "page": idx,
                        "text": text,
                        "tables_markdown": md_tables,
                        "image_count": image_count,
                        "vector_object_count": vector_count,
                        "has_images": image_count > 0 or vector_count >= VECTOR_FIGURE_THRESHOLD,
                    }
                )
        return pages_data

    from pypdf import PdfReader
    reader = PdfReader(pdf_path)
    for idx, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        try:
            image_count = len(page.images)
        except Exception:
            image_count = 0
        pages_data.append(
            {
                "page": idx,
                "text": text,
                "tables_markdown": [],
                "image_count": image_count,
                "vector_object_count": None,
                "has_images": image_count > 0,
            }
        )
    return pages_data


def find_headings(full_lines):
    """Return [(line_index, heading_text, section_name)] for standalone heading lines."""
    found = []
    for i, line in enumerate(full_lines):
        s = line.strip()
        if 0 < len(s) < 60 and HEADING_LINE.match(s):
            found.append((i, s, _section_name(s)))
    return found


def split_sections(full_lines, headings):
    """Split the paper into sections keyed by canonical name (first body occurrence wins,
    later occurrences of the same name are appended)."""
    sections = {}
    for n, (i, heading, name) in enumerate(headings):
        end = headings[n + 1][0] if n + 1 < len(headings) else len(full_lines)
        body = "\n".join(full_lines[i + 1:end]).strip()
        if not body:
            continue
        sections.setdefault(name, [])
        sections[name].append({"heading": heading, "line": i, "text": body})
    return sections


def extract_conclusion(full_lines, headings):
    """Conclusion = LAST conclusion heading before the reference list, up to the next heading.
    Falls back to the end of the Discussion, then to the old last-pages heuristic."""
    ref_lines = [i for i, _, name in headings if name == "references"]
    ref_start = ref_lines[-1] if ref_lines else len(full_lines)
    concl = [(n, i) for n, (i, _, name) in enumerate(headings) if name == "conclusions" and i < ref_start]
    if concl:
        n, i = concl[-1]
        end = headings[n + 1][0] if n + 1 < len(headings) else ref_start
        text = "\n".join(full_lines[i + 1:min(end, ref_start)]).strip()
        if len(text) > 40:
            return text[:2000], "conclusion_heading"
    disc = [(n, i) for n, (i, _, name) in enumerate(headings) if name == "discussion" and i < ref_start]
    if disc:
        n, i = disc[-1]
        end = headings[n + 1][0] if n + 1 < len(headings) else ref_start
        text = "\n".join(full_lines[i + 1:min(end, ref_start)]).strip()
        if text:
            return text[-1500:], "end_of_discussion"
    body = "\n".join(full_lines[:ref_start]).strip()
    return body[-1500:], "end_of_body_text"


def parse_phase1_elements(pages_data):
    """Extract Title, Abstract, Headings, Captions, and Conclusions with minimal tokens."""
    first_page_lines = [
        line.strip()
        for line in pages_data[0]["text"].splitlines()
        if line.strip()
    ] if pages_data else []

    title_candidates = first_page_lines[:8]

    # Abstract (first two pages)
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

    # Whole-paper line index (with page map) for headings, sections and conclusion
    full_lines, line_page = [], []
    for p in pages_data:
        for line in p["text"].splitlines():
            full_lines.append(line)
            line_page.append(p["page"])
    headings = find_headings(full_lines)
    conclusion_text, conclusion_source = extract_conclusion(full_lines, headings)

    figure_captions, table_captions = [], []
    figure_pages, table_pages = set(), set()
    fig_pattern = re.compile(r"^(?:Figure|Fig\.?|Scheme)\s*\d+[A-Za-z0-9\-]*[\.:\s].+", re.IGNORECASE)
    tbl_pattern = re.compile(r"^(?:Table|Tbl\.?)\s*\d+[A-Za-z0-9\-]*[\.:\s].+", re.IGNORECASE)

    for p in pages_data:
        pno = p["page"]
        lines = [line.strip() for line in p["text"].splitlines() if line.strip()]
        for i, line in enumerate(lines):
            if fig_pattern.match(line):
                caption_block = " ".join(lines[i: min(i + 4, len(lines))])
                figure_captions.append({"page": pno, "caption": caption_block[:500]})
                figure_pages.add(pno)
            if tbl_pattern.match(line):
                caption_block = " ".join(lines[i: min(i + 3, len(lines))])
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
        "section_headings": [
            {"page": line_page[i], "heading": h, "section": name} for i, h, name in headings
        ],
        "figure_captions": figure_captions,
        "table_captions": table_captions,
        "extracted_markdown_tables": extracted_tables,
        "figure_pages": sorted(figure_pages),
        "table_pages": sorted(table_pages),
        "pages_with_vector_graphics": [
            p["page"] for p in pages_data
            if (p.get("vector_object_count") or 0) >= VECTOR_FIGURE_THRESHOLD
        ],
        "conclusion": conclusion_text,
        "conclusion_source": conclusion_source,
        "_full_lines": full_lines,
        "_headings": headings,
    }


def write_sections(summary, out_dir: Path, wanted: str):
    """Write one Markdown file per requested section for a targeted Phase 2 read."""
    sections = split_sections(summary["_full_lines"], summary["_headings"])
    names = list(sections.keys()) if wanted.strip().lower() == "all" else [
        x.strip().lower() for x in wanted.split(",") if x.strip()
    ]
    sec_dir = out_dir / "sections"
    sec_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name in names:
        if name not in sections:
            continue
        # Skip the structured-abstract copies of a heading (e.g. "Results" inside the
        # abstract) by preferring the longest occurrence as the real body section.
        parts = sorted(sections[name], key=lambda s: len(s["text"]), reverse=True)
        body = parts[0]["text"]
        path = sec_dir / f"{name}.md"
        path.write_text(f"# {parts[0]['heading']}\n\n{body}\n", encoding="utf-8")
        written.append({"section": name, "file": str(path.resolve()), "chars": len(body)})
    missing = [n for n in names if n not in sections]
    return written, missing, sorted(sections.keys())


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
            imgs = convert_from_path(pdf_path, dpi=dpi, first_page=pno, last_page=pno)
            if imgs:
                out_file = out_dir / f"figure_page_{pno:02d}.png"
                imgs[0].save(out_file, optimize=True)
                rendered_files.append(str(out_file.resolve()))
    except Exception as exc:
        print(f"Warning: could not render figure pages: {exc}", file=sys.stderr)

    return rendered_files


def main():
    parser = argparse.ArgumentParser(description="Token-efficient Phase 1 triage for scientific PDFs.")
    parser.add_argument("pdf_path", help="Path to the scientific article PDF")
    parser.add_argument("--output-dir", default="./triage_out",
                        help="Directory to write triage_summary.json and optional figure renders")
    parser.add_argument("--render-figures", action="store_true",
                        help="Render only pages containing figures at low DPI")
    parser.add_argument("--dpi", type=int, default=120,
                        help="DPI for selective figure page rendering (default: 120)")
    parser.add_argument("--pages", type=str, default="",
                        help="Comma-separated page numbers to render (overrides auto-detected figure pages)")
    parser.add_argument("--sections", type=str, default="",
                        help="Write section text files for Phase 2, e.g. 'methods,results' or 'all'")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    pages_data = extract_text_pages(args.pdf_path)
    summary = parse_phase1_elements(pages_data)

    if args.render_figures:
        if args.pages.strip():
            target_pages = [int(x.strip()) for x in args.pages.split(",") if x.strip().isdigit()]
        else:
            target_pages = summary["figure_pages"]
        summary["rendered_figure_files"] = render_selected_pages(args.pdf_path, target_pages, out_dir, dpi=args.dpi)
    else:
        summary["rendered_figure_files"] = []

    if args.sections.strip():
        written, missing, available = write_sections(summary, out_dir, args.sections)
        summary["section_files"] = written
        summary["sections_missing"] = missing
        summary["sections_available"] = available
    summary.pop("_full_lines", None)
    summary.pop("_headings", None)

    json_path = out_dir / "triage_summary.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"Phase 1 triage saved to: {json_path.resolve()}")
    print(f"Total pages: {summary['total_pages']}")
    print(f"Detected figure pages: {summary['figure_pages']}")
    print(f"Detected table pages: {summary['table_pages']}")
    print(f"Figure captions found: {len(summary['figure_captions'])}")
    print(f"Table captions found: {len(summary['table_captions'])}")
    print(f"Conclusion source: {summary['conclusion_source']}")
    if summary["rendered_figure_files"]:
        print("Rendered figure pages:")
        for rf in summary["rendered_figure_files"]:
            print(f"  - {rf}")
    if summary.get("section_files"):
        print("Section files:")
        for s in summary["section_files"]:
            print(f"  - {s['section']}: {s['file']} ({s['chars']} chars)")
    if summary.get("sections_missing"):
        print(f"Sections not found: {summary['sections_missing']} (available: {summary['sections_available']})")


if __name__ == "__main__":
    main()
