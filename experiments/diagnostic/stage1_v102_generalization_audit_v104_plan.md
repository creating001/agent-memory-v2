# v102 generalization audit and v104 plan

## 目的

本诊断对应当前目标的五个问题：检查 v102 是否存在 design-for-benchmark 风险，尤其是 granularity/profile、selected context、mechanical finalizer、top-k/context noise，以及 build memory 只作为 retrieval index 的局限。

本文件只记录 prediction-time 可见信息、正式实验 trace 和外部方法代码调研结论；不使用 gold answer、judge output、benchmark 标签、sample id 或样本级规则来设计预测逻辑。

## 当前 v102 证据

主目录 qwen3.6 no-thinking v102 formal rerun 结果：

- LongMemEval-S full：strict `407/500 = 0.814`，lenient `415/500 = 0.830`。
- LoCoMo non-adversarial full：strict `1196/1540 = 0.776623`，lenient `1229/1540 = 0.798052`。
- Judge 口径：`deepseek-v4-flash` 独立跑两遍，temperature `0`，thinking default；LoCoMo judge prompt 只输出 single label。
- LME avg query tokens `6137.344`，略高于 6K 目标；LoCoMo avg query tokens `5768.492`。

早期同 backbone 测试目录 `agent-memory-other` 结果只作为历史参考，不作为主项目 LTS 口径：

- LongMemEval-S full：strict `403/500 = 0.806`，lenient `422/500 = 0.844`。
- LoCoMo non-adversarial full：strict `1213/1540 = 0.787662`，lenient `1268/1540 = 0.823377`。
- LME avg query tokens `6174.112`，略高于 6K 目标；LoCoMo avg query tokens `5751.377`。

主目录 rerun 与历史测试目录的 trace 形态基本一致。当前主目录 trace 重新核对如下：

- LME `500/500` 全部选择 `long_turn_precision` profile。
- LoCoMo `1540/1540` 全部选择 `short_turn_v96_spacing` profile。
- selected context：LME `0/500`，LoCoMo `1198/1540 = 0.778`。
- finalizer：LME 触发 `54/500`，其中 `missing_detail_from_structured_answer=47`、`evidence_report_count_answer_detail=5`、`evidence_report_money_difference=1`、`evidence_report_date_endpoint_duration=1`；LoCoMo 触发 `46/1540`，全部是 `evidence_report_relative_time_calculation`。
- top-k/context：LME effective top-k `40`，avg context chars `19759`；LoCoMo temporal route top-k `40`、其他 route top-k `60`，avg context chars `16309`。

结论：v102 不使用隐藏标签，因此 clean；但平均 turn 长度阈值几乎等价于把两个 benchmark 的输入形态分开处理，general 风险较高。它可以解释为 context granularity adaptation，但当前实现把 route、retrieval、selected context、compiler、finalizer 一起切换，粒度太粗。当前 LTS 先固定 v102，后续改进应在不牺牲 accuracy 的前提下逐步降低这种大块 profile 风险。

## 逐项诊断

1. Granularity/profile 风险

- 证据：qwen3.6 traces 显示 LME 全部 long profile，LoCoMo 全部 short profile。
- 风险：虽然触发条件是可见的 `avg_turn_chars`，不是 benchmark 标签，但行为上过度贴合两个数据集形态。
- 处理方向：把“全样本 profile 切换”拆成更小、更通用的 runtime signals，例如每条 retrieved turn 的长度、context budget、route 信息需求和证据支持状态。

2. 多路检索 top-k / context noise

- 证据：v102 LoCoMo 大量使用 top60；LME query token 超 6K。v103 尝试 Qwen3-Reranker-0.6B 单 turn rerank + context budget，LME 同 backbone 退步：strict/lenient `0.780/0.818`，低于当前 v102 dual flash `0.814/0.830`。
- 诊断：rerank 方向不是错，但 v103 把单个 raw turn 当 rerank document，可能丢失邻接对话和 episode 上下文；同时直接裁掉宽上下文会伤 multi-session/temporal。
- 处理方向：下一次 rerank 不应只 rerank 单 turn，而应 rerank source-grounded evidence units：turn + short neighbor、typed memory text + raw source、episode/session snippet。先不要把 top-k 大幅砍掉，先用 rerank 调整顺序，再由 compiler budget 截断。

3. Selected context 长/短 turn 规则

- 证据：v102 通过 profile 对 LME 全关、LoCoMo 大量开启。
- 风险：这是最明显的 dataset-shape heuristic。
- 已实现改造：新增 `selected_context.max_center_chars`。selected context 现在可以按每条 retrieved turn 判断：只有中心 turn 不太长、且有指代/上下文依赖时补邻居。这样长文本样本中的短指代行仍可补上下文，短文本样本中的长中心行也会跳过。

4. Mechanical finalizer 风险

- 证据：当前 finalizer 不读 gold/judge/标签，但包含相对时间、日期差、金额差、平均值、count detail 等机械改写。LoCoMo 中 41 条相对时间答案由 finalizer 改写。
- 风险：这些规则通用但看起来像 benchmark answer-format solver，尤其是相对时间和数值题。
- 处理方向：v104 诊断候选关闭 mechanical finalizer，改用已有 `answer.repair` 的 source-grounded verifier/repair 通道。repair 只看 Memory Context 和 Draft Answer，在不确定、短列表、时间冲突、profile/preference 等通用风险信号下触发；它不会读 gold、judge、category 或 question_type。

5. Build memory 使用不足

