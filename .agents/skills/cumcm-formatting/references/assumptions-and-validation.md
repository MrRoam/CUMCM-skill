# Assumptions, symbols, sensitivity, and error

Use this reference when reviewing or drafting model assumptions, symbol definitions, parameters, sensitivity analysis, error analysis, robustness, or limitations.

## Assumption test

An assumption is useful only when it changes the model or its interpretation. For every assumption, identify:

1. what is asserted or excluded;
2. why the simplification is needed and plausible;
3. where it enters data processing, equations, constraints, parameters, or solver behavior;
4. which result may change if it fails;
5. whether evidence, sensitivity, scenarios, or a limitation statement addresses that risk.

Do not require a fixed number of assumptions. Remove generic statements that have no downstream use.

## Five-category review taxonomy

The following categories were supplied by the user as review prompts. They are not official scoring modules and should not become a five-item template.

| Category | Necessary interpretation | Review action | Common failure |
|---|---|---|---|
| Fidelity to the problem (`真实性`) | Respect facts, fixed conditions, and constraints stated by the problem | classify stated facts as givens or constraints; check that the model preserves them | calling a given fact an assumption, or silently changing it |
| Simplification (`简化性`) | Ignore a factor only when its effect is negligible, unavailable, or outside scope | state the excluded factor, rationale, expected direction, and affected result; test it if consequential | writing “ignore secondary factors” without naming or bounding them |
| Stability (`平稳性`) | Treat a process or environment as stable only over a defined horizon and regime | state time window and excluded shocks; examine trend, change points, residuals, holdout periods, or scenarios as appropriate | assuming stationarity across structural change without evidence |
| Parameter (`参数`) | Fix or estimate constants with source, unit, method, and applicable range | distinguish measured, literature-derived, calibrated, and assumed values; propagate or test important uncertainty | choosing a convenient value with no source or sensitivity |
| No interference (`无干扰`) | Exclude rare shocks or external interventions only when the scope permits | name the events/interventions excluded and state the validity boundary; stress-test important cases | duplicating stability/simplification wording or claiming universal validity |

`真实性` is usually a model-fidelity check rather than a genuine assumption. `无干扰` often overlaps with simplification or stability; merge it unless it represents a distinct external intervention. These distinctions prevent the five labels from producing redundant assumptions.

## Symbol review

Maintain one symbol table containing symbol, meaning, unit, type/domain, scope, and first definition. Check:

- every important symbol is defined before or at first use;
- one symbol has one meaning within its scope;
- different symbols do not silently represent the same quantity;
- units and dimensions are compatible in equations;
- indices, superscripts, vectors, matrices, random variables, and estimates are typographically distinguishable;
- symbols in equations, code, tables, figures, and prose agree.

Do not create a global symbol table for one-off local notation if defining it next to the equation is clearer.

## Validation selection

Choose the check from the risk:

| Risk | Suitable evidence |
|---|---|
| data noise or measurement error | uncertainty propagation, resampling, repeated measurement, error bounds |
| parameter uncertainty | local/global sensitivity, intervals, scenario grid |
| model misspecification | residual diagnostics, alternative model, ablation, out-of-sample comparison |
| algorithm instability | convergence trace, repeated seeds, initialization study, optimality gap |
| temporal or environmental change | holdout period, rolling test, change-point check, stress scenario |
| extrapolation | domain boundary, scenario envelope, external comparison |
| numerical or implementation error | unit tests, conservation checks, independent recomputation, order-of-magnitude check |

For every validation, state what changed, why the range or comparator is reasonable, which metric was observed, and within what range the conclusion remains valid.

## Distinguish sensitivity, error, and limitation

- **Sensitivity** asks how outputs change when inputs or assumptions change.
- **Error analysis** quantifies discrepancy introduced by data, approximation, estimation, computation, or comparison with observations.
- **Robustness** asks whether the decision or main conclusion survives plausible changes.
- **Limitation** states where the model or evidence no longer supports the claim.

Do not use one of these headings as a substitute for the others. A conclusion may be numerically sensitive while the recommended decision remains robust, or vice versa.
