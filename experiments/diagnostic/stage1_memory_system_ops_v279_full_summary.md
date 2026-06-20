# v279 Memory System Operations Full Summary

## Purpose

把 build memory 从 typed-memory retrieval hint 推进为更完整的 Agent Memory system view。v279 继承 v278 的 query、retrieval、compiler 和 answer 行为，只增强 build 侧 `memory_system_graph`：新增 `operation_manifest_v1` 和 `state_conflict_manifest_v1`，让 memory 明确参与状态管理、冲突组织、上下文扩展契约和 source-backed audit。

## Method Lens

- ReMe / LightMem：长期记忆系统需要 working / long-term / archival / quarantine 分层，而不是单一 summary 或 flat typed memory。
- LangMem：collection/profile 需要可持续 create / update / consolidate，并保留来源，profile 当前状态不能替代历史 collection。
- Mem0：ADD/UPDATE/DELETE/NOOP 的接口有价值，但 DELETE 在本项目中改为 non-destructive supersede。
- Graphiti：状态和时间冲突应保留 temporal/provenance chain，旧事实 invalidation 不能破坏历史问题。
- Memanto / memory OS 类系统：operation log、conflict resolver、audit row 和 source expansion 是系统能力，不应散落在 query prompt 里。

v279 的取舍：先在 build artifact 中形成通用 schema 和指标，暂不改 query surface。这样可以降低“memory 只是检索 hint”的风险，同时用 full diff 证明性能面不变；后续再逐步让 query 消费这些 build-owned manifests，并删除旧兼容层。

## Configuration

- config: `configs/stage1_memory_system_ops_v279_seeded_qwen36_no_think_build4k_cached.json`
- method/config commit: `623e79d`
- parent LTS: v278 `configs/stage1_state_profile_tier_activation_v278_seeded_qwen36_no_think_build4k_cached.json`
- answer model: `Qwen/Qwen3.6-35B-A3B`, no-thinking, temperature `0`
- build model: `Qwen/Qwen3.6-35B-A3B`, no-thinking, `max_tokens=4096`
- clean setting: prediction uses no gold answer, judge output, benchmark tags, sample ids, test feedback, labels, or sample-level rules.

## Method Change

`src/memory/build.py` now emits:

- `memory_operation_manifest_v1`: build-owned create / update / merge / supersede / retrieve / expand / verify / audit contract over source-backed memory objects.
- `memory_state_conflict_manifest_v1`: managed state/profile slots with active + superseded records, active/historical source order, source-backed coverage, and temporal anchors.
- object schema signals: `operation_contract`, `operation_contract_ready`, `state_conflict_cluster`, `build_owned_operation_manifest`, `build_owned_conflict_cluster`.

`scripts/run_stage1.py` now reports operation manifest coverage/counts and state-conflict source-backed coverage. Final answer evidence remains raw Memory rows.

## Main Accuracy

v279 has zero answer changes against v278 on both full benchmarks, so no changed-answer judge is needed and the main DeepSeek dual flash judge accuracy is inherited from v278:

| Benchmark | strict / lenient | strict count | lenient count | avg build tokens | avg query tokens |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S full | `0.832000 / 0.844000` | `416/500` | `422/500` | `85393.566` | `6463.628` |
| LoCoMo non-adversarial full | `0.794156 / 0.819481` | `1223/1540` | `1262/1540` | `62015.57402597403` | `6093.794155844156` |

Exact/F1/BLEU are auxiliary only and were not used for the LTS decision.

## Full Diff Vs v278

```text
LME: answer_diff=0/500, prompt_diff=0, route_diff=0, final_evidence_diff=0, retrieval_diff=0, token_diff=0, build_memory_diff=500, answer_cache=500/0
LoCoMo: answer_diff=0/1540, prompt_diff=0, route_diff=0, final_evidence_diff=0, retrieval_diff=0, token_diff=0, build_memory_diff=1540, answer_cache=1540/0
```

`build_memory_diff` is expected because v279 adds new build manifest fields. Query and answer surfaces are unchanged.

## Build System Coverage

| Benchmark | operation manifest | state-conflict manifest | state-conflict clusters | source-backed clusters | incomplete clusters |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S full | `500/500` | `500/500` | `2814` | `2814` | `0` |
| LoCoMo non-adversarial full | `1540/1540` | `1540/1540` | `8514` | `8514` | `0` |

Operation totals:

| Benchmark | create | update | supersede | retrieve | expand | verify | audit | lifecycle audit | state-conflict audit |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| LongMemEval-S full | `57909` | `5499` | `5499` | `57909` | `72476` | `57909` | `44630` | `6620` | `2814` |
| LoCoMo non-adversarial full | `232409` | `13622` | `13622` | `232409` | `319724` | `232409` | `196651` | `21984` | `8514` |

Tier totals:

| Benchmark | working | long-term | archival | quarantine |
|---|---:|---:|---:|---:|
| LongMemEval-S full | `32606` | `19804` | `5499` | `0` |
| LoCoMo non-adversarial full | `117311` | `101476` | `13622` | `0` |

## Validation

```text
python -m py_compile src/memory/build.py scripts/run_stage1.py src/tests/test_build_memory.py src/tests/test_clean_skeleton.py
python -m unittest src.tests.test_build_memory.BuildMemoryTest.test_memory_system_graph_tracks_namespaces_sources_and_operations
python -m unittest src.tests.test_clean_skeleton.CleanSkeletonTest.test_memory_system_graph_records_schema_and_quality
python -m unittest src.tests.test_build_memory src.tests.test_clean_skeleton
python -m unittest discover -s src/tests
git diff --check
```

Observed result: `355` tests passed.

## Decision

Promote v279 to local LTS.

Rationale: v279 directly reduces the first goal risk: build is no longer only typed-memory extraction plus retrieval hints. It exposes a general, source-backed memory system contract with memory tiers, operation lifecycle, non-destructive state supersession, conflict clusters, source expansion, verification, and audit. Performance does not regress because full answer/prompt/evidence/retrieval/token diff vs v278 is zero, so v279 inherits v278's main judge accuracy.

## Outputs

```text
outputs/diagnostic/stage1_memory_system_ops_v279_lme_probe50/predictions.jsonl
outputs/diagnostic/stage1_memory_system_ops_v279_lme_probe50/traces.jsonl
outputs/diagnostic/stage1_memory_system_ops_v279_locomo_probe50/predictions.jsonl
outputs/diagnostic/stage1_memory_system_ops_v279_locomo_probe50/traces.jsonl
outputs/diagnostic/stage1_memory_system_ops_v279_lme_full/predictions.jsonl
outputs/diagnostic/stage1_memory_system_ops_v279_lme_full/traces.jsonl
outputs/diagnostic/stage1_memory_system_ops_v279_locomo_full/predictions.jsonl
outputs/diagnostic/stage1_memory_system_ops_v279_locomo_full/traces.jsonl
experiments/diagnostic/stage1_memory_system_ops_v279_lme_full/
experiments/diagnostic/stage1_memory_system_ops_v279_locomo_full/
```

## Next Steps

1. Let query consume `operation_manifest` / `state_conflict_manifest` directly, then delete overlapping `memory_state_guide` compatibility code if full diff stays safe.
2. Move more state conflict and context organization decisions from prompt-side guide into build-owned source-backed manifests.
3. Keep improving query simplification, but gate each change with full diff or changed-answer dual judge.
