# v291 memory operation plan full summary

## 结论

v291 升为当前本地 LTS。

v291 在 v290 的 build-owned `memory_workspace_manifest_v1` 上新增 `memory_operation_plan_v1`。它把每个 source-backed workspace slot 转成显式的 memory operation plan：`create / update / merge / supersede / retrieve / expand / verify / audit / context_pack`，并记录 current、historical、as-of view policy、source expansion、verification、audit 和 context pack contract。

query behavior 保持 v290/v288 等价：`memory_state_guide` / `memory_value_slot_guide` 继续启用，compact `Memory Workspace Plan` 继续关闭。最终答案仍只以 raw Memory rows 为 evidence。

## 方法

- 算法 commit：`7161e68f630e993124c8c74d5c9ab477d0262def`
- 配置：`configs/stage1_memory_operation_plan_v291_query_restore_seeded_qwen36_no_think_build4k_cached.json`
- 参考来源：
  - xMemory / EverOS / Nemori：derived memory 必须能 expand 到 source episode / raw row。
  - Mem0 / Memanto / Graphiti：update/delete 改成 non-destructive supersede、archival、as-of view 和 provenance。
  - MemoryOS / Letta / MIRIX：working / long-term / archival / quarantine tier 和多类 memory object taxonomy。
- 本项目取舍：operation plan 是 question-independent build artifact，不读 question label、gold、judge、sample id 或 test feedback；derived memory 只做 activation、state management、audit 和 context organization，不能替代 raw evidence。

## Full Metrics

| Benchmark | n | full dual judge strict/lenient accuracy | avg build/query tokens | operation plan | answer diff vs v290 |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S full | 500 | `0.834000 / 0.846000` | `85393.566 / 6455.588` | `500/500` records, `44630` slot plans | `0/500` |
| LoCoMo non-adversarial full | 1540 | `0.794156 / 0.819481` | `62015.57402597403 / 6093.962337662338` | `1540/1540` records, `196651` slot plans | `0/1540` |

Accuracy 继承自 v290/v288 full dual judge。v291 full prediction 相对 v290 的 answer diff 为 `0`，changed-output judge 集合为空；无需新增 DeepSeek judge 调用即可得到 full 合并口径。

## Diff Audit vs v290

| Benchmark | answer | prompt | route | compiled evidence | compiled memory | stable retrieval | build records | memory object index | workspace manifest |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| LongMemEval-S full | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| LoCoMo non-adversarial full | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Diff file: `experiments/diagnostic/stage1_memory_operation_plan_v291_diff_vs_v290.json`.

## Operation Plan Coverage

| Benchmark | applied records | total slot plans | update/supersede plans | merge plans | audit conflict obligations | as-of views |
|---|---:|---:|---:|---:|---:|---:|
| LongMemEval-S full | `500/500` | `44630` | `2814` | `76` | `2814` | `44630` |
| LoCoMo non-adversarial full | `1540/1540` | `196651` | `8514` | `2800` | `8514` | `196651` |

## 决策

升 LTS。v291 相对 v290 不改变已验证 query path 和答案，但把 build 阶段从 workspace manifest 进一步推进到 operation-plan 层：memory 不只是 retrieval hint，而是有 source expansion、current/historical/as-of view、non-destructive update/supersede、verify、audit 和 context-pack contract 的系统化 Agent Memory artifact。

下一步应在 v291 上做 guarded/additive query 消费实验：优先从 current-state conflict、as-of source expansion、verifier audit 小范围开始，不能再用 compact workspace plan 直接替换已验证 query guide。

## Output Paths

- LME full run: `outputs/diagnostic/stage1_memory_operation_plan_v291_lme_full/`
- LoCoMo full run: `outputs/diagnostic/stage1_memory_operation_plan_v291_locomo_full/`
- LME experiment record: `experiments/diagnostic/stage1_memory_operation_plan_v291_lme_full/`
- LoCoMo experiment record: `experiments/diagnostic/stage1_memory_operation_plan_v291_locomo_full/`
- Diff audit: `experiments/diagnostic/stage1_memory_operation_plan_v291_diff_vs_v290.json`
