# v225 State/Update Organization Ledger

## Decision

Promote `configs/stage1_state_update_organization_ledger_v225_seeded_qwen36_no_think_build4k_cached.json` as the local LTS.

v225 inherits v222 prediction behavior and adds a trace-only State/Update Organization Ledger inside the Memory Lifecycle Manifest. The ledger separates source-backed active/superseded state chains from ordinary multi-value memory slots, so future state/update reasoning does not treat every fact/profile/preference value difference as a stale-state conflict.

No judge rerun is needed: full answer diff vs v222 is `0` on both benchmarks, so v225 inherits v222 DeepSeek dual flash judge accuracy.

## Clean Setting

- Method commit: `944db7d532f21eb3d8b82e47a997f840cb7be220`
- Prediction uses only question text, raw Memory Context, build-memory records, source backpointers, and prediction-time route.
- No gold answer, judge output, benchmark label, sample id, test feedback, or sample-level rule is used.
- The ledger is trace-only and is not read by retrieval, compiler, answer, repair, finalizer, or cache keys.

## Full Diff vs v222

| Benchmark | Answer diff | Prompt diff | Evidence rows diff | Retrieval hits diff | Selected-context diff | Ledger coverage |
|---|---:|---:|---:|---:|---:|---:|
| LongMemEval-S full | `0/500` | `0/500` | `0/500` | `0/500` | `0/500` | `500/500` |
| LoCoMo non-adversarial full | `0/1540` | `0/1540` | `0/1540` | `0/1540` | `0/1540` | `1540/1540` |

## Inherited Accuracy and Cost

| Benchmark | strict / lenient | Avg build / query tokens | Answer cache |
|---|---:|---:|---:|
| LongMemEval-S full | `0.834000 / 0.846000` | `85393.566 / 6580.196` | `500/0/0` |
| LoCoMo non-adversarial full | `0.793506 / 0.818831` | `62015.57402597403 / 6095.268181818182` | `1540/0/0` |

Thinking tokens are `0.0` for both build and query. Token counts are logical cold-build/query visible LLM tokens, following the project protocol.

## Ledger Signals

| Benchmark | Built update slots | Activated update slots | Activated visible update slots | Missing active source | Missing superseded source | Activated non-state multi-value |
|---|---:|---:|---:|---:|---:|---:|
| LongMemEval-S full | `2816` | `156` | `123` | `5` | `38` | `19` |
| LoCoMo non-adversarial full | `8514` | `422` | `293` | `60` | `168` | `1` |

These counts make #5 more auditable: state/update chains can be separated from ordinary multi-value fact/list memory before any future verifier, repair, or compiler behavior is added.

## Rejected Behavior Direction

Before v225, I tested fixed-set memory-source interleave offline using v222 traces. Conservative fact/list ordering still had a broad LoCoMo prompt-order surface:

- fact-only `anchor=48, memory_rows=1`: LoCoMo changed `79/1540`, LME changed `0/500`.
- fact/list `anchor=32, memory_rows=1`: LoCoMo changed `1046/1540`, LME changed `8/500`.
- fact-only `anchor=32, memory_rows=1`: LoCoMo changed `796/1540`, LME changed `4/500`.

This is not a safe next LTS direction without a narrower source/span preserving rerank or a changed-answer judge plan. v225 therefore stays trace-only.

## Dirty State Note

The LoCoMo run recorded `dirty: False`. The LME run recorded `dirty: True` because the LoCoMo experiment directory was generated in parallel before the LME summary was written. Code and config for both runs were at method commit `944db7d`; this is recorded rather than rerun for cosmetic cleanliness.

## Output Paths

- `outputs/diagnostic/stage1_state_update_organization_ledger_v225_lme_s_full/`
- `outputs/diagnostic/stage1_state_update_organization_ledger_v225_locomo_nonadv_full/`
- `experiments/diagnostic/stage1_state_update_organization_ledger_v225_lme_s_full/`
- `experiments/diagnostic/stage1_state_update_organization_ledger_v225_locomo_nonadv_full/`

## Next Step

Use v225 ledger to design a narrow state/update verifier or compiler guide that only triggers on source-backed lifecycle update chains, and explicitly blocks ordinary non-state multi-value slots from stale-conflict logic. Keep #2 rerank work source/span preserving and require narrow prompt or final evidence diff before judge.