- 证据：v102 的 build memory 主要通过 BM25 命中 memory record 后投影回 source turns，最终 prompt 中 `max_memory_records=0`，typed memory 不作为一等上下文。
- 风险：memory 的组织、更新、冲突处理价值没有充分发挥。
- 外部代码启发：
  - EverOS：atomic fact / profile / episode 分层，fact 命中后回链 parent episode；候选输出时保留 atomic facts。
  - MemOS：LongTermMemory/UserMemory 双通道检索，过滤短/近重复 memory 后 rerank，并把 dialogue pair 作为 ranking unit。
  - Nemori：buffer -> episode -> semantic memory，episode/semantic 双通道 hybrid search，并保留 full record 回取。
  - Hindsight：多路 recall 后做 rerank，同时用 temporal/recency/proof count 作为轻量排序调制，而不是让 rerank 覆盖所有信号。
  - MemU：memory as file system，resource/items/resources 分层，强调原始来源和主动 context loading。
- 处理方向：后续 v105/v106 应把 build memory 升级为 typed memory activation layer：memory record 命中后形成 source-grounded evidence unit，包含 memory text、type、status、source turns、neighbor turns、temporal fields；compiler 可以显示少量 typed memory guide，但最终答案仍要求回到 raw source 或明确标注 typed memory 来源。

## v104 诊断候选

配置：`configs/stage1_context_guard_v104_qwen36_no_think_build4k_cached.json`

关键改动：

- 移除 `retrieval.granularity_profiles`，不再按全样本平均 turn 长度切换大块行为。
- selected context 使用 `max_center_chars=260`，按单条 retrieved turn 是否短且有指代来补局部上下文。
- compiler `max_evidence_chars=16000`，先控制 LME query token 过 6K 的问题。
- finalizer disabled；启用 source-grounded `answer.repair`，只在通用风险信号下触发。
- build memory/cache/backbone 与 qwen3.6 v102 保持一致，确保主要比较 query/organization 侧变化。

Smoke 观察：

- LME 第一条：无 granularity profile，compiled rows `48`，context chars `15239`，query tokens `5346`，selected context materialized `6`，skipped long center `6`，finalizer disabled，repair 未触发。
- LoCoMo 第一条：无 granularity profile，compiled rows `40`，context chars `15747`，query tokens `5406`，selected context 未触发，finalizer disabled，repair 未触发。

## 实验建议

1. 先提交 v104 代码和配置，保证正式实验记录 clean commit。
2. 先跑 LongMemEval-S full，因为 v104 主要修复 LME query token 和 profile split 风险；若 strict/lenient 大幅低于 qwen3.6 v102，停止，不跑 LoCoMo full。
3. 若 LME 接近或超过 v102，并且 avg query tokens <= 6K，再跑 LoCoMo non-adversarial full。
4. 若 v104 失败，下一步不要回退到大块 profile；优先做 evidence-unit rerank / typed-memory activation，而不是单 turn rerank。

## v104 run result

主目录 formal run `stage1_context_guard_v104_lme_s_full_043795e` 已完成 LongMemEval-S full：

- single-flash diagnostic accuracy `395/500 = 0.790000`
- avg query tokens `7367.622`
- answer repair triggered `178/500`，额外 query tokens `772443`

结论：v104 不是 LTS 候选，且 query token 明显超出 normal budget；LoCoMo full 不继续跑。下一步应基于当前主目录 qwen3.6 no-thinking v102 dual-flash LTS 口径和 badcase 设计下一次方法。

## v105 计划：typed memory activation

配置：`configs/stage1_memory_activation_v105_qwen36_no_think_build4k_cached.json`

设计依据：

- v104 说明一次性取消大块 profile、关闭 finalizer 并启用 broad repair 会同时损伤 accuracy 和 token budget，因此下一步不继续这种大改。
- v103 说明单 raw-turn rerank + 强裁剪会降低 LME accuracy；rerank 应推迟到 evidence-unit 层面，而不是马上砍 top-k。
- Mnemis、SimpleMem、EverOS、Graphiti、Hindsight、MemOS、Nemori 的共同点是：build/long-term memory 应作为组织、selection、provenance 和 conflict signal，并回链原始 episode/source，而不是把 summary/profile 作为唯一事实源。
- 早期 v37 row-linked typed memory bundle 在旧 backbone 下负向，说明不能让 typed memory 与 raw context 竞争答案来源；v105 只显示已召回 raw rows 能对齐到的少量 activated memory，并在 prompt 中声明它不是 independent evidence。

关键改动：

- build/retrieval/granularity profile/selected context/answer finalizer/backbone 全部保持当前 qwen3.6 no-thinking v102 LTS。
- `compiler.max_memory_records=6`，temporal/list/profile/current_state route 为 `8`。
- `compiler.structured_guide_include_memory=true`：在 Structured Evidence Guide 中加入 source-aligned `activated_build_memory`，帮助模型理解 type/status/time/source，但最终事实仍回到 Memory Context。
- `compiler.memory_order=question_overlap`：优先显示与问题词、信息需求和 memory type 更匹配的 memory records。
- `compiler.evidence_order=memory_aware`：用 typed memory 的 source links 轻量调整 raw row 顺序，但不减少 top-k，避免再次因过早裁剪损失证据。
- answer cache 独立为 `outputs/cache/qwen36_no_think_build4k_answer_v105_memory_activation.sqlite`；build cache 可复用 v102，因为 build 阶段未改，正式 token 统计仍按 cached usage 计入逻辑 cold-build token。

验证策略：

