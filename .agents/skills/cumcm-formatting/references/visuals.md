# Figures and tables

Use this reference for visual planning, plotting, diagrams, tables, captions, and figure–text review.

## Evidence first

For each visual, record the question, source data/model output, filtering or aggregation, axes/units, comparison baseline, intended finding, and output file. Do not smooth, impute, remove outliers, or change scales without an explicit analytical reason recorded in the paper.

Generative images may illustrate a concept but must not serve as numerical evidence.

## Choose by information task

| Task | Preferred forms | Required check |
|---|---|---|
| trend, iteration, or parameter path | line, interval band | time/parameter scale, units, key range |
| relationship or fit | scatter with fit and/or residuals | observations, anomalies, fit definition |
| discrete comparison | dot plot, bar chart, compact table | common baseline, sorting, uncertainty |
| distribution | box, histogram, density, interval plot | sample size, scale, outliers |
| spatial position/path/coverage | map, coordinate or trajectory plot | coordinate system, scale, legend |
| matrix relation | heatmap | color scale, ordering, numeric context |
| method dependency | flow/framework diagram | one reading direction, semantic nodes, inputs/outputs |
| exact values | three-line or otherwise restrained table | units, precision, optimal-value criterion |
| robustness | sensitivity curve, interval, scenario table | perturbation range, baseline, conclusion threshold |

Avoid decorative figures, duplicated graph-and-table presentations, rainbow palettes, misleading truncated axes, unnecessary 3D, and unexplained dual axes.

## Design and annotation

- Introduce the reading question before the visual and state the finding and consequence nearby.
- Put figure captions below and table titles above; make them identify object, condition, and metric.
- Use actual semantic legend labels, axis names, and units.
- Keep a variable's color, line, marker, and symbol consistent across the paper.
- Use line style, marker, direct labels, fill, or luminance in addition to hue so grayscale printing remains readable.
- Keep multi-panel dimensions, fonts, ranges, legends, and `(a)(b)(c)` labels consistent.
- Prefer vector PDF/SVG/EMF; when raster output is needed, normally export a 300 dpi PNG. Do not use screenshots in place of source figures.

## Optional visual tokens

The file [visual-style-tokens.json](../assets/visual-style-tokens.json) is an empirical starting palette, not an official or award-causing rule. Adapt it to the data and medium. Use one main color, one emphasis color, and neutral support before adding more hues.

## Verification

Check the plotted data against the source after filtering, sorting, aggregation, normalization, and unit conversion. Confirm that the caption, visual, body result, abstract, and support-material code report the same quantity and condition. Render the final paper and inspect legibility at normal page scale and in grayscale.
