# v307 Operation Overflow Preserved Source Chain Full Summary

## Decision

Promote v307 to current LTS.

v307 keeps v305/v306's guarded source-chain coverage policy and fixes a shallow-consumption failure: an operation source expansion could be selected/emitted in trace but fail to enter the candidate pool when earlier utilities had already occupied overflow tail capacity. v307 adds an explicit `preserve_existing_overflow` policy so a guarded operation raw source can be appended after existing overflow hits before context-budget audit.

## Clean Setting

- Algorithm commit: `e9940e7b7d66606727acd451a4155a7c4ed05d66`
- Config: `configs/stage1_operation_overflow_preserved_source_chain_v307_query_restore_seeded_qwen36_no_think_build4k_cached.json`
- No gold answer, judge output, benchmark label, sample id, test feedback, or sample-level rule is used by prediction.
- LME full judge accuracy is inherited from v306/v305 because answer/prompt/evidence diff is `0`.
- LoCoMo has one changed answer/prompt/evidence sample; both v306 and v307 changed outputs are strict correct under dual DeepSeek flash judge, so full accuracy is unchanged.

## Formal Runs

- LME: `experiments/formal/stage1_operation_overflow_preserved_source_chain_v307_lme_s_full_e9940e7/`
- LoCoMo: `experiments/formal/stage1_operation_overflow_preserved_source_chain_v307_locomo_nonadv_full_e9940e7/`
- LME predictions: `outputs/formal/stage1_operation_overflow_preserved_source_chain_v307_lme_s_full_e9940e7/predictions.jsonl`
- LoCoMo predictions: `outputs/formal/stage1_operation_overflow_preserved_source_chain_v307_locomo_nonadv_full_e9940e7/predictions.jsonl`
- Changed LoCoMo judge: `experiments/diagnostic/stage1_operation_overflow_preserved_source_chain_v307_changed_vs_v306_locomo/`

## Full Metrics

| Benchmark | strict/lenient | counts | avg build tokens | avg query tokens |
|---|---:|---:|---:|---:|
| LongMemEval-S full | `0.834000 / 0.846000` | `417/500`, `423/500` | `85393.566` | `6455.588` |
| LoCoMo non-adversarial full | `0.794156 / 0.819481` | `1223/1540`, `1262/1540` | `62015.57402597403` | `6093.87012987013` |

## Diff vs v306

| Benchmark | answer diff | prompt diff | evidence diff | retrieval diff | changed judge |
|---|---:|---:|---:|---:|---|
| LongMemEval-S full | `0/500` | `0/500` | `0/500` | `1/500` | not needed |
| LoCoMo non-adversarial full | `1/1540` | `1/1540` | `1/1540` | `1/1540` | v306 `1/1` strict, v307 `1/1` strict |

LME still has operation source expansion applied/selected/emitted `1/1/1`. The emitted source now reaches context-budget consideration and appears in dropped source ids, rather than disappearing before budget audit. It is still not included in final evidence because the context budget drops it under the current character budget.

LoCoMo has no operation source expansion. The single changed output is unrelated to operation expansion and remains strict correct under both flash judge passes.

## Why v307 Replaces v305

v305 reduced weak-overlap expansion risk but still left a system-level gap: source expansion could be selected and emitted without becoming a real candidate for context organization. v306 added a budget protection hook but showed that the hook could not fire because the operation source disappeared before budget. v307 fixes that boundary by making overflow preservation explicit and configurable.

This reduces the "memory only as shallow retrieval hint" risk without using labels or benchmark-specific rules, and it preserves full judge accuracy. The method remains conservative: the operation source can reach budget audit, but final prompt inclusion still depends on context-budget policy.

## Next Step

Use v307 as the baseline for a budget-aware source coverage selector: keep raw evidence-first and the current source-chain utility gates, then decide whether one operation source should replace a lower-utility tail row under the character budget rather than simply forcing more tokens.