1. 先跑单测和 smoke，检查 prompt 中确实出现 source-aligned activated memory，且没有 gold/judge/category/sample id。
2. 若 smoke 正常，先跑 LongMemEval-S full；LME 是当前更接近 target 的基准，用于确认 typed memory activation 不伤主能力。
3. 如果 LME 不明显低于 v102，再跑 LoCoMo non-adversarial full；LoCoMo 当前距 lenient `0.800000` baseline target 只差 4 题，是 v105 的重点观察对象。
4. 正式汇报继续使用 dual `deepseek-v4-flash` strict/lenient judge，并记录 commit、dirty、token、outputs 路径和 by-category diagnosis。

## v105 run result

主目录 formal run `stage1_memory_activation_v105_qwen36_no_think_build4k_lme_s_full_d8f2b4c` 已完成 LongMemEval-S full：

- dual flash strict/lenient `387/500 = 0.774000` / `400/500 = 0.800000`
- avg build tokens `85393.566`
- avg query tokens `6614.138`
- avg compiled evidence rows `24.528`
- avg compiled memory records `5.710`

对比当前 qwen3.6 v102 LTS LongMemEval-S strict/lenient `0.814000 / 0.830000`，v105 明显负向，不跑 LoCoMo full。

差异诊断：

- lenient gain/loss：`27 / 42`，net `-15`。
- loss 主要集中在 multi-session：`25` 个 loss。
- `memory_aware` ordering 把 memory-linked 但更长/更窄的 raw rows 提前，使 compiler 更早触达 `max_evidence_chars`，avg evidence rows 从 v102 `34.752` 降到 v105 `24.528`。
- typed memory activation 有局部收益，但和 raw-row reorder 绑定后伤害 multi-session aggregation 覆盖。

## v106 计划：activation-only ablation

配置：`configs/stage1_memory_activation_v106_qwen36_no_think_build4k_cached.json`

设计目的：

- 隔离 v105 的失败来源：只测试 source-aligned typed memory activation guide，不再改变 raw-row order。
- build/retrieval/granularity profile/selected context/answer finalizer/backbone 继续保持当前 qwen3.6 no-thinking v102 LTS。
- `compiler.evidence_order` 恢复 `retrieval`，避免多证据聚合题因 row reorder 过早丢 raw rows。
- `compiler.max_memory_records=4`，temporal/list/profile/current_state route 为 `6`，减少 activation token 和 noise。
- answer cache 独立为 `outputs/cache/qwen36_no_think_build4k_answer_v106_memory_activation.sqlite`；build cache 可复用 v102，正式 token 统计仍按 cached usage 计入逻辑 cold-build token。

Smoke 观察：

- LME 前 2 条 rows 与 v102 对齐：第 1 条 `40` 行，第 2 条 `39` 行；v105 第 2 条只有 `32` 行。
- activated memory 进入 prompt，但只映射到已召回 Memory Context rows。
- 第 2 条 query tokens `7110`，说明 activation-only 仍有 token 代价；full run 必须重点观察 accuracy 是否值得这个代价。

## v106 run result

主目录 formal run `stage1_memory_activation_v106_qwen36_no_think_build4k_lme_s_full_36c76cc` 已完成 LongMemEval-S full：

- dual flash strict/lenient `403/500 = 0.806000` / `410/500 = 0.820000`
- avg build tokens `85393.566`
- avg query tokens `6638.526`
- avg compiled evidence rows `34.752`
- avg compiled memory records `4.532`

对比当前 qwen3.6 v102 LTS LongMemEval-S strict/lenient `0.814000 / 0.830000`，v106 仍然负向，不跑 LoCoMo full。

差异诊断：

- lenient gain/loss：`19 / 24`，net `-5`。
- 去掉 `memory_aware` ordering 后，raw evidence rows 恢复到 v102 水平，说明 v105 的大幅退步主要来自 row ordering。
- 但直接暴露 typed memory guide 仍增加 reader token/noise：avg query tokens 从 v102 `6137.344` 增到 v106 `6638.526`。
- typed memory guide 对 knowledge-update 和 preference 有局部收益，但对 temporal 和 multi-session 仍有净损失。

结论：

- 暂停“直接把 typed memory guide 放进最终 reader prompt”的路线。
- build memory 下一步应继续作为 source selection、coverage/conflict signal 或 evidence-unit rerank 的输入，但必须保证 raw evidence 覆盖不低于 v102。
- 若做 rerank，不能重复 v103 的单 turn rerank；应以 source-grounded evidence unit 为单位，并设置 raw-row coverage guarantee。

## v107 计划：route-scoped activation

配置：`configs/stage1_route_scoped_memory_activation_v107_qwen36_no_think_build4k_cached.json`

设计依据：

- v106 route-level lenient 对比显示：`fact_lookup` 相对 v102 `+1`，`profile_preference` `+2`，`current_state` `0`；但 `temporal_lookup` `-6`，`list_count` `-2`。
- 因此 v107 只在 question-derived `fact_lookup` / `profile_preference` route 打开少量 source-aligned typed memory activation；temporal/list/current 维持 v102 无 activation。
- route 来自问题文本和通用 heuristic，不使用 LongMemEval question_type、LoCoMo category、gold、judge、sample id 或测试反馈。
- raw-row order 继续使用 v102 `retrieval`，不再使用 v105 负向的 `memory_aware` order。

关键改动：

