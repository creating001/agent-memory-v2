# v55 turn-window dense32 消融规划

## 背景

v54 在 LongMemEval-S `weak_route_87` 诊断上与 v42 持平：`59/87`，gain/loss `7/7`。按 information_need 看，`list_count` 有小正向，但 `current_state`、`profile_preference`、`temporal_lookup` 抵消。badcase 检查显示若干 loss 发生在 v54 替换掉 v42 的 evidence rows 后；v54 同时把 dense hard-protect 从 32 降到 28，因此需要分辨问题来自 window retrieval，还是来自 dense protect 放松。

## 方法

v55 只做一个改动：

- 保留 v54 的 `turn_window_bm25`：`top_k=24`，`window_before=1`，`window_after=1`，每个 window 最多投影 3 个原始 source turn。
- 将 dense `protect_top_n` 从 v54 的 `28` 恢复到 v42 的 `32`。
- answer max input/output 仍为 `131072/16384`。
- build/query token 统计口径不变，cache hit 仍按 logical cold-run token 成本计入。

## Clean 边界

该消融不新增任何 prediction-time 信息源，不使用 gold answer、judge output、benchmark 标签、sample id、row index、test feedback 或样本级规则。DeepSeek judge 只用于预测完成后的离线比较。

## Gate

仍在 `weak_route_87` 上与 v42 same87 对比：

- 若 v55 不高于 v42 same87，停止 turn-window retrieval 当前参数方向，不跑 full。
- 若 v55 明确高于 v42 且 avg query tokens 仍低于 6K，再考虑 LongMemEval-S full。
- 若只出现同答案 judge variance 或弱正向，先做 LoCoMo/更多 badcase 分析，不直接 full。
