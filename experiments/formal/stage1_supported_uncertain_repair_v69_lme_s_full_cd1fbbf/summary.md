# v69 Supported Uncertain Repair

## 目的

验证一个很窄的 clean verifier/repair 组件：在 v42 可复现基线之上，只对 draft 自己明确表现为 insufficient / unknown / missing，且 draft evidence_report 至少有 1 条 support item 的样本触发二次回答。目标是修复“证据已经在 context 中但初答拒答”的 case，同时不让 query token 超过 6K。

该设计参考外部 `creating001-agent-memory` 的 evidence verification / repair 思路，但没有迁移其 benchmark-specific guardrail，也没有使用 gold、judge、question_type、sample id、row index 或测试反馈。repair 输入只来自运行时可见 question、route、compiled context、draft JSON 和 draft evidence_report。

## 结论

v69 不作为当前主线配置保留。

- DeepSeek judge full accuracy：0.760，380/500，invalid=0。
- v42 复现控制：0.772，386/500。
- prediction changed：6/500。
- 6 条实际改动的 judge transition：WRONG->CORRECT 2，WRONG->WRONG 4，没有观察到 changed subset 回退。
- 494 条未改 prediction 的重跑 transition：CORRECT->WRONG 13，WRONG->CORRECT 5，说明 full judge 差异混入明显同答案 judge variance。
- evidence_recall：1.0，500/500。

整体判断：supported repair 有很小的局部正向信号，但 full judge 重跑低于 v42，且 profile/preference repair 仍会生成外部平台或过宽类别，风险高于收益。后续不继续沿 broad answer repair 作为主线，应转向低噪声的 build/query memory organization。

## Token 成本

- avg build tokens：80346.246。
- total build tokens：40173123。
- build token 口径：逻辑 cold-build 成本；即使 build cache 全命中，也按 cached usage 计入新环境构建 memory 的成本。
- avg query tokens：5981.198。
- total query tokens：2990599。
- answer max input/output：131072 / 16384。
- repair triggered：20/500。
- repair applied：6/500。
- repair total query tokens：58246。
- repair avg query tokens when triggered：2912.3。
- answer draft cache：500 hits / 0 misses / 0 writes。
- repair cache：0 hits / 20 misses / 20 writes。

## 配置与 clean 记录

- benchmark/subset：LongMemEval-S full。
- config：`configs/stage1_supported_uncertain_repair_v69_cached.json`。
- formal config snapshot：`experiments/formal/stage1_supported_uncertain_repair_v69_lme_s_full_cd1fbbf/config_snapshot.json`。
- git commit：`cd1fbbfec4b6a0c665cd8abd0d208dcdcd7388a5`。
- prediction dirty：false。
- 离线 judge/evidence 文件的 git dirty 为 true，因为评测时实验目录本身尚未提交；这不影响 prediction clean 状态。
- clean 口径：prediction pipeline 未使用 gold answer、judge 输出、benchmark 标签、sample id、row index、question_type 或 test feedback。

## 输出路径

- predictions：`outputs/formal/stage1_supported_uncertain_repair_v69_lme_s_full_cd1fbbf/predictions.jsonl`
- traces：`outputs/formal/stage1_supported_uncertain_repair_v69_lme_s_full_cd1fbbf/traces.jsonl`
- metrics：`experiments/formal/stage1_supported_uncertain_repair_v69_lme_s_full_cd1fbbf/metrics.json`
- judge：`experiments/formal/stage1_supported_uncertain_repair_v69_lme_s_full_cd1fbbf/deepseek_judge.json`
- evidence recall：`experiments/formal/stage1_supported_uncertain_repair_v69_lme_s_full_cd1fbbf/evidence_recall.json`
- v42 对比：`experiments/formal/stage1_supported_uncertain_repair_v69_lme_s_full_cd1fbbf/judge_comparison_vs_v42_repro.json`

## 下一步

不要继续靠更宽的 repair 或更接近 6K 的上下文换分。v42/v66/v69 共同说明：LongMemEval-S 当前 evidence recall 已是 1.0，主要瓶颈是证据密度、冲突组织、列表/时间端点完整性和 profile/event 边界。下一阶段应做更有结构的候选聚类、event chain / profile-event 双通道和低噪声 compiler，而不是简单增加 token。
