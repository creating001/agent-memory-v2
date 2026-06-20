# v276 Memory Tier Manifest Full Summary

## Purpose

Make build memory look more like a system-level memory manager rather than a flat set of typed records.

v276 keeps v275 prediction behavior unchanged, but adds a build-owned `memory_tier_manifest_v1` to the memory system graph. Records are assigned to `working_memory`, `long_term_memory`, `archival_memory`, or `quarantine_memory` from lifecycle status, source backing, confidence, and managed memory type. Query-time retrieval, compiler, route, answer, verifier, and cache behavior are unchanged.

## Method Lens

- ReMe / LightMem: agent memory should expose working / short-term / long-term style organization instead of only recall hints.
- A-mem / LangMem: memory should continuously organize and consolidate durable objects.
- Mem0: production memory benefits from explicit operations and lifecycle state.
- Graphiti: temporal validity and provenance should remain tied to source-backed records.

Takeaway for v276: keep raw evidence as final authority, but make build memory publish lifecycle tiers that later retrieval, context organization, and verification can consume as memory-system state.

## Configuration

- config: `configs/stage1_memory_tier_manifest_v276_seeded_qwen36_no_think_build4k_cached.json`
- method commit: `e54fb50`
- parent LTS: v275 `configs/stage1_build_slot_source_policy_v275_seeded_qwen36_no_think_build4k_cached.json`
- tier manifest: `memory_system_graph.tier_manifest.schema_version=memory_tier_manifest_v1`
- clean setting: prediction uses no gold answer, judge output, benchmark tags, sample ids, test feedback, labels, or sample-level rules.

## Method Change

`src/memory/build.py` now emits a build-side tier manifest under `memory_system_graph.tier_manifest`. Each graph record also carries `memory_tier`, and graph governance records aggregate tier counts. `scripts/run_stage1.py` aggregates tier coverage and counts under the `build_memory` metrics section.

The tier policy is source-backed and lifecycle-aware:

- `quarantine_memory`: unbacked or low-confidence records.
- `archival_memory`: superseded or validity-closed records.
- `working_memory`: managed stateful records and plans that should remain active for task/current-state reasoning.
- `long_term_memory`: durable source-backed semantic, episodic, profile, and relationship records.

## Full Results

| Benchmark | strict / lenient | avg build tokens | avg query tokens | note |
|---|---:|---:|---:|---|
| LongMemEval-S full | `0.832000 / 0.844000` | `85393.566` | `6463.04` | inherited from v275; full answer diff `0/500` |
| LoCoMo non-adversarial full | `0.794156 / 0.819481` | `62015.57402597403` | `6093.8493506493505` | inherited from v275; full answer diff `0/1540` |

Auxiliary lexical metrics, offline-only and not used as the main performance metric:

| Benchmark | exact | F1 | unigram BLEU |
|---|---:|---:|---:|
| LongMemEval-S full | `0.432000` | `0.6382564639794627` | `0.5945745847818985` |
| LoCoMo non-adversarial full | `0.2422077922077922` | `0.5375986999424064` | `0.4833665475326201` |

## Full Diff

v276 vs v275 full:

```text
LME: answer_diff=0/500, prompt_diff=0, route_diff=0, final_evidence_diff=0, retrieval_diff=0, token_diff=0, build_memory_diff=500, answer_cache=500/0, tier_manifest=500/500, source_policy=500/500
LoCoMo: answer_diff=0/1540, prompt_diff=0, route_diff=0, final_evidence_diff=0, retrieval_diff=0, token_diff=0, build_memory_diff=1540, answer_cache=1540/0, tier_manifest=1540/1540, source_policy=1540/1540
```

The build memory diff is expected: v276 adds `memory_system_graph.tier_manifest` and per-record `memory_tier`. No answer changed, so no changed-answer judge was needed.

## Tier Coverage

