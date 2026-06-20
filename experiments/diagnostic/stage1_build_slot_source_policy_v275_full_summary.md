# v275 Build Slot Source Policy Full Summary

## Purpose

Move validity-aware graph utility source ordering into the build memory system.

v275 keeps the v274 behavior but makes the build graph expose a `memory_slot_source_policy_v1` manifest. Query-time graph utility now consumes the same source-order helper owned by `build.py`, instead of carrying duplicated validity/source-confidence ordering logic in `pipeline.py`.

## External Method Lens

- Graphiti/Zep: temporal context graphs keep changing facts with validity windows and provenance back to raw episodes: https://github.com/getzep/graphiti
- LangMem: long-term memory benefits from background extraction, consolidation, and update management: https://github.com/langchain-ai/langmem
- Mem0: production agent memory is treated as a reusable memory layer, not one benchmark prompt trick: https://github.com/mem0ai/mem0
- Letta: stateful agents organize durable memory blocks as part of agent state: https://github.com/letta-ai/letta

Takeaway for v275: keep raw turns as final authority, but let build memory own source policy and lifecycle organization so query code becomes a consumer of a memory system, not a pile of scattered heuristics.

## Configuration

- config: `configs/stage1_build_slot_source_policy_v275_seeded_qwen36_no_think_build4k_cached.json`
- method commit: `1e650ac`
- parent LTS: v274 `configs/stage1_validity_aware_graph_utility_v274_seeded_qwen36_no_think_build4k_cached.json`
- source policy: `memory_system_graph.source_policy.schema_version=memory_slot_source_policy_v1`
- clean setting: prediction uses no gold answer, judge output, benchmark tags, sample ids, test feedback, labels, or sample-level rules.

## Method Change

`src/memory/build.py` now exports `memory_slot_record_source_policy_sort_key` and records a build-side `source_policy` manifest for graph slots. The policy precomputes current/open and historical/closed source orders from validity status, source confidence, temporal anchors, lifecycle state, timestamps, and source ids.

`src/memory/pipeline.py` keeps the same `validity_aware` behavior, but delegates ordering to the build-owned helper. Route, top-k, compiler, answer prompt, answer cache, and verifier behavior are unchanged.

## Full Results

| Benchmark | strict / lenient | avg build tokens | avg query tokens | note |
|---|---:|---:|---:|---|
| LongMemEval-S full | `0.832000 / 0.844000` | `85393.566` | `6463.04` | inherited from v274; full answer diff `0/500` |
| LoCoMo non-adversarial full | `0.794156 / 0.819481` | `62015.57402597403` | `6093.8493506493505` | inherited from v274; full answer diff `0/1540` |

Auxiliary lexical metrics, offline-only and not used as the main performance metric:

| Benchmark | exact | F1 | unigram BLEU |
|---|---:|---:|---:|
| LongMemEval-S full | `0.432000` | `0.6382564639794627` | `0.5945745847818985` |
| LoCoMo non-adversarial full | `0.2422077922077922` | `0.5375986999424064` | `0.4833665475326201` |

## Full Diff

v275 vs v274 full:

```text
LME: answer_diff=0/500, prompt_diff=0, route_diff=0, final_evidence_diff=0, retrieval_diff=0, token_diff=0, build_memory_diff=500, answer_cache=500/0, source_policy=500/500
LoCoMo: answer_diff=0/1540, prompt_diff=0, route_diff=0, final_evidence_diff=0, retrieval_diff=0, token_diff=0, build_memory_diff=1540, answer_cache=1540/0, source_policy=1540/1540
```

The build memory diff is expected: v275 adds `memory_system_graph.source_policy`. No answer changed, so no changed-answer judge was needed.

## Source Policy Coverage

| Benchmark | source_policy coverage | avg slot_count | min slot_count | max slot_count |
|---|---:|---:|---:|---:|
| LongMemEval-S full | `500/500` | `89.26` | `61` | `126` |
| LoCoMo non-adversarial full | `1540/1540` | `127.69545454545455` | `80` | `153` |

## Token Cost

| Benchmark | v274 avg query tokens | v275 avg query tokens | delta |
|---|---:|---:|---:|
| LongMemEval-S full | `6463.04` | `6463.04` | `0` |
| LoCoMo non-adversarial full | `6093.8493506493505` | `6093.8493506493505` | `0` |

Build tokens are unchanged: LME `85393.566`, LoCoMo `62015.57402597403`.

## Validation

```text
python -m json.tool configs/stage1_build_slot_source_policy_v275_seeded_qwen36_no_think_build4k_cached.json
python -m py_compile src/memory/build.py src/memory/pipeline.py src/tests/test_clean_skeleton.py
python -m unittest src.tests.test_clean_skeleton.CleanSkeletonTest.test_memory_system_graph_records_schema_and_quality src.tests.test_clean_skeleton.CleanSkeletonTest.test_memory_graph_utility_validity_policy_prefers_anchored_open_source src.tests.test_clean_skeleton.CleanSkeletonTest.test_memory_graph_utility_validity_policy_prefers_historical_closed_source
python -m unittest src.tests.test_build_memory src.tests.test_clean_skeleton
python -m unittest discover -s src/tests
git diff --check
```

Observed unit-test result before the method commit: `355` tests passed.

## Decision

Promote v275 to local LTS.

Rationale: v275 has no performance or token regression on full outputs and reduces system risk by moving graph utility source policy into the build memory system. It is a structural improvement toward a real memory system: build owns lifecycle/source policy, query consumes it, and final evidence remains raw-source grounded.

## Outputs

```text
outputs/diagnostic/stage1_build_slot_source_policy_v275_lme_probe50/predictions.jsonl
outputs/diagnostic/stage1_build_slot_source_policy_v275_lme_probe50/traces.jsonl
outputs/diagnostic/stage1_build_slot_source_policy_v275_locomo_probe50/predictions.jsonl
outputs/diagnostic/stage1_build_slot_source_policy_v275_locomo_probe50/traces.jsonl
outputs/diagnostic/stage1_build_slot_source_policy_v275_lme_full/predictions.jsonl
outputs/diagnostic/stage1_build_slot_source_policy_v275_lme_full/traces.jsonl
outputs/diagnostic/stage1_build_slot_source_policy_v275_locomo_full/predictions.jsonl
outputs/diagnostic/stage1_build_slot_source_policy_v275_locomo_full/traces.jsonl
experiments/diagnostic/stage1_build_slot_source_policy_v275_lme_probe50/
experiments/diagnostic/stage1_build_slot_source_policy_v275_locomo_probe50/
experiments/diagnostic/stage1_build_slot_source_policy_v275_lme_full/
experiments/diagnostic/stage1_build_slot_source_policy_v275_locomo_full/
```

## Next Steps

1. Add build-owned consolidation/conflict clusters that can replace narrow query state guides.
2. Add trace metrics for source_policy into `run_stage1.py` metrics aggregation.
3. Continue `src/` cleanup by deleting or isolating compatibility branches only after full trace diff proves they are unused or behavior-equivalent.
