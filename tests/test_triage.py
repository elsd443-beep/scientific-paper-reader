"""Run with: python3 -m pytest tests/  (needs pdfplumber + reportlab)."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("reportlab")
pytest.importorskip("pdfplumber")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from make_fixture import build  # noqa: E402


@pytest.fixture(scope="module")
def triage(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("triage")
    pdf = tmp / "paper.pdf"
    build(str(pdf))
    out = tmp / "out"
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "phase1_triage.py"), str(pdf),
         "--output-dir", str(out), "--sections", "methods,results,discussion,conclusions"],
        check=True, capture_output=True, text=True,
    )
    return json.loads((out / "triage_summary.json").read_text()), out


def test_conclusion_found_before_long_reference_list(triage):
    summary, _ = triage
    assert summary["conclusion_source"] == "conclusion_heading"
    assert "cold tolerance" in summary["conclusion"]
    assert "Smith J" not in summary["conclusion"]


def test_vector_only_figure_page_detected(triage):
    summary, _ = triage
    assert 2 in summary["figure_pages"]
    assert 2 in summary["pages_with_vector_graphics"]
    assert any(c["caption"].startswith("Figure 1.") for c in summary["figure_captions"])


def test_reference_pages_not_flagged_as_figures(triage):
    summary, _ = triage
    assert not set(summary["figure_pages"]) & {3, 4, 5, 6}


def test_two_column_text_is_not_interleaved(triage):
    summary, out = triage
    disc = (out / "sections" / "discussion.md").read_text()
    # Discussion lives only in the right column; left-column Results text must not leak in.
    assert "Discussion" in disc
    assert disc.count("Octopods rely") >= 3


def test_section_files_written(triage):
    summary, _ = triage
    written = {s["section"] for s in summary["section_files"]}
    assert {"methods", "results", "conclusions"} <= written
