# v39 diagnosis

## 诊断结论

v39 的假设被 full run 否定：typed memory 作为 source selector 的通用思路本身 clean，但当前 deterministic memory-aware ordering 不够稳。它确实改变了一部分答案，修复了 22 条 v36 错例；但同时破坏了 46 条 v36 正例，净 `-24`。

不要跑 LoCoMo。顶层 `configs/stage1_memory_aware_selector_v39_cached.json` 不长期保留，历史追溯依赖本 formal 目录的 `config_snapshot.json`。

## 与基线对比

| 对比 | both_correct | both_wrong | gained | lost | delta |
|---|---:|---:|---:|---:|---:|
| v39 vs v36 | 340 | 92 | 22 | 46 | -24 |
| v39 vs v38 | 338 | 100 | 24 | 38 | -14 |

v39 vs v36 lost 分布：

| group | lost |
|---|---:|
| temporal_lookup | 19 |
| list_count | 17 |
| fact_lookup | 7 |
| current_state | 3 |

v39 vs v36 gained 分布：

| group | gained |
|---|---:|
| temporal_lookup | 10 |
| fact_lookup | 9 |
| list_count | 2 |
| profile_preference | 1 |

## Route / Token Audit

| information_need | n | top_k | avg query | p90 query | max query | avg rows |
|---|---:|---:|---:|---:|---:|---:|
| current_state | 22 | 40 | 6235.227 | 6905 | 7150 | 33.773 |
| fact_lookup | 183 | 40 | 5351.251 | 5756 | 6867 | 34.262 |
| list_count | 119 | 60 | 5609.345 | 5900 | 6906 | 33.824 |
| profile_preference | 15 | 40 | 5097.733 | 5505 | 5665 | 35.800 |
| temporal_lookup | 161 | 60 | 6648.112 | 7237 | 22902 | 36.037 |

整体 avg query tokens `5861.556`，仍低于 6K 主线预算；但存在 2 条 `>8000` query token 的 temporal outlier，其中 1 条触发长循环并判错。这说明 answer output guard 仍有工程改进空间，但不能解释 v39 的主要 -24 回退；主要回退来自 evidence ordering 改变后的 list/temporal operand 错选。

## Badcase 观察

- `list_count` 回退多为多项枚举/计数边界错误，例如总游戏时长、慈善金额、订阅数量、列表第 N 项等；memory-aware selector 会把局部相关 row 提前，但缺少“覆盖所有 operand”的保证。
- `temporal_lookup` 回退多为时间链条中选错起点/终点，或把相邻事件当成目标事件；source-linked memory bonus 并不能稳定区分 operand role。
- `current_state` 少量回退说明即使非目标 route 保持 retrieval order，answer 方差仍存在；但主要损失不在这里。
- Evidence recall 为 `1.0`，所以不能简单继续加 top_k 或塞更多 memory。需要改的是 evidence organization、operand coverage 和 answer contract。

## 方法层判断

从外部方法借鉴角度看，HippoRAG/Graphiti/LightMem/Memary 的“派生 memory 回链 raw evidence”方向仍然有价值；v39 失败的是当前实现过于粗糙：

- memory record overlap 和 source link 只知道“相关”，不知道 evidence 在最终推理里是 operand、distractor、superseded fact 还是相邻背景。
- list/count 需要 set coverage 和 dedup，而不是只按 source row 分数排序。
- temporal 需要 event role、起止点和有效期组织，而不是只用通用 time/quantity signal。

## 下一步

下一轮不要再跑基于 row score 的轻量排序 full run。先做 v36 badcase 复盘和外部方法代码复查，再设计更结构化但仍 clean 的 build/query 改进：

- 从 v36 的 wrong cases 中抽样分析 retrieval miss、operand missing、wrong speaker、stale fact、answer synthesis error。
- 优先考虑“raw evidence + structured operand table”的 compiler，而不是继续调整 top-k 排序。
- 如果要利用 build memory，应该让它产生可追溯的 event/list/profile candidates，并回链 raw rows 后由 compiler 组织，不让 memory score 直接决定最终 row order。
