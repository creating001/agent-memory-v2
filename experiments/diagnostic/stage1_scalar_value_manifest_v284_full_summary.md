# v284 Scalar Value Manifest Full Summary

## Purpose

Move value/state handling from query-side prompt heuristics toward a build-owned
Agent Memory system view. v284 keeps v283 prediction behavior, but adds a
source-backed `scalar_value_manifest` to `memory_system_graph` so typed memory is
organized as value objects and value slots with lifecycle, source-order,
operation, and audit signals.

## Method Change

- Adds `memory_scalar_value_manifest_v1` under `memory_system_graph_v3`.
- Creates value objects from typed memories with source back-pointers, subject,
  predicate, and value/text.
- Extracts scalar expressions as a subview of value objects, not as final
  evidence.
- Tracks create, update, merge, supersede, retrieve, expand, verify, audit, and
  quarantine operations for value slots.
- Keeps final answer authority on raw Memory rows. The new manifest is
  question-independent and uses no gold answers, judge output, benchmark labels,
  sample ids, test feedback, or sample-level rules.

This borrows the useful parts of MemoryOS/MemOS, Zep/Graphiti, LangMem/MIRIX,
xMemory, and Everything-is-Context style systems: namespace/lifecycle/versioned
objects, raw-source lineage, conflict-retaining supersede, and auditable context
manifests. It deliberately avoids copying a heavy memory OS or using derived
memory as standalone answer evidence.

## Configuration

- config: `configs/stage1_scalar_value_manifest_v284_seeded_qwen36_no_think_build4k_cached.json`
- method/config commit: `2c85ceb`
- parent LTS: v283 `configs/stage1_order_safe_value_parser_v283_seeded_qwen36_no_think_build4k_cached.json`
- answer cache: seeded from v283 prediction traces only with
  `scripts/seed_answer_cache_from_traces.py`; no labels, judge outputs,
  benchmark categories, sample ids, or test feedback were read.

## Accuracy

v284 has full answer/prompt/evidence identity with v283 on LongMemEval-S and
LoCoMo. Therefore v284 inherits v283 full DeepSeek dual flash judge accuracy:

| Benchmark | strict / lenient | avg build tokens | avg query tokens |
|---|---:|---:|---:|
| LongMemEval-S full | `0.834000 / 0.846000` | `85393.566` | `6464.954` |
| LoCoMo non-adversarial full | `0.794156 / 0.819481` | `62015.57402597403` | `6093.794155844156` |

No fresh judge call was needed because prediction identity makes the existing
v283 full judge outputs applicable to v284 predictions.

## Full Diff Vs v283

```text
LME: answer_diff=0/500, prompt_diff=0, route_diff=0, compiled_evidence_rows_diff=0, compiled_memory_records_diff=0, retrieval_materialized_diff=0, build_memory_records_diff=0, build_memory_management_diff=500, management_diff_after_removing_scalar_manifest=0
LoCoMo: answer_diff=0/1540, prompt_diff=0, route_diff=0, compiled_evidence_rows_diff=0, compiled_memory_records_diff=0, retrieval_materialized_diff=0, rerank_response_trace_only_diff=2, build_memory_records_diff=0, build_memory_management_diff=1540, management_diff_after_removing_scalar_manifest=0
```

The only intentional full-run diff is the new build management artifact. The two
LoCoMo `rerank_response` differences are raw floating-point score trace changes;
compiled evidence rows, prompt, and answer are unchanged.

Diff artifact:
`experiments/diagnostic/stage1_scalar_value_manifest_v284_diff_vs_v283.json`

## Build Manifest Coverage

| Benchmark | scalar manifest applied | avg value objects | avg scalar value objects | avg value slots | avg scalar value slots | avg active/superseded value slots |
|---|---:|---:|---:|---:|---:|---:|
| LongMemEval-S full | `500/500` | `115.818` | `9.724` | `89.26` | `9.004` | `5.628` |
| LoCoMo non-adversarial full | `1540/1540` | `150.91493506493507` | `2.414285714285714` | `127.69545454545455` | `2.3344155844155843` | `5.5285714285714285` |

Operation counts:

```text
LME: create_value_object=57909, create_scalar_value=4862, update_value_slot=2814, merge_value_slot=81, supersede_value=5499, retrieve_value=57909, expand_value_source=72476, verify_value_source=57909, audit_value_slot=44630, audit_scalar_value_slot=4502, audit_conflict_value_slot=2814, quarantine_value=0
LoCoMo: create_value_object=232409, create_scalar_value=3718, update_value_slot=8514, merge_value_slot=3075, supersede_value=13622, retrieve_value=232409, expand_value_source=319724, verify_value_source=232409, audit_value_slot=196651, audit_scalar_value_slot=3595, audit_conflict_value_slot=8514, quarantine_value=0
```

Cache/token checks:

```text
LME: answer_cache=500/0/0 hits/misses/writes, build_cache=3341/0/0, avg build/query tokens=85393.566/6464.954
LoCoMo: answer_cache=1540/0/0 hits/misses/writes, build_cache=12411/0/0, avg build/query tokens=62015.57402597403/6093.794155844156
```

## Validation

```text
python -m py_compile src/memory/build.py scripts/run_stage1.py src/tests/test_clean_skeleton.py
python -m unittest src.tests.test_clean_skeleton.CleanSkeletonTest.test_memory_system_graph_records_schema_and_quality src.tests.test_clean_skeleton.CleanSkeletonTest.test_memory_scalar_value_manifest_tracks_source_backed_values
python -m unittest discover -s src/tests
git diff --check
```

Observed result: `359` tests passed. A cache-hit smoke run also verified
`answer_cache_hits=1`, `answer_cache_misses=0`, and scalar manifest metrics in
summary output.

## Decision

Promote v284 to local LTS.

Rationale: v284 reduces the current build-stage risk that typed memory is only a
retrieval hint. It adds a general, clean, source-backed value/state organization
layer that can support state management, conflict handling, context
organization, and later verifier consumption, while keeping performance exactly
equal to v283.

## Outputs

```text
outputs/diagnostic/stage1_scalar_value_manifest_v284_lme_full/predictions.jsonl
outputs/diagnostic/stage1_scalar_value_manifest_v284_lme_full/traces.jsonl
outputs/diagnostic/stage1_scalar_value_manifest_v284_locomo_full/predictions.jsonl
outputs/diagnostic/stage1_scalar_value_manifest_v284_locomo_full/traces.jsonl
experiments/diagnostic/stage1_scalar_value_manifest_v284_lme_full/
experiments/diagnostic/stage1_scalar_value_manifest_v284_locomo_full/
experiments/diagnostic/stage1_scalar_value_manifest_v284_diff_vs_v283.json
```

## Next Steps

1. Let query/compiler consume build-owned value slots where useful, without
   increasing prompt tokens or bypassing raw evidence.
2. Move remaining update/conflict guide logic behind build-owned operation,
   state-conflict, and value manifests.
3. Continue removing old compatibility paths after each manifest-backed behavior
   is covered by tests and full diff.
