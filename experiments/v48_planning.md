# v48 规划：Candidate Evidence Map

## 背景

v42 是当前 LongMemEval-S full 最好结果，但只有 `0.774`，弱项集中在：

- multi-session / count-list 聚合
- current_state 最新状态
- profile_preference 个性化建议
- temporal_lookup 的事件定位和时间窗口

v47 尝试让 answer model 在 `evidence_report` 中输出 `count_increment`，并用 mechanical finalizer 修正，但同 106 条诊断集从 v42 `81/106` 退到 v47 `75/106`。失败原因是 schema 变长、重复计数、过度相信 answer 自报字段。

因此 v48 不再扩大 answer schema，也不做机械 count finalizer。目标是在 compiler 侧给 answer model 一个极短、source-preserving 的候选证据图，帮助它比较已召回 raw rows。

## 方法设计

底座：v42 operation workpad。

新增配置：`configs/stage1_candidate_evidence_map_v48_cached.json`

新增模块：

- `compiler.candidate_guide=true`
- `compiler.candidate_guide_information_needs=["current_state","list_count","profile_preference","temporal_lookup"]`
- `compiler.candidate_guide_max_rows=6`
- `compiler.candidate_guide_snippet_chars=150`

Candidate Evidence Map 只从 prediction-time 可见信息生成：

- question text
- question-derived route / information_need
- retrieved raw evidence rows
- visible row metadata: date、role、retrieval rank

它会输出很短的候选行：

- Memory index
- date / role
- matched question terms
- short quantity mentions
- short time phrase mentions
- query-focused snippet

它不是新事实源，只是 Memory Context 的索引。最终事实仍必须来自 raw Memory Context。

## 外部方法参考

- `xMemory`：参考 component/group 到 original messages 的回链思想；v48 不做 learned uncertainty 或 hierarchical grouping，只做轻量 row candidate map。
- `SimpleMem`：参考 intent-aware multi-view retrieval 后的 structured context；v48 不加 query LLM planner，避免额外 token/cost。
- `Mnemis`：参考枚举问题需要“概念区域内候选覆盖”，但不引入 graph global selection。
- `Graphiti/Zep`：参考 semantic/episode 分层和 provenance；v48 保留 raw rows 为最终证据，不让派生摘要代替原文。
- `creating001-agent-memory`：参考 evidence-first context materialization；舍弃 target phrase、category、sample-level guardrail、gold/judge 相关逻辑。

## Clean 边界

- 不读 gold answer、judge output、benchmark label、question_type、category、sample id、row index、qid 或 test feedback。
- 不写测试实体、测试答案或样本级规则。
- 不改变 retrieval selection，不使用 offline badcase 信息进行样本分支。
- prompt 中的 Memory index 只是当前 prompt 内的局部编号，不是 benchmark row index。

## 预期收益

- count/list：把数量、时间短语、candidate snippet 放在短 map 中，减少漏掉相邻候选和 out-of-scope 混入。
- profile/current_state：即使 structured guide 因 personalized route 被禁用，也能给出偏好/约束/当前状态候选，降低过度 abstain 和通用建议。
- temporal：帮助先定位事件行，再使用 Temporal Aid 和 operation workpad。

## 风险

- v42 query token 只有约 135 token 的 full 平均空间，candidate map 可能导致超预算。
- snippet 可能强化错误候选，尤其是 retrieval 已经噪声较多的样本。
- profile recommendation 如果 map 选错 row，可能从 over-abstain 变成 unsupported recommendation。

## Gate 计划

先做诊断，不直接 full：

1. 创建 LongMemEval-S question-derived weak-route diagnostic，按 clean router 选 current_state、list_count、profile_preference、temporal_lookup，尽量包含多种 question text pattern。
2. 跑 v48 prediction，检查 answer max input/output `131072/16384`、avg query tokens、candidate map 生效率、prompt clean scan。
3. 用 DeepSeek judge 离线比较 v48 vs v42 same set。
4. 只有在 same-set accuracy 净正、changed-answer regression 可解释、estimated full avg query tokens <= 6K 时，才考虑 LongMemEval-S full。

通过条件：

- prediction 全成功。
- DeepSeek judge same-set 净正向，不能只靠 same-answer judge variance。
- full avg query token 估计不超过 6K。
- prompt clean scan 无真实 forbidden metadata 泄漏。

如果 v48 失败，回退该 config，不跑 full；下一步转向 build-side event/profile/state typed view 的 source-linked retrieval，而不是继续加 reader prompt。

## 诊断结果

v48 已完成 LongMemEval-S `weak_route_87` 诊断，结论为失败，不进入 full。

- v42 same-87 DeepSeek judge accuracy: `59/87 = 0.678161`
- v48 same-87 DeepSeek judge accuracy: `56/87 = 0.643678`
- gain/loss: `6 / 9`
- answer_changed: `32`
- avg_build_tokens: `80991.862069`
- avg_query_tokens: `6618.068966`
- estimated full avg query tokens: `6250.456`

按 information_need：

- current_state: v42 `12/22` -> v48 `14/22`
- list_count: v42 `15/20` -> v48 `14/20`
- profile_preference: v42 `10/15` -> v48 `8/15`
- temporal_lookup: v42 `22/30` -> v48 `20/30`

决策：

- 不跑 LongMemEval-S full。
- 删除顶层候选配置 `configs/stage1_candidate_evidence_map_v48_cached.json`，只保留诊断目录里的 `config_snapshot.json`。
- Candidate Evidence Map 模块保留为可消融能力，但不在全部 weak routes 上开启。
- 下一步只尝试 current_state-only、token-safe 的 v49，验证局部正向是否稳定。
