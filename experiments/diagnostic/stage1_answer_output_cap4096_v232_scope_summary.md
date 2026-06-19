# V232 Answer Output Cap Guard Summary

## Decision

V232 does not replace v231 as LTS.

V232 is a clean, general cost-guard diagnostic: it lowers answer and repair `max_output_tokens` from `16384` to `4096`, seeds unchanged answer-cache entries from v231 `answer_draft`, and regenerates only rows whose v231 answer completion exceeded the new cap. This reduces average query tokens, but it changes one LongMemEval-S answer from correct to wrong. Under the current LTS rule, a version that regresses a benchmark accuracy cannot replace the LTS.

## Clean Boundary

- Prediction uses only question text, raw Memory Context, visible metadata, and build-stage memory generated before the question.
- No gold answer, judge output, benchmark label, sample id, row index, test feedback, or sample-level rule is used.
- The changed-answer paired judge is offline evaluation only and is not consumed by prediction, retrieval, compiler, answer, repair, finalizer, cache construction, or later prediction runs.
- V232 changes only generation length budget and cache namespace; retrieval, compiler, finalizer, repair triggers, source-backed ledgers, and prompt organization remain inherited from v231.

## Full Prediction And Judge Evidence

| Benchmark | Prediction diff vs v231 | Token cost | Changed-answer dual judge | Derived full accuracy | Decision |
|---|---:|---:|---:|---:|---|
| LongMemEval-S full | answer diff `1/500` | avg build/query `85393.566 / 6605.952` | v231 `1/1`, v232 `0/1` strict/lenient | v232 `0.832000 / 0.844000` | regress vs v231 `0.834000 / 0.846000`, not LTS |
| LoCoMo non-adversarial full | answer diff `3/1540` | avg build/query `62015.57402597403 / 6070.648701298701` | v231 `1/3`, v232 `2/3` strict/lenient | v232 `0.794156 / 0.819481` | improves LoCoMo, but LME regression blocks LTS |

Changed rows:

| Benchmark | Record | Gold | v231 | v232 | Judge result |
|---|---|---|---|---|---|
| LME | `8c6ec8aa7a13c8b4b8ec3d1a` | `Five months ago` | `5 months` | `The provided information is not enough.` | correct -> wrong |
| LoCoMo | `211056f99bbbef8b9615fb93` | `filmmaker.` | `**Director**` | `Filmmaker (or Director)` | correct -> correct |
| LoCoMo | `21f5a526bb7978490a1feb58` | `2021` | `The provided information is not enough.` | `2022` | wrong -> wrong |
| LoCoMo | `01ce76a2b43dbc8ed2465432` | `Dad` | `insufficient` | `Dave's dad` | wrong -> correct |

## Diagnosis

The output cap is directionally useful as a query-cost and runaway-generation guard: it lowers average query tokens by `31.872` on LME and `30.34350649350654` on LoCoMo. However, the LME changed row shows that a hard cap can shift a temporal answer into abstention. This is an answer-protocol issue, not a retrieval or memory-management improvement.

For the new Agent Memory goal, the lesson is to replace hard output truncation with a more systematic source-grounded answer contract: generate a short answer first, then run a compact consistency verifier over numbers, time, entity/speaker, state conflicts, and unsupported claims. A pure max-token cap is too blunt to be an LTS method.

## Artifacts

- Config: `configs/stage1_answer_output_cap4096_v232_seeded_qwen36_no_think_build4k_cached.json`
- Method commit: `f6de1700397c2e3febea4cf24cd3604bef6f33d0`
- LME full: `experiments/diagnostic/stage1_answer_output_cap4096_v232_lme_s_full/`
- LoCoMo full: `experiments/diagnostic/stage1_answer_output_cap4096_v232_locomo_nonadv_full/`
- Changed-answer judge: `experiments/diagnostic/stage1_answer_output_cap4096_v232_changed_vs_v231/`
- Outputs: `outputs/diagnostic/stage1_answer_output_cap4096_v232_*`

## Next

- Keep v231 as current LTS.
- Do not use a simple answer `max_output_tokens=4096` cap as the next LTS change.
- If generation runaway is revisited, use a structured answer-first protocol or source-grounded verifier that can preserve early correct answers without causing temporal abstention regressions.
