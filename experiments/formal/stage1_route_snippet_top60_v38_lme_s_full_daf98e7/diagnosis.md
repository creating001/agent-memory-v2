# v38 诊断

## 结论

v38 没有超过 v36。LME full DeepSeek judge accuracy 为 `0.752`，比 v36 的 `0.772` 少 `10` 条正确样本。虽然 evidence recall 仍为 `1.0`，但 answer 侧在更多候选证据下更容易混入相邻事件、过期状态或不该计数的项目。

这说明当前瓶颈不是简单 recall，而是 evidence selection / memory organization / reader decision。扩大 raw context 能修复一部分漏召回或漏聚合，但会让计数和时间边界问题更脆弱。

## 与 v36 的差异

- both correct: `356`
- both wrong: `94`
- v38 gained: `20`
- v38 lost: `30`
- answer changed: `129`
- changed-answer net: `-9`
- same-answer judge flip net: `-1`

按 information_need：

| need | gained | lost | net |
|---|---:|---:|---:|
| `fact_lookup` | 9 | 6 | +3 |
| `profile_preference` | 1 | 0 | +1 |
| `current_state` | 1 | 2 | -1 |
| `list_count` | 3 | 10 | -7 |
| `temporal_lookup` | 6 | 12 | -6 |

按 question_type：

| question_type | gained | lost | net |
|---|---:|---:|---:|
| `knowledge-update` | 1 | 1 | 0 |
| `temporal-reasoning` | 6 | 5 | +1 |
| `single-session-preference` | 5 | 4 | +1 |
| `single-session-user` | 0 | 1 | -1 |
| `single-session-assistant` | 0 | 6 | -6 |
| `multi-session` | 8 | 13 | -5 |

## 有效信号

v38 的 gains 主要来自确实需要更多候选项的问题：

- 露营天数：v36 答 `3`，v38 找到 `8`。
- 三个 road trip 驾驶总时长：v36 判断信息不足，v38 答 `15 hours`。
- 最近一个月涨粉最多的平台：v36 答 Twitter，v38 答 TikTok。
- 最近两个月买的首饰数量：v36 答 `2`，v38 答 `3`。
- 当前拥有的乐器数：v36 答 `3`，v38 答 `4`。

这些说明：更宽 raw evidence 对跨 session 聚合有价值，但不能直接把更多 row 交给最终 reader。

## 负向信号

主要 lost case 是噪声和边界污染：

- 游戏总时长：v36 `140 hours` 正确，v38 把额外候选加进来答 `170 hours`。
- 过去两周烘焙次数：v36 `4` 正确，v38 答 `6`。
- 三周以来写作作品数：v36 `23` 正确，v38 答 `25`。
- 三个月毕业典礼次数：v36 `3` 正确，v38 答 `1`。
- 单 session assistant 类问题损失 6 条，说明 snippet/top60 会破坏原本精确的局部问答定位。

这类错误不是 clean 问题，而是方法质量问题：reader 看到了更多近似相关证据，却没有稳定区分 include/exclude 边界。

## Token 与预算

- avg query tokens `5934.178`，仍低于主线 `6000` 平均预算，但距离上限很近。
- `temporal_lookup` avg query tokens `6705.025`，p90 `7343`，max `7752`；如果再扩大 context，会直接进入 expensive/diagnostic 风险。
- avg build tokens `80346.246`，与 v36 相同量级；build cache 全命中只代表本地复跑节省调用，不代表方法构建成本为 0。

## 方法取舍

保留的经验：

- v37 已证明 typed memory 直接进入 answer prompt 会显著伤害 LME；v38 相比 v37 净 +4，确认最终 reader 不应被未筛选 typed facts 干扰。
- raw evidence 扩容能修一些聚合漏项，但必须增加更强的 evidence selection 或 operation-aware organization，不能只扩 top_k。

放弃的方向：

- 不把 v38 作为主线。
- 不跑 v38 LoCoMo full。
- 不长期保留顶层 v38 config；正式 `config_snapshot.json` 足够复现该负向实验。

## 下一步

下一阶段应从 v36 出发，而不是从 v38 出发。候选方向需要先做 badcase 和外部方法代码分析，再开 full run：

- build 阶段生成可检索的 operation-aware memory views，例如可计数实体、时间窗口、状态变更链，但只用于候选选择和证据排序。
- query 阶段减少最终 prompt 负担：让 memory manager 做 include/exclude 边界筛选，最终 answer 仍主要依据 raw evidence。
- 对 list/temporal 问题优先研究 rerank/selection，而不是继续扩大 top_k。
