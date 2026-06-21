# V296 Readiness-Gated Operation Guide Full Summary

## Status

Rejected LTS candidate. V296 correctly limits the method surface to
readiness-gated current_state operation plans, but rendering plan values in the
answer prompt caused LongMemEval-S regressions.

## Configuration

- Commit: `7b4c4e2`
- Config: `configs/stage1_readiness_gated_operation_guide_v296_query_restore_seeded_qwen36_no_think_build4k_cached.json`
- Change vs v294: enable `Memory Operation Plan Guide` only for `current_state`, gated by `memory_query_readiness_manifest_v1`.
- Cache protocol: v296 answer cache was seeded from v294 prediction-time traces/answers; only prompt-changed samples were regenerated.
- Clean note: seed and changed-only judge used completed prediction-time outputs and offline labels only after prediction.

## Metrics

| Benchmark | full strict/lenient | avg build tokens | avg query tokens | answer diff vs v294 | changed dual judge |
| --- | ---: | ---: | ---: | ---: | --- |
| LongMemEval-S full | `0.826000 / 0.838000` (`413/500`, `419/500`) | `85393.566` | `6328.962` | `9/500` | old `8/9`, new `4/9` |
| LoCoMo non-adversarial full | `0.794156 / 0.819481` (`1223/1540`, `1262/1540`) | `62015.57402597403` | `6094.875974025974` | `1/1540` | old `1/1`, new `1/1` |

## Diagnostics

- LME changed answers are all `current_state` and all include `Memory Operation Plan Guide`.
- LoCoMo changed answer is also `current_state` and remains correct.
- LME badcases show the risky part is not readiness gating itself, but prompt-visible derived plan values. The guide sometimes makes the model prefer stale/incorrect active values or give over-short insufficiency answers.

## Output Paths

- LME prediction: `outputs/formal/stage1_readiness_gated_operation_guide_v296_lme_s_full_7b4c4e2/predictions.jsonl`
- LoCoMo prediction: `outputs/formal/stage1_readiness_gated_operation_guide_v296_locomo_nonadv_full_7b4c4e2/predictions.jsonl`
- LME changed judge: `outputs/diagnostic/stage1_readiness_gated_operation_guide_v296_changed_vs_v294_lme/`
- LoCoMo changed judge: `outputs/diagnostic/stage1_readiness_gated_operation_guide_v296_changed_vs_v294_locomo/`

## Next Step

V297 should keep readiness-gated operation plan consumption, but remove
active/historical/scalar value rendering from the prompt. The operation plan
should act as source expansion, lifecycle/audit, and context organization
metadata, while stable state/value guides and raw rows remain the only
answer-shaping value surface.
