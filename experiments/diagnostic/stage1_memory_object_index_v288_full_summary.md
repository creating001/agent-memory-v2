# v288 memory object index full summary

## 结论

v288 升为当前本地 LTS。它在 v287 的 state-only value slot guide 基础上，新增 build-owned `memory_object_index_v1`，把 tier、operation、state-conflict、source-policy 和 scalar/value manifest 收敛成统一的 source-backed Agent Memory object interface。query compiler 优先从该 index 读取 state-only value slots，旧 `scalar_value_manifest` 仍保留为兼容 fallback。

v288 没有改变 prediction-time 行为：相对 v287，LongMemEval-S full 和 LoCoMo non-adversarial full 的 answer、prompt、route、compiled evidence、compiled memory records、materialized retrieval 和 build memory records diff 全部为 `0`。build management diff 只来自新增 `memory_object_index_v1`；剥离该 index 和 schema signal 后 diff 为 `0`。因此 v288 继承 v287/v283 dual judge accuracy，同时进一步降低“memory 只是 retrieval hint、build memory system 不统一”的系统风险。

## 方法

- 算法 commit：`286a8a8c12a5363093e83e1052de078615ece4a3`
- 配置：`configs/stage1_memory_object_index_v288_seeded_qwen36_no_think_build4k_cached.json`
- 主要改动：
  - build 阶段新增 `memory_object_index_v1`。
  - index 统一表达 working / long-term / archival / quarantine tier。
  - index 统一表达 create / update / merge / supersede / retrieve / expand / verify / audit 操作。
  - index 统一承载 state conflict slots、value slots、source policy、operation counts 和 source-backed activation readiness。
  - compiler 的 Memory Value Slot Guide 优先消费 `memory_object_index.value_slot_index`，并回退到旧 `scalar_value_manifest`。
- Clean 边界：prediction 不使用 gold answer、judge output、benchmark label、sample id、test feedback 或样本级规则；final evidence policy 仍是 raw source rows。

## Full metrics

| Benchmark | n | inherited strict/lenient accuracy | avg build/query tokens | index applied | answer diff vs v287 |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S full | 500 | `0.834000 / 0.846000` | `85393.566 / 6455.588` | `500/500` | `0/500` |
| LoCoMo non-adversarial full | 1540 | `0.794156 / 0.819481` | `62015.57402597403 / 6093.962337662338` | `1540/1540` | `0/1540` |

## Diff audit vs v287

| Benchmark | prompt diff | route diff | evidence diff | retrieval diff | build records diff | build management diff after removing index |
|---|---:|---:|---:|---:|---:|---:|
| LongMemEval-S full | 0 | 0 | 0 | 0 | 0 | 0 |
| LoCoMo non-adversarial full | 0 | 0 | 0 | 0 | 0 | 0 |

Diff file: `experiments/diagnostic/stage1_memory_object_index_v288_diff_vs_v287.json`

## Output paths

- LME full run: `experiments/diagnostic/stage1_memory_object_index_v288_lme_full/`
- LoCoMo full run: `experiments/diagnostic/stage1_memory_object_index_v288_locomo_full/`
- Smoke/probe record: `experiments/diagnostic/stage1_memory_object_index_v288_probe_summary.md`
- Predictions/traces:
  - `outputs/diagnostic/stage1_memory_object_index_v288_lme_full/predictions.jsonl`
  - `outputs/diagnostic/stage1_memory_object_index_v288_lme_full/traces.jsonl`
  - `outputs/diagnostic/stage1_memory_object_index_v288_locomo_full/predictions.jsonl`
  - `outputs/diagnostic/stage1_memory_object_index_v288_locomo_full/traces.jsonl`

## 下一步

1. 让 retrieval/context organization 逐步消费 `memory_object_index_v1` 的 source pressure、same-slot coverage、temporal validity 和 conflict state，而不是继续堆 query-side guide。
2. 把 current-state guide、operation utility、graph utility 等兼容层收敛到 unified candidate activation + context compiler。
3. 做小范围 `src/` cleanup，删除已被 `memory_object_index_v1` 覆盖且不影响复现/消融的旧 trace-only 分支。