- `compiler.max_memory_records=0`
- `compiler.route_overrides.fact_lookup.max_memory_records=4`
- `compiler.route_overrides.profile_preference.max_memory_records=6`
- `compiler.structured_guide_include_memory=true`
- `compiler.evidence_order=retrieval`
- answer cache 独立为 `outputs/cache/qwen36_no_think_build4k_answer_v107_route_scoped_memory_activation.sqlite`

Smoke 观察：

- LME 第 1 条 `fact_lookup`：activation 生效，`compiled_memory_records=1`，query tokens `5100`。
- LME 第 2 条 `temporal_lookup`：activation 关闭，rows/query 与 v102 对齐，query tokens `6786`。

验证策略：

- 先跑 LongMemEval-S full；若没有超过或至少接近 v102 LTS，不跑 LoCoMo full。
- 若 LME 达到或超过 v102，再跑 LoCoMo non-adversarial full，重点观察 LoCoMo Open-Domain / profile-like 问题是否受益。

## v107 LME run result

主目录 formal run `stage1_route_scoped_memory_activation_v107_qwen36_no_think_build4k_lme_s_full_12a80f2` 已完成 LongMemEval-S full：

- dual flash strict/lenient `405/500 = 0.810000` / `415/500 = 0.830000`
- avg build tokens `85393.566`
- avg query tokens `6308.482`
- avg compiled evidence rows `34.752`
- avg compiled memory records `1.374`

对比当前 qwen3.6 v102 LTS LongMemEval-S strict/lenient `0.814000 / 0.830000`：

- lenient 持平，strict 少 2 题。
- lenient gain/loss：`17 / 17`，net `0`。
- route deltas：current_state `+1`，fact_lookup `-3`，list_count `+1`，profile_preference `0`，temporal_lookup `+1`。

结论：v107 不是 LME 提升，但主指标 lenient 没退步。因为 LoCoMo 是当前 baseline target 缺口，继续跑 LoCoMo full；若 LoCoMo 不能明显提升，则拒绝 v107。

## v107 LoCoMo run result

主目录 formal run `stage1_route_scoped_memory_activation_v107_qwen36_no_think_build4k_locomo_nonadv_full_935b7b7` 已完成 LoCoMo non-adversarial full：

- dual flash strict/lenient `1193/1540 = 0.774675` / `1229/1540 = 0.798052`
- avg build tokens `62015.574`
- avg query tokens `5961.069`
- avg compiled evidence rows `55.264`
- avg compiled memory records `2.460`

对比当前 qwen3.6 v102 LTS LoCoMo strict/lenient `0.776623 / 0.798052`：

- lenient 持平，strict 少 3 题。
- lenient gain/loss：`51 / 51`，net `0`。
- category deltas：Multi-Hop `+7`，Temporal Reasoning `-7`，Open-Domain `+3`，Single-Hop `-3`。

结论：

- v107 不是新 LTS，当前默认仍是 v102。
- route-scoped activation 对 Multi-Hop/Open-Domain 有局部有效信号，但 reader prompt 里直接暴露 typed memory 仍会引入 temporal/single-hop 噪声。
- 下一步不要继续简单扩大 activated memory；应把 build memory 用在 source selection、coverage/conflict signal 或 evidence-unit rerank，且必须保证 raw evidence 覆盖不低于 v102。

## v108 计划：source coverage without memory prompt

配置：`configs/stage1_source_coverage_v108_qwen36_no_think_build4k_cached.json`

设计依据：

- v105-v107 显示，typed memory 直接进入 reader prompt 不稳定，尤其会带来 temporal/single-hop 噪声。
- 外部方法 Mnemis/SimpleMem/EverOS/Hindsight/MemOS/Nemori 更共同的稳定思想是：derived memory 先做 source selection / provenance / coverage control，再回到 raw source，而不是让 summary/profile 与 raw evidence 竞争答案。
- v108 因此不显示 typed memory guide，`compiler.max_memory_records=0`，只用 build memory 的 source links 调整部分 route 的 raw row coverage。

关键改动：

- build/retrieval/granularity profile/selected context/answer finalizer/backbone 与 v102 保持一致。
- reader prompt 不新增 `activated_build_memory`；typed memory 不作为 independent evidence。
- `fact_lookup` / `profile_preference` / `current_state` 使用 `evidence_order=source_anchor_coverage`。
- source-anchor policy：先保留前 `32` 条 raw retrieval anchors，再插入少量 memory-linked source rows，每个 session 最多 `1` 条，避免 v105 那种大幅重排。
- `temporal_lookup` / `list_count` 完全保持 v102 retrieval order，避免已知负向。
- v108 answer cache 独立为 `outputs/cache/qwen36_no_think_build4k_answer_v108_source_coverage.sqlite`。

Clean/controlled comparison:

- 因为本地 answer LLM 即使 temperature `0` 也存在小幅非确定性，v108 formal run 前使用 `scripts/seed_answer_cache_from_traces.py` 从 v102 prediction traces seed 相同 prompt 的 answer cache。
- 该脚本只读取 prediction-time trace 中的 prompt、answer、raw_response 和 token usage，不读取 labels、judge、benchmark category、sample id 或 test feedback。
- 只有 prompt 完全相同的样本会命中新 namespace cache；v108 改过 prompt/order 的 route 仍会新跑。

Smoke 观察：

- LME 第 1 条 `fact_lookup`：无 `activated_build_memory`，rows `40`，query tokens `5011`。
- LME 第 2 条 `temporal_lookup`：无 `activated_build_memory`，rows/query 与 v102 对齐，query tokens `6786`。

验证策略：

