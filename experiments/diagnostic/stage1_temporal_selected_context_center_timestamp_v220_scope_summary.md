# stage1_temporal_selected_context_center_timestamp_v220 rejection summary

## Decision

V220 is rejected and does not replace v217 LTS.

V220 keeps selected-context local dialogue text, but for `temporal_lookup` wrappers it exposes timestamps only on the center turn and removes timestamps from nearby turns. This avoids hard-removing local context, but still changes enough temporal answers to hurt LoCoMo judge accuracy.

## Clean Boundary

- Prediction uses only question text, raw dialogue, source-backed typed memory, and retrieval traces.
- No gold answer, judge output, benchmark label, sample id, test feedback, or sample-level rule is used.
- Judge is run only offline after prediction.
- Retrieval hits and selected-context source ids are unchanged.

## Full Prediction Diff

| Benchmark | prompt/evidence diff | answer diff | retrieval hits diff | selected-context source-id diff | answer cache |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S full | `0/500` | `0/500` | `0/500` | `0/500` | `500/0/0` |
| LoCoMo non-adversarial full | `338/1540` | `99/1540` | `0/1540` | `0/1540` | `1203/337/337` |

## Risk And Cost

| Benchmark | avg build tokens | avg query tokens | selected-context applied | selected-context risk rows |
|---|---:|---:|---:|---:|
| LongMemEval-S full | `85393.566` | `6637.824` | `3/500` | `0` |
| LoCoMo non-adversarial full | `62015.57402597403` | `6048.207792207792` | `1536/1540` | `5841` |

Compared with v217, LoCoMo avg query tokens drop from `6095.268181818182` to `6048.207792207792`, but selected-context risk rows remain `5841`. The token reduction is too small to justify the answer regressions.

## Changed-Answer Judge

| Benchmark | changed answers | v217 strict/lenient | v220 strict/lenient | delta |
|---|---:|---:|---:|---:|
| LongMemEval-S full | `0` | inherited | inherited | `0 / 0` |
| LoCoMo non-adversarial full | `99` | `63/99`, `65/99` | `59/99`, `62/99` | `-4 / -3` |

Derived LoCoMo full accuracy would become strict/lenient `0.790909 / 0.816883`, down from v217 `0.793506 / 0.818831`. This fails the LTS requirement.

## Diagnosis

V218, v219, and v220 together show that selected-context temporal wrappers are useful to the reader even when they carry risk. Removing rows, removing temporal rows, or removing nearby timestamps all reduce prompt/cost or perceived risk but reduce judge accuracy. The next direction should not mutate prompt-visible selected-context formatting directly. Prefer trace-only scoring plus a second-stage rerank or compiler decision that changes source ordering only when evidence support is strong.

## Artifacts

- Method commit: `4ddfe42`
- Config: `configs/stage1_temporal_selected_context_center_timestamp_v220_seeded_qwen36_no_think_build4k_cached.json`
- LME run: `experiments/diagnostic/stage1_temporal_selected_context_center_timestamp_v220_lme_s_full/`
- LoCoMo run: `experiments/diagnostic/stage1_temporal_selected_context_center_timestamp_v220_locomo_nonadv_full/`
- Changed judge outputs: `outputs/diagnostic/stage1_temporal_selected_context_center_timestamp_v220_changed_vs_v217/`
