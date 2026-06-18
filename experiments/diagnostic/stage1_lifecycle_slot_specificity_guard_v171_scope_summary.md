# v171 Lifecycle-Slot Specificity Guard

## Decision

Promote `configs/stage1_lifecycle_slot_specificity_guard_v171_qwen36_no_think_build4k_cached.json` to current local LTS.

v171 inherits v170 and changes only the source-grounded finalizer gate. v170 blocked all `previous/current/latest` questions from source value specificity preservation to avoid temporal overreach. v171 keeps the hard blocks for count/date/duration/sum/order/option questions, but allows a narrow lifecycle-slot exception for previous/current occupation, role, job, position, title, or career questions.

The guard still only fires when the draft answer is a short substring of exactly one more-specific support `value` emitted by the answer model's own prediction-time `evidence_report`. It does not compute values, merge evidence, use support `reason` as an answer source, or read labels/judge/sample ids/test feedback.

## Metrics

| Benchmark | Result |
|---|---:|
| LongMemEval-S full | strict/lenient `415/500` / `420/500` = `0.830000 / 0.840000` |
| LoCoMo non-adversarial full | strict/lenient `1217/1540` / `1256/1540` = `0.790260 / 0.815584` |

LongMemEval-S is paired-delta derived from v170. v171 changes `1/500` answer; changed-answer paired dual judge improves from strict/lenient `0/1` to `1/1`. LoCoMo changes `0/1540` answers versus v170, so it inherits v170 paired-delta derived metrics.

Changed answer:

- `d4bfe0f95ae6b5d7a565a8c1`: `Marketing specialist` -> `marketing specialist at a small startup`; question: `What was my previous occupation?`

## Verification

- LME full cached replay: answer cache `500/500`, build cache misses `0`, repair cache misses `0`, finalizer applied `2/500`.
- LoCoMo full cached replay: answer cache `1540/1540`, build cache misses `0`, repair cache misses `0`, finalizer applied `8/1540`.
- Changed-answer judge:
  - `experiments/diagnostic/stage1_lifecycle_slot_specificity_guard_v171_changed_vs_v170/v170_dual_judge.json`
  - `experiments/diagnostic/stage1_lifecycle_slot_specificity_guard_v171_changed_vs_v170/v171_dual_judge.json`

Token costs are unchanged from v170:

- LongMemEval avg build/query visible tokens: `85393.566 / 6239.336`
- LoCoMo avg build/query visible tokens: `62015.574026 / 6047.909091`

## Risk Conclusion

Compared with v170:

- Reduced #4 answer-surface specificity risk: a correct but underspecified lifecycle slot can preserve the source-backed full value.
- Reduced a narrow part of #5 lifecycle/query-time reasoning risk: previous/current role-like slots are no longer treated as generic dangerous temporal questions when the answer model has already exposed a unique support value.
- Not increased: broad temporal/order/list/count questions remain blocked; option questions with `or` remain blocked; multiple candidate values still no-op.

Remaining risks:

- #1 granularity/profile design risk remains.
- #2 top-k/context noise and rerank/context organization remain.
- #3 selected-context generalization remains.
- #5 still needs broader lifecycle/update/conflict reasoning beyond occupation/role-like slot specificity.

## Clean Note

Prediction code uses only question text, route, raw Memory Context, build memory, and the answer model's prediction-time structured response. Labels and dual judge are used only after prediction for offline evaluation.

Full replay paths:

- `outputs/diagnostic/stage1_lifecycle_slot_specificity_guard_v171_lme_s_full/`
- `outputs/diagnostic/stage1_lifecycle_slot_specificity_guard_v171_locomo_nonadv_full/`

