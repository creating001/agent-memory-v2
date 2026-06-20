# v288 memory object index probe summary

## 结论

本文件是 v288 smoke/probe 记录；最终 LTS 决策已由 full run 记录 `experiments/diagnostic/stage1_memory_object_index_v288_full_summary.md` supersede。v288 把 build 阶段已有的 tier、operation、state-conflict、source-policy 和 scalar/value manifest 收敛成统一的 `memory_object_index_v1`，并让 compiler 的 state-only Memory Value Slot Guide 优先从该 index 读取 value slots；旧 `scalar_value_manifest` 仍保留为兼容 fallback。

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

该 probe 之后已完成 v287 full diff audit，并在 `stage1_memory_object_index_v288_full_summary.md` 中将 v288 升为当前 LTS。若后续启用更多 query consumers，需要先做 changed-answer judge。
