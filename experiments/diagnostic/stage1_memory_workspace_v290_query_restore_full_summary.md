# v290 memory workspace query-restore full summary

## 结论

v290 升为当前本地 LTS。

v290 保留 v289 新增的 build-owned `memory_workspace_manifest_v1`，但恢复 v288 的 query behavior：重新启用 `memory_state_guide` / `memory_value_slot_guide`，关闭 compact `Memory Workspace Plan`。这样把 build-side Agent Memory system organization 与 query-side 风险解耦。

v290 相对 v288 的 prediction-time 行为保持等价：LME/LoCoMo full answer、prompt、route、compiled evidence、compiled memory records、build records 均为 `0` diff；memory object index summary 为 `0` diff；workspace manifest applied `2040/2040`。因此 v290 继承 v288 full dual judge accuracy，同时进一步降低“build memory system 不够系统化、memory object 缺少统一 workspace/lifecycle/operation contract”的风险。

## 方法

- 算法 commit：`ef89fc29d8386777add84bd85dc619cf2fa464cd`
- 实现 commit：`c1b879a3846d2fe37082c047016b9d5de2e508a5`
- 配置：`configs/stage1_memory_workspace_v290_query_restore_seeded_qwen36_no_think_build4k_cached.json`
- 主要改动：
  - build 阶段保留 `memory_workspace_manifest_v1`。
  - workspace manifest 统一表达 source-backed activation group、memory tier、lifecycle state、conflict state、operation hints、context_pack policy。
  - query 阶段恢复 v288 的 state/value guide pair。
  - compact `Memory Workspace Plan` 在 v290 LTS 配置中关闭，仅保留为后续 guarded/additive 实验入口。
  - answer cache namespace 复用 v287/v288 prompt-equivalent cache，两个 full run 均为 answer cache `100%` hit。
- Clean 边界：prediction 不使用 gold answer、judge output、benchmark label、sample id、test feedback 或样本级规则；最终答案仍以 raw Memory rows 为证据。

## Full Metrics

| Benchmark | n | inherited strict/lenient accuracy | avg build/query tokens | workspace manifest | workspace plan | answer diff vs v288 |
|---|---:|---:|---:|---:|---:|---:|
| LongMemEval-S full | 500 | `0.834000 / 0.846000` | `85393.566 / 6455.588` | `500/500` | `0/500` | `0/500` |
| LoCoMo non-adversarial full | 1540 | `0.794156 / 0.819481` | `62015.57402597403 / 6093.962337662338` | `1540/1540` | `0/1540` | `0/1540` |

## Diff Audit vs v288

| Benchmark | prompt | route | compiled evidence | compiled memory | stable retrieval | build records | memory object index summary | workspace manifest summary |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| LongMemEval-S full | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 500 |
| LoCoMo non-adversarial full | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1540 |

Diff file: `experiments/diagnostic/stage1_memory_workspace_v290_diff_vs_v288.json`.

LoCoMo raw retrieval trace had `10/1540` diffs only in volatile trace fields (`embedding_cache`, `rerank_response`). After removing those diagnostic/cache fields, stable retrieval diff is `0/1540`; compiled evidence and prompts are also `0` diff.

## 决策

v290 升 LTS。它不追求短期 query trick，而是先把 build 阶段推进成更像 Agent Memory system 的结构化 workspace：

- memory object 有 source-backed activation group；
- working / long-term / archival / quarantine tier 有统一 query-facing contract；
- create / update / merge / supersede / retrieve / expand / verify / audit / context_pack 操作进入 build artifact；
- query 仍保持 v288 已验证路径，避免 v289 那种 compact plan 直接替换造成的 accuracy 回退。

下一步在 v290 LTS 上探索 v291：workspace plan 只能以 guarded/additive 方式进入 query，优先 current-state conflict / source expansion / verifier audit 小范围场景；不能再直接替换已验证 guide。

## Output Paths

- LME full run: `outputs/diagnostic/stage1_memory_workspace_v290_query_restore_lme_full/`
- LoCoMo full run: `outputs/diagnostic/stage1_memory_workspace_v290_query_restore_locomo_full/`
- LME experiment record: `experiments/diagnostic/stage1_memory_workspace_v290_query_restore_lme_full/`
- LoCoMo experiment record: `experiments/diagnostic/stage1_memory_workspace_v290_query_restore_locomo_full/`
- Diff audit: `experiments/diagnostic/stage1_memory_workspace_v290_diff_vs_v288.json`