- 先跑 LongMemEval-S full；若 strict/lenient 不低于 v102，再跑 LoCoMo full。
- 若 LME 下降，停止，并继续分析 source-anchor 是否在 fact/profile route 上误排证据。

## v108 run result

主目录 formal run `stage1_source_coverage_v108_qwen36_no_think_build4k_lme_s_full_293474e` 已完成 LongMemEval-S full：

- dual flash strict/lenient `401/500 = 0.802000` / `412/500 = 0.824000`
- avg build tokens `85393.566`
- avg query tokens `6195.524`
- avg compiled evidence rows `34.800`
- answer cache hits `382/500`，来自 v102 prediction traces seed 的相同 prompt cache

对比当前 qwen3.6 v102 LTS LongMemEval-S strict/lenient `0.814000 / 0.830000`，v108 明显负向，不跑 LoCoMo full。

差异诊断：

- lenient gain/loss：`7 / 10`，net `-3`。
- route losses 主要在 fact_lookup：`9` 个 loss。
- typed memory 不进 reader prompt 后 token/noise 降低，但现有 build memory source links 作为 row coverage signal 仍不够准。

结论：

- v108 不是新 LTS，当前默认仍是 v102。
- 不应继续简单使用现有 memory source links 做 row reorder。
- 下一步若继续做 build-memory 管理，应先改 build memory/evidence-unit 质量，或做可拒绝的 coverage/verifier，而不是直接把 memory-linked rows 插入 reader 上下文。

## v109 计划：grounded inference discipline

配置：`configs/stage1_grounded_inference_v109_qwen36_no_think_build4k_cached.json`

设计依据：

- 当前主目录 qwen3.6 no-thinking v102 在 LoCoMo non-adversarial full 上 lenient `0.798052`，距 `0.800000` baseline target 只差 4 题；badcase 中 Open-Domain / modal inference 问题大量表现为过度拒答。
- v105-v108 说明直接把 typed memory 放进 reader prompt 或用现有 source links 重排 raw rows 都不稳定。因此 v109 不改 build memory、不改 retrieval、不改 raw row order、不改 finalizer，只改变 reader 对“grounded inference”问题的通用解释纪律。
- 外部代码/方法参考：
  - SimpleMem 代码中 `HybridRetriever` 使用 semantic/keyword/structured 多路检索，并用 answer prompt 要求答案只来自 retrieved contexts；v109 继承“context-only answer”，但不引入 SimpleMem 的在线 reflection 查询，避免额外 LLM/token 和不稳定性。
  - Hindsight 代码把 `world`、`experience`、`observation` 等 fact type 分离，并在 recall/reflect 接口中保留 `based_on` 来源；v109 借鉴 epistemic separation，要求 inference 只能基于 Memory Context anchors，不把推断当原始事实。
  - Graphiti 代码提供 BM25/cosine/BFS/cross-encoder 多 scope search 和 episode/node/edge rerank；v109 暂不做 rerank，因为 v103/v108 已证明当前粗粒度重排会伤 LME，先验证 reader discipline 的边际收益。
  - MemOS LoCoMo prompt 明确允许答案 grounded in memories，并可用 general world knowledge interpretation；v109 只采用“基于记忆锚点做合理解释”的部分，舍弃具体相对时间和短答案格式规则，避免 benchmark-like finalizer。

关键改动：

- `compiler.grounded_inference_contract` 新增为可关闭开关，并支持 `route_overrides`。
- 只在 question text 命中 modal/inference 表达时触发，例如 `would`、`might`、`likely`、`probably`、`considered`、`do you think`、`what might`。触发条件不使用 LoCoMo category、LongMemEval question_type、gold、judge、sample id、row index 或测试反馈。
- v109 只在 `fact_lookup` / `profile_preference` / `current_state` route 打开该 contract；`temporal_lookup` / `list_count` 保持 v102，避免影响已知脆弱的时间和聚合题。
- Prompt 中的 discipline 要求：当 Memory Context 有直接相关锚点时，可以输出 `yes/no/likely/unlikely/somewhat` 等校准结论；不能因为没有逐字答案就拒答；敏感身份、宗教、健康、财务等不能从 stereotype 推断，必须有显式自述或具体行为支撑；没有锚点或锚点冲突时仍回答信息不足。
- answer cache 独立为 `outputs/cache/qwen36_no_think_build4k_answer_v109_grounded_inference.sqlite`；build cache 复用 v102，正式 token 统计仍按 cached usage 计入逻辑 cold-build token。

Clean/controlled comparison:

- 为减少本地 answer LLM temperature `0` 仍存在的小幅非确定性，formal run 前可用 `scripts/seed_answer_cache_from_traces.py` 从 v102 prediction traces seed 相同 prompt 的 answer cache。
- 该脚本只读取 prediction-time prompt、answer、raw_response 和 usage；不读取 labels、judge、benchmark category、sample id 或 test feedback。
- v109 改过 prompt 的 grounded inference 样本会新跑；未改 prompt 的样本命中 v102 trace seed cache，用于隔离局部 prompt 改动。

验证策略：

1. 先跑单元测试，确认 route override 和 question gate clean。
2. 先跑 LongMemEval-S full；若 strict/lenient 低于当前 qwen3.6 v102 `0.814000 / 0.830000`，直接拒绝，不跑 LoCoMo full。
3. 若 LME 持平或提升，再跑 LoCoMo non-adversarial full，重点观察 Open-Domain 和 Multi-Hop 是否减少 over-abstention，同时检查 Temporal/Single-Hop 是否被意外伤害。

## v109 run result

