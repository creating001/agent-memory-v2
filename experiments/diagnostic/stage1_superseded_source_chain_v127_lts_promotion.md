# V127 LTS Promotion

## Decision

Promote `configs/stage1_superseded_source_chain_v127_qwen36_no_think_build4k_cached.json` as the current local LTS.

V127 is a source-backed memory organization method. It does not expose typed memory text as reader evidence. Instead, build-memory records are used as clean query-time organization signals that point back to raw Memory Context rows. V126 introduced profile/current source interleave; V127 extends that mechanism by allowing active/superseded update chains to contribute source backpointers for `profile_preference` and `current_state`.

This is a better fit for the project direction than hard prompt hacks: it synthesizes useful ideas from memory activation, source expansion, and update/conflict tracking into a general agent-memory mechanism with explicit source grounding.

## Clean Boundary

- Prediction uses question text, raw Memory Context, build-memory records generated from dialogue, source backpointers, and prediction-time route.
- It does not use gold/reference answers, judge outputs, benchmark labels, sample ids/qids, row indices, or test feedback.
- Typed memory text is not shown to the answer model as standalone evidence.
- Judge and labels are used only offline after prediction.

## Risk Audit

| Goal risk | Status |
|---|---|
| #1 granularity/profile design-for-benchmark | still open; v127 inherits the historical profile split |
| #2 multi-route top-k/context noise/rerank | still open; v134 showed hard pruning can hurt coverage |
| #3 selected-context long/short heuristic | partially reduced by v125; v135 hard neighbor gate rejected |
| #4 mechanical finalizer | reduced by v121/v125 source-grounded guard |
| #5 build-memory organization/update/conflict/query-time reasoning | reduced by v126/v127 source-backed memory source interleave and active/superseded chain |

## Judge Evidence

V126 profile/current source interleave:

| Benchmark subset | Baseline | Candidate | Delta |
|---|---:|---:|---:|
| LoCoMo profile/current `50` | strict/lenient `0.720000 / 0.720000` | `0.800000 / 0.800000` | `+4 / +4` |
| LongMemEval profile/current `37` | strict/lenient `0.648649 / 0.675676` | `0.621622 / 0.648649` | `-1 / -1` |

V127 active/superseded source chain on top of v126:

| Benchmark changed subset | V126 | V127 | Delta |
|---|---:|---:|---:|
| LongMemEval changed prompts `5` | strict/lenient `0.400000 / 0.400000` | `0.800000 / 0.800000` | `+2 / +2` |
| LoCoMo changed prompts `24` | strict/lenient `0.666667 / 0.666667` | `0.708333 / 0.750000` | `+1 / +2` |

Inherited route-only aggregate:

| Benchmark | Previous LTS | V127 aggregate | Delta |
|---|---:|---:|---:|
| LongMemEval-S full | v125/v116 inherited `0.812000 / 0.834000` | `0.814000 / 0.836000` | `+1 / +1` vs v125 inherited |
| LoCoMo non-adversarial full | v125 route-only `0.789610 / 0.807792` | `0.792857 / 0.811688` | `+5 / +6` |

The LongMemEval and LoCoMo full values are inherited route-only aggregates, not fresh full answer/judge reruns. They are acceptable for local LTS promotion because the changed scopes are small, clean, route-contained, and judged directly.

## Outputs

- V126 LoCoMo paired judge: `experiments/diagnostic/stage1_memory_source_interleave_v126_locomo_profile_state_route_all/paired_judge_comparison_vs_v125.json`
- V126 LME paired judge: `experiments/diagnostic/stage1_memory_source_interleave_v126_lme_profile_state_route_all/paired_judge_comparison_vs_v116.json`
- V127 LoCoMo paired judge: `experiments/diagnostic/stage1_superseded_source_chain_v127_locomo_changed_prompts/paired_judge_comparison_vs_v126.json`
- V127 LME paired judge: `experiments/diagnostic/stage1_superseded_source_chain_v127_lme_changed_prompts/paired_judge_comparison_vs_v126.json`
- V127 LoCoMo inherited aggregate: `experiments/diagnostic/stage1_superseded_source_chain_v127_locomo_nonadv_full_route_only_merge/deepseek_dual_judge_route_only_merge_vs_v126.json`
- V127 LME inherited aggregate: `experiments/diagnostic/stage1_superseded_source_chain_v127_lme_s_full_route_only_merge/deepseek_dual_judge_route_only_merge_vs_v126.json`

## Next

Do not keep extending #5 by small source-order tweaks. The next priority is #2 context noise/rerank/budget or #1 profile generalization, with a src cleanup pass before another broad algorithm variant.
