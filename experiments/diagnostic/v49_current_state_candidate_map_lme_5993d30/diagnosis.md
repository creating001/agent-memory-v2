# v49 诊断结论

## 核心判断

v49 是一个干净但弱信号的 query-side compiler 诊断，不应进入主线 full 实验。

它解决了一部分“当前状态被旧事实覆盖”的问题，但也把少量高相关候选行过度前置，导致 temporal duration 和 ordered-list 题错误。这个问题不是靠继续加 prompt 就能稳定解决，原因是 Candidate Evidence Map 仍然缺少 build-stage 的状态生命周期管理。

## 对比 v42

- v42 same-22: `12/22`
- v49 same-22: `13/22`
- gain: `3`
- loss: `2`
- same_correct: `10`
- same_wrong: `7`
- avg query delta: `+428.363636`
- weighted full avg query delta: `+18.848`
- estimated full avg query tokens: `5884.492`

同子集 build tokens 完全一致：`79065.818182`。这说明 v49 只改变 query/compiler prompt，不改变 build memory。

## 改对样本

- Instagram followers: `1250 -> 1300`，Candidate Map 帮助模型看到后续更新。
- Shinjuku apartment false premise: `7 months -> not enough information`，模型正确排除 Harajuku/Shinjuku 混淆。
- most recent family trip: `Hawaii -> Paris`，模型更重视最新状态。

这些收益都属于“当前状态 / 最新事实 / false premise”类问题。

## 改错样本

- NovaTech current job duration: v42 正确回答 `4 years and 9 months`，v49 变成 insufficient information。
- sports events chronological order: v42 正确，v49 把 charity soccer tournament 错成 volleyball league game。

这两个 loss 表明短 candidate list 会让模型忽略完整时间链或枚举边界。它不是单纯 evidence 不足，而是 context organization 把局部候选放得太突出。

## Clean 和成本

- prediction input 只含 question、question_time、record_key 和 sessions。
- prompt clean scan 没有发现 forbidden metadata。
- DeepSeek judge、gold answer、question_type 只在预测完成后离线读取。
- answer max input/output 为 `131072 / 16384`。
- build token 统计按冷启动逻辑成本，不因 cache hit 记为 0。
- current_state 子集 avg query tokens 为 `6628.409091`，但 full 加权估计为 `5884.492`，预算通过。

## 下一步

不要扩大 v49 full。下一阶段应做 build-to-query 的 general memory management：

- build 阶段抽取 typed state/event/profile，并记录 source、时间和可能的 supersede 关系。
- query 阶段用 typed memory 做召回和 conflict hints，而不是直接把二手 summary 当唯一事实。
- compiler 只给 answer model 结构化的状态候选、冲突链和 raw evidence 回链，避免把短候选 list 变成强制答案。
- 先在 v42 badcases 上做离线 retrieval/context 诊断，再设计一个能同时覆盖 LongMemEval 和 LoCoMo 的全量候选方法。
