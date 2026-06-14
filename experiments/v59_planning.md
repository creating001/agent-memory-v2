# v59 规划：Provenance Alignment + Source Anchor Coverage

## 背景

v42 是当前 LongMemEval-S full 最好结果，但只有 `387/500 = 0.774`，相对 v36 只净增 1 条。继续加长 answer prompt、checklist 或 post-answer repair 的收益不稳定，且容易推高 query tokens。

最近几轮诊断给出的约束很明确：

- v37：把 row-linked typed memory 直接放进 answer prompt 后，LME full 从 v36 `0.772` 降到 `0.744`，说明派生 memory 不能和 raw evidence 无约束竞争。
- v39：用 build-memory source signal 直接全局重排 raw rows，LME full 降到 `0.724`，说明不能让 memory 分数替代原始检索覆盖。
- v56：更细粒度 build extraction 增加 build tokens 和 memory records，但 weak-route accuracy 下降，说明“多抽”不等于 answer 更会用。
- v58：单文档 rerank 在 weak-route 上从 v42 same87 `59/87` 降到 `55/87`，temporal 小正向但 list/profile 明显回退，说明单纯相关性排序会破坏多证据覆盖。

离线 badcase 还显示，v42 的一些错误并不是完全没召回：目标 session / source row 往往已经在 retrieval 或 compiled rows 中，问题更像是 context organization 和 answer 阶段用错证据。例如当前 Instagram follower 数、turbinado sugar preference、项目数量等案例，raw rows 或 source-linked memory 已经能指向关键证据，但最终答案选了旧事实或噪声项。

v59 初版 2 条 smoke 暴露了一个更基础的问题：build memory 已经抽出 “The user is nearing 1300 Instagram followers.”，但 `source_ids` 指到相邻 user turn，而真正包含 `1300 followers` 的 raw row 是 assistant turn。这说明只做 source-anchor ordering 不够，必须先修复 build-stage memory 的 provenance alignment。

## 外部代码参考

本轮只采用通用机制，不迁移 benchmark 专门逻辑。

- `external/creating001-agent-memory/src/agent_memory/baseline/context.py`：参考 turn-pair/source-turn materialization 和 context expansion 的思想。采用“命中派生/组合单位后回到 raw source turns”的形式；不迁移其中任何 financial sample rule、route shortcut 或不 clean guardrail。
- `external/EverOS/src/everos/memory/search/hierarchy.py`：参考 atomic fact child retrieval -> parent episode retrieval，再融合 episode 证据。采用“typed/fact memory 只激活 raw parent”的思想；不引入其后端或复杂 fact eviction。
- `external/xMemory/evaluation/locomo/xMemory_search_framework.py`：参考 representative selection 和 semantic -> episode induction，以及按需展开 original messages。采用 coverage-aware 的方向；不引入其数据格式或 benchmark-specific runner。
- `external/Mnemis/global_selection/global_selector.py`：参考 selected node -> one-hop episodes / edges 回链。采用“结构节点是导航入口，不是最终答案”的原则；不引入图数据库。
- `external/SimpleMem/simplemem/core/hybrid_retriever.py`：参考 semantic / lexical / structured multi-view retrieval 和先分析信息需求再组织 context。v59 不新增 LLM planning，以控制 token 和变量。

## 方法设计

底座：v42 `stage1_operation_workpad_v42_cached`。

新增模块：

- `source_alignment`：build memory 生成后，用 memory 文本和同 session 邻近 raw turns 做轻量 provenance repair。它不调用 LLM，不读取问题答案或 judge，只解决 LLM extractor 把 source 指到相邻 turn 的工程问题。
- `source_anchor_coverage`：compiler evidence order，用修正后的 source links 做 raw evidence organization。
- `current_state_update_contract`：route-scoped reader contract。对于 current/latest/recent 问题，最新近似或自述状态如果直接匹配问题槽位，应作为可用当前状态，并在答案里保留 `about/close to/nearing` 等 qualifier，而不是回退到旧精确值。

核心机制：

- build-stage typed memory 继续由 Qwen LLM 从 raw dialogue 构建，使用现有 cache 和 token 统计。
- source alignment 在每条 memory record 的原 `source_ids` 同 session `window=1` 邻近 turn 内，根据数字、实体、关键词重合补充更匹配的 source turn，并保留原 source。默认阈值 `min_score=2.0`，且新 source 必须比原 source 至少高 `min_delta=1.5`，每条 record 最多 4 个 source。
- query 时仍先执行 v42 的 raw-turn BM25 + dense + build-memory source expansion。
- compiler 使用 `memory_record_source=evidence_rows`：只选择已经进入 raw evidence 候选集的 source-linked memory records。
- typed memory 文本不进入 prompt，`max_memory_records=0`，只通过 `source_ids` 影响 raw evidence rows 的顺序。
- evidence order 保留原始 retrieval top-8 作为 anchor。
- 之后提前最多 10 条 source-linked raw rows，每个 session 最多 2 条，避免单个主题/session 占满前段 context。
- 对被 memory anchor 命中的 session 额外保留 1 条原始检索邻近/连续 context row，然后按原 retrieval 顺序补齐。
- 只在 `current_state`、`list_count`、`profile_preference`、`temporal_lookup` 开启；`fact_lookup` 保持 v42 原样。
- current-state update contract 只对 `current_state` 语义生效，不包含任何具体实体、数字、答案或样本信息。

