# v306 Operation Budget Protected Source Chain Full Summary

## Decision

Do not promote v306 to LTS.

v306 adds a configurable context-budget protection hook for raw hits emitted by `build_memory_operation_source_expansion`. The hook is clean and ablatable, but on the full LME/LoCoMo runs it did not change retrieval, compiled evidence, prompts, or answers relative to v305.

## Clean Setting

- Algorithm commit: `fa7d7cf0d50b85e6a099699462fc939b37f47b91`
- Config: `configs/stage1_operation_budget_protected_source_chain_v306_query_restore_seeded_qwen36_no_think_build4k_cached.json`
- No gold answer, judge output, benchmark label, sample id, test feedback, or sample-level rule is used by prediction.
- Full judge accuracy is inherited from v305 because both benchmarks have zero answer/prompt/evidence diff vs v305.

## Formal Runs

- LME: `experiments/formal/stage1_operation_budget_protected_source_chain_v306_lme_s_full_fa7d7cf/`
- LoCoMo: `experiments/formal/stage1_operation_budget_protected_source_chain_v306_locomo_nonadv_full_fa7d7cf/`
- LME predictions: `outputs/formal/stage1_operation_budget_protected_source_chain_v306_lme_s_full_fa7d7cf/predictions.jsonl`
- LoCoMo predictions: `outputs/formal/stage1_operation_budget_protected_source_chain_v306_locomo_nonadv_full_fa7d7cf/predictions.jsonl`

## Full Metrics

| Benchmark | strict/lenient | counts | avg build tokens | avg query tokens |
|---|---:|---:|---:|---:|
| LongMemEval-S full | `0.834000 / 0.846000` | `417/500`, `423/500` | `85393.566` | `6455.588` |
| LoCoMo non-adversarial full | `0.794156 / 0.819481` | `1223/1540`, `1262/1540` | `62015.57402597403` | `6093.879220779221` |

## Diff vs v305

| Benchmark | answer diff | prompt diff | evidence diff | retrieval diff | context-budget protected overflow |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S full | `0/500` | `0/500` | `0/500` | `0/500` | `0` samples |
| LoCoMo non-adversarial full | `0/1540` | `0/1540` | `0/1540` | `0/1540` | `0` samples |

LME still has operation source expansion applied/selected/emitted `1/1/1`, and LoCoMo has `0/0/0`. The protected-budget hook did not fire because the emitted operation source was not present in `pre_context_budget_hits`; it was lost before context-budget retention.

## Lesson

The useful next fix is not a wider budget rule. The operation source expansion consumer must first make sure an emitted raw source actually enters the candidate pool when prior overflow utilities have already occupied the tail. v307 should make this explicit with a separate, ablatable overflow-preservation policy instead of silently relying on the old `tail_rescue` behavior.
