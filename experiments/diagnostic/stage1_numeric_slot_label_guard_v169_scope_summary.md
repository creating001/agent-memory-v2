# v169 Numeric Slot Label Guard Scope Summary

## Decision

Promote `configs/stage1_numeric_slot_label_guard_v169_qwen36_no_think_build4k_cached.json` to current local LTS.

v169 inherits v168 and adds one narrow source-grounded finalizer guard. For non-count questions where the draft answer is a bare number, the question asks for a `level` slot, and the answer model's own support evidence links the same number to a level slot, the guard preserves the slot label, e.g. `100` -> `level 100`.

## Clean Status

- Prediction uses only question text, raw Memory Context, build memory, and the answer model's prediction-time structured response.
- No gold answer, judge output, benchmark label, sample id, test feedback, or sample-level rule is used.
- The guard does not compute a new value; it only preserves a source-backed answer slot label.
- Answer prompt and repair prompt are unchanged from v168, so v169 reuses the parent answer/repair caches intentionally.

## Metrics

| Benchmark | Result |
|---|---|
| LongMemEval-S full | v169 vs v168 answer diff `1/500`; changed-answer dual judge strict `0/1 -> 1/1`, lenient `1/1 -> 1/1`; patched full strict/lenient `414/500` / `419/500` = `0.828000 / 0.838000` |
| LoCoMo non-adversarial full | v169 vs v168 answer diff `0/1540`; inherits strict/lenient `1216/1540` / `1256/1540` = `0.789610 / 0.815584` |

Changed LME answer:

- `c8e1ba8228ec76a80757b503`: `100` -> `level 100`; dual judge changed from strict wrong / lenient correct to strict correct / lenient correct.

Cache/cost notes:

- LME prediction replay: answer cache `500/500` hits, build/embedding cache misses `0`, repair cache misses `0`, finalizer applied `1/500`.
- LoCoMo prediction replay: answer cache `1540/1540` hits, build/embedding cache misses `0`, repair cache misses `0`, finalizer applied `0/1540`.

## Risk Assessment

- Reduced: #4 answer surface / source-grounded guardrail risk. The old source-grounded guard could leave an answer with the right numeric value but lose the requested slot label; v169 preserves the slot label only when both question and support evidence agree.
- Not solved: #1 granularity/profile design risk, #2 top-k/context noise/rerank, #3 selected-context generalization, and broader #5 memory lifecycle/update/conflict/query-time reasoning.
- Next direction: move from narrow answer-surface repair toward source-backed answer-slot-aware lifecycle/update/conflict reasoning, while keeping typed memory as an index/activation layer rather than independent evidence.

## Artifacts

- LME predictions/traces: `outputs/diagnostic/stage1_numeric_slot_label_guard_v169_lme_s_full/`
- LoCoMo predictions/traces: `outputs/diagnostic/stage1_numeric_slot_label_guard_v169_locomo_nonadv_full/`
- LME changed-answer judge: `experiments/diagnostic/stage1_numeric_slot_label_guard_v169_lme_changed_vs_v168/v169_dual_judge.json`
- LME run record: `experiments/diagnostic/stage1_numeric_slot_label_guard_v169_lme_s_full/`
- LoCoMo run record: `experiments/diagnostic/stage1_numeric_slot_label_guard_v169_locomo_nonadv_full/`
