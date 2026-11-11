---
name: scientific-paper-reader
description: Methodically read, analyze, and critically appraise scientific papers in three progressive phases with token-efficient figure and table triage. Use when the user uploads, links, or asks to read, study, summarize, critique, review, or extract methodology and research gaps from a scientific article, journal paper, preprint, clinical trial, or systematic review.
---

# Scientific Paper Reader

Read and critically appraise scientific literature using an evidence-based, three-phase workflow that integrates [Subramanyam (2013)](https://doi.org/10.4103/0973-029X.110733), [Keshav (2007)](http://ccr.sigcomm.org/online/files/p83-keshavA.pdf), [Carey et al. (2020)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7392212/), [Raff (2013)](https://violentmetaphors.com/2013/08/25/how-to-read-and-understand-a-scientific-paper-2/), and [EQUATOR/CASP reporting standards](https://pmc.ncbi.nlm.nih.gov/articles/PMC10833025/). Maximize comprehension while minimizing token consumption by triaging text, captions, and tables before rendering visual figures or ingesting the full manuscript.

## When to Use

- The user provides a scientific PDF, preprint, DOI, or article text and wants to study, understand, or critique it.
- The user asks for a structured literature review note, journal club preparation, or methodology breakdown.
- The user wants to screen a paper quickly (Phase 1) before deciding whether to spend time and tokens on a full deep dive (Phases 2 and 3).
- The user wants to identify statistical validity, methodological flaws, research gaps, or future project ideas from a study.

## Token-Efficient Architecture

Never ingest or vision-render an entire multi-page PDF at once unless explicitly asked for an immediate full-paper review. Use progressive disclosure across three phases:

1. **Phase 1 (Low-Token Triage, ~500-1,200 tokens)**: Run `scripts/phase1_triage.py` on local PDFs to extract only the Title, Abstract, Section Headings, Conclusions, Figure/Table Captions, and parsed Markdown tables. Inspect visual figures only via caption-first triage or selective page rendering (`--render-figures`).
2. **Phase 2 (Targeted Deep Read, ~1,500-3,000 tokens)**: Read the Introduction, Materials and Methods, Results, and Discussion text only after Phase 1 confirms relevance (or immediately if the user requested a complete analysis upfront).
3. **Phase 3 (Critical Reconstruction, ~800-1,500 tokens)**: Evaluate internal/external validity, statistical vs. clinical significance, unstated assumptions, research gaps, and actionable takeaways using `references/appraisal-checklists.md`.

## Steps

### Step 1: Identify Article Type and Reader Intent

Before reading linearly, classify the manuscript and clarify the reading goal ([Subramanyam 2013](https://doi.org/10.4103/0973-029X.110733); [Carey et al. 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7392212/)):

- **Primary Literature**: Original empirical research (IMRAD structure), Randomized Controlled Trials (RCTs), Cohort/Case-Control studies, Case Reports/Series, or Technical Notes.
- **Secondary Literature**: Narrative Reviews, Systematic Reviews, Meta-Analyses, Clinical Practice Guidelines, or Editorials/Commentaries.
- **Execution Mode**: Check whether the user wants **Interactive Phased Mode** (stop after Phase 1 for go/no-go confirmation) or **Full 3-Phase Mode** (execute all three phases in one pass). Default to **Interactive Phased Mode** when the user asks to "screen", "triage", or "start studying" a paper; default to **Full 3-Phase Mode** when the user asks for a "complete analysis", "full study guide", or "full review".

### Step 2: Phase 1 - Initial Reading, General Comprehension, and Figure/Table Triage

Never start reading an article from beginning to end. Establish the bird's-eye view and inspect data visuals using a three-tier token budget:

1. **Extract Core Framing (Text-Only)**:
   - If a local PDF is available, run:
     ```bash
     python3 scripts/phase1_triage.py "<path-to-paper.pdf>" --output-dir ./triage_out
     ```
   - Read only the **Title**, **Abstract**, **Section Headings**, and **Conclusion** (located at the end of the paper or final paragraph of the Discussion).
   - Answer **Keshav's 5 Cs** ([Keshav 2007](http://ccr.sigcomm.org/online/files/p83-keshavA.pdf)):
     - **Category**: What exact study design is this?
     - **Context**: Which theoretical framework or prior papers does it build on?
     - **Correctness**: Do the core premise and hypothesis appear sound?
     - **Contributions**: What are the 1-3 main findings or innovations?
     - **Clarity**: Is the manuscript clearly structured and well written?

2. **Token-Smart Observation of Figures and Tables**:
   - **Tier A - Captions and Parsed Tables First (0 Vision Tokens)**: Read all extracted `Figure N` and `Table N` captions/legends and parsed Markdown tables from `triage_summary.json`. Captions and table headers almost always reveal the experimental design, independent/dependent variables, sample sizes (`n`), and statistical outcomes without vision token overhead.
   - **Tier B - Selective Low-DPI Page Rendering (Low Vision Tokens)**: If a figure's trends, axes, or error bars cannot be verified from its caption alone, run `scripts/phase1_triage.py "<path-to-paper.pdf>" --render-figures --dpi 120 --pages <figure_pages>` to render only the specific pages containing figures at 120 DPI. Do not render text-only pages or bibliography pages.
   - **Tier C - Panel-by-Panel Deconstruction**: For each key figure or table, apply **Carey's 6 Panel Questions** ([Carey et al. 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7392212/)):
     - What hypothesis or question does this specific figure/table test?
     - What experimental method generated these data?
     - What are the exact axes, units, groups, error bars (SD, SEM, or 95% CI), and sample sizes?
     - What objective trend or difference is visible in the data?
     - Does the visual evidence match the claim in the abstract/caption?
     - What control group or comparison is shown (or missing)?

3. **Phase 1 Gate**:
   - Formulate 2-3 specific questions raised by the Abstract and Figures to verify in Phase 2.
   - In **Interactive Phased Mode**, present the Phase 1 synthesis and ask if the user wants to proceed to Phase 2 (or inspect specific figures in higher resolution).

### Step 3: Phase 2 - Detailed Reading and Methodology Analysis

Once relevance is confirmed, analyze the execution and context of the study:

1. **Introduction (Context, Gap, and Hypothesis)**:
   - Summarize the background context in 3-5 sentences ([Raff 2013](https://violentmetaphors.com/2013/08/25/how-to-read-and-understand-a-scientific-paper-2/)).
   - Pinpoint the exact **knowledge gap** in prior literature that motivated the authors.
   - State the explicit **research question**, **aims/objectives**, and **study hypothesis** (null vs. alternative).

2. **Materials and Methods (Architecture Over Memorization)**:
   - Map the study execution as a clean step-by-step workflow or diagram without getting lost in minor reagent or parameter minutiae unless needed for replication.
   - Extract the **PICOS / Experimental Architecture**:
     - **Population / Sample**: Sample size (`N`), grouping/categorization, sampling strategy, **inclusion criteria**, and **exclusion criteria** ([Subramanyam 2013](https://doi.org/10.4103/0973-029X.110733)).
     - **Intervention / Independent Variables**: Treatments, exposures, or experimental conditions.
     - **Comparators / Controls**: Positive, negative, sham, or baseline controls.
     - **Outcomes / Dependent Variables**: Instruments, assays, or metrics used, and whether they are valid and reliable.
     - **Statistical Plan**: Parametric vs. non-parametric tests selected, alpha threshold, and multiple-testing corrections (consult `references/appraisal-checklists.md`).

3. **Results and Discussion (Data vs. Interpretation)**:
   - **Independent Data Interpretation**: State what the Results and tables/figures objectively show *before* adopting the authors' narrative in the Discussion ([Carey et al. 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7392212/)).
   - **Subject Accounting Check**: Verify whether all participants/samples present at baseline are accounted for at the end of the study, and whether dropouts/exclusions are explained ([Subramanyam 2013](https://doi.org/10.4103/0973-029X.110733)).
   - **Significance Audit**: Separate statistically significant results from non-significant results, and evaluate **clinical or practical significance** (effect size and real-world magnitude, not just `p < 0.05`).
   - **Discussion Contextualization**: Compare how the authors interpret the findings against prior studies, and distinguish proven data from the authors' opinions or speculations.

### Step 4: Phase 3 - Critical Reconstruction and Gap Identification

Perform a rigorous peer-reviewer appraisal ([Keshav 2007](http://ccr.sigcomm.org/online/files/p83-keshavA.pdf); [CASP](https://casp-uk.net/casp-tools-checklists/); [EQUATOR Network](https://pmc.ncbi.nlm.nih.gov/articles/PMC10833025/)):

1. **Virtual Re-Implementation and Strengths/Weaknesses**:
   - Mentally re-create the study from the authors' starting assumptions ([Keshav 2007](http://ccr.sigcomm.org/online/files/p83-keshavA.pdf)): Where do their methods, controls, or statistical tests fall short?
   - Check whether the statistical test matched the data distribution and pairing (e.g., using an unpaired t-test on skewed or paired data; consult `references/appraisal-checklists.md`).
   - Apply the relevant study-design bias lens (**CONSORT** for RCTs, **STROBE** for observational studies, **PRISMA** for systematic reviews).
   - Check whether the authors extrapolated conclusions beyond the range of their actual data.

2. **Study Limitations and Unanswered Gaps**:
   - Extract **author-acknowledged limitations** (typically in the final paragraphs of the Discussion).
   - Identify **unacknowledged limitations** (confounders, sample power, selection bias, missing controls, external validity limits).
   - List concrete **open research questions** that remain unanswered.

3. **Re-Read Conclusion and Map Contributions to Your Work ("Lego Brick" Synthesis)**:
   - Re-read the Conclusion to verify whether your initial Phase 1 inference still holds and whether the data truly support the final claims ([Subramanyam 2013](https://doi.org/10.4103/0973-029X.110733)).
   - Apply Carey's **Rule 10 (Build on It)**: Identify transferable methodologies, theoretical frameworks, datasets, or experimental designs that the user can replicate, adapt, or extend in their own research.
   - Format the final output using `assets/study-note-template.md` when producing a complete study note.

## Gotchas

- **Vision Token Bloat**: Never convert every page of a PDF to high-resolution PNGs in Phase 1. Always parse text captions and tables first via `scripts/phase1_triage.py`, and render only targeted figure pages at 120 DPI when visual inspection is required.
- **Confusing Statistical with Practical Significance**: A small p-value (`p < 0.05`) in a large sample does not mean the effect is clinically or practically meaningful. Always report effect sizes, confidence intervals, or absolute differences alongside p-values.
- **Accepting Discussion Claims as Raw Facts**: Authors naturally frame their Discussion to support their hypothesis. Always compare the raw numbers in the Results/Tables against the rhetorical claims in the Discussion.
- **Skipping Baseline-to-End Subject Accounting**: Unexplained sample attrition or excluded outliers can invalidate an otherwise clean statistical test. Always check whether `N` in the Methods matches `n` in the Results tables and figures.
