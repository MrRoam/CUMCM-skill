# Workflow and routing

Use this reference when the request spans more than one mode or asks Codex to coordinate several tasks automatically.

## Required shared state

Before drafting, collect or construct only what the project needs:

| Item | Minimum content | If missing |
|---|---|---|
| Problem map | each subproblem, requested output, dependencies | extract from the problem statement and ask only about material ambiguity |
| Evidence ledger | claim, source/location, transformation, uncertainty, intended section | mark unsupported claims; do not fill them with plausible text |
| Model record | choice, reason, assumptions, variables, equations, solver | preserve author choice; propose alternatives separately |
| Result record | value/pattern, condition, unit, precision, producing file/code | block strong prose claims that lack a traceable result |
| Symbol table | symbol, meaning, unit, scope, first definition | reconcile collisions before drafting dependent sections |
| Visual plan | question, data, form, caption, conclusion, output file | create only when it adds evidence or compresses explanation |
| Style target | language, audience, tone, length, file format | infer conservatively from the existing manuscript |

## Stage gates

1. **Material gate:** identify usable evidence, conflicts, and missing inputs.
2. **Argument gate:** create the question–claim–evidence map and section dependencies.
3. **Draft gate:** draft only sections whose evidence and symbols are ready.
4. **Integration gate:** reconcile terminology, assumptions, variables, numbers, citations, and cross-references.
5. **Abstract gate:** write the abstract from stable body results.
6. **Delivery gate:** run format and submission checks, render, and visually inspect.

Each gate should leave a small receipt: inputs used, output created, unresolved items, and the next allowed stage. Do not repeat the full reasoning history.

## Automatic task composition

A single request may combine multiple internal tasks. Select them from the requested outcome rather than invoking every mode:

- **Outline supplied, evidence supplied:** audit the map, reconcile symbols, draft approved sections, integrate, refresh abstract, then audit.
- **Outline supplied, evidence incomplete:** map missing evidence and draft only supported passages.
- **Draft supplied:** review claims and structure first; revise only the scope authorized by the user.
- **Formatting only:** load official rules, preserve content, format a copy, render, inspect, and report.
- **Visualization only:** verify data and intended claim, choose the visual, create reproducible outputs, and audit figure–text consistency.
- **Final package:** perform content, official-format, anonymity, support-material, AI-disclosure, and rendered-output checks.

## Parallel and sequential work

Parallelize only independent, read-only, or separately owned outputs when the environment and user authorization allow it. Good parallel lanes include evidence indexing, citation checking, symbol extraction, figure planning, and official-rule checking.

Keep these sequential under one coordinator:

1. shared assumptions and symbols;
2. model construction and solution explanation;
3. results and validation;
4. conclusions and evaluation;
5. abstract;
6. whole-document integration and final rendering.

Never let several workers edit the same manuscript file concurrently. Give each worker a distinct artifact or proposal, then merge after checking shared state.

## Stop and ask the author

Prepare the reviewable work first, then stop when proceeding would require any of the following:

- choosing or replacing a core model;
- introducing data, experiments, parameter values, or external claims not supplied or verified;
- resolving materially conflicting evidence;
- strengthening a conclusion beyond the reported validation;
- removing an author claim, changing interpretation, or replacing a citation;
- publishing or submitting the final package.
