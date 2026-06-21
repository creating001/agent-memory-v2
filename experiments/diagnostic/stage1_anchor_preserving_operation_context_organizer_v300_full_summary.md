# v300 Anchor-Preserving Operation Context Organizer Full Summary

## Status

Rejected LTS candidate. v300 fixes most of v299's over-aggressive behavior but still causes a small LongMemEval-S regression.

The method keeps the first `32` retrieved/layout evidence rows in original order and only lets guarded-ready operation plans reorder tail raw Memory rows. Derived memory values are not rendered, no hidden rows are added, and final evidence remains raw Memory rows.

## Configuration

- Commit: `df81c5ce9a744c9b6034a6510d7038cc209a938a`
- Config: `configs/stage1_anchor_preserving_operation_context_organizer_v300_query_restore_seeded_qwen36_no_think_build4k_cached.json`
- Baseline: current LTS v298
- Prediction workers: LME `6`, LoCoMo `6`
- Organizer scope: `current_state`
- `memory_operation_context_organizer_anchor_keep=32`
- `memory_operation_context_organizer_max_plans=4`
- Prompt-visible operation guide: disabled
- Derived values rendered to prompt: `0`

## Full Metrics

Full accuracy is merged from v298 full dual judge counts plus v300 changed-output dual judge. Unchanged answers inherit v298 judgment; changed answers are judged offline with two independent `deepseek-v4-flash` runs at temperature `0` using `.env` for the API key.

| Benchmark | n | strict/lenient accuracy | avg build tokens | avg query tokens | answer diff vs v298 | prompt diff vs v298 |
|---|---:|---:|---:|---:|---:|---:|
| LongMemEval-S full | 500 | `0.832000 / 0.844000` (`416/500`, `422/500`) | `85393.566` | `6455.934` | `3` | `7` |
| LoCoMo non-adversarial full | 1540 | `0.794156 / 0.819481` (`1223/1540`, `1262/1540`) | `62015.57402597403` | `6093.9233766233765` | `1` | `3` |

## Changed-Output Judge

| Benchmark | changed answers | base strict/lenient | v300 strict/lenient | strict delta | lenient delta |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S full | `3` | `3/3`, `3/3` | `2/3`, `2/3` | `-1` | `-1` |
| LoCoMo non-adversarial full | `1` | `1/1`, `1/1` | `1/1`, `1/1` | `0` | `0` |

## Organizer Coverage

| Benchmark | organizer present | applied | changed order | ready visible plans | selected plans | planned boosted sources | tail boosted sources | anchor-preserved boosted sources | values rendered |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| LongMemEval-S full | `22` | `9` | `7` | `357` | `88` | `118` | `17` | `101` | `0` |
| LoCoMo non-adversarial full | `3` | `3` | `3` | `65` | `12` | `16` | `10` | `6` | `0` |

## Diagnosis

v300 is a better direction than v299:

- LME answer diffs drop from `10` to `3`.
- LME prompt diffs drop from `22` to `7`.
- Hard top-evidence disruption is mostly removed: LME preserves `101/118` boosted sources inside the anchor prefix.

It is still not good enough for LTS because the remaining tail reorders lose one LME strict/lenient correct answer. The next version should either raise the anchor or add a stronger safe-change gate so operation plans cannot reorder tail rows unless the target source is clearly useful and the existing answer-critical evidence remains before it.

## Decision

Do not promote v300 to LTS. Current LTS remains v298.

v300 reduces the system risk introduced by v299, but it does not match v298 full accuracy. Keep the anchor-preserving mechanism as the basis for the next safer consumer.

## Artifacts

- LME formal record: `experiments/formal/stage1_anchor_preserving_operation_context_organizer_v300_lme_s_full_df81c5c/`
- LoCoMo formal record: `experiments/formal/stage1_anchor_preserving_operation_context_organizer_v300_locomo_nonadv_full_df81c5c/`
- LME predictions: `outputs/formal/stage1_anchor_preserving_operation_context_organizer_v300_lme_s_full_df81c5c/predictions.jsonl`
- LME traces: `outputs/formal/stage1_anchor_preserving_operation_context_organizer_v300_lme_s_full_df81c5c/traces.jsonl`
- LoCoMo predictions: `outputs/formal/stage1_anchor_preserving_operation_context_organizer_v300_locomo_nonadv_full_df81c5c/predictions.jsonl`
- LoCoMo traces: `outputs/formal/stage1_anchor_preserving_operation_context_organizer_v300_locomo_nonadv_full_df81c5c/traces.jsonl`
- LME changed judge: `outputs/diagnostic/stage1_anchor_preserving_operation_context_organizer_v300_changed_vs_v298_lme/`
- LoCoMo changed judge: `outputs/diagnostic/stage1_anchor_preserving_operation_context_organizer_v300_changed_vs_v298_locomo/`

## Verification

- `python -m py_compile src/memory/compiler.py src/memory/pipeline.py src/tests/test_compiler.py`
- `python -m pyflakes src`
- `python -m unittest discover -s src/tests`
- Full LME and LoCoMo predictions
- Changed-output dual `deepseek-v4-flash` judge for answer diffs
