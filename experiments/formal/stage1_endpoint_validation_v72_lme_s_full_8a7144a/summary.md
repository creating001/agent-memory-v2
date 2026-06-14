# v72 endpoint validation LongMemEval-S full

## 目的

验证用户提出的假设：query token 不是越多越好，性能可能受上下文噪声和过推断影响。v72 从 v42 出发，不增加 retrieval top-k、不压缩 raw rows、不改 build memory，只对排序/比较类问题加入 question-gated endpoint validation，让 answer model 在回答 A/B 或 order 问题前确认每个候选端点都在 Memory Context 中有源行支持。

## 方法与外部参考

- 借鉴 creating001-agent-memory 的通用 evidence table 思路：区分 support / exclude / missing；没有迁移其中具体实体、场景、样本级或疑似 benchmark shortcut 规则。
- 借鉴 SimpleMem / xMemory 的多视角检索后合并、去重、覆盖和最终回到上下文答题的思路；本轮只做 reader discipline，不改 retrieval。
- v72 的新规则只读 question text 和 retrieved Memory Context，不读取 gold answer、judge output、benchmark label、sample id、row index 或 test feedback。

## 配置与运行

- benchmark/subset：LongMemEval-S full。
- run config：`experiments/formal/stage1_endpoint_validation_v72_lme_s_full_8a7144a/config_snapshot.json`。顶层 v72 config 已在负向结论后删除，避免污染主线配置入口。
- git commit：`8a7144a9d24e6c78ccfad90388f4bf8140e2c0a7`。
- prediction dirty：false。
- workers：4。
- answer model：Qwen/Qwen3-30B-A3B-Instruct-2507。
- answer max input/output：131072 / 16384。

## 结果

- DeepSeek judge accuracy：0.766，383/500，invalid=0。
- v42 修复复现对照：0.772，386/500。
- delta：-0.006。
- evidence recall：1.0，500/500。
- endpoint validation 实际触发：68/500，其中 temporal_lookup 33，list_count 35。
- prediction changed：15/500。
- changed subset：WRONG->CORRECT 1，CORRECT->WRONG 4，CORRECT->CORRECT 8，WRONG->WRONG 2。

## Token 成本

- avg build tokens：80346.246。
- total build tokens：40173123。
- avg query tokens：5884.82。
- total query tokens：2942410。
- build cache：3341 hit / 0 miss / 0 write；按 logical cold-build usage 计入 build token。
- answer cache：432 hit / 68 miss / 68 write；miss 对应 endpoint validation 改变 prompt 的样本。

## 输出路径

- predictions：`outputs/formal/stage1_endpoint_validation_v72_lme_s_full_8a7144a/predictions.jsonl`
- traces：`outputs/formal/stage1_endpoint_validation_v72_lme_s_full_8a7144a/traces.jsonl`
- metrics：`experiments/formal/stage1_endpoint_validation_v72_lme_s_full_8a7144a/metrics.json`
- judge：`experiments/formal/stage1_endpoint_validation_v72_lme_s_full_8a7144a/deepseek_judge.json`
- evidence recall：`experiments/formal/stage1_endpoint_validation_v72_lme_s_full_8a7144a/evidence_recall.json`
- v42 对比：`experiments/formal/stage1_endpoint_validation_v72_lme_s_full_8a7144a/judge_comparison_vs_v42_repro.json`

## 结论

v72 负向，不进入主线。端点校验确实减少了部分过推断，但更常见的问题是让模型在已有足够证据时变得过度保守，或改变了回答格式导致 judge 回退。下一步不应继续加 prompt 约束，而应优先分析 badcase，寻找能提升正确率的 source-preserving candidate organization 或 build/query 协同机制。
