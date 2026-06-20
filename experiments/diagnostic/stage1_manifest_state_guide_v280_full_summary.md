# v280 Manifest State Guide Full Summary

## Purpose

让 query-time `Managed Memory State Guide` 优先消费 build-owned `state_conflict_manifest_v1`，减少 compiler 侧重复推导 state conflict slot 的逻辑。v280 继承 v279 的 build memory system view，并把 `compiler.memory_state_guide_conflict_source` 设置为 `build_manifest`。

## Method Change

- `EvidenceCompiler.compile()` 新增可选 `memory_state_conflict_manifest`。
- `Stage1Pipeline` 从 `built_memory.management.memory_system_graph.state_conflict_manifest` 传入 compiler。
- `memory_state_guide_conflict_source=build_manifest` 时，state guide 的 conflict slot 集合来自 build manifest。
- state guide 展示内容仍只来自可见 Memory Context rows 链接到的 `MemoryRecord`；manifest 不直接成为 answer evidence。
- 默认 `memory_state_guide_conflict_source=records` 保持旧配置完全兼容。

## Configuration

- config: `configs/stage1_manifest_state_guide_v280_seeded_qwen36_no_think_build4k_cached.json`
- method/config commit: `8fee82b`
- parent LTS: v279 `configs/stage1_memory_system_ops_v279_seeded_qwen36_no_think_build4k_cached.json`
- clean setting: prediction uses no gold answer, judge output, benchmark tags, sample ids, test feedback, labels, or sample-level rules.

## Main Accuracy

v280 has zero answer changes against v279 on both full benchmarks, so no changed-answer judge is needed and the main DeepSeek dual flash judge accuracy is inherited:

| Benchmark | strict / lenient | avg build tokens | avg query tokens |
|---|---:|---:|---:|
| LongMemEval-S full | `0.832000 / 0.844000` | `85393.566` | `6463.628` |
| LoCoMo non-adversarial full | `0.794156 / 0.819481` | `62015.57402597403` | `6093.794155844156` |

## Full Diff Vs v279

```text
LME: answer_diff=0/500, prompt_diff=0, route_diff=0, final_evidence_diff=0, retrieval_diff=0, token_diff=0, build_memory_diff=0, answer_cache=500/0
LoCoMo: answer_diff=0/1540, prompt_diff=0, route_diff=0, final_evidence_diff=0, retrieval_diff=0, token_diff=0, build_memory_diff=0, answer_cache=1540/0
```

Because prompt diff is `0`, v280 does not change model inputs; it only changes the compiler's internal source of conflict slot truth from query-side recomputation to the build-owned manifest.

## Validation

```text
python -m py_compile src/memory/compiler.py src/memory/pipeline.py src/tests/test_compiler.py src/tests/test_clean_skeleton.py
python -m unittest src.tests.test_compiler.CompilerTest.test_memory_state_guide_can_use_build_conflict_manifest
python -m unittest src.tests.test_clean_skeleton.CleanSkeletonTest.test_pipeline_traces_update_conflict_guide_config
python -m unittest src.tests.test_compiler
python -m unittest discover -s src/tests
git diff --check
```

Observed result: `356` tests passed.

## Decision

Promote v280 to local LTS.

Rationale: v280 reduces query-stack risk without changing prediction behavior. The state guide now consumes a build-owned conflict manifest, while final answers remain grounded in raw Memory rows. This is a small but concrete step toward a cleaner Agent Memory system where build/management owns lifecycle and conflict state, and query-time compiler consumes that system contract instead of re-deriving it.

## Outputs

```text
outputs/diagnostic/stage1_manifest_state_guide_v280_lme_probe50/predictions.jsonl
outputs/diagnostic/stage1_manifest_state_guide_v280_lme_probe50/traces.jsonl
outputs/diagnostic/stage1_manifest_state_guide_v280_locomo_probe50/predictions.jsonl
outputs/diagnostic/stage1_manifest_state_guide_v280_locomo_probe50/traces.jsonl
outputs/diagnostic/stage1_manifest_state_guide_v280_lme_full/predictions.jsonl
outputs/diagnostic/stage1_manifest_state_guide_v280_lme_full/traces.jsonl
outputs/diagnostic/stage1_manifest_state_guide_v280_locomo_full/predictions.jsonl
outputs/diagnostic/stage1_manifest_state_guide_v280_locomo_full/traces.jsonl
experiments/diagnostic/stage1_manifest_state_guide_v280_lme_full/
experiments/diagnostic/stage1_manifest_state_guide_v280_locomo_full/
```

## Next Steps

1. Delete or shrink query-side conflict gates now covered by build manifest, but only after a probe/full diff proves prompt behavior stays stable.
2. Let context organization consume `operation_manifest_v1` for explicit create/update/supersede/expand/verify/audit sections.
3. Continue small `src/` cleanup around old state-guide compatibility branches.