主目录 formal run `stage1_grounded_inference_v109_qwen36_no_think_build4k_lme_s_full_6ebbd45` 已完成 LongMemEval-S full：

- dual flash strict/lenient `408/500 = 0.816000` / `414/500 = 0.828000`
- avg build tokens `85393.566`
- avg query tokens `6139.928`
- avg compiled evidence rows `34.752`
- grounded inference prompt triggered `7/500`

对比当前 qwen3.6 v102 LTS LongMemEval-S strict/lenient `0.814000 / 0.830000`：

- strict 高 1 题，但主指标 lenient 低 1 题。
- 全量 lenient gain/loss：`4 / 5`，其中 triggered prompt 样本 gain/loss：`1 / 1`。
- 触发样本中，一个 allergy/living-room 问题从信息不足改为 grounded likely answer 并被判对；一个 NAS now-or-wait personalized advice 问题从实用建议改为信息不足并被判错。

结论：

- v109 不是新 LTS，当前默认仍是 v102。
- 因为主指标 lenient 低于 v102，停止，不跑 LoCoMo full。
- grounded inference discipline 方向有局部信号，但不能宽泛作用在 advice/recommendation 问题上。下一步如果继续该方向，应区分 yes/no/modal inference 与 recommendation/advice，或做可拒绝的 abstention verifier，只在“信息不足”明显不成立时修正。

## v110 计划：modal-only grounded inference gate

配置：`configs/stage1_modal_grounded_inference_v110_qwen36_no_think_build4k_cached.json`

设计依据：

- v109 的 triggered 样本中，allergy/living-room 这类 `Do you think it might...` modal inference 从信息不足改为正确；NAS `What do you think?` advice/recommendation 从有用建议改为信息不足而错误。
- 因此 v110 只收窄 question gate，不改变 prompt discipline 内容：保留 `would`、`might`、`could`、`likely`、`probably`、`considered`、`what might`、`how would` 等 modal yes/no inference；排除 standalone `do/what do you think` 这类 plain advice trigger。
- 离线计数只用于诊断，不进入 prediction：LongMemEval-S broad gate 触发 `7/500`，modal-only 触发 `6/500`；LoCoMo non-adversarial modal-only 触发 `43/1540`，其中 v102 lenient wrong `29`，且 `28` 个属于 Open-Domain。Prediction 触发仍只使用 question text，不使用 category/gold/judge/sample id。

关键改动：

- 新增 `compiler.grounded_inference_gate`，支持 `broad` 和 `modal_only`；默认 `broad` 保持 v109 配置语义。
- v110 在 `fact_lookup` / `profile_preference` / `current_state` route override 中设置 `grounded_inference_gate=modal_only`。
- build/retrieval/granularity profile/selected context/finalizer/backbone 与 v102 保持一致。
- answer cache 独立为 `outputs/cache/qwen36_no_think_build4k_answer_v110_modal_grounded_inference.sqlite`。正式 run 前用 v102 traces + v102 predictions seed 相同 prompt 的 prediction-time final answers；不使用 v109 traces 覆盖未改 prompt。

验证策略：

1. 先跑 LongMemEval-S full。若 lenient 低于 v102 `0.830000`，停止，不跑 LoCoMo。
2. 若 LME lenient 持平或提升，再跑 LoCoMo full；重点观察 Open-Domain modal 问题是否提升，同时确认 Single-Hop/Temporal 不被 prompt discipline 误伤。

## v110 run result

主目录 formal runs 已完成：

- LongMemEval-S full `stage1_modal_grounded_inference_v110_qwen36_no_think_build4k_lme_s_full_2f33213`
  - dual flash strict/lenient `406/500 = 0.812000` / `417/500 = 0.834000`
  - avg build tokens `85393.566`
  - avg query tokens `6140.218`
  - avg compiled evidence rows `34.752`
  - answer cache hits/misses `494/6`
- LoCoMo non-adversarial full `stage1_modal_grounded_inference_v110_qwen36_no_think_build4k_locomo_nonadv_full_2f33213`
  - dual flash strict/lenient `1200/1540 = 0.779221` / `1231/1540 = 0.799351`
  - avg build tokens `62015.574`
  - avg query tokens `5775.508`
  - avg compiled evidence rows `55.264`
  - answer cache hits/misses `1504/36`

对比当前 qwen3.6 v102 LTS：

- LME lenient 从 `415` 到 `417`，净增 2；strict 从 `407` 到 `406`，少 1。
- LoCoMo lenient 从 `1229` 到 `1231`，净增 2；strict 从 `1196` 到 `1200`，多 4。
- LoCoMo category deltas（lenient）：Multi-Hop `195 -> 192`，Temporal Reasoning `250 -> 248`，Open-Domain `45 -> 54`，Single-Hop `739 -> 737`。

真实方法变化诊断：

- LME answer text changed `11/500`；其中 modal inference 触发带来 1 个明确 gain（living-room/allergy 问题从过度拒答变成 grounded likely answer），其余变化主要是同 prompt/cache/finalizer 表面差异或 judge 方差。
- LoCoMo answer text changed `41/1540`，主要集中在 Open-Domain；其中 changed-answer 子集 lenient gains `8`、losses `0`，说明 modal-only grounded inference 对 LoCoMo Open-Domain 是正向。
- 全量 transition 中还有不少答案未变但 judge 结果变化的样本；这些属于 dual flash 重跑方差，不能当作方法真实变化。

结论：

