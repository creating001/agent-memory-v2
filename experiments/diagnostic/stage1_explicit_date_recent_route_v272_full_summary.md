# v272 Explicit Date Recent Route Full Summary

## Purpose

Promote the useful part of v271 into a narrow, general route policy. v272 inherits v269 and only lets explicit date/month-year text override `latest/recent/current` routing when both signals appear in the same question. Explicit dates alone do not preempt fact/list/profile routes.

## Configuration

- config: `configs/stage1_explicit_date_recent_route_v272_seeded_qwen36_no_think_build4k_cached.json`
- method commit: `82a1a2a`
- parent LTS: v269 `configs/stage1_memory_activation_utility_v269_seeded_qwen36_no_think_build4k_cached.json`
- clean setting: prediction uses no gold answer, judge output, benchmark tags, sample ids, test feedback, labels, or sample-level rules.

## Full Results

| Benchmark | strict / lenient | avg build tokens | avg query tokens | note |
|---|---:|---:|---:|---|
| LongMemEval-S full | `0.832000 / 0.844000` | `85393.566` | `6462.478` | inherited from v269; full diff `0` |
| LoCoMo non-adversarial full | `0.794156 / 0.819481` | `62015.57402597403` | `6093.84025974026` | changed-answer paired judge delta `0 / 0` |

## Full Diff

v272 vs v269 full:

```text
LME: answer_diff=0/500, prompt_diff=0, final_evidence_diff=0, retrieval_diff=0, pre_context_budget_diff=0, memory_hits_diff=0, memory_source_hits_diff=0, route_diff=0, token_diff=0, answer_cache=500/0
LoCoMo: answer_diff=2/1540, prompt_diff=2, final_evidence_diff=2, retrieval_diff=2, pre_context_budget_diff=2, memory_hits_diff=0, memory_source_hits_diff=0, route_diff=1, token_diff=2, answer_cache=1538/2
```

The single LoCoMo route change is `current_state -> temporal_lookup` for an explicit-date + recent/current conflict. The second LoCoMo answer diff came from evidence/retrieval prompt drift without a route change.

## Token Cost

| Benchmark | v269 avg query tokens | v272 avg query tokens | delta |
|---|---:|---:|---:|
| LongMemEval-S full | `6462.478` | `6462.478` | `0` |
| LoCoMo non-adversarial full | `6094.017532467533` | `6093.84025974026` | `-0.17727272727279342` |

Build tokens are unchanged: LME `85393.566`, LoCoMo `62015.57402597403`.

## Changed-Answer Judge

Dual `deepseek-v4-flash`, temperature `0`, default thinking:

| Benchmark | changed answers | base strict/lenient | new strict/lenient | delta |
|---|---:|---:|---:|---:|
| LongMemEval-S full | `0` | inherited | inherited | `0 / 0` |
| LoCoMo non-adversarial full | `2` | `1/2` strict, `1/2` lenient | `1/2` strict, `1/2` lenient | `0 / 0` |

Judge output paths:

```text
outputs/diagnostic/stage1_explicit_date_recent_route_v272_locomo_full_changed_vs_v269/base_dual_judge.json
outputs/diagnostic/stage1_explicit_date_recent_route_v272_locomo_full_changed_vs_v269/new_dual_judge.json
```

## Validation

```text
python -m json.tool configs/stage1_explicit_date_recent_route_v272_seeded_qwen36_no_think_build4k_cached.json
python -m py_compile src/memory/route.py src/memory/pipeline.py src/tests/test_route.py
python -m unittest src.tests.test_route
python -m unittest discover -s src/tests
git diff --check
```

Observed unit-test result: `353` tests passed.

## Decision

Promote v272 to local LTS.

Rationale: v272 keeps v269 accuracy, does not increase build/query cost, and reduces the route-risk exposed by v271. It keeps the mechanism clean and general: explicit date routing is a narrow information-need conflict resolver, not a benchmark label or sample-specific rule.

## Outputs

```text
outputs/diagnostic/stage1_explicit_date_recent_route_v272_lme_full/predictions.jsonl
outputs/diagnostic/stage1_explicit_date_recent_route_v272_lme_full/traces.jsonl
outputs/diagnostic/stage1_explicit_date_recent_route_v272_locomo_full/predictions.jsonl
outputs/diagnostic/stage1_explicit_date_recent_route_v272_locomo_full/traces.jsonl
experiments/diagnostic/stage1_explicit_date_recent_route_v272_lme_probe50/
experiments/diagnostic/stage1_explicit_date_recent_route_v272_locomo_probe50/
experiments/diagnostic/stage1_explicit_date_recent_route_v272_lme_full/
experiments/diagnostic/stage1_explicit_date_recent_route_v272_locomo_full/
```

## Next Steps

1. Move the next improvement back to build-stage memory management: richer event/state/profile/relation objects with temporal scope, validity, merge/supersede, confidence and utility.
2. Keep query route additions narrow and ablatable; avoid broad route priority rules unless full changed-answer judge proves safety.
3. Continue reducing query-time compatibility code only when tests and LTS traces show the branch is unused.
