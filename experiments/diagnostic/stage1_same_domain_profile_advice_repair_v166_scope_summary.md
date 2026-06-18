# stage1_same_domain_profile_advice_repair_v166 diagnostic summary

## Purpose

V166 continues the #5 profile/advice repair line after v165.

V165 safely limited repair to surface insufficient-information answers but produced no answer changes. V166 keeps the same trigger and strengthens the repair rules: when raw Memory Context has same-domain preference anchors, repair may answer with preference-aligned criteria, option types, or search terms instead of requiring exact named options.

## Config

- Config: `configs/stage1_same_domain_profile_advice_repair_v166_qwen36_no_think_build4k_cached.json`
- Parent diagnostic: `configs/stage1_surface_profile_advice_repair_v165_qwen36_no_think_build4k_cached.json`
- Parent LTS: `configs/stage1_memory_lifecycle_manifest_v162_qwen36_no_think_build4k_cached.json`
- Prediction run: `stage1_same_domain_profile_advice_repair_v166_lme_profile_preference`
- Tests: `python -m unittest discover -s src/tests` passed, `244` tests.
- Prediction commit recorded by run: `2d99724`
- Dirty state in run manifest: expected; v166 source/config files were uncommitted during prediction.

## Method

V166 keeps the safe v165 trigger:

- only `profile_preference` routes;
- only advice/recommendation/resource/activity/option questions;
- only when the final surface draft answer itself contains an insufficient-information refusal;
- broad JSON uncertainty remains restricted to `current_state`.

The new repair rules allow same-domain preference transfer, for example using prior hotel feature preferences for another hotel search or prior baking experiments for related baking advice. They also tell the model not to transfer unrelated anchors across domains and not to invent current/live facts.

## Metrics

LongMemEval-S profile-preference diagnostic prediction:

| Metric | Value |
|---|---:|
| Samples | `15` |
| Draft answer cache | `15` hits, `0` misses, `0` writes |
| Repair cache | `0` hits, `4` misses, `4` writes |
| Repair triggered | `4/15` |
| Repair applied | `3/15` |
| avg build tokens | `88100.333` |
| avg query tokens | `6664.000` |
| repair query tokens | `19170` |

Changed answers vs v162: `3/15`.

Dual DeepSeek flash judge on the changed answers:

| Version | strict | lenient |
|---|---:|---:|
| v162 parent answers | `0/3` = `0.000000` | `0/3` = `0.000000` |
| v166 answers | `3/3` = `1.000000` | `3/3` = `1.000000` |

If patched into the v162 LongMemEval-S full count, this slice would imply LME strict/lenient `414/500` and `420/500`, but v166 is not eligible for LTS because of the clean issue below.

## Clean Issue

V166 is accuracy-positive but not clean enough to promote.

One changed answer recommended "MICCAI" and "IPMI" as example conference names. These names were not present in the visible Memory Context for that sample. Even though judge marked the answer correct, this violates the repair rule that unsupported named conferences, publications, venues, products, shows, or events must not be introduced.

The right next version is not to accept v166, but to keep the same trigger and same-domain repair idea while enforcing no-new-names more strongly.

## Decision

Do not promote v166 to LTS.

V166 is an important positive direction for #5 and profile/advice performance, but it still has a source-grounding risk. V162 remains the current local LTS.

## Next Step

V167 should preserve the v166 gains while removing unsupported named examples:

- no "such as <proper noun>" examples unless the name appears in the question or Memory Context;
- for recent/current/local requests, answer with generic criteria/search directions only;
- rerun the same 15 LME profile examples and judge only changed answers.

## Outputs

- LME profile predictions: `outputs/diagnostic/stage1_same_domain_profile_advice_repair_v166_lme_profile_preference/predictions.jsonl`
- LME profile traces: `outputs/diagnostic/stage1_same_domain_profile_advice_repair_v166_lme_profile_preference/traces.jsonl`
- Changed-answer files: `outputs/diagnostic/stage1_same_domain_profile_advice_repair_v166_lme_changed_vs_v162/`
- Changed-answer judge metrics snapshot: `experiments/diagnostic/stage1_same_domain_profile_advice_repair_v166_lme_changed_vs_v162/metrics.json`
- Run record: `experiments/diagnostic/stage1_same_domain_profile_advice_repair_v166_lme_profile_preference/`

