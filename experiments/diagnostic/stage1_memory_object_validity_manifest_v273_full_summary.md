# v273 Memory Object Validity Manifest Full Summary

## Purpose

Strengthen the build-stage memory system without adding query-time rules. v273 inherits v272 and upgrades the memory system graph/governance manifest with question-independent `temporal_scope_kind`, `validity_status`, and `source_confidence_bucket` fields and aggregate counts.

## Configuration

- config: `configs/stage1_memory_object_validity_manifest_v273_seeded_qwen36_no_think_build4k_cached.json`
- method commit: `87866ff`
- parent LTS: v272 `configs/stage1_explicit_date_recent_route_v272_seeded_qwen36_no_think_build4k_cached.json`
- clean setting: prediction uses no gold answer, judge output, benchmark tags, sample ids, test feedback, labels, or sample-level rules.

## Full Results

| Benchmark | strict / lenient | avg build tokens | avg query tokens | note |
|---|---:|---:|---:|---|
| LongMemEval-S full | `0.832000 / 0.844000` | `85393.566` | `6462.478` | inherited from v272; full diff `0` |
| LoCoMo non-adversarial full | `0.794156 / 0.819481` | `62015.57402597403` | `6093.8493506493505` | changed-answer paired judge delta `0 / 0` |

## Full Diff

v273 vs v272 full:

```text
LME: answer_diff=0/500, prompt_diff=0, route_diff=0, final_evidence_diff=0, retrieval_diff=0, token_diff=0, answer_cache=500/0
LoCoMo: answer_diff=1/1540, prompt_diff=1, route_diff=0, final_evidence_diff=1, retrieval_diff=1, token_diff=1, answer_cache=1539/1
```

The single LoCoMo changed answer is the Anthony relation question. Both v272 and v273 are judged correct.

## Manifest Coverage

The full traces contain the new build manifest schema for every sample:

```text
LME: memory_system_graph_v3=500/500, memory_system_governance_v2=500/500
LoCoMo: memory_system_graph_v3=1540/1540, memory_system_governance_v2=1540/1540
```

New build-stage fields:

```text
temporal_scope_kind
validity_status
source_confidence_bucket
temporal_scope_counts
validity_status_counts
source_confidence_bucket_counts
```

## Token Cost

| Benchmark | v272 avg query tokens | v273 avg query tokens | delta |
|---|---:|---:|---:|
| LongMemEval-S full | `6462.478` | `6462.478` | `0` |
| LoCoMo non-adversarial full | `6093.84025974026` | `6093.8493506493505` | `+0.009090909090446075` |

Build tokens are unchanged: LME `85393.566`, LoCoMo `62015.57402597403`.

## Changed-Answer Judge

Dual `deepseek-v4-flash`, temperature `0`, default thinking:

| Benchmark | changed answers | base strict/lenient | new strict/lenient | delta |
|---|---:|---:|---:|---:|
| LongMemEval-S full | `0` | inherited | inherited | `0 / 0` |
| LoCoMo non-adversarial full | `1` | `1/1` strict, `1/1` lenient | `1/1` strict, `1/1` lenient | `0 / 0` |

Judge output paths:

```text
outputs/diagnostic/stage1_memory_object_validity_manifest_v273_locomo_full_changed_vs_v272/base_dual_judge.json
outputs/diagnostic/stage1_memory_object_validity_manifest_v273_locomo_full_changed_vs_v272/new_dual_judge.json
```

## Validation

```text
python -m json.tool configs/stage1_memory_object_validity_manifest_v273_seeded_qwen36_no_think_build4k_cached.json
python -m py_compile src/memory/build.py src/tests/test_clean_skeleton.py
python -m unittest src.tests.test_clean_skeleton.CleanSkeletonTest.test_memory_system_graph_records_schema_and_quality
python -m unittest src.tests.test_build_memory src.tests.test_clean_skeleton
python -m unittest discover -s src/tests
git diff --check
```

Observed unit-test result: `353` tests passed.

## Decision

Promote v273 to local LTS.

Rationale: v273 directly reduces build-system risk by making temporal scope, state validity, and source confidence first-class build outputs. It does not add benchmark-specific route/retrieval logic, does not change LME behavior, and has no judge accuracy regression on the only changed LoCoMo answer.

## Outputs

```text
outputs/diagnostic/stage1_memory_object_validity_manifest_v273_lme_full/predictions.jsonl
outputs/diagnostic/stage1_memory_object_validity_manifest_v273_lme_full/traces.jsonl
outputs/diagnostic/stage1_memory_object_validity_manifest_v273_locomo_full/predictions.jsonl
outputs/diagnostic/stage1_memory_object_validity_manifest_v273_locomo_full/traces.jsonl
experiments/diagnostic/stage1_memory_object_validity_manifest_v273_lme_probe50/
experiments/diagnostic/stage1_memory_object_validity_manifest_v273_locomo_probe50/
experiments/diagnostic/stage1_memory_object_validity_manifest_v273_lme_full/
experiments/diagnostic/stage1_memory_object_validity_manifest_v273_locomo_full/
```

## Next Steps

1. Use the v273 build manifest in a conservative retrieval/context ablation: source confidence and validity should guide activation before adding any new query prompt logic.
2. Keep changed-answer paired judge as the default promotion gate for any behavior-changing use of these fields.
3. Continue small `src/` cleanup around confirmed-unused query compatibility branches after LTS traces prove they do not affect outputs.