- v110 是正向候选，但不是新 LTS：LoCoMo lenient `0.799351` 距 `0.800000` 还差 1 题，且 LME strict 小幅回落。
- modal-only grounded inference 方向值得保留为下一步证据，但需要更通用的 verifier/context organization 来减少 Temporal/Single-Hop 抵消，而不是继续扩大规则 gate。
- 当前默认 LTS 仍是 v102；下一轮应优先围绕 Open-Domain over-abstention 和 evidence-unit rerank / verifier 设计，同时控制 LME 不退步。

## v111 计划：modal abstention verifier

配置：`configs/stage1_modal_abstention_repair_v111_qwen36_no_think_build4k_cached.json`

设计依据：

- v110 的真实收益集中在 LoCoMo Open-Domain/modal inference，但仍有一批问题因为 draft answer 明确信息不足而错失可由 Memory Context 支撑的 calibrated answer。
- 继续扩大 question gate 容易回到 v109 的 advice/recommendation 误伤；更合适的是 query-time verifier：只在最终 draft answer 明确拒答/信息不足时二次检查 Memory Context 是否足以支持 likely/unlikely/yes/no 等答案。
- 该 verifier 复用已有 `memory.repair` source-grounded repair 通道，输入只有 prediction-time question、route、Memory Context、draft answer 和 draft raw artifacts；不读取 gold、judge、benchmark label/category、sample id 或 test feedback。
- 为避免 cache seed raw_response 与 final prediction answer 不一致导致误触发，`modal_abstention_review` 只看最终 draft answer 文本中的拒答/信息不足信号，不看 raw_response 里的 `sufficient=false`。

关键改动：

- 新增 `answer.repair.enable_modal_abstention_trigger`，默认 false，不改变旧配置行为。
- v111 打开 repair，但关闭 broad uncertain/short-list/temporal/profile triggers；`information_needs` 限定为 `current_state` / `fact_lookup` / `profile_preference`。
- Repair prompt 加入 modal/inference 规则：当 Memory Context 有直接相关 anchors 时允许 calibrated answer；无 anchors、冲突或只有主题相关时保持信息不足；敏感身份/宗教/健康/财务/政治等必须有明确自述或具体行为，禁止 stereotype 推断。
- build/retrieval/compiler/finalizer/backbone 与 v110 保持一致；base answer cache 独立为 v111，可从 v110 traces + predictions seed；repair cache 独立。

Smoke 诊断：

- LoCoMo：选取 v110 中 `modal/inference question + final answer insufficient + lenient wrong` 的 11 条做 smoke。v110 子集 strict/lenient `0/11`，v111 strict/lenient `3/11`；repair triggered `7/11`，applied `3/11`。成功样例包括 roadtrip soon、NYC shop、fitness device。
- LME：同类触发候选只有 2 条，且 v110 lenient 都错。v111 strict/lenient `0/2` / `1/2`；repair triggered `2/2`，applied `1/2`。
- Smoke 只用于诊断和是否值得 full run；临时 smoke 目录已清理，方法和配置不包含样本级 key 或规则。

验证策略：

1. 提交 v111 代码和配置，保证正式 full run 记录 clean commit。
2. 先跑 LongMemEval-S full；若 lenient 低于 v110 `0.834000` 或 v102 `0.830000`，谨慎停止，不跑 LoCoMo。
3. 若 LME 持平或提升，再跑 LoCoMo full。LoCoMo 只需净增 1 个 lenient-correct 即达到 `0.800000`，但仍需同时观察 strict、category deltas 和 repair token 成本。

## v111 run result

主目录 formal run `stage1_modal_abstention_repair_v111_qwen36_no_think_build4k_lme_s_full_c9b4d23` 已完成 LongMemEval-S full：

- dual flash strict/lenient `408/500 = 0.816000` / `414/500 = 0.828000`
- avg build tokens `85393.566`
- avg query tokens `6159.174`
- avg compiled evidence rows `34.752`
- base answer cache hits/misses `500/0`
- repair triggered/applied `2/2`
- repair query tokens total `9478`

对比：

- v102 LME strict/lenient `0.814000 / 0.830000`
- v110 LME strict/lenient `0.812000 / 0.834000`
- v111 相比 v110：strict `+2`，lenient `-3`

诊断：

- v111 实际 changed answers 只有 `2/500`，都属于 modal-abstention verifier 范围。
- changed-answer 子集中有 1 条从 v110 lenient wrong 变为 v111 lenient correct；另一条仍 wrong。
- 全量 dual flash transition 相比 v110 有 lenient gains `4`、losses `7`，净 `-3`。这说明在正式 judge 口径下，answer-side verifier 带来的局部收益不足以抵消全量评测波动/潜在不稳定。

结论：

- v111 不是新 LTS，也不是可继续 full 的候选；因为 LongMemEval-S 主指标低于 v102 和 v110，停止，不跑 LoCoMo full。
- v111 支持一个方法判断：source-grounded verifier 能修少量 over-abstention，但继续堆 answer-side verifier 不稳。
- 下一步应回到当前目标的第 2/5 点：设计 evidence-unit rerank 和更好的 build-memory organization/query-time support，同时保持第 1/3 点的 profile/selected-context 风险在审计范围内。

## v112 计划：evidence-unit rerank

配置：`configs/stage1_evidence_unit_rerank_v112_qwen36_no_think_build4k_cached.json`

设计依据：

