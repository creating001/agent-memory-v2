# stage1_long_profile_route_selected_context_v156 diagnostic

## Purpose

V156 inherits the current v154 LTS and tests whether the long-turn selected-context blanket disable can be replaced by a cleaner route-scoped, per-row policy.

The only intended method change is inside the `long_turn_precision` granularity profile:

- v154: `selected_context.enabled=false`
- v156: selected context enabled only for question-derived `profile_preference` and `current_state`, still gated by per-row anaphora, center-turn length, row count, and same-session raw-source expansion

No gold answer, judge output, benchmark label, sample id, row index, test feedback, or sample-level shortcut is used by prediction.

## Config

- Config: `configs/stage1_long_profile_route_selected_context_v156_qwen36_no_think_build4k_cached.json`
- Parent: `configs/stage1_current_state_lifecycle_ledger_v154_qwen36_no_think_build4k_cached.json`
- Prediction commit recorded by runs: `93ae03f`
- Dirty state in run manifests: expected; the v156 config and diagnostic run directories were uncommitted during prediction.
- Answer cache seed: v156 answer cache was seeded from v154 prediction traces only, with no labels or judge outputs.

## Prediction Results

### LongMemEval-S full

| Metric | v154 | v156 |
|---|---:|---:|
| selected-context applied | `0/500` | `37/500` |
| selected materialized rows avg | `0.000` | `0.296` |
| avg context chars | `19769.610` | `19800.964` |
| avg query tokens | `6179.012` | `6192.020` |
| answer cache misses | `0` | `37` |
| repair triggered / applied | `4 / 2` | `3 / 1` |
| answer changed | - | `17/500` |

Route scope:

| Route | n | selected applied | materialized rows | skipped long-center rows |
|---|---:|---:|---:|---:|
| `current_state` | `22` | `22` | `88` | `355` |
| `profile_preference` | `15` | `15` | `60` | `206` |
| other routes | `463` | `0` | `0` | `0` |

### LoCoMo non-adversarial full

LoCoMo is unchanged versus v154:

- answer diff: `0/1540`
- selected-context applied: `1536/1540`
- avg query tokens: `6047.909`
- full judge can be inherited from v154 because prediction answers are identical.

## Offline Paired Judge

Changed-answer subset: `17` LME records.

Dual `deepseek-v4-flash` judge, temperature `0`, default thinking:

| Subset | strict | lenient |
|---|---:|---:|
| v154 changed keys | `11/17` | `12/17` |
| v156 changed keys | `7/17` | `7/17` |
| paired delta | `-4` | `-5` |

Full-result implication relative to current v154 LME count: paired delta would reduce LME from `411/500` strict and `417/500` lenient to approximately `407/500` strict and `412/500` lenient. This is a performance regression, so v156 cannot become LTS.

## Badcase Conclusion

The negative cases show that row-level anaphora alone is too broad. In recommendation and current-state questions, selected context often injected nearby generic assistant/user turns into already-retrieved rows. This made answers more generic or disturbed state/time ordering, for example:

- cultural-events recommendation became broader and less aligned with the desired rubric;
- current-role duration changed from the previously correct duration to an older/stale duration;
- trip ordering changed after local context mixed unrelated same-session turns;
- NAS advice became over-abstentive despite sufficient prior evidence.

The next safer direction is not to restore the old long-turn blanket disable, but to add a question-level local-reference gate: long-turn selected context should expand adjacent turns only when the question itself has a local/deictic reference that plausibly needs neighboring dialogue, not merely because an evidence row contains words like "this" or "that".

## Decision

Reject v156 as an LTS candidate. Keep v154 as current LTS.

V156 is useful structural evidence for #3: it confirms that replacing benchmark-shaped long/short gating requires both route scope and question-level need detection; evidence-row anaphora alone is not safe enough.

## Outputs

- LME predictions: `outputs/diagnostic/stage1_long_profile_route_selected_context_v156_lme_s_full/predictions.jsonl`
- LME traces: `outputs/diagnostic/stage1_long_profile_route_selected_context_v156_lme_s_full/traces.jsonl`
- LME metrics: `experiments/diagnostic/stage1_long_profile_route_selected_context_v156_lme_s_full/metrics.json`
- LoCoMo predictions: `outputs/diagnostic/stage1_long_profile_route_selected_context_v156_locomo_nonadv_full/predictions.jsonl`
- LoCoMo traces: `outputs/diagnostic/stage1_long_profile_route_selected_context_v156_locomo_nonadv_full/traces.jsonl`
- LoCoMo metrics: `experiments/diagnostic/stage1_long_profile_route_selected_context_v156_locomo_nonadv_full/metrics.json`
- Changed subset and paired judge: `outputs/diagnostic/stage1_long_profile_route_selected_context_v156_lme_changed_vs_v154/`