这不是基于样本的规则。它是一个通用 agent memory 机制：build memory 作为导航和覆盖信号，最终 answer 仍阅读 raw evidence。

## Clean 边界

- prediction 只读取 question、question_time、raw dialogue、visible metadata、build-stage typed memory 和 runtime retrieval/route 结果。
- 不使用 gold answer、DeepSeek judge output、LongMemEval question_type、LoCoMo category、sample id、record key、offline evidence label、test feedback 或样本级规则。
- route 是 question-text/runtime route，不读取 benchmark hidden label。
- DeepSeek judge 只在预测完成后离线使用。
- planning 里的 gold/badcase 信息只用于实验后设计总结，不进入配置、prompt 或 prediction code。

## Token 预期

- build token：应与 v42 同一 build memory 方法一致；cache 命中也按 logical cold-build usage 计入 `avg_build_tokens`。source alignment 不调用 LLM，不增加 build LLM token，但必须记录 alignment stats。
- query token：不增加 LLM 调用，不扩大 top-k，不提高 evidence budget；只改变 raw rows 在 char budget 内的先后顺序，目标仍为 `avg_query_tokens <= 6000`。
- answer max input/output 固定为 `131072/16384`。

## 诊断 gate

先跑 LongMemEval-S `weak_route_87`，因为它覆盖当前最弱的 current_state/list_count/profile_preference/temporal_lookup，且 v54-v58 都在该集合上有可比结果。

必须满足：

- prediction `87/87` 成功。
- prompt clean scan 无 hidden metadata/gold/judge/sample id 泄漏。
- answer max input/output = `131072/16384`。
- `avg_query_tokens <= 6000`，`avg_build_tokens` 正确记录 logical cold-build token。
- DeepSeek judge accuracy 必须高于 v42 same87 的 `59/87 = 0.678161`，否则不跑 full。
- 如果只是持平，必须有清晰的 high-value fixed cases 且无系统性 loss，才考虑后续更精细 ablation；不能直接跑 full。

## 预期风险

- source-linked memory type bonus 可能把相关但不回答问题的 profile/state/event row 前置，造成噪声。
- list/count 题需要覆盖多个独立 operands，若 anchor 行数过少可能仍漏项；若过多又会重演 v39/v58 的覆盖损失。
- 当前机制只在已召回 evidence rows 内重排，不能修复真正 retrieval miss。

## 下一步

1. 单元测试和 smoke 确认 config 生效、typed memory 文本不进 prompt。
2. 提交可复现代码状态。
3. 跑 `weak_route_87` 诊断和 DeepSeek judge。
4. 按 v42 same87 做 gain/loss、by information_need 和 token 对比，再决定是否进入 full。

## 诊断结果

运行：

- run: `v59_source_anchor_lme_weakroute_b086fea`
- commit: `b086fea8dc863cceb4868ca1db0a12496de04ac5`
- dirty: true，仅包含用户改动的 `docs/architecture.md` 和 `docs/clean_protocol.md`
- benchmark/subset: LongMemEval-S `weak_route_87`
- workers: prediction 4，DeepSeek judge 8
- outputs: `outputs/diagnostic/v59_source_anchor_lme_weakroute_b086fea/predictions.jsonl`
- traces: `outputs/diagnostic/v59_source_anchor_lme_weakroute_b086fea/traces.jsonl`
- experiment dir: `experiments/diagnostic/v59_source_anchor_lme_weakroute_b086fea/`

核心指标：

- DeepSeek judge accuracy: `55/87 = 0.632184`
- v42 same87: `59/87 = 0.678161`
- gain/loss: `4/8`
- answer_changed: `31/87`
- avg_build_tokens: `80991.862`
- avg_query_tokens: `6065.920`
- query token > 6000: `42/87`
- query token > 8000: `0/87`
- avg compiled evidence items: `31.092`
- avg context chars: `20485.368`
- build cache: `585` hit / `0` miss / `0` write；build token 仍按 logical cold-build usage 统计
- answer cache: `2` hit / `85` miss / `85` write
- source alignment changed records: total `1621`，avg `18.632`
- source alignment added sources: total `1975`，avg `22.701`

分桶结果：

- `current_state`: v42 `12/22` -> v59 `13/22`，gain/loss `1/0`
- `list_count`: v42 `15/20` -> v59 `13/20`，gain/loss `1/3`
- `profile_preference`: v42 `10/15` -> v59 `7/15`，gain/loss `0/3`
- `temporal_lookup`: v42 `22/30` -> v59 `22/30`，gain/loss `2/2`

结论：v59 是失败诊断，不跑 full，不保留顶层 config。`source_alignment` 能修复一个代表性 current-state provenance 问题，但全路由 source-anchor ordering 引入了明显噪声：profile/preference 和 list/count 的证据覆盖被破坏，query token 也超过 6K 软预算。下一步不能继续扩大 source-anchor；只能把 current-state 的正向信号作为更窄消融候选，并优先从 badcase 和外部实现重新设计 build-to-query 组织方式。
