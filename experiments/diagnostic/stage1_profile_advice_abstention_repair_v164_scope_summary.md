# stage1_profile_advice_abstention_repair_v164 diagnostic summary

## Purpose

V164 tests a narrower alternative to v163 for risk #5.

Instead of adding typed profile memory into the answer prompt, v164 inherits v162 LTS and adds a profile/advice abstention repair. The intended behavior is to repair only profile-preference advice questions where the draft answer refuses despite visible user preference anchors.

This follows the external-method lesson recorded in `docs/method.md`: typed memory should act as source-backed state and query-time organization, while final claims remain grounded in raw evidence.

## Config

- Config: `configs/stage1_profile_advice_abstention_repair_v164_qwen36_no_think_build4k_cached.json`
- Parent LTS: `configs/stage1_memory_lifecycle_manifest_v162_qwen36_no_think_build4k_cached.json`
- Changed-answer scope: LongMemEval-S `profile_preference`
- Prediction run: `stage1_profile_advice_abstention_repair_v164_lme_profile_preference`
- Tests: `python -m unittest discover -s src/tests` passed, `243` tests.
- Prediction commit recorded by run: `b89181a`
- Dirty state in run manifest: expected; v164 source/config files were uncommitted during prediction.

## Method

V164 adds two repair controls:

- `enable_profile_advice_abstention_trigger`: a new opt-in trigger for `profile_preference` advice/recommendation/resource/activity/option questions.
- `uncertain_trigger_information_needs`: keeps the old broad uncertainty repair restricted to `current_state`, so profile repair is meant to use only the new narrow trigger.

The repair prompt uses raw Memory Context only. It can revise a refusal into personalized option types, criteria, or constraints, but cannot invent unsupported named places, events, shows, products, conferences, hotels, or publications.

## Metrics

LongMemEval-S profile-preference diagnostic prediction:

| Metric | Value |
|---|---:|
| Samples | `15` |
| Draft answer cache | `15` hits, `0` misses, `0` writes |
| Repair cache | `0` hits, `5` misses, `5` writes |
| Repair triggered | `5/15` |
| Repair applied | `1/15` |
| avg build tokens | `88100.333` |
| avg query tokens | `6886.200` |
| repair query tokens | `22503` |

Changed answers vs v162: `1/15`.

Dual DeepSeek flash judge on the changed answer:

| Version | strict | lenient |
|---|---:|---:|
| v162 parent answer | `1/1` = `1.000000` | `1/1` = `1.000000` |
| v164 answer | `0/1` = `0.000000` | `0/1` = `0.000000` |

Judge token usage:

| Version | prompt tokens | completion tokens | total tokens |
|---|---:|---:|---:|
| v162 parent answer | `460` | `268` | `728` |
| v164 answer | `490` | `481` | `971` |

## Badcase

Question:

> Can you recommend some interesting cultural events happening around me this weekend?

V162 answer was judged correct because it used the user's French/Spanish and cultural-exchange interests to recommend language festivals, international festivals, and cultural exchange meetups.

V164 revised that answer and added Nigerian/Mozambican culture keywords. Both judge runs marked the revised answer wrong. The failure mode is not leakage; it is an over-eager repair trigger. The trigger used draft JSON uncertainty as well as surface refusal text, so it called repair even when the final surface answer was already useful and correct.

## Decision

Do not promote v164 to LTS.

V164 worsens the primary judge metric on changed LongMemEval profile answers and increases query cost through repair calls. V162 remains the current local LTS.

## Next Step

V165 should keep the same clean idea but narrow the trigger further:

- trigger profile/advice repair only when the surface draft answer itself contains an insufficient-information refusal;
- do not use raw draft JSON uncertainty alone for profile/advice repair;
- preserve already-helpful profile answers even if draft metadata is conservative;
- run changed-answer judge before any full or LoCoMo evaluation.

## Outputs

- LME profile predictions: `outputs/diagnostic/stage1_profile_advice_abstention_repair_v164_lme_profile_preference/predictions.jsonl`
- LME profile traces: `outputs/diagnostic/stage1_profile_advice_abstention_repair_v164_lme_profile_preference/traces.jsonl`
- Changed-answer files: `outputs/diagnostic/stage1_profile_advice_abstention_repair_v164_lme_changed_vs_v162/`
- Changed-answer judge metrics snapshot: `experiments/diagnostic/stage1_profile_advice_abstention_repair_v164_lme_changed_vs_v162/metrics.json`
- Run record: `experiments/diagnostic/stage1_profile_advice_abstention_repair_v164_lme_profile_preference/`

