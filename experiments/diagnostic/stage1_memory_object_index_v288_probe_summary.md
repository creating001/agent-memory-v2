# v288 memory object index probe summary

## 结论

v288 是候选版本，不升 LTS。它把 build 阶段已有的 tier、operation、state-conflict、source-policy 和 scalar/value manifest 收敛成统一的 `memory_object_index_v1`，并让 compiler 的 state-only Memory Value Slot Guide 优先从该 index 读取 value slots；旧 `scalar_value_manifest` 仍保留为兼容 fallback。

这一步的目标是降低“memory 只是 retrieval hint”的系统风险：memory object index 成为后续 retrieval、context organization、answer verifier 和 audit 共用的 source-backed 接口。v288 仍保持 raw evidence-first，final answer evidence 必须回到 raw Memory rows。

## Probe

- 算法配置：`configs/stage1_memory_object_index_v288_seeded_qwen36_no_think_build4k_cached.json`
- Probe run：`experiments/diagnostic/stage1_memory_object_index_v288_lme_smoke5/`
- 输入：LongMemEval-S 前 5 条 smoke
- Unit tests：`python -m unittest discover -s src/tests`，`362` tests OK
- Trace 检查：`memory_object_index_v1` 出现在 `trace.build_memory.management.memory_system_graph.memory_object_index`
- Answer cache：复用 v287 cache namespace，避免未变 prompt 的 answer 重采样污染 diff

## Probe metrics

| 指标 | 结果 |
|---|---:|
| `memory_object_index` applied | `5/5` |
| avg index objects | `127.0` |
| avg index value slots | `95.8` |
| avg index state conflict slots | `9.4` |
| avg build/query tokens | `92386.0 / 5567.2` |
| answer diff vs v287 on same 5 records | `0/5` |

## 决策

保留为候选。下一步应对 v287 做 full diff audit；若 answer/prompt/evidence 基本不变，且 build management diff 只来自 `memory_object_index_v1`，可以考虑升 LTS。若后续启用更多 query consumers，需要先做 changed-answer judge。
