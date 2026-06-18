# V176 Cross-Route Profile Advice Repair LTS

## Decision

Promote v176 to the current local LTS.

v176 inherits v175 and adds a narrow cross-route profile/advice abstention repair trigger. It reduces #5 query-time profile/event memory reasoning risk by catching advice, suggestion, and decision-support questions that were routed as `fact_lookup` or `list_count`, while keeping the existing no-new-names verifier discipline.

## Method

- Parent LTS: v175 (`52239cb`).
- Config: `configs/stage1_cross_route_profile_advice_repair_v176_qwen36_no_think_build4k_cached.json`.
- Trigger: `profile_advice_abstention_review` for cross-route advice refusals.
- Scope:
  - routes: `fact_lookup`, `list_count`;
  - draft answer must be an insufficient-information refusal;
  - question must ask for advice, suggestions, tips, recommendations, or decision support;
  - prediction-time `evidence_report` must contain at least one source-backed support item;
  - blocks specific external-name requests such as company, state, composer, shop, book, movie, show, restaurant, venue, product, or brand names.
- The repair prompt reuses profile advice rules: answer with source-backed criteria, option types, or constraints; do not invent unsupported names.

## Full Results

| Benchmark | Answer diff vs v175 | Changed-answer dual judge | Patched full strict/lenient |
|---|---:|---:|---:|
| LongMemEval-S full | `2/500` | strict `0/2 -> 1/2`, lenient `0/2 -> 2/2` | `0.834000 / 0.846000` (`417/500`, `423/500`) |
| LoCoMo non-adversarial full | `0/1540` | no judge needed | `0.792857 / 0.818182` (`1221/1540`, `1260/1540`) |

Changed LME answers:

- `39f2adfa686f1fa663896c83`: cocktail suggestion refusal -> source-backed Pimm's Cup / summer drink suggestion; lenient-correct, strict split.
- `676f08cb0b1213adf24077d5`: high-school reunion refusal -> source-backed decision-support answer; strict/lenient correct.

## Cost

- LME avg query tokens: `6291.590`; avg build tokens: `85393.566`; repair triggered/applied `11/5`, repair miss/write `3/3`.
- LoCoMo avg query tokens: `6064.337`; avg build tokens: `62015.574`; repair triggered/applied `5/3`, repair miss/write `0/0`.
- The change remains below the hard query-token limit, but avg query tokens are still above the preferred `6k` target; #2 context organization remains open.

## Risk Impact

- #5 profile/event query-time reasoning: reduced. Advice questions that are semantically profile/preference questions but routed as fact/list now get the same source-grounded verifier.
- #4 clean verifier risk: unchanged or slightly reduced. The no-new-names rule remains active and v176 blocks specific external-name requests.
- #1 granularity/profile, #2 top-k/context noise, #3 selected-context generalization, and broader lifecycle/update/conflict reasoning remain open.

## Artifacts

- LME full run: `experiments/diagnostic/stage1_cross_route_profile_advice_repair_v176_lme_s_full/`
- LoCoMo full run: `experiments/diagnostic/stage1_cross_route_profile_advice_repair_v176_locomo_nonadv_full/`
- Changed-answer judge: `experiments/diagnostic/stage1_cross_route_profile_advice_repair_v176_changed_vs_v175/`
- Changed subset predictions/labels: `outputs/diagnostic/stage1_cross_route_profile_advice_repair_v176_changed_vs_v175/`
- Full predictions/traces:
  - `outputs/diagnostic/stage1_cross_route_profile_advice_repair_v176_lme_s_full/`
  - `outputs/diagnostic/stage1_cross_route_profile_advice_repair_v176_locomo_nonadv_full/`
