# v50 诊断结论

## 核心判断

v50 的 hypothesis 是合理的，但实现方式失败：把 advice 类问题路由到 `profile_preference`，并给 answer model 看 source-linked build memory guide，并不能稳定提升 personalized recommendation。

这说明当前瓶颈不只是“router 没识别 advice”，也不只是“prompt 没提醒个性化”。模型需要更可靠的 build-side memory management，尤其是 profile/preference/event 的可用 slot、时间、source 和 delta，而不是更多 reader 侧提示。

## 对比 v42

- v42 same-30: `13/30`
- v50 same-30: `12/30`
- gain: `1`
- loss: `2`
- same_correct: `11`
- same_wrong: `16`
- net: `-1`
- route_changed: `15/30`
- answer_changed: `25/30`
- avg query delta: `+461.833333`

v50 只改 query/route/compiler，不改 build memory；同子集 avg build tokens 与 v42 完全一致。

## 改对样本

- `Can you suggest some accessories that would complement my current photography setup?`
- v50 答出与摄影装备相关的品牌/配件方向，被 DeepSeek 判为正确。

这个 gain 可能更多来自重新生成和 guide 排布，而不是一个稳定机制；同样方向在 v49 也出现过，但 close-margin 明显。

## 改错样本

- `Can you recommend some interesting cultural events happening around me this weekend?`
  - v42 和 v50 文本几乎相同，但 judge label 从 correct 变 wrong，属于 same-answer judge variance 或边界样本，不可作为方法收益。
- `Any tips on what to look for in a new guitar?`
  - v42 已经正确提到 Stratocaster / Les Paul / open D tuning，v50 改写后丢掉部分关键个性化细节，被判错。

## Route 审计

full LongMemEval-S 上，v50 只改变 `15/500` 条 route：

- `fact_lookup -> profile_preference`: `13`
- `list_count -> profile_preference`: `1`
- 其他 route 不变

这说明 v50 即使成功，上限也比较窄；实际 same-30 失败，因此没有 full 价值。

## Clean 和成本

- prediction input 不含 gold、judge、question_type、category、sample id、qid、row index 或 test feedback。
- prompt clean scan 为 `0` findings。
- DeepSeek judge 和 gold 只在预测完成后离线使用。
- answer max input/output 为 `131072 / 16384`。
- avg query tokens `5801.666667`，局部预算通过，但相对 v42 增加 `461.833333`，没有换来 accuracy。

## 后续取舍

不要继续做 advice prompt 叠加，也不要扩大到 full。下一步更值得做：

- 离线审计 v42 single-session-preference 的 raw evidence 与 build memory record：哪些用户约束被 build 漏掉，哪些被抽成 generic event。
- 设计 build-side profile/event delta：把“用户拥有/偏好/正在尝试/已成功/遇到问题”等 slot 做成更可靠的 typed memory。
- query 阶段只用 typed memory 做 source activation 和 conflict/profile hints，answer 阶段仍回到 raw evidence。
- LoCoMo category 1/2/3 也需要类似的 profile/event activation，因此下一轮方法必须同时考虑 LME preference 和 LoCoMo evidence recall。
