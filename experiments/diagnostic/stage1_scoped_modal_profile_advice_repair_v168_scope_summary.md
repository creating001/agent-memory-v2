# stage1_scoped_modal_profile_advice_repair_v168 LTS summary

## Purpose

V168 promotes the no-new-names same-domain profile/advice repair line to LTS.

It inherits v162 LTS and keeps build memory, retrieval, compiler prompt, draft answer prompt, source-grounded finalizer, current-state repair behavior, and trace-only lifecycle manifest intact. The only prediction-side addition is a narrow `profile_preference` repair for surface insufficient-information advice answers.

This directly targets risk #5: typed/source-backed memory is used for query-time preference activation and answer repair, not merely as retrieval index. It also reduces risk from v163-v167 by keeping the trigger narrow, preserving raw-source grounding, banning unsupported named examples, and scoping modal abstention repair back to current-state only.

## Config

- Config: `configs/stage1_scoped_modal_profile_advice_repair_v168_qwen36_no_think_build4k_cached.json`
- Parent LTS: `configs/stage1_memory_lifecycle_manifest_v162_qwen36_no_think_build4k_cached.json`
- Direct diagnostic parent: `configs/stage1_no_new_names_profile_advice_repair_v167_qwen36_no_think_build4k_cached.json`
- Tests: `python -m unittest discover -s src/tests` passed, `244` tests.
- Prediction commit recorded by runs: `33c7309`
- Dirty state in run manifests: expected; v168 source/config/summary files were uncommitted during prediction.

## Method

V168 repair triggers only when all conditions hold:

- route is `profile_preference`;
- the question asks for advice, recommendation, resources, activities, options, or choices;
- the final surface draft answer contains an insufficient-information refusal;
- same-domain anchors are available in visible raw Memory Context;
- the revised answer can use criteria, option types, or search terms without adding unsupported names.

No-new-names discipline:

- no parenthetical examples or `such as` examples with unseen named entities;
- no named conferences, papers, venues, products, shows, events, organizations, platforms, or brands unless the exact name appears in the question or Memory Context;
- recent/current/local requests can get source-grounded search criteria, not invented live facts.

V168 also adds `modal_abstention_information_needs` and sets it to `["current_state"]`, which removes v167's LoCoMo profile wrong-to-wrong modal repair.

## Metrics

| Benchmark | strict | lenient | Evidence |
|---|---:|---:|---|
| LongMemEval-S full | `413/500` = `0.826000` | `419/500` = `0.838000` | v168 vs v162 answer diff `2/500`; paired dual judge `0/2 -> 2/2` strict/lenient |
| LoCoMo non-adversarial full | `1216/1540` = `0.789610` | `1256/1540` = `0.815584` | v168 vs v162 answer diff `0/1540`; inherits v162 judge |

Token/call summary from full cached runs:

| Benchmark | answer cache | repair triggered | repair applied | repair query tokens | avg query tokens |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S full | `500/500` hits | `6` | `2` | `29260` | `6239.336` |
| LoCoMo non-adversarial full | `1540/1540` hits | `0` | `0` | `0` | `6047.909` |

## Changed Answers

The two LME improvements are same-domain profile/advice refusals:

- chocolate chip cookie advice now uses the user's turbinado sugar experimentation as a baking anchor;
- recent publications/conferences now uses the user's medical image analysis, multi-modal fusion, and interpretability interests as search criteria without naming unsupported conferences.

Both changed answers are dual-judge correct. The v162 parent answers were dual-judge wrong.

## Decision

Promote v168 to current local LTS.

Reasons:

- Performance: LME strict/lenient improves by `+2/+2`; LoCoMo is unchanged.
- Risk reduction: #5 now has a narrow source-backed query-time profile/advice repair path, not just trace-only lifecycle manifest.
- Clean/general: no gold answers, judge output, benchmark labels, sample ids, row indices, test feedback, sample-level rules, or unsupported named examples are used.
- Scope control: modal abstention repair is restricted to current-state; profile repair uses only the surface advice refusal trigger.

Remaining risks:

- #1 granularity/profile still relies partly on avg-turn profile and route heuristics.
- #2 top-k/context noise and route-aware context organization remain open.
- #5 still needs broader lifecycle/update/conflict reasoning beyond profile/advice refusal repair.

## Outputs

- LME full predictions: `outputs/diagnostic/stage1_scoped_modal_profile_advice_repair_v168_lme_s_full/predictions.jsonl`
- LME full traces: `outputs/diagnostic/stage1_scoped_modal_profile_advice_repair_v168_lme_s_full/traces.jsonl`
- LME changed-answer judge: `outputs/diagnostic/stage1_scoped_modal_profile_advice_repair_v168_lme_changed_vs_v162/v168_dual_judge.json`
- LoCoMo full predictions: `outputs/diagnostic/stage1_scoped_modal_profile_advice_repair_v168_locomo_nonadv_full/predictions.jsonl`
- LoCoMo full traces: `outputs/diagnostic/stage1_scoped_modal_profile_advice_repair_v168_locomo_nonadv_full/traces.jsonl`
- Metrics snapshot: `experiments/diagnostic/stage1_scoped_modal_profile_advice_repair_v168_lme_changed_vs_v162/metrics.json`
- Run records:
  - `experiments/diagnostic/stage1_scoped_modal_profile_advice_repair_v168_lme_s_full/`
  - `experiments/diagnostic/stage1_scoped_modal_profile_advice_repair_v168_locomo_nonadv_full/`

