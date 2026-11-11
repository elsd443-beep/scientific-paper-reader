# Scientific Paper Critical Appraisal Checklists & Statistical Reference

This reference combines the structured appraisal frameworks from:

- **R.V. Subramanyam (2013)**: *Art of reading a journal article: Methodically and effectively* ([DOI: 10.4103/0973-029X.110733](https://doi.org/10.4103/0973-029X.110733))
- **S. Keshav (2007)**: *How to Read a Paper* ([ACM SIGCOMM CCR](http://ccr.sigcomm.org/online/files/p83-keshavA.pdf))
- **Carey, Steiner, & Petri (2020)**: *Ten simple rules for reading a scientific paper* ([PLOS Comput Biol / PMC7392212](https://pmc.ncbi.nlm.nih.gov/articles/PMC7392212/))
- **Jennifer Raff (2013)**: *How to read and understand a scientific paper* ([Violent Metaphors](https://violentmetaphors.com/2013/08/25/how-to-read-and-understand-a-scientific-paper-2/))
- **EQUATOR Network & CASP Checklists**: **CONSORT**, **STROBE**, and **PRISMA** ([Johansen & Thomsen 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC10833025/); [CASP Checklists](https://casp-uk.net/casp-tools-checklists/))

## 1. Quick Article Type Triage (Subramanyam Table 2)

| Goal / Intent | Primary Literature to Prioritize | Secondary Literature to Prioritize |
| :--- | :--- | :--- |
| **New research idea or experimental protocol** | Original Research (IMRAD), Experimental Studies, Technical Notes | Systematic Reviews (Future Directions section) |
| **Clinical diagnosis, therapy, or prognosis** | Randomized Controlled Trials (RCTs), Controlled Clinical Trials (CCTs), Cohort & Case-Control Studies, Case Series | Systematic Reviews, Meta-Analyses, Clinical Practice Guidelines |
| **Entering a new field or broad topic update** | Landmark Original Research (highly cited in introductions) | Narrative Reviews, Systematic Reviews, Meta-Analyses, Editorials |

## 2. Panel-by-Panel Figure & Table Audit (Carey et al. Rules 3 & 4 + Keshav Pass 2)

For each key figure or table in Phase 1 and Phase 2, verify:

1. **Question / Purpose**: What specific claim or sub-hypothesis does this visual test?
2. **Assay / Measurement**: How were the data generated (e.g., RT-qPCR, Western blot, Kaplan-Meier survival, survey, simulation)?
3. **Axes & Scales**: Are both axes labeled with clear units? Is the scale linear or logarithmic, and is the y-axis truncated?
4. **Sample Size & Uncertainty**: Are sample sizes (`n` of biological vs. technical replicates) and error bars (SD, SEM, or 95% CI) explicitly defined in the caption?
5. **Controls**: Are appropriate positive, negative, or baseline controls included in the same figure/table?
6. **Take-Home vs. Overclaim**: Does the visual trend genuinely support the authors' caption and Results text?

## 3. Statistical Test Appropriateness Audit (Subramanyam Table 3)

Check whether the authors chose a statistical test that matches their data distribution and study design:

| Data Type & Distribution | Research Goal | Appropriate Test | Common Misuse / Red Flag |
| :--- | :--- | :--- | :--- |
| **Quantitative, Parametric** (Normal / bell-shaped distribution) | Compare 2 independent group means | **Unpaired Student's t-test** (or Z-test for large samples) | Used on heavily skewed data, ordinal scales, or small `n` without normality check |
| **Quantitative, Parametric** (Normal distribution) | Compare 2 paired/matched measurements (e.g., pre vs. post) | **Paired t-test** | Using an unpaired test on longitudinal/repeated measures |
| **Quantitative, Parametric** (Normal distribution) | Compare means across 3 or more groups | **ANOVA** (with post-hoc multiple-comparison correction) | Running multiple pairwise t-tests without p-value correction (p-hacking / Type I error inflation) |
| **Quantitative, Parametric** | Measure linear association or predict continuous outcome | **Pearson correlation (`r`)** or **Linear regression** | Claiming causation from correlation, or fitting linear models to non-linear/outlier-driven data |
| **Quantitative, Non-Parametric** (Skewed / distribution-free / ordinal) | Compare 2 independent groups | **Mann-Whitney U (rank-sum) test** | Reporting mean +/- SD instead of median and interquartile range (IQR) |
| **Quantitative, Non-Parametric** (Skewed / matched) | Compare 2 paired/matched groups | **Wilcoxon signed-rank test** | Ignoring paired structure in non-normal data |
| **Quantitative, Non-Parametric** | Compare 3 or more independent groups | **Kruskal-Wallis test** | Omitting post-hoc Dunn's test correction |
| **Qualitative / Categorical** (Frequencies / proportions) | Compare proportions across unmatched groups | **Chi-square test** (or **Fisher's exact test** when expected cell counts < 5) | Using Chi-square when expected cell frequencies are below 5 |
| **Qualitative / Categorical** (Matched / paired binary outcomes) | Compare paired proportions (e.g., discordant pairs) | **McNemar's test** | Using standard Chi-square on matched/pre-post binary data |

**Clinical vs. Statistical Significance Check**: Always ask whether a statistically significant difference (`p < 0.05`) is large enough in effect size (e.g., Cohen's `d`, Hazard Ratio, Odds Ratio, Relative Risk Reduction, or absolute difference) to matter practically or clinically ([Subramanyam 2013](https://doi.org/10.4103/0973-029X.110733)).

## 4. Subramanyam's 40-Question Appraisal Matrix (Condensed by Phase)

### Phase 1: Overview & Conclusions (Questions 1-3, 24, 32-37)
- What is the article type, descriptive title, and author/institution context?
- Are the tables and graphs self-explanatory and easy to comprehend?
- What are the primary conclusions, and are they reasonable, logical, and grounded in reported data?
- Will the results be useful in clinical/practical application or future research?

### Phase 2: Introduction, Methods & Results (Questions 4-23)
- **Introduction**: What is the research problem, prior literature context, study rationale, aims/objectives, and explicit hypothesis?
- **Methods**: How was sampling performed and grouped? What were the exact inclusion and exclusion criteria? What procedures, equipment/instruments, and measured variables were used, and were they appropriate? Were the statistical methods apt for evaluation?
- **Results**: What were the key findings? Were **all subjects present at the beginning of the study accounted for at the end**? Are the results reliable (reproducible) and valid (measuring what they claim to measure)? Which results were statistically significant vs. non-significant?

### Phase 3: Discussion, Critique & References (Questions 25-31, 38-40)
- **Discussion**: Did the results actually answer the research question? How do the authors' interpretations compare with prior studies? What are the strengths and limitations? **Were there any extrapolations of findings beyond the range of data?**
- **References**: Are citations accurate, up to date, and free of missing landmark work ([Keshav 2007](http://ccr.sigcomm.org/online/files/p83-keshavA.pdf))?

## 5. Study-Design Specific Bias Checks (EQUATOR / CASP)

- **Randomized Controlled Trials (CONSORT / CASP RCT)**:
  - Was randomization sequence generation truly random and allocation concealed?
  - Were participants, clinicians/experimenters, and outcome assessors blinded?
  - Were baseline characteristics balanced across groups (Table 1)?
  - Was an Intention-to-Treat (ITT) analysis performed, and were all adverse events/harms reported?
- **Observational Cohort / Case-Control / Cross-Sectional Studies (STROBE / CASP)**:
  - Is there selection bias in how cases, controls, or cohorts were recruited?
  - Were key confounding variables measured and adjusted for in multivariable analysis?
  - Was follow-up long enough and complete enough across exposure groups?
- **Systematic Reviews & Meta-Analyses (PRISMA / CASP SR)**:
  - Was a comprehensive multi-database search strategy with explicit inclusion/exclusion criteria used (PRISMA flow diagram)?
  - Was risk of bias assessed for each included primary study?
  - Was statistical heterogeneity (`I^2`, Cochran's `Q`) evaluated before pooling results, and was publication bias (funnel plot) checked?
