# v171 Changed-Answer Judge vs v170

## Scope

This changed-set contains the single LongMemEval-S answer changed by v171:

- `d4bfe0f95ae6b5d7a565a8c1`

v171 changes `Marketing specialist` to `marketing specialist at a small startup` by preserving the unique source-backed support value for the question `What was my previous occupation?`

## Result

| Version | strict | lenient |
|---|---:|---:|
| v170 | `0/1` | `0/1` |
| v171 | `1/1` | `1/1` |

Both `deepseek-v4-flash` judge runs mark the v171 answer correct.

## Paths

- Labels: `experiments/diagnostic/stage1_lifecycle_slot_specificity_guard_v171_changed_vs_v170/labels.jsonl`
- v170 predictions: `experiments/diagnostic/stage1_lifecycle_slot_specificity_guard_v171_changed_vs_v170/v170_predictions.jsonl`
- v171 predictions: `experiments/diagnostic/stage1_lifecycle_slot_specificity_guard_v171_changed_vs_v170/v171_predictions.jsonl`
- v170 dual judge: `experiments/diagnostic/stage1_lifecycle_slot_specificity_guard_v171_changed_vs_v170/v170_dual_judge.json`
- v171 dual judge: `experiments/diagnostic/stage1_lifecycle_slot_specificity_guard_v171_changed_vs_v170/v171_dual_judge.json`

Clean boundary: labels and judge output are offline diagnostics only and are not used by prediction, retrieval, compiler, answer, finalizer, repair, or cache construction.

