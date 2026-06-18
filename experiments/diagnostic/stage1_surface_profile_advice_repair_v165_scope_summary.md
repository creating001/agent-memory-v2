# stage1_surface_profile_advice_repair_v165 diagnostic summary

## Purpose

V165 fixes the v164 trigger failure.

V164 trusted conservative draft JSON uncertainty and repaired one already-correct surface answer. V165 keeps the same clean repair idea but triggers profile/advice repair only when the final surface draft answer itself contains an insufficient-information refusal.

## Config

- Config: `configs/stage1_surface_profile_advice_repair_v165_qwen36_no_think_build4k_cached.json`
- Parent LTS: `configs/stage1_memory_lifecycle_manifest_v162_qwen36_no_think_build4k_cached.json`
- Direct parent diagnostic: `configs/stage1_profile_advice_abstention_repair_v164_qwen36_no_think_build4k_cached.json`
- Prediction run: `stage1_surface_profile_advice_repair_v165_lme_profile_preference`
- Tests: `python -m unittest discover -s src/tests` passed, `243` tests.
- Prediction commit recorded by run: `e9d4d61`
- Dirty state in run manifest: expected; v165 source/config files were uncommitted during prediction.

## Method

The only method change from v164 is trigger narrowing:

- profile/advice repair still applies only to `profile_preference` advice/recommendation/resource/activity/option questions;
- broad `uncertain_trigger` remains restricted to `current_state`;
- profile/advice repair now requires an insufficient-information phrase in the final surface draft answer;
- raw draft JSON metadata such as `sufficient=false` or `answer_type=unknown` cannot trigger profile/advice repair on its own.

This keeps the clean setting: prediction uses only question text, route, draft answer artifacts, raw Memory Context, and source-linked memory state. It does not use gold answers, judge outputs, benchmark labels, sample ids, row indices, test feedback, or sample-level rules.

## Metrics

LongMemEval-S profile-preference diagnostic prediction:

| Metric | Value |
|---|---:|
| Samples | `15` |
| Draft answer cache | `15` hits, `0` misses, `0` writes |
| Repair cache | `0` hits, `4` misses, `4` writes |
| Repair triggered | `4/15` |
| Repair applied | `0/15` |
| avg build tokens | `88100.333` |
| avg query tokens | `6734.400` |
| repair query tokens | `18061` |

Answer diff vs v162: `0/15`.

Because answers are identical to v162 on this slice, changed-answer judge is unnecessary; v165 inherits v162 correctness for these 15 profile-preference examples.

## Diagnosis

V165 fixes v164's over-repair risk but produces no answer improvement.

The triggered repair cases are the surface refusals for publications/conferences, Miami hotel, show/movie, and chocolate-chip-cookie advice. Repair kept all four answers. This points to an evidence-coverage bottleneck rather than a repair-prompt bottleneck: the necessary user anchors are not reliably present in the repair Memory Context.

## Decision

Do not promote v165 to LTS.

V165 is safer than v164 but answer-identical to v162 while adding repair calls and query-token cost. It does not reduce a current LTS risk enough to justify replacing v162.

## Next Step

Move from repair prompting to profile/advice evidence coverage:

- keep the surface-refusal trigger as a safe diagnostic hook;
- improve source-backed retrieval/context organization so durable preferences and prior successful examples enter the visible Memory Context;
- avoid broad profile guides that make the answer over-abstain;
- judge changed answers before running LoCoMo or full evaluations.

## Outputs

- LME profile predictions: `outputs/diagnostic/stage1_surface_profile_advice_repair_v165_lme_profile_preference/predictions.jsonl`
- LME profile traces: `outputs/diagnostic/stage1_surface_profile_advice_repair_v165_lme_profile_preference/traces.jsonl`
- Answer diff files: `outputs/diagnostic/stage1_surface_profile_advice_repair_v165_lme_changed_vs_v162/`
- Run record: `experiments/diagnostic/stage1_surface_profile_advice_repair_v165_lme_profile_preference/`

