# v169 LME Changed-Answer Judge vs v168

## Scope

- Benchmark: LongMemEval-S full
- Changed predictions: `1/500`
- Changed key: `c8e1ba8228ec76a80757b503`
- Prediction file: `predictions.jsonl`
- Judge output: `v169_dual_judge.json`

## Result

| Key | v168 answer | v169 answer | v168 dual judge | v169 dual judge |
|---|---|---|---|---|
| `c8e1ba8228ec76a80757b503` | `100` | `level 100` | strict wrong, lenient correct | strict correct, lenient correct |

Full patched LongMemEval-S result after replacing this single record: strict/lenient `414/500` / `419/500` = `0.828000 / 0.838000`.

## Clean Note

Judge is offline evaluation only. The prediction that produced `level 100` used only prediction-time question text, Memory Context, and the answer model structured response; it did not read labels, judge output, sample id, or test feedback.
