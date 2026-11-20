# scientific-paper-reader

Agent Skill for Claude (and usable as instructions in Gemini): a 3-phase scientific paper reading and critical appraisal workflow with token-efficient figure/table triage, plus a **Divulgation mode** that turns a paper into story material for science communication.

## What it does
- **Step 0 - full text first**: PMC full text when available; local PDF otherwise; never bypasses paywalls.
- **Phase 1 - triage** (`scripts/phase1_triage.py`): title, abstract, headings, conclusion, figure/table captions, parsed tables, figure-page detection (embedded images *and* vector charts), optional low-DPI rendering of only the figure pages.
- **Phase 2 - targeted deep read**: `--sections methods,results,...` writes one file per section so only what is needed gets read.
- **Phase 3 - critical reconstruction**: validity, statistics, limitations and research gaps (`references/appraisal-checklists.md`, `assets/study-note-template.md`).
- **Divulgation mode**: hook number with its assumptions, problem, solutions and their cost, comparison, open questions, figure worth recreating, and a do-not-say list (`assets/divulgation-brief-template.md`).

## Install
**Claude.ai / Claude Desktop**: Settings -> Capabilities/Skills -> upload a zip of this folder (the folder must contain `SKILL.md`).

**Claude Code**: copy or clone the folder into `~/.claude/skills/scientific-paper-reader` (all projects) or `<project>/.claude/skills/scientific-paper-reader` (one project).

**Gemini (Gems)**: paste `SKILL.md` as the Gem instructions. Gems cannot run the Python script, so use the PMC/full-text route or upload the PDF directly.

Dependencies for the script:
```bash
pip install -r requirements.txt
```

## Script usage
```bash
python3 scripts/phase1_triage.py paper.pdf --output-dir ./triage_out
python3 scripts/phase1_triage.py paper.pdf --output-dir ./triage_out --render-figures --dpi 120
python3 scripts/phase1_triage.py paper.pdf --output-dir ./triage_out --sections methods,results,discussion
```
Outputs `triage_out/triage_summary.json` (with `conclusion_source`, `figure_pages`, `pages_with_vector_graphics`, `section_files`), optional `figure_page_NN.png` renders, and `sections/*.md`.

## Tests
```bash
pip install -r requirements-dev.txt
python3 -m pytest tests/
```
The tests build a synthetic two-column, BMC-style PDF (conclusion before Methods, long reference list, vector-only chart) and check conclusion extraction, figure detection, column order and section files.

## License
MIT
