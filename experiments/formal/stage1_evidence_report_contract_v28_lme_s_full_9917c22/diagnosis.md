# Diagnosis for stage1_evidence_report_contract_v28_lme_s_full_9917c22

## 诊断结论

v28 是当前最强 LME 方法，但还不是目标完成状态。DeepSeek judge accuracy 为 `0.766`，高于 v26 `0.746` 和 v18 `0.732`，但距离 LongMemEval-S baseline target `0.800` 仍差 `17/500` correct。

## 为什么有效

- v28 强制 answer model 输出可见 `evidence_report`，比 v27 的私有 workpad 更能稳定执行证据选择。
- `fact_lookup` 达到 `0.803`，明显修复了一些错槽位和过度拒答，例如 Spotify、previous occupation、uncle/niece false premise。
- `list_count` 达到 `0.807`，是目前该 information_need 的最好结果；模型更常列出 distinct items 和 operands。
- `knowledge-update` 回到 v18 的 `0.821`，同时没有像 v26 那样显著牺牲更新类问题。
- source/session coverage diagnostic 仍为 `1.0`，说明提升主要来自读证和证据组织，而不是单纯召回更多参考 session。

## 仍然失败在哪里

- `temporal_lookup` 只有 `0.727`，低于 v26 的 `0.739`。可见 evidence report 对复杂时间窗口、最近一个月、美国境内/范围过滤等题仍不够稳。
- `multi-session` 为 `0.647`，略低于 v26 `0.654`。v28 改好了一些 sum/count，但也引入了过度保守或错误过滤。
- `single-session-preference` 为 `0.433`，高于 v18/v26，但低于 v27 `0.500`。说明 preference reader 还没有同时做到“个性化迁移”和“不乱造命名实体”。
- query tail 偏长：avg `5736.928` 在预算内，但 `147/500` 超过 6K、`3/500` 超过 8K。后续需要压缩 evidence_report 输出或更精细地按 route 启用。

## 代表性变化

v28 vs v26:
- both_correct `345`
- v26_only `28`
- v28_only `38`
- both_wrong `89`
- same normalized answer judge diffs `2`

v28 改对的类型：
- doctor count: `4` -> `3 different doctors`
- total game hours: `90/100` -> `140 hours`
- kitchen items: `4` -> `5 kitchen items`
- previous occupation: `Senior marketing analyst` -> `marketing specialist at a small startup`
- false-premise uncle birthday baking: wrong concrete cake -> insufficient

v28 新增错误：
- coupon redeemed location: 过度保守，拒答 Target
- camping days in U.S.: `8` -> `3`
- social media most followers: `TikTok` -> `Twitter`
- some concise numeric answers lost unit or context, e.g. `3.5` vs `3.5 weeks`
- some correct concise answer被 judge 判错的风险仍存在，例如 `sister` vs `my sister`

## Clean 与成本

- prediction commit clean: `9917c229064fe7ff2e27ba07460eef549fc18352`
- prediction dirty: `false`
- judge/diagnosis dirty: `true` only because experiment files were created after prediction.
- build token 统计为新环境 cold-build logical LLM cost；cache hit 只减少实际 API 调用，不减少方法成本统计。
- avg build tokens `80346.246`，avg query tokens `5736.928`，满足主线 avg 预算。
- answer LLM max input/output: `131072/16384`。
- answer finalizer disabled；没有用 judge、gold、question_type、sample id 或样本级规则修答案。

## 下一步

v28 值得跑 LoCoMo non-adversarial full，因为它是当前 LME 最好结果且方法 general。LoCoMo 如果提升，v28 可作为下一轮主线底座；如果下降，则说明 visible evidence report 主要适配 LME reader，需要回到更底层的 memory organization。

后续方法方向：
- 对 temporal_lookup 做 source-aware time window view：事件日期、mention date、relative phrase、range filter 分开呈现。
- 对 multi-session list/count 引入更紧凑的 candidate table，减少长尾 token，同时保留 included/excluded 候选。
- 对 preference/profile 分离 stable preference 与 one-off event，避免 v27/v28 在 preference 上互相拉扯。
- 考虑 build-side typed memory schema 改进，但必须重新全流程跑，并继续记录 cold-build logical tokens。
