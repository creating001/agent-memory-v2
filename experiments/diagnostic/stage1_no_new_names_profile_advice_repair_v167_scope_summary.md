# stage1_no_new_names_profile_advice_repair_v167 diagnostic summary

## Purpose

V167 fixes v166's no-new-names clean failure while preserving the same-domain profile/advice repair direction.

V166 improved LongMemEval profile answers but introduced unsupported conference names. V167 keeps the surface-refusal trigger and same-domain criteria/type answer, while explicitly forbidding parenthetical examples, `such as` examples, and unsupported named entities.

## Config

- Config: `configs/stage1_no_new_names_profile_advice_repair_v167_qwen36_no_think_build4k_cached.json`
- Parent diagnostic: `configs/stage1_same_domain_profile_advice_repair_v166_qwen36_no_think_build4k_cached.json`
- Parent LTS: `configs/stage1_memory_lifecycle_manifest_v162_qwen36_no_think_build4k_cached.json`
- Tests: `python -m unittest discover -s src/tests` passed, `244` tests.
- Prediction commit recorded by runs: `b2084af`
- Dirty state in run manifests: expected; v167 source/config files were uncommitted during prediction.

## Full Diff

| Benchmark | full answer diff vs v162 | changed-answer judge delta |
|---|---:|---:|
| LongMemEval-S full | `2/500` | strict/lenient `0/2 -> 2/2` |
| LoCoMo non-adversarial full | `1/1540` | strict/lenient `0/1 -> 0/1` |

Patched full metrics:

| Benchmark | v167 strict | v167 lenient |
|---|---:|---:|
| LongMemEval-S full | `413/500` = `0.826000` | `419/500` = `0.838000` |
| LoCoMo non-adversarial full | `1216/1540` = `0.789610` | `1256/1540` = `0.815584` |

Token/call summary from full cached runs:

| Benchmark | answer cache | repair triggered | repair applied | repair query tokens | avg query tokens |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S full | `500/500` hits | `6` | `2` | `29367` | `6239.550` |
| LoCoMo non-adversarial full | `1540/1540` hits | `1` | `1` | `5871` | `6051.721` |

## Diagnosis

V167 is accuracy-positive and fixes v166's unsupported-name issue on LongMemEval.

The two LME changed answers are clean same-domain criteria/type repairs:

- chocolate chip cookie advice uses the user's turbinado sugar experimentation as a baking anchor;
- recent publications/conferences uses the user's medical image analysis and explainable AI interests without naming unsupported conferences.

LoCoMo does not lose accuracy, but the one changed answer reveals a remaining overreach: `modal_abstention_review` can fire on a `profile_preference` question even when the question is not a profile/advice refusal. It changed one answer from wrong to wrong, adding risk and cost without benefit.

## Decision

Do not promote v167 to LTS.

V167 is close, but v168 should remove the unnecessary profile/modal trigger before promotion. V162 remains current local LTS until that risk is removed and full diff is rechecked.

## Next Step

V168 should restrict modal abstention repair to the original current-state scope and let `profile_preference` use only the surface profile/advice trigger. Expected result:

- keep the LME `+2/+2` gains;
- remove the LoCoMo wrong->wrong answer diff;
- reduce #5 profile/advice risk and repair cost.

## Outputs

- LME full predictions: `outputs/diagnostic/stage1_no_new_names_profile_advice_repair_v167_lme_s_full/predictions.jsonl`
- LME full traces: `outputs/diagnostic/stage1_no_new_names_profile_advice_repair_v167_lme_s_full/traces.jsonl`
- LoCoMo full predictions: `outputs/diagnostic/stage1_no_new_names_profile_advice_repair_v167_locomo_nonadv_full/predictions.jsonl`
- LoCoMo full traces: `outputs/diagnostic/stage1_no_new_names_profile_advice_repair_v167_locomo_nonadv_full/traces.jsonl`
- LME changed-answer judge metrics: `experiments/diagnostic/stage1_no_new_names_profile_advice_repair_v167_lme_changed_vs_v162/metrics.json`
- LoCoMo changed-answer judge metrics: `experiments/diagnostic/stage1_no_new_names_profile_advice_repair_v167_locomo_changed_vs_v162/metrics.json`

