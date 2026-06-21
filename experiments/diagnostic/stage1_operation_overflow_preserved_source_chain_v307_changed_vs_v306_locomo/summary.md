# v307 vs v306 LoCoMo Changed Sample Judge

## Scope

- Benchmark: LoCoMo non-adversarial full
- Changed record count: `1/1540`
- Changed record key: `27baf30e807665dacb4ec386`
- Base predictions: `v306_changed_predictions.jsonl`
- New predictions: `v307_changed_predictions.jsonl`
- Labels: `changed_labels.jsonl`

## Dual Judge Result

| Version | strict | lenient | judge agreement |
|---|---:|---:|---:|
| v306 | `1/1` | `1/1` | `1.0` |
| v307 | `1/1` | `1/1` | `1.0` |

## Full Metric Merge

The changed sample is strict correct for both v306 and v307, so LoCoMo full counts stay unchanged at strict `1223/1540` and lenient `1262/1540`.

This judge is offline evaluation only. It was not used by prediction, retrieval, compiler, answer, verifier, or cache build logic.
