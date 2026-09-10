---
name: cumcm-formatting
description: Draft, review, format, visualize, or audit a CUMCM mathematical-modeling paper from user-provided evidence, including abstracts, argument structure, assumptions, symbols, validation, figures, references, and submission files. Use for 全国大学生数学建模竞赛/CUMCM论文写作、审阅、排版、可视化或提交检查; do not use for solving an unrelated modeling problem or silently inventing models, data, results, experiments, or citations.
---

# CUMCM Paper Writing and Formatting

Help the author turn verified modeling work into a clear, traceable, compliant CUMCM paper. Preserve the author's mathematical decisions and make uncertainty visible.

## Select the mode

Choose only the modes needed by the request:

- **Material audit:** inventory data, models, results, citations, figures, and missing evidence.
- **Argument design:** build or review the question–claim–evidence structure and heading hierarchy.
- **Drafting/revision:** draft from an approved outline and evidence, or revise existing prose without changing its claims.
- **Assumption/validation review:** inspect assumptions, symbols, sensitivity, error, robustness, or limitations.
- **Visualization:** plan or create evidence-bearing figures and tables.
- **Formatting/submission:** apply current official requirements and inspect the rendered deliverable.

For a multi-stage request, read [workflow-and-routing.md](references/workflow-and-routing.md). For a narrow request, read only the references named below.

An outline is not an existing manuscript. A request to turn an outline into a paper selects drafting/revision plus formatting, unless the user explicitly asks to preserve the outline as-is. For a complete paper, read [full-draft-depth.md](references/full-draft-depth.md): establish the length scope and section budget, expand supported reasoning, and review evidence coverage before treating the draft as complete. Do not infer final length from the outline's length.

## Route supporting guidance

- Read [official-format.md](references/official-format.md) for format, anonymity, appendix, support-material, AI-disclosure, or final-submission work. Verify that no newer official rule or local competition notice supersedes it.
- Read [writing-and-review.md](references/writing-and-review.md) for outlines, sections, paragraphs, abstracts, citations, drafting, or substantive review.
- Read [assumptions-and-validation.md](references/assumptions-and-validation.md) when assumptions, symbols, parameters, sensitivity, error, robustness, or model limitations are in scope.
- Read [visuals.md](references/visuals.md) for figures, tables, diagrams, palettes, captions, or reproducible plotting.
- Read [evidence-boundaries.md](references/evidence-boundaries.md) when calibrating a complete paper's scope or comparing sample papers, and when distinguishing requirements from conventions. Its corpus statistics are provisional context unless their underlying records have been verified, never length or figure quotas.

## Non-negotiable behavior

1. Follow this priority: explicit user instruction; current national CUMCM rule; applicable regional/school rule; task evidence; this Skill's recommendations.
2. Distinguish official requirements from recommendations in every audit. Never call a typical font, paragraph length, heading depth, figure count, abstract length, or palette an official requirement without a current source.
3. Do not invent or silently repair data, citations, model choices, parameter values, experiments, numerical results, or author conclusions. Mark missing support and continue only where evidence is sufficient.
4. Treat the outline, evidence ledger, symbol table, and approved results as shared state. Update the draft through one coordinating writer; parallel work may inspect or propose, but must not independently overwrite the same manuscript.
5. Preserve the original file. Write to a named copy unless the user explicitly requests an in-place edit.
6. A formatting-only task must not change mathematical meaning, terminology, numerical values, references, or conclusions.
7. New models, new data, new experiments, stronger conclusions, citation replacement, deletion of material claims, and final submission require explicit author approval.

## Execute

For a narrow mode, follow its routed reference and the completion contract below. For combined work, follow the stage gates in [workflow-and-routing.md](references/workflow-and-routing.md) and leave a compact receipt at each gate. Reuse user-supplied ledgers, symbols, and approved decisions after validating them.

## Completion contract

Report results under three labels:

- **Hard violations:** conflicts with a verified official or applicable local rule.
- **Recommended improvements:** evidence-backed improvements that remain author choices.
- **Manual decisions:** missing evidence, ambiguous formulas, disputed interpretations, or author-owned scientific judgments.

For a complete manuscript or final file, provide the output path, rules version/date, checks actually run, unresolved items, and whether the final PDF was rendered and visually inspected. A successful file conversion alone is not completion.

For a complete draft, also report abstract/body/appendix pages separately, the planning range and its counting convention, substantive coverage gaps, and any material evidence left outside the manuscript with its destination or reason. Passing structural or page-limit checks does not establish sufficient scientific explanation.

Use [audit_manuscript.py](scripts/audit_manuscript.py) for a reproducible text/content scan and [audit_submission.py](scripts/audit_submission.py) for submission-package checks. Treat their findings as diagnostics; visually inspect formulas, layout, figures, and ambiguous matches.
