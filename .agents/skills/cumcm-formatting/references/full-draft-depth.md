# Full-paper scope and depth

Read for a complete paper drafted from an outline/evidence package, or for a requested review of substantive depth. Do not apply expansion requirements to formatting-only tasks, abstracts, short reports, or explicitly concise versions.

## Establish the working scope before drafting

Record the following in one compact working note, outside the anonymous paper:

- Deliverable type: full paper, concise paper, or formatting only. An outline's brevity is not a request for a brief final paper.
- Problem year, applicable rule year, national body limit and any supplied local notice. Never silently substitute one year for another. If a requested length conflicts with a verified rule, explain the conflict and develop the supported content within the applicable submission limit; a longer study edition requires that intended scope.
- Counting convention: abstract, narrative body, references/AI declaration, and appendices separately. For the working budget, explicitly say whether references/AI pages are included; use that same convention in the final comparison. Overall PDF pages do not measure body depth.
- User's page/word range and template, if supplied. Treat an explicit user target as a task requirement unless stated as a preference; an agent-inferred range is a planning estimate, not an author-approved requirement.
- Evidence-supported section budget and readable typography. If no range is supplied, infer a provisional range from section responsibilities, available results, and any inspected comparable examples; disclose it and continue without a mandatory approval round. Do not choose a universal default from one previous case or the corpus median.

Use a table with columns: `section/question | claim to explain | evidence IDs/files | necessary derivations/comparisons/visuals | estimated pages | evidence gaps`. Reuse the existing evidence ledger instead of duplicating it. Estimate pages under the intended template; a few representative rendered pages can calibrate prose, equations, tables and code when layout is unfamiliar. Estimates are ranges, not promises of exact pagination.

When reference papers are provided, inspect their actual body boundaries, problem type, template and section functions. Transfer useful depth and organization, not their scientific conclusions or page counts. Without comparable papers, explain that the budget is inferred; do not claim an award-winning-paper norm was verified.

## Expand the scientific explanation, not the claim strength

For each substantive question, use the applicable checks below. A common section may satisfy several questions if each points to it and explains its own differences. Irrelevant checks may be omitted with a brief reason; do not force optimization structure onto every problem.

| Function | Evidence of sufficient explanation |
|---|---|
| Task and choice | Reader can identify the requested mathematical output, design variables and why the supplied model addresses it. Do not invent retrospective model-selection experiments. |
| Construction | Assumptions enter named quantities or constraints; important equations have defined symbols and the reasoning needed to follow them. Explain non-obvious normalization, geometry and boundary cases where they affect results. |
| Solution | Reader can follow inputs → key steps → parameters/search settings → stopping or selection rule → outputs without reverse-engineering the source code. |
| Decisions and comparison | Where candidate results exist, show the consequential comparisons and selection evidence, including relevant rejected/infeasible alternatives. Keep different sampling settings or search stages distinguishable; do not sum logs into a unique candidate count without deduplication. |
| Results | Exact answers, units, conditions, spatial/temporal patterns and their implications are connected. A table or filename alone does not explain a result. |
| Validation | Explain the risk tested, setup/baseline, observed discrepancy and conclusion boundary. A count of passing tests is not a substitute for describing representative cases. Do not invent confidence intervals or experiments. |
| Evaluation | Strengths and limitations follow from the actual evidence, with no unsupported optimality, robustness or engineering claims. |

Expanding a supplied derivation, explaining an existing algorithm and plotting already-supplied results normally fall within a full-drafting request when mathematical meaning is preserved. Distinguish these from choosing a new model, changing assumptions, collecting new evidence, rerunning expensive studies or strengthening conclusions. Apply the existing authorization boundary to those scientific changes, not to ordinary supported elaboration.

## Review unused evidence and depth before final formatting

For each planned claim/function, record `explained` with a manuscript location, `supported but unwritten`, `missing evidence`, or `not applicable` with a reason. Heading presence, a citation or a filename does not establish `explained`; inspect the actual reasoning and its relation to the evidence.

Review high-value evidence still outside the paper: candidate comparisons, derivations, diagnostic examples, validation cases and interpretable patterns. Assign it to `body`, `appendix`, `electronic support`, or `omit with reason`. Do not print every array or search row by default. The purpose is to expose relevant evidence left unused, not maximize figure count or appendix bulk.

Resolve `supported but unwritten` items necessary to answer the problem before calling the full draft complete. For `missing evidence`, finish independent supported sections and state how the gap limits the result or requested length. Do not relabel an unmet user target as achieved. A justified short paper may be sufficient; a long paper with unexplained decisions may not be.

## Compare rendered length with the plan

Measure actual pages using verified boundaries. If below the working range, revisit depth coverage and unused evidence first. If above it, remove repetition and relocate genuinely supporting detail without removing the rationale needed in the body. If the range itself was mistaken, revise an agent-inferred estimate with an explicit evidence-based reason; never silently lower a user's target after seeing a short output.

Do not attain length by enlarging fonts, excessive whitespace, repeated tables, extra background, fabricated evidence or needlessly listing all coordinates. Do not satisfy a maximum by shrinking code into unreadable text. Use the supplied template; absent one, choose readable body and appendix type and verify at normal page scale. About 9–10.5 pt can be a useful code starting point, not a national rule or mandatory minimum.

Keep appendices proportional to reproducibility needs. They may be short or long depending on program volume, derivations and necessary detailed results; there is no universal 80–90-page total target.

The text scanner can report length diagnostics for a rendered PDF:

```text
python scripts/audit_manuscript.py paper.pdf --full-draft --body-start-page 2 --body-end-page 25 --target-body-pages 24 28 --output audit.json
```

Numbers here demonstrate the interface, not a recommended universal range. Page arguments are one-based physical PDF pages, inclusive; determine them from the actual manuscript. The target uses the recorded body-count convention. A short/long-range finding prompts substantive review and is not an official-rule violation. Its scanner severity `recommended` distinguishes it from an official hard violation; it does not make an explicit user's unmet length requirement optional. The script cannot certify explanation quality. Without a verified page range it must not silently count the whole PDF as body.
