# Scientific Paper Reader (`scientific-paper-reader`)

An open [Agent Skills](https://agentskills.io/home) package for **Google Gemini CLI / Gemini** and **Anthropic Claude Code / Claude** that implements a structured, token-efficient **3-Phase Scientific Article Study Workflow**, plus an optional **Divulgation mode** that turns a paper into story material for science communication (videos, posts, classes).

## Theoretical Foundations

This skill synthesizes five complementary methodologies for reading and critically appraising scientific literature:

1. **R.V. Subramanyam (2013)** - [*Art of reading a journal article: Methodically and effectively*](https://doi.org/10.4103/0973-029X.110733): Non-linear reading order (Title -> Abstract -> Conclusion before full text), article taxonomy (primary vs. secondary literature), statistical vs. clinical significance (Table 3), baseline-to-end subject accounting, and the 40-question appraisal matrix (Table 4).
2. **S. Keshav (2007)** - [*How to Read a Paper*](http://ccr.sigcomm.org/online/files/p83-keshavA.pdf): The **Three-Pass Method**, the **Five Cs** (*Category, Context, Correctness, Contributions, Clarity*) in Pass 1, visual graph/error-bar scrutiny in Pass 2, and **Virtual Re-Implementation** in Pass 3.
3. **Carey, Steiner, & Petri (2020)** - [*Ten simple rules for reading a scientific paper*](https://pmc.ncbi.nlm.nih.gov/articles/PMC7392212/): Aligning reading priority to reader/author goals, the **Six Core Questions** applied to every individual figure and table panel, separating objective Results from Discussion interpretations, guarding against confirmation bias, and the **"Lego Brick" synthesis** for building on the paper.
4. **Jennifer Raff (2013/2016)** - [*How to read and understand a scientific paper*](https://violentmetaphors.com/2013/08/25/how-to-read-and-understand-a-scientific-paper-2/): Summarizing background in <=5 sentences, mapping experimental workflows step-by-step, and interpreting raw results prior to reading the authors' Discussion.
5. **EQUATOR Network & CASP Standards** - [*CONSORT, STROBE, PRISMA & CASP Checklists*](https://pmc.ncbi.nlm.nih.gov/articles/PMC10833025/): Study-design-specific bias and reporting audits for Randomized Controlled Trials ([CONSORT](https://equator-network.org/reporting-guidelines/consort/)), observational studies ([STROBE](https://www.strobe-statement.org/checklists/)), and systematic reviews ([PRISMA](https://www.prisma-statement.org/prisma-2020-checklist) / [CASP](https://casp-uk.net/casp-tools-checklists/)).

## Repository Structure

```text
scientific-paper-reader/
├── SKILL.md                             # Core Agent Skill instructions & 3-phase workflow
├── README.md                            # GitHub documentation & installation guide
├── requirements.txt                     # Script dependencies (pdfplumber, pypdf, pypdfium2)
├── requirements-dev.txt                 # + pytest and reportlab for the tests
├── scripts/
│   └── phase1_triage.py                 # Token-saving Phase 1 parser, section splitter & selective figure renderer
├── references/
│   └── appraisal-checklists.md          # Statistical test audit table, 40-Q checklist & EQUATOR/CASP guides
├── assets/
│   ├── study-note-template.md           # Structured 3-phase Markdown template for study notes
│   └── divulgation-brief-template.md    # Paper-to-story brief for science communication
└── tests/
    ├── make_fixture.py                  # Builds a synthetic two-column, BMC-style test PDF
    └── test_triage.py                   # pytest checks for the triage script
```

## How Token-Smart Figure & Table Triage Works (Phase 1)

Instead of converting an entire 20-page PDF into high-resolution images or dumping 15,000+ words into the context window on turn 1, `scripts/phase1_triage.py` implements a **3-tier token budget**:

1. **Tier A (0 Vision Tokens, ~500-1,200 Text Tokens)**: Extracts only the **Title**, **Abstract**, **Section Headings**, **Conclusion**, **Figure/Table Captions**, and **Markdown Tables** (`pdfplumber`) into `triage_summary.json`.
2. **Tier B (Selective Low-DPI Vision On-Demand)**: When visual inspection of plots or microscopy is needed, running `python3 scripts/phase1_triage.py paper.pdf --render-figures --dpi 120` renders **only** the specific pages containing figures at 120 DPI, cutting multimodal vision token usage by 80-90%.
3. **Tier C (Phase Gate)**: In Interactive Phased Mode, the agent presents the Phase 1 triage (5 Cs + Figure/Table Map) and waits for your go-ahead before ingesting the full Introduction, Methods, Results, and Discussion in Phases 2 and 3.

### What the triage script handles
- **Full text first (Step 0)**: if the paper is in PubMed Central, the agent reads the PMC full text before touching any PDF (zero vision tokens). Paywalls are never bypassed: the user provides the PDF.
- **Conclusion extraction** uses the last *Conclusion* heading before the reference list (falls back to the end of the Discussion) and reports `conclusion_source`, so long bibliographies or BMC-style layouts (Conclusions before Methods) do not return reference entries.
- **Vector figures**: pages with many vector drawing objects (most charts) are flagged as figure pages (`pages_with_vector_graphics`), not only pages with embedded images.
- **Two-column PDFs** are read column by column (full-width title block first), so headings and captions are not interleaved.
- **Targeted Phase 2**: `--sections methods,results,discussion` (or `all`) writes one Markdown file per section to `triage_out/sections/`.

```bash
python3 scripts/phase1_triage.py paper.pdf --output-dir ./triage_out
python3 scripts/phase1_triage.py paper.pdf --output-dir ./triage_out --render-figures --dpi 120
python3 scripts/phase1_triage.py paper.pdf --output-dir ./triage_out --sections methods,results,discussion
```

## Divulgation Mode (Step 5)

For science communication, after reading the full text the agent fills `assets/divulgation-brief-template.md`: the **hook number** with its section/figure and assumptions, **the problem**, **the solutions and their cost**, **the comparison**, **the twist / open questions** (keeping the authors' hedging), **the figure worth recreating** (axes, groups, values) and a **do-not-say list** of popular claims the paper does not support.

## Installation for Gemini & Claude

### 1. Google Gemini CLI (`gemini`)
Install directly from your GitHub repository or local clone ([Gemini CLI Agent Skills Docs](https://geminicli.com/docs/cli/skills/)):

```bash
# Install from GitHub repository
gemini skills install https://github.com/elsd443-beep/scientific-paper-reader.git

# Or copy into your workspace or global Gemini skills folder
mkdir -p .gemini/skills/
cp -r scientific-paper-reader .gemini/skills/
```

### 2. Anthropic Claude Code (`claude`)
Copy or symlink into your project or global Claude Code skills directory:

```bash
# Project-level installation
mkdir -p .claude/skills/
cp -r scientific-paper-reader .claude/skills/

# Global installation across all projects
mkdir -p ~/.claude/skills/
cp -r scientific-paper-reader ~/.claude/skills/
```

### 3. Claude.ai / Claude Desktop
Upload a zip of this folder in Settings -> Skills (the zip must contain `SKILL.md`). In a chat, the agent clones this repository to run the script if it is not bundled.

### 4. Gemini web (Gems)
Paste `SKILL.md` as the Gem instructions. Gems cannot run the Python script, so use the PMC full-text route or upload the PDF directly.

### 5. Universal Agent Skills CLI (`npx skills`)
```bash
npx skills add elsd443-beep/scientific-paper-reader --skill scientific-paper-reader
```

## Python Dependencies for `scripts/phase1_triage.py`

```bash
pip install -r requirements.txt
```
*(Note: The script automatically falls back to `pypdf` and `pdf2image` if optional libraries are absent.)*

## Tests

```bash
pip install -r requirements-dev.txt
python3 -m pytest tests/
```
The tests build a synthetic two-column, BMC-style PDF (conclusion before Methods, multi-page reference list, vector-only chart) and check conclusion extraction, figure detection, column order and section files.

## Example Prompts

- **Phase 1 Fast Triage**: *"Use `scientific-paper-reader` to run Phase 1 triage on `paper.pdf` and show me the 5 Cs and figure/table breakdown before we read the full paper."*
- **Full 3-Phase Study Note**: *"Study `clinical_trial.pdf` using all 3 phases of `scientific-paper-reader` and save the complete critical appraisal note as Markdown."*
- **Divulgation Brief**: *"Read `papers/octopus.pdf` with `scientific-paper-reader` in Divulgation mode and give me the brief for a 90-second science video."*
