# v76 uncertain profile repair LongMemEval-S full

## 目的

v75 的 all-profile compact repair 在 changed-prediction 子集有轻微信号，但 fresh full judge 负向，主要问题是会重写已经足够个性化的答案。v76 在 v75/v73 基础上只验证一个变量：保留 advice/profile 路由和 compact repair prompt，但只在 draft answer 或 draft JSON 显示 unknown / insufficient / missing 时触发 profile repair。

本轮设计参考了 `docs/method.md`，以及本地只读外部代码：
- creating001 agent-memory：二阶段 evidence-to-answer / verify 思路，但不迁移其 benchmark-specific 或样本级规则。
- SimpleMem：adequacy / reflection 只在信息不足时补救的思路。
- xMemory：multi-view retrieval 作为证据激活基础，本轮不改 retrieval，只保持已有 dense+BM25。

## Clean 记录

- 预测阶段未使用 gold answer、judge output、benchmark label、sample id、row index、test feedback 或样本级规则。
- repair 只读取 question、question_time、route、retrieved Memory Context、draft answer 和 draft JSON。
- v76 answer cache 从 v73 prediction traces seed，用于隔离非目标样本重跑噪声；seed 脚本未读取 labels/judge/gold。
- build cache hit 仍按 cached usage 计入 build tokens，表示新环境冷构建 memory 的真实 LLM 成本。

## 配置与运行

- benchmark/subset：LongMemEval-S full。
- config：预测时为 `configs/stage1_profile_uncertain_compact_repair_v76_cached.json`；负向结论后顶层配置已删除，复现以本目录 `config_snapshot.json` 为准。
- git commit：`5e1d4eb5fae3fbf7c153303e465c2d69ed183240`。
- prediction dirty：false。
- workers：8。
- answer model：Qwen/Qwen3-30B-A3B-Instruct-2507。
- answer max input/output：131072 / 16384。

## 结果

- DeepSeek judge accuracy：0.768，384/500，invalid=0。
- v73 fresh accuracy：0.778，389/500。
- v75 fresh accuracy：0.766，383/500。
- evidence recall：1.0，500/500。
- prediction_changed vs v73：16/500。
- changed subset vs v73：WRONG->CORRECT 6，CORRECT->WRONG 4，WRONG->WRONG 5，CORRECT->CORRECT 1。
- controlled accuracy using v73 judgments for unchanged predictions：391/500 = 0.782。

By type fresh v76：
- knowledge-update：64/78 = 0.821。
- multi-session：85/133 = 0.639。
- single-session-assistant：53/56 = 0.946。
- single-session-preference：14/30 = 0.467。
- single-session-user：65/70 = 0.929。
- temporal-reasoning：103/133 = 0.774。

## Token 成本

- avg build tokens：80346.246。
- total build tokens：40173123。
- avg query tokens：5880.232。
- total query tokens：2940116。
- build cache：3341 hit / 0 miss / 0 write。
- answer cache：485 hit / 15 miss / 15 write。
- repair：6 triggered / 4 applied。
- repair total query tokens：14235。
- repair avg query tokens when triggered：2372.5。

## 输出路径

- predictions：`outputs/formal/stage1_profile_uncertain_compact_repair_v76_lme_s_full_5e1d4eb/predictions.jsonl`
- traces：`outputs/formal/stage1_profile_uncertain_compact_repair_v76_lme_s_full_5e1d4eb/traces.jsonl`
- metrics：`experiments/formal/stage1_profile_uncertain_compact_repair_v76_lme_s_full_5e1d4eb/metrics.json`
- judge：`experiments/formal/stage1_profile_uncertain_compact_repair_v76_lme_s_full_5e1d4eb/deepseek_judge.json`
- evidence recall：`experiments/formal/stage1_profile_uncertain_compact_repair_v76_lme_s_full_5e1d4eb/evidence_recall.json`
- comparison：`experiments/formal/stage1_profile_uncertain_compact_repair_v76_lme_s_full_5e1d4eb/judge_comparison_vs_v73.json`
- badcases：`experiments/formal/stage1_profile_uncertain_compact_repair_v76_lme_s_full_5e1d4eb/delta_badcases.md`

## 结论

v76 不进入主线。它比 v75 更干净地验证了“只修不确定 profile draft”的思路，token 合格且 controlled changed subset 比 v73 净 +2；但 fresh full judge 仍低于 v73 1 个百分点，single-session-preference 也没有恢复。下一步不要继续扩大 repair 触发面，应回到 badcase 里分析 profile/preference evidence organization 和答案选择问题。
