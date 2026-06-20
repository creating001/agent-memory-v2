# v270 Priority Memory Retrieval Full Summary

## Purpose

Test a performance-oriented, clean use of the v269 build-stage activation-priority manifest. v270 expands the typed-memory BM25 candidate pool for `current_state` and `profile_preference`, applies a bounded question-independent activation-priority prior, then truncates back to the same memory `top_k=20`. Final evidence still resolves to raw Memory rows.

## Configuration

- config: `configs/stage1_priority_memory_retrieval_v270_seeded_qwen36_no_think_build4k_cached.json`
- method commit: `c7778d9`
- parent LTS: v269 `configs/stage1_memory_activation_utility_v269_seeded_qwen36_no_think_build4k_cached.json`
- priority settings: `pool_k=40`, `score_boost=0.5`, `max_rank=80`, information needs `current_state` and `profile_preference`
- clean setting: prediction uses no gold answer, judge output, benchmark tags, sample ids, test feedback, labels, or sample-level rules.

## Full Diff

v270 vs v269 full:

```text
LME: answer_diff=1/500, prompt_diff=1, final_evidence_diff=1, retrieval_diff=2, pre_context_budget_diff=3, memory_hits_diff=34, memory_source_hits_diff=34, token_diff=1, answer_cache=499/1
LoCoMo: answer_diff=8/1540, prompt_diff=24, final_evidence_diff=24, retrieval_diff=21, pre_context_budget_diff=22, memory_hits_diff=50, memory_source_hits_diff=50, token_diff=24, answer_cache=1518/22
```

## Token Cost

| Benchmark | avg build tokens | avg query tokens | priority applied | priority reordered |
|---|---:|---:|---:|---:|
| LongMemEval-S full | `85393.566` | `6462.884` | `34` | `6` |
| LoCoMo non-adversarial full | `62015.57402597403` | `6093.772727272727` | `50` | `46` |

## Changed-Answer Judge

Dual `deepseek-v4-flash`, temperature `0`, default thinking:

| Benchmark | changed answers | base strict/lenient | new strict/lenient | delta |
|---|---:|---:|---:|---:|
| LongMemEval-S full | `1` | `1/1` | `1/1` | `0 / 0` |
| LoCoMo non-adversarial full | `8` | `7/8` | `7/8` | `0 / 0` |

Judge output paths:

```text
outputs/diagnostic/stage1_priority_memory_retrieval_v270_lme_full_changed_vs_v269/base_dual_judge.json
outputs/diagnostic/stage1_priority_memory_retrieval_v270_lme_full_changed_vs_v269/new_dual_judge.json
outputs/diagnostic/stage1_priority_memory_retrieval_v270_locomo_full_changed_vs_v269/base_dual_judge.json
outputs/diagnostic/stage1_priority_memory_retrieval_v270_locomo_full_changed_vs_v269/new_dual_judge.json
```

## Validation

```text
python -m json.tool configs/stage1_priority_memory_retrieval_v270_seeded_qwen36_no_think_build4k_cached.json
python -m py_compile src/memory/pipeline.py scripts/run_stage1.py src/tests/test_clean_skeleton.py
python -m unittest src.tests.test_clean_skeleton.CleanSkeletonTest.test_memory_activation_priority_reorders_with_manifest_prior src.tests.test_clean_skeleton.CleanSkeletonTest.test_memory_activation_priority_is_route_scoped src.tests.test_clean_skeleton.CleanSkeletonTest.test_memory_governance_activation_filters_unready_records
python -m unittest discover -s src/tests
git diff --check
```

Observed full unit-test result: `348` tests passed.

## Decision

Do not promote v270 to LTS.

Rationale: v270 does not regress changed-answer judge accuracy, but it also does not improve strict or lenient accuracy. Because it adds a query-side prior, the extra mechanism is not justified as a new LTS. Keep v269 as current LTS.

## Outputs

```text
outputs/diagnostic/stage1_priority_memory_retrieval_v270_lme_full/predictions.jsonl
outputs/diagnostic/stage1_priority_memory_retrieval_v270_lme_full/traces.jsonl
outputs/diagnostic/stage1_priority_memory_retrieval_v270_locomo_full/predictions.jsonl
outputs/diagnostic/stage1_priority_memory_retrieval_v270_locomo_full/traces.jsonl
experiments/diagnostic/stage1_priority_memory_retrieval_v270_lme_probe50/
experiments/diagnostic/stage1_priority_memory_retrieval_v270_locomo_probe50/
experiments/diagnostic/stage1_priority_memory_retrieval_v270_lme_full/
experiments/diagnostic/stage1_priority_memory_retrieval_v270_locomo_full/
```

## Next Steps

1. Shift from weak memory-hit priors to source-coverage utility: same-slot coverage, temporal validity, and missing-source pressure should affect raw evidence coverage directly.
2. Avoid adding more query-side knobs unless they replace an older route/context heuristic.
3. Continue performance work with changed-answer judge as the default guardrail.
