# v271 Explicit Date Temporal Route Full Summary

## Purpose

Test whether explicit date/month-year recognition plus temporal-over-recent routing improves source coverage for date-scoped questions. v271 inherits v269 and routes month/year expressions such as `July 2023` to `temporal_lookup`; it also enables `route.temporal_priority_over_recent=true`.

## Configuration

- config: `configs/stage1_explicit_date_temporal_route_v271_seeded_qwen36_no_think_build4k_cached.json`
- method commit: `f40119b`
- parent LTS: v269 `configs/stage1_memory_activation_utility_v269_seeded_qwen36_no_think_build4k_cached.json`
- clean setting: prediction uses no gold answer, judge output, benchmark tags, sample ids, test feedback, labels, or sample-level rules.

## Full Diff

v271 vs v269 full:

```text
LME: answer_diff=5/500, prompt_diff=9, final_evidence_diff=2, retrieval_diff=0, pre_context_budget_diff=0, route_diff=10, token_diff=9, answer_cache=491/9
LoCoMo: answer_diff=75/1540, prompt_diff=168, final_evidence_diff=168, retrieval_diff=168, pre_context_budget_diff=168, route_diff=183, token_diff=168, answer_cache=1373/167
```

## Token Cost

| Benchmark | v269 avg query tokens | v271 avg query tokens | delta |
|---|---:|---:|---:|
| LongMemEval-S full | `6462.478` | `6376.384` | `-86.094` |
| LoCoMo non-adversarial full | `6094.017532467533` | `6013.757792207793` | `-80.25974025974028` |

Build tokens are unchanged: LME `85393.566`, LoCoMo `62015.57402597403`.

## Changed-Answer Judge

Dual `deepseek-v4-flash`, temperature `0`, default thinking:

| Benchmark | changed answers | base strict/lenient | new strict/lenient | delta |
|---|---:|---:|---:|---:|
| LongMemEval-S full | `5` | `4/5` strict, `5/5` lenient | `2/5` strict, `3/5` lenient | `-2 / -2` |
| LoCoMo non-adversarial full | `75` | `58/75` strict, `59/75` lenient | `45/75` strict, `45/75` lenient | `-13 / -14` |

Judge output paths:

```text
outputs/diagnostic/stage1_explicit_date_temporal_route_v271_lme_full_changed_vs_v269/base_dual_judge.json
outputs/diagnostic/stage1_explicit_date_temporal_route_v271_lme_full_changed_vs_v269/new_dual_judge.json
outputs/diagnostic/stage1_explicit_date_temporal_route_v271_locomo_full_changed_vs_v269/base_dual_judge.json
outputs/diagnostic/stage1_explicit_date_temporal_route_v271_locomo_full_changed_vs_v269/new_dual_judge.json
```

## Validation

```text
python -m json.tool configs/stage1_explicit_date_temporal_route_v271_seeded_qwen36_no_think_build4k_cached.json
python -m py_compile src/memory/route.py src/tests/test_route.py
python -m unittest src.tests.test_route
python -m unittest discover -s src/tests
git diff --check
```

Observed full unit-test result: `350` tests passed.

## Decision

Do not promote v271 to LTS.

Rationale: v271 reduces query tokens but substantially hurts judge accuracy. The route policy is too broad: explicit dates should not automatically override fact/list/current-state information needs. The useful part is narrower: when `latest/recent/current` conflicts with an explicit date expression, temporal routing may be appropriate.

## Outputs

```text
outputs/diagnostic/stage1_explicit_date_temporal_route_v271_lme_full/predictions.jsonl
outputs/diagnostic/stage1_explicit_date_temporal_route_v271_lme_full/traces.jsonl
outputs/diagnostic/stage1_explicit_date_temporal_route_v271_locomo_full/predictions.jsonl
outputs/diagnostic/stage1_explicit_date_temporal_route_v271_locomo_full/traces.jsonl
experiments/diagnostic/stage1_explicit_date_temporal_route_v271_lme_probe50/
experiments/diagnostic/stage1_explicit_date_temporal_route_v271_locomo_probe50/
experiments/diagnostic/stage1_explicit_date_temporal_route_v271_lme_full/
experiments/diagnostic/stage1_explicit_date_temporal_route_v271_locomo_full/
```

## Next Steps

1. Replace v271 with a narrower policy: explicit date should only override `latest/recent/current` routing, not fact/list routes.
2. Keep `temporal_priority_over_recent=false` for broad duration/latest cases that rely on current-state context.
3. Judge any changed answers before considering LTS promotion.