| Benchmark | tier manifest coverage | working | long-term | archival | quarantine |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S full | `500/500` | `32606` | `19804` | `5499` | `0` |
| LoCoMo non-adversarial full | `1540/1540` | `117311` | `101476` | `13622` | `0` |

`quarantine_memory=0` is expected for this cache-backed run because generated graph records are source-backed and confidence-valid; the tier still exists as a general policy hook for future noisy or partially backed memory builders.

## Token Cost

| Benchmark | v275 avg query tokens | v276 avg query tokens | delta |
|---|---:|---:|---:|
| LongMemEval-S full | `6463.04` | `6463.04` | `0` |
| LoCoMo non-adversarial full | `6093.8493506493505` | `6093.8493506493505` | `0` |

Build tokens are unchanged: LME `85393.566`, LoCoMo `62015.57402597403`.

## Validation

```text
python -m json.tool configs/stage1_memory_tier_manifest_v276_seeded_qwen36_no_think_build4k_cached.json
python -m py_compile src/memory/build.py scripts/run_stage1.py src/tests/test_clean_skeleton.py
python -m unittest src.tests.test_clean_skeleton.CleanSkeletonTest.test_memory_system_graph_records_schema_and_quality
python -m unittest src.tests.test_build_memory src.tests.test_clean_skeleton
python -m unittest discover -s src/tests
python scripts/evaluate_predictions.py --predictions outputs/diagnostic/stage1_memory_tier_manifest_v276_lme_full/predictions.jsonl --labels outputs/prepare_longmemeval_s_cleaned/labels.jsonl --output outputs/diagnostic/stage1_memory_tier_manifest_v276_lme_full/offline_metrics.json
python scripts/evaluate_predictions.py --predictions outputs/diagnostic/stage1_memory_tier_manifest_v276_locomo_full/predictions.jsonl --labels outputs/prepare_locomo_non_adversarial/labels.jsonl --output outputs/diagnostic/stage1_memory_tier_manifest_v276_locomo_full/offline_metrics.json
git diff --check
```

Observed unit-test result before the method commit: `355` tests passed.

## Decision

Promote v276 to local LTS.

Rationale: v276 has no accuracy, answer, prompt, retrieval, evidence, or token regression, and it reduces the build-memory-system risk by adding explicit lifecycle tiers. This is still a structural step rather than a direct performance gain; the next useful move is to make retrieval/context/verifier consume the tier manifest and then remove equivalent query-side compatibility logic once full diffs prove it is safe.

## Outputs

```text
outputs/diagnostic/stage1_memory_tier_manifest_v276_lme_probe50/predictions.jsonl
outputs/diagnostic/stage1_memory_tier_manifest_v276_lme_probe50/traces.jsonl
outputs/diagnostic/stage1_memory_tier_manifest_v276_locomo_probe50/predictions.jsonl
outputs/diagnostic/stage1_memory_tier_manifest_v276_locomo_probe50/traces.jsonl
outputs/diagnostic/stage1_memory_tier_manifest_v276_lme_full/predictions.jsonl
outputs/diagnostic/stage1_memory_tier_manifest_v276_lme_full/traces.jsonl
outputs/diagnostic/stage1_memory_tier_manifest_v276_locomo_full/predictions.jsonl
outputs/diagnostic/stage1_memory_tier_manifest_v276_locomo_full/traces.jsonl
experiments/diagnostic/stage1_memory_tier_manifest_v276_lme_probe50/
experiments/diagnostic/stage1_memory_tier_manifest_v276_locomo_probe50/
experiments/diagnostic/stage1_memory_tier_manifest_v276_lme_full/
experiments/diagnostic/stage1_memory_tier_manifest_v276_locomo_full/
```

## Next Steps

1. Let retrieval and compiler consume `memory_tier` as a general activation/context policy, then delete equivalent query-side guide branches only after answer-equivalent diffs.
2. Add build-owned consolidation/conflict clusters that can replace narrow current-state guide logic.
3. Audit compatibility code in `src/memory/pipeline.py` and `src/memory/context.py` in small, behavior-checked commits.
