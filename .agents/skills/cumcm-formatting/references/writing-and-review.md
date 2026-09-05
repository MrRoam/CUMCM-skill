# Writing and review

Use this reference for argument design, drafting, revision, abstract work, or substantive manuscript review.

## Trace claims before writing prose

Maintain a compact evidence ledger with these fields:

| Field | Meaning |
|---|---|
| claim_id | stable identifier |
| claim | proposed factual or analytical statement |
| source | problem statement, data, code output, figure/table, literature, or author judgment |
| location | file, page, cell, figure, table, or run identifier |
| transformation | calculation, filtering, estimation, comparison, or paraphrase |
| conditions | scenario, unit, parameter range, precision, and scope |
| uncertainty | known limitations or unresolved conflict |
| destination | planned section and, if relevant, abstract sentence |

Strong claims and numerical results need a source and location. Missing support remains an explicit gap.

## Build the argument map

For each subproblem, connect:

`objective → inputs → assumptions → variables → model/algorithm → solution → result → validation → direct answer`

Nodes may be combined when the relationship remains clear. Shared data processing, definitions, assumptions, or models should be defined once and referenced from dependent sections.

Choose organization from dependency:

- Use a question-led structure when subproblems are substantially independent.
- Use a model-process structure when several subproblems share data, state variables, or one core model.
- Use a mixed structure when common foundations lead to question-specific methods or results.

Do not repeat a full “analysis–model–solution” template under every question when most material is shared.

## Section responsibilities

- **Restatement/introduction:** compress the task context and identify the mathematical object; avoid copying the problem statement.
- **Problem analysis:** explain dependencies, difficulties, and planned transformations without prematurely claiming results.
- **Data/preprocessing:** record sources, cleaning, exclusions, transformations, and their effect on interpretation.
- **Model choice/building:** explain why the method fits, define variables and constraints, and connect equations to the problem.
- **Solution:** give enough algorithm, parameter, convergence, or implementation detail to reproduce the result; move full code to support material.
- **Results:** answer the question with conditions, units, precision, and interpretation; do not write only “results are shown below.”
- **Validation:** test a risk that could change the conclusion, not an arbitrary parameter merely to include a sensitivity section.
- **Evaluation:** connect strengths to evidence, limitations to boundaries, and proposed improvements to those limitations.

## Paragraphs and language

Give each paragraph one primary job: define, justify, derive, solve, compare, interpret, validate, or evaluate. A useful internal shape is `main point → basis/action → consequence`. Length follows function; do not force a word target.

Use concrete verbs such as define, establish, estimate, compare, verify, obtain, and indicate. Qualify “significant,” “optimal,” “accurate,” “robust,” and “effective” with a metric, baseline, test, or scope. `本文` or `我们` may identify an author action but must not replace the logical subject.

Check transitions for actual relations: purpose, cause, elaboration, sequence, comparison, reference, or figure–text linkage. Delete transitions that add no relation and sentences that repeat a caption or nearby conclusion.

## Heading hierarchy

- Level 1 represents a major paper stage or independently readable module.
- Level 2 represents an object, subproblem, model component, or necessary step within that stage.
- Level 3 is justified only when one level-2 topic has at least two distinct technical substeps that need separate reference.
- Prefer a paragraph lead, numbered list, or equation explanation over a fourth level unless navigation genuinely improves.
- Keep sibling titles grammatically parallel and name the object/action rather than using empty labels such as “analysis” or “solution process.”

These are structural recommendations, not national format rules.

## Abstract

Write or refresh the abstract after the body, results, and figures stabilize. For each main problem, provide a verifiable delivery containing the objective, essential treatment/model, principal result, and interpretation or reliability where material.

Map every abstract result to a body location and check numerical equality, units, conditions, and direction of comparison. Do not add results absent from the body or impose a fixed word count; obey the current one-page boundary.

## Review sequence

Review in this order so later polish does not hide upstream gaps:

1. unsupported or conflicting claims;
2. unanswered subproblems and broken dependencies;
3. assumptions, symbols, and formula meaning;
4. result interpretation and validation;
5. abstract–body, figure–text, and citation consistency;
6. paragraph purpose, redundancy, and language;
7. format and rendering.

Return proposed scientific changes separately from safe editorial edits. Preserve the author's terminology and stance unless approval is given.