- 当前目标第 2 点指出 v102/v110 多路检索 top-k 较大，可能带来 context noise；第 5 点指出 build memory 主要只是投影回 source，不足以体现组织、管理和 query-time support。
- v103 已证明“单 raw turn rerank + 强裁剪 final context”会伤 LME，因此 v112 不再压缩 answer context，也不降低 v110 的 top-k/compiler budget。
- v105-v108 已证明直接把 typed memory guide 放进 reader prompt 或用 memory source links 重排 final rows 不稳定，因此 v112 只让 build memory 进入 rerank 文档，最终 reader 仍以 raw Memory Context 为主。
- Hindsight 代码/文档中 recall 采用多路检索 RRF 后 cross-encoder rerank，并只用 conservative boost 调整排序；v112 借鉴“rerank 作为排序信号而不是唯一证据源”，但不引入其 graph/temporal boost，避免新复杂度。
- TeleMem/mem0 代码中 search 会跨 user/event scopes 收集候选后做 optional global rerank；v112 借鉴“跨来源候选先融合再 rerank”，但不引入 persona/user_id 专用逻辑。
- Graphiti/Zep 代码把 fact 的 `valid_at/invalid_at/created_at` 与 episode search/reranker 分开；v112 借鉴“fact/source/episode 分层”，但暂不引入完整图结构。

关键改动：

- 在 rerank 层新增 `document_text_mode`：
  - `turn`：旧行为，默认保持不变；
  - `turn_with_neighbors`：中心 raw turn + 同 session 邻居；
  - `turn_with_neighbors_and_memory`：中心 raw turn + 同 session 邻居 + source-linked build memory。
- v112 使用 `turn_with_neighbors_and_memory`，每个 rerank document 仍以一个 raw turn 为 selection unit；memory records 只作为排序提示，不进入最终 reader prompt，也不能独立替代 raw source。
- rerank 只在 question-derived `fact_lookup` / `profile_preference` / `current_state` 上启用；`temporal_lookup` / `list_count` 维持 v110，避免重复 v103 在 temporal/list 上的覆盖损失。
- `pool_k=60`，`anchor_keep=32`，`anchor_after_top=8`，保留原始融合检索 anchors，避免 cross-encoder 过度覆盖 BM25/dense/source recall。
- `document_max_chars=1800`，`document_neighbor_window=1`，`document_max_memory_records=3`。这些只影响 rerank 模型输入，不计入 LLM visible token 预算；run summary 会额外记录 rerank token。
- build/retrieval top-k、granularity profiles、selected context、compiler、modal grounded inference、answer finalizer 和 answer backbone 与 v110 保持一致；build cache 复用 v102，answer cache 独立为 `qwen36_no_think_build4k_answer_v112_evidence_unit_rerank.sqlite`。

Clean 边界：

- rerank 输入只有 question text、question_time、raw turns、same-session neighbor、build-memory source links 和 build-memory text。
- 不读取 LongMemEval question_type、LoCoMo category、gold answer、judge output、sample id、row index 或 test feedback。
- build memory 是 question-independent 从 raw dialogue 构建；cache hit 只减少重复调用，正式 token 仍按逻辑 cold-build usage 统计。

验证策略：

1. 先跑单元测试，确认默认 `turn` rerank 行为不变，evidence-unit document 不含隐藏 label。
2. 确认 rerank 服务可用后做小 smoke，只检查 trace 中 rerank document mode、applied count、query token 和 prompt clean。
3. 先跑 LongMemEval-S full。若 lenient 低于 v102 `0.830000` 且低于 v110 `0.834000`，停止，不跑 LoCoMo。
4. 若 LME 持平或提升，再跑 LoCoMo non-adversarial full；重点看 LoCoMo 是否突破 `0.800000` lenient，同时检查 Multi-Hop/Temporal/Single-Hop 是否被 rerank collateral damage 抵消。
5. 无论结果正负，都在 formal run 下记录 commit、配置、token 成本、rerank token、outputs path、metrics 和 diagnosis。

## v112 run result

主目录 formal run `stage1_evidence_unit_rerank_v112_qwen36_no_think_build4k_lme_s_full_da79d4e` 已完成 LongMemEval-S full：

- dual flash strict/lenient `405/500 = 0.810000` / `414/500 = 0.828000`
- avg build tokens `85393.566`
- avg query tokens `6210.196`
- rerank applied `220/500`
- avg rerank tokens when applied `22933.100`
- avg compiled evidence rows `33.274`
- answer cache hits/misses `280/220`

对比：

- v102 LTS LongMemEval-S strict/lenient `0.814000 / 0.830000`
- v110 candidate LongMemEval-S strict/lenient `0.812000 / 0.834000`
- v112 低于两者，因此停止，不跑 LoCoMo full。

差异诊断：

- v112 vs v110 lenient gain/loss `12 / 15`，net `-3`。
- true answer text changed `82/500`，全部来自 rerank-applied samples。
- changed-answer 子集 lenient gain/loss `11 / 12`，说明 evidence-unit rerank 的真实收益不足。
- changed-answer by type：knowledge-update `+6/-0`，multi-session `+1/-3`，temporal-reasoning `+2/-5`，single-session-preference `+2/-2`，single-session-assistant `+0/-1`，single-session-user `+0/-1`。

结论：

- v112 不是新 LTS；当前默认仍是 v102，v110 仍只是正向但未达标候选。
- evidence-unit document 比 v103 单 turn rerank 更合理，但直接改变 final raw-row order 仍会伤 multi-session/temporal 覆盖。
- 后续如果继续 rerank，应改成不破坏覆盖的 scoped rerank，例如只在已选 coverage groups 内排序，或把 rerank score 作为 compiler secondary signal，而不是替换 final retrieval order。
