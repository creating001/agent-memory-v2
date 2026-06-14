# v49 规划：Current-State Candidate Map

## 背景

v48 Candidate Evidence Map 在 LongMemEval-S `weak_route_87` 上整体失败：

- v42 same-87: `59/87`
- v48 same-87: `56/87`
- estimated full avg query tokens: `6250.456`

但 v48 的 `current_state` 子集有局部正向：

- v42: `12/22`
- v48: `14/22`
- gain/loss: `4/2`

LongMemEval-S full 中 current_state under clean router 总共就是 `22` 条。因此 v49 只打开 current_state candidate map，可以精确覆盖全部受影响样本，同时把 full token 增量控制在约 `22/500` 的范围。

## 方法设计

底座：v42 operation workpad。

配置：`configs/stage1_current_state_candidate_map_v49_cached.json`

相对 v48 收窄：

- `candidate_guide_information_needs=["current_state"]`
- `candidate_guide_max_rows=4`
- `candidate_guide_snippet_chars=120`
- 其他 route 完全保持 v42 行为

answer cache 复用 v42 namespace。未改变 prompt 的 route 会命中 cache，但 metrics 仍按 cached usage 计入 query tokens；current_state prompt 改变会 miss 并重新生成。

## 外部方法参考

- `xMemory`：保留 selected candidate -> raw message 回链思想，但只用于 current_state，不做 hierarchy/uncertainty。
- `SimpleMem`：保留 structured context 思路，不引入 LLM planner。
- `Graphiti/Zep`：借鉴当前状态/历史事实需要 provenance 和时间对比，仍以 raw row 为最终事实源。
- `Memobase/MIRIX`：借鉴 profile/state 与 event 分开的思想；v49 不新增 build memory 类型，只在 query compiler 中提示比较 current-state candidates。

## Clean 边界

- 只按 clean router 的 current_state route 开关。
- 不读 gold、judge、question_type、category、sample id、row index 或 test feedback。
- Candidate Map 只使用 prediction-time question text、raw row text、row date/role/rank。

## Gate 计划

先跑 LongMemEval-S current_state 全 22 条：

- 这 22 条是 v49 在 LME full 中全部会改变 prompt 的样本。
- 同集比较 v49 vs v42 DeepSeek judge。
- 估算 full token：只把 current_state 的 token delta 加到 v42 full。

通过条件：

- current_state same-22 相对 v42 净正向，且 loss 可解释。
- estimated full avg query tokens <= 6K。
- prompt clean scan 无真实 forbidden metadata。

如果通过，再考虑 LongMemEval-S full；如果不通过，删除顶层 config，只保留诊断。
