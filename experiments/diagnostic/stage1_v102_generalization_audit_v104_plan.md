# v102 generalization audit and v104 plan

## 目的

本诊断对应当前目标的五个问题：检查 v102 是否存在 design-for-benchmark 风险，尤其是 granularity/profile、selected context、mechanical finalizer、top-k/context noise，以及 build memory 只作为 retrieval index 的局限。

本文件只记录 prediction-time 可见信息、正式实验 trace 和外部方法代码调研结论；不使用 gold answer、judge output、benchmark 标签、sample id 或样本级规则来设计预测逻辑。

## v102 风险基线证据

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

结论：v102 不使用隐藏标签，因此 clean；但平均 turn 长度阈值几乎等价于把两个 benchmark 的输入形态分开处理，general 风险较高。它可以解释为 context granularity adaptation，但当前实现把 route、retrieval、selected context、compiler、finalizer 一起切换，粒度太粗。后续 v104-v116 的探索都以降低这种大块 profile 风险、同时保持 accuracy 为目标。

## 当前 v116 结果

主目录 qwen3.6 no-thinking v116 formal/compatibility 结果：

- LongMemEval-S full：strict `406/500 = 0.812000`，lenient `417/500 = 0.834000`；predictions 与 v110 完全一致，继承 v110 dual flash judge。
- LoCoMo non-adversarial full：strict `1200/1540 = 0.779221`，lenient `1243/1540 = 0.807143`。
- LoCoMo 相比 v110：strict `+0`，lenient `+12`；相比 v102：strict `+4`，lenient `+14`。
- Token：LME avg query `6140.218`，略高于 6K normal target；LoCoMo avg query `5956.221`，在 6K 内。
- selected context：LME `0/500`，LoCoMo `1198/1540 = 0.777922`。
- finalizer：LME `8/500`，LoCoMo `0/1540`；LoCoMo 收益不来自 mechanical finalizer。

结论：v116 是当前默认 LTS，两个 benchmark 使用同一算法并达到 baseline target。它缓解了 selected-context 邻域不足和 LoCoMo baseline 缺口，但没有根治 granularity/profile 大块切换、LME query token 略高、多路 top-k/context noise，以及 build memory 主要作为 retrieval index 的问题。下一轮探索仍应围绕当前目标的五个问题继续推进。

## 逐项诊断

1. Granularity/profile 风险

- 证据：qwen3.6 traces 显示 LME 全部 long profile，LoCoMo 全部 short profile。
- 风险：虽然触发条件是可见的 `avg_turn_chars`，不是 benchmark 标签，但行为上过度贴合两个数据集形态。
- 处理方向：把“全样本 profile 切换”拆成更小、更通用的 runtime signals，例如每条 retrieved turn 的长度、context budget、route 信息需求和证据支持状态。

2. 多路检索 top-k / context noise

- 证据：v102 LoCoMo 大量使用 top60；LME query token 超 6K。v103 尝试 Qwen3-Reranker-0.6B 单 turn rerank + context budget，LME 同 backbone 退步：strict/lenient `0.780/0.818`，低于当前 v102 dual flash `0.814/0.830`。
- 诊断：rerank 方向不是错，但 v103 把单个 raw turn 当 rerank document，可能丢失邻接对话和 episode 上下文；同时直接裁掉宽上下文会伤 multi-session/temporal。
- 处理方向：下一次 rerank 不应只 rerank 单 turn，而应 rerank source-grounded evidence units：turn + short neighbor、typed memory text + raw source、episode/session snippet。先不要把 top-k 大幅砍掉，先用 rerank 调整顺序，再由 compiler budget 截断。
- v129 route-scoped context budget 诊断：继承 v127，不改 retrieval top-k，只对 `fact_lookup` / `profile_preference` / `current_state` 设置 compiler route budget `max_evidence_chars=17000`，不碰 `temporal_lookup` / `list_count`。LME changed prompts `118/500`，full route-only lexical exact/F1/BLEU1 `0.428000/0.633744/0.589603 -> 0.430000/0.636173/0.592207`；LoCoMo changed prompts `581/1540`，full route-only `0.244156/0.537674/0.483784 -> 0.245455/0.538048/0.483962`。但 token 收益有限：LME full avg context chars 只从 `19769.610` 降到 `19390.896`，LoCoMo 从 `17400.642` 降到 `17113.901`，LoCoMo changed subset avg query 仍为 `6112.337`。结论：固定 route char budget 是 clean 的窄正向诊断，但没有解决 top-k/context noise；下一步应做 evidence-density policy 或 rerank-assisted tail pruning，保留高支撑 raw rows、裁掉低边际 tail。
- v130-v132 fact tail pruning 诊断：v130/v131 证明 `memory_source_interleave` 即使收窄到 fact route，也会产生大面积 order-only prompt drift；v132 新增 `memory_tail_filter_preserve_order`，只保留 LoCoMo fact 的前 40 retrieval anchors 并加入最多 1 条 memory-linked tail raw row，按原 retrieval order 输出。v132 显著降成本：LoCoMo fact avg query `5115.770`，fact context chars `17637.0 -> 14678.1`，rows `55.85 -> 41.00`；但准确率负向，changed subset exact/F1/BLEU1 `0.249433/0.550951/0.488438 -> 0.241497/0.536504/0.476871`，exact gain/loss `14/21`。结论：hard row-count pruning 不适合 `fact_lookup`，后续应保留事实覆盖，用更软的 row-text compression、low-support long-row truncation 或 rerank/memory 作为预算分配信号。

3. Selected context 长/短 turn 规则

- 证据：v102 通过 profile 对 LME 全关、LoCoMo 大量开启。
- 风险：这是最明显的 dataset-shape heuristic。
- 已实现改造：新增 `selected_context.max_center_chars`。selected context 现在可以按每条 retrieved turn 判断：只有中心 turn 不太长、且有指代/上下文依赖时补邻居。这样长文本样本中的短指代行仍可补上下文，短文本样本中的长中心行也会跳过。
- v122 dry-run：继承 v121，只移除 long-turn profile 的 `selected_context.enabled=false`。LME full 编译诊断显示 selected_context 会应用到 `317/500`，avg context chars `+528.594`，avg evidence rows `-2.738`，changed evidence row count `308/500`。结论是不跑 full answer：直接把 short-turn selected context 搬到 long-turn 场景会大范围改变 prompt 并压缩 raw evidence 覆盖。后续应把 profile 改成更通用的 token-budget / evidence-density policy，而不是扩大邻域窗口。
- v124 dry-run：继承 v121，在 short-turn policy 中加入 `temporal_lookup` 并把 `max_rows` 提到 `10`。LoCoMo full 编译诊断显示 changed `1536/1540`，selected_context applied `1536` vs v116 `1198`，avg context chars `+2101.65`，avg evidence rows `-5.008`。结论是不跑 full answer：全局 local evidence unit 太宽，会影响 fact/list/profile 并压缩 raw rows；下一步改为 `temporal_lookup` route-scoped 小窗口。
- v125 dry-run/answer/judge 诊断：新增 `retrieval.selected_context.route_overrides.temporal_lookup`，只在 temporal route 加小窗口 local evidence unit。LoCoMo full dry-run 显示只改变 temporal prompt `338/338`，非 temporal route prompt 全部不变，evidence row ids `0/1540` 改变；temporal avg context chars `+1688.524`。temporal paired dual judge strict/lenient 从 v116 `0.772189/0.786982` 到 v125 `0.792899/0.813609`，净 strict `+7`、lenient `+9`。full route-only strict/lenient 从 v116 LTS `0.779221/0.807143` 到 v125 `0.789610/0.807792`，strict 正向但 lenient 仅 `+1/1540`。结论：保留为 promising diagnostic，需 LME compatibility 和 badcase 分析，不能直接升 LTS。
- v128 dry-run/answer 诊断：继承 v127，只在 `long_turn_precision` profile 的 `profile_preference/current_state` 路由启用已有 per-row selected-context policy，用 route + anaphora/center-length 替代全 profile disable。LME 只改变 `37/500` prompts，fact/list/temporal 不变；LoCoMo changed prompt/rows/context 为 `0/1540`。LME changed-prompt answer 诊断 exact 持平 `0.351351`，F1/BLEU1 小幅上升，但 avg query tokens `6480.730` 超 6K normal target；full route-only exact 也持平 `0.428000`。结论：这是 clean 的结构证据，说明可以把 v122 的宽影响收窄，但没有 accuracy gain，不升级、不优先 judge。

4. Mechanical finalizer 风险

- 证据：v102 finalizer 不读 gold/judge/标签，但包含相对时间、日期差、金额差、平均值、count detail 等机械改写。v102 finalizer-impact 诊断显示 LME 触发 `54` 条、LoCoMo 触发 `46` 条；LoCoMo relative-time finalizer 在触发子集上从 draft lenient `40/46` 降到 final `34/46`。
- v116 现状：LME finalizer 只触发 `8/500`，LoCoMo `0/1540`；这 8 条全部是 `missing_detail_from_structured_answer`，不是算术或相对时间改写。对这 8 条做 draft-only 双 flash：draft strict/lenient `1/8 / 1/8`，v116 final subset `1/8 / 2/8`，说明 missing-detail 有极小正收益，但 broad mechanical finalizer 的其它规则没有当前 LTS 收益证据。
- 风险：相对时间、日期差、金额差、平均值、count detail 这类规则虽然不作弊，但容易像 benchmark answer-format solver；保留它们会增加 general 解释成本。
- 已实现收敛：v121 新增 `source_grounded_consistency_guard` mode。该 mode 不做 count/date/money/relative-time 机械算答案，只允许在 answer model 自己结构化输出 `sufficient=false` 且给出 `missing` 字段时，把短拒答扩写成 source-grounded 缺失说明。v121 在 v116 LME finalizer-applied 8 条 smoke 上输出与 v116 完全一致，只把 trace reason 改为 `source_grounded_missing_detail`。

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
- v126 trace audit：v116 traces 显示 build memory 已广泛参与 source projection，而不是完全闲置。LME `489/500` 有 memory hits、`486/500` 有 memory-projected source 进入最终 rows；LoCoMo `1539/1540` 有 memory hits 且有 memory-projected source 进入最终 rows。LoCoMo 平均 memory hits `19.858`、memory source hits `25.938`、最终 rows 中 memory source ids `11.582`。结论：build memory 的下一步不是继续给 reader 加 hint，而是做 source-backed coverage/conflict/entity/temporal organization，仍让最终答案回到 raw Memory Context rows。
- v126 profile/current diagnostic：新增 `memory_source_interleave` raw-row ordering，先保留 retrieval anchors，再按原 retrieval order 提前少量 build-memory-linked raw rows，不把 typed memory 文本暴露给 reader。最初 broad version 影响 LoCoMo `929/1540` prompts，过宽；最终配置只作用于 `profile_preference/current_state`。LoCoMo dry-run 只改 `50/1540` prompts，LME 只改 `12/500` prompts。LoCoMo profile/current lexical exact/F1/BLEU1 从 v125 subset `0.320000/0.526452/0.472298` 到 v126 `0.360000/0.577031/0.522415`；LoCoMo full route-only lexical 也小幅正向。LME full route-only exact 持平 `0.426000`，F1/BLEU1 从 `0.631668/0.587792` 降到 `0.630589/0.586597`。结论：保留为窄范围待 judge candidate，不能升级 LTS；若 dual judge 不正向应停止。
- v127 superseded source-chain diagnostic：继承 v126，只允许 profile/current route 的 memory BM25 召回 superseded build-memory records，从而把 older/newer state chains 投影回 raw source rows。LME 只改 `5/500` prompts，full route-only lexical exact `0.426000 -> 0.428000`；LoCoMo 只改 `24/1540` prompts，full exact 持平但 F1/BLEU1 小幅上升。结论：保留为 narrow positive diagnostic candidate，仍需 dual flash judge，不能升级 LTS。

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

- build/retrieval/granularity profile/selected context/answer finalizer/backbone 全部保持当时的 qwen3.6 no-thinking v102 LTS。
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

对比当时的 qwen3.6 v102 LTS LongMemEval-S strict/lenient `0.814000 / 0.830000`，v105 明显负向，不跑 LoCoMo full。

差异诊断：

- lenient gain/loss：`27 / 42`，net `-15`。
- loss 主要集中在 multi-session：`25` 个 loss。
- `memory_aware` ordering 把 memory-linked 但更长/更窄的 raw rows 提前，使 compiler 更早触达 `max_evidence_chars`，avg evidence rows 从 v102 `34.752` 降到 v105 `24.528`。
- typed memory activation 有局部收益，但和 raw-row reorder 绑定后伤害 multi-session aggregation 覆盖。

## v106 计划：activation-only ablation

配置：`configs/stage1_memory_activation_v106_qwen36_no_think_build4k_cached.json`

设计目的：

- 隔离 v105 的失败来源：只测试 source-aligned typed memory activation guide，不再改变 raw-row order。
- build/retrieval/granularity profile/selected context/answer finalizer/backbone 继续保持当时的 qwen3.6 no-thinking v102 LTS。
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

对比当时的 qwen3.6 v102 LTS LongMemEval-S strict/lenient `0.814000 / 0.830000`，v106 仍然负向，不跑 LoCoMo full。

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

对比当时的 qwen3.6 v102 LTS LongMemEval-S strict/lenient `0.814000 / 0.830000`：

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

对比当时的 qwen3.6 v102 LTS LoCoMo strict/lenient `0.776623 / 0.798052`：

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

对比当时的 qwen3.6 v102 LTS LongMemEval-S strict/lenient `0.814000 / 0.830000`，v108 明显负向，不跑 LoCoMo full。

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

对比当时的 qwen3.6 v102 LTS LongMemEval-S strict/lenient `0.814000 / 0.830000`：

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

对比当时的 qwen3.6 v102 LTS：

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
- 当时默认 LTS 仍是 v102；后续 v116 已继承 v110 并补齐 LoCoMo baseline target。继续探索应优先围绕 Open-Domain over-abstention、evidence-unit planning / verifier 和 build-memory organization，同时控制 LME 不退步。

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

## v113 计划：移除 relative-time mechanical finalizer

配置：`configs/stage1_no_relative_time_finalizer_v113_qwen36_no_think_build4k_cached.json`

设计依据：

- 当前目标第 4 点指出 mechanical finalizer 可能像 design-for-benchmark。v102 finalizer-impact 离线诊断显示，风险最高的 `evidence_report_relative_time_calculation` 在 LoCoMo 触发样本上是净负：draft dual-flash lenient `40/46`，finalizer 后 `34/46`。
- LoCoMo judge prompt 已经允许等价 relative-time answer；把 relative phrase 强行改成绝对日期不仅不必要，还会在 event time / mention time 判断不稳时引入错误。
- LongMemEval-S 的 long-turn profile 原本已关闭 relative-time calculation，因此 v113 对 LME 预测 prompt 和 base answer 不应产生变化；只会影响短-turn/LoCoMo 类输入中的 finalizer。
- LME 中其它 non-relative finalizer 触发样本仍有净正收益：draft `22/54`，final `27/54`。因此 v113 不全关 finalizer，只移除当前最不 general 且净负的 relative-time mechanical rule。
- 外部方法参考：Hindsight 强调 temporal search 以 source window 和 relevance 为主，不要求在 answer 后做机械日期改写；SimpleMem/LightMem 更倾向让 answer/verifier 判断 context sufficiency，而不是用固定 answer-format solver。v113 先做低风险消融，后续再设计更通用的 source-grounded verifier 替代剩余 mechanical finalizer。

关键改动：

- 继承 v110 modal-only grounded inference。
- `answer.finalizer.enable_relative_time_calculation=false`。
- build/retrieval/granularity profiles/selected context/compiler/answer backbone 全部保持 v110。
- 使用独立 answer cache：`outputs/cache/qwen36_no_think_build4k_answer_v113_no_relative_time_finalizer.sqlite`。

Clean 边界：

- 预测阶段只使用 question text、question_time、raw Memory Context、build memory 和 v110 的通用 prompt discipline。
- 关闭 relative-time finalizer 的依据来自离线诊断，但规则本身是全局配置开关，不包含 gold answer、judge output、benchmark category、sample id、row index、test feedback 或样本级规则。

验证策略：

1. 先用 v110 prediction traces seed 相同 prompt 的 base answer cache；该操作只读 prediction-time prompt/answer/raw_response/usage，不读 labels 或 judge。
2. 先跑 LongMemEval-S full，预期与 v110 基本一致；若 LME lenient 不低于 v102 `0.830000`，继续跑 LoCoMo。
3. LoCoMo 重点观察 relative-time finalizer 不再触发后是否突破 `0.800000` lenient，同时记录 strict、category delta 和 token 成本。

## v113 run result

正式预测和诊断已完成：

- LME full run `stage1_no_relative_time_finalizer_v113_qwen36_no_think_build4k_lme_s_full_570ddfc`
  - dual flash strict/lenient `409/500 = 0.818000` / `414/500 = 0.828000`
  - avg build/query tokens `85393.566 / 6140.218`
  - answer cache hits/misses `500/0`
  - answer text changed vs v110 `0/500`
  - finalizer applied `8/500`，relative-time finalizer `0`
- LoCoMo prediction run `stage1_no_relative_time_finalizer_v113_qwen36_no_think_build4k_locomo_nonadv_full_570ddfc`
  - avg build/query tokens `62015.574 / 5775.508`
  - answer cache hits/misses `1540/0`
  - answer text changed vs v110 `0/1540`
  - finalizer applied `0/1540`
  - 因 predictions 与 v110 完全一致，未重跑 LoCoMo judge；继续 judge 只会测量 dual flash 方差，不会证明方法变化。

结论：

- v113 拒绝为 no-op。v102 finalizer-impact 诊断说明 relative-time mechanical rule 有风险，但该规则在 v110 路径上已经没有实际触发，因此关闭它不能提升当前正向候选。
- 后续第 4 点不能只关 finalizer 开关，应设计真正的 source-grounded verifier / consistency guardrail；同时第 2/5 点需要继续围绕 evidence sufficiency、coverage-preserving rerank 或 typed memory 作为校验信号，而不是直接重排 final raw rows。

## v114/v115 诊断：替换式 scoped evidence 与 short-list verifier

当前 badcase 复查显示，v110 LoCoMo 的错误主要集中在 `fact_lookup`、`list_count` 和 `temporal_lookup`；其中一批错误的 gold evidence source 已经在 Memory Context 或相邻 turn 附近，但 answer 阶段没有稳定使用。为避免盲目扩大 top-k，先做了两个小诊断：

- v114：对 `list_count` 直接启用 scoped evidence 两阶段抽取/回答。
  - 结果：3 条 smoke 中，模型能抽取 item，但把 `what/where` list 问题回答成数量；修正 prompt 后仍出现过度枚举和漏地点。
  - 成本：smoke avg query tokens 约 `12K`，明显不适合直接 full。
  - 结论：替换式 scoped answer 风险高，先不保留配置，不跑 full。
- v115：改为 short-list consistency guardrail，只在 `list_count` 且 draft 明显短列表时调用 source-grounded repair，默认 keep。
  - 触发估算：修正 trigger 后 LME `0/500`，LoCoMo `21/1540`。
  - 结果：5 条 smoke 中触发 3 条，只修改 1 条，且修改为不够 source-grounded 的 “plus unspecified books”；关键漏项多数没有补上。
  - 结论：answer-side verifier 不是当前最强方向；问题更像 selected context 没把邻近 turn 的完整答案带入，而不是 verifier 不会判断。

这两个诊断均只使用 prediction-time trace、question、draft answer 和 Memory Context；gold/judge 只用于离线分析，不进入预测逻辑。相关临时配置和 smoke 目录已清理，避免污染主目录。

## v116 计划：extended selected context

配置：`configs/stage1_extended_selected_context_v116_qwen36_no_think_build4k_cached.json`

设计依据：

- 当前目标第 3 点指出 selected context 按长/短 turn 处理可能不够 general。v104 一次性移除大块 profile 并启用 broad repair 已失败，因此 v116 不再做大改。
- LoCoMo v110 错例中，gold source 未覆盖的 wrong 样本里，有 `45` 个在已选 source 的 `±1` 邻域内、另有 `23` 个在 `±2` 邻域内；这说明部分错误不是 top-k 大小，而是短 turn 对话邻域不完整。
- 典型模式是：retrieval 命中一个 anchor turn，下一轮提出澄清问题，再下一轮才给出答案。v110 `window_after=1` 只能看到澄清问题，看不到答案 turn。
- 该机制是通用对话结构，不依赖 LongMemEval/LoCoMo 标签、category、gold、judge、sample id 或 row index。

关键改动：

- 继承 v110 build/retrieval top-k/granularity profile/compiler/modal grounded inference/finalizer/backbone。
- 全局 short-turn selected context：
  - `window_before=1`
  - `window_after=2`
  - `max_neighbor_chars=180`
  - `max_center_chars=320`
  - `max_rows=6`
- long-turn profile 仍保持 `selected_context.enabled=false`，因此 LME 预期基本不变；LoCoMo 是主要验证对象。
- answer cache 独立为 `outputs/cache/qwen36_no_think_build4k_answer_v116_extended_selected_context.sqlite`。

Smoke：

- run：`diagnostic/stage1_extended_selected_context_v116_locomo_neighbor_smoke`
- 6 个刻意挑选的 LoCoMo 邻域错例中，dual flash strict/lenient `1/6`。
- 明确修正：`What are the new shoes that Melanie got used for?` 从拒答改为 `running`，dual flash 判对。
- 未修正/风险：有一条从拒答改为不够具体的 `an abstract painting`，说明扩展邻域能补证据，但仍可能带入不够精确的上下文。
- smoke avg query tokens `5594.833`，没有显示过预算风险。

验证策略：

1. 提交 v116 代码/config/诊断记录，保证 formal run 有 clean commit。
2. 先跑 LoCoMo non-adversarial full，因为 v116 主要影响短 turn selected context；记录 dual flash strict/lenient、avg query/build tokens、selected_context applied、answer changed vs v110。
3. 如果 LoCoMo lenient 提升且不过 8K hard budget，再确认 LME prediction 与 v110 是否 answer text changed；若 LME 没变化，可记录 compatibility；若变化，再跑 LME full judge。
4. 若 LoCoMo full 负向，v116 拒绝；下一步应考虑更细的 per-turn adjacency trigger，而不是继续扩大 window。

## v116 run result

正式结果入口：

- LME: `experiments/formal/stage1_extended_selected_context_v116_qwen36_no_think_build4k_lme_s_full_aeac792/`
- LoCoMo: `experiments/formal/stage1_extended_selected_context_v116_qwen36_no_think_build4k_locomo_nonadv_full_aeac792/`

结果：

- LME strict/lenient `0.812000 / 0.834000`，answer text changed vs v110 `0/500`。
- LoCoMo strict/lenient `0.779221 / 0.807143`，answer text changed vs v110 `575/1540`，changed-answer lenient gain/loss `46/36`。
- LoCoMo by-category lenient delta vs v110：Multi-Hop `+5`，Temporal Reasoning `+0`，Open-Domain `-3`，Single-Hop `+10`。

结论：

- v116 达到 baseline target，可作为当前默认 LTS。
- selected context 后向邻域扩展有净收益，但继续扩大窗口的性价比不明确。
- 未来若要冲 minimum target，应重点做 build-memory organization / query-time evidence planning / source-grounded consistency guardrail，而不是简单增加 top-k、上下文长度或样本级 answer 规则。

## v117 smoke result: narrow source-grounded repair rejected

候选思路：

- 继承 v116，只打开现有 `answer.repair` 的窄触发器。
- 触发器：`uncertain_min_support_items=1` 和 `modal_abstention_review`。
- 明确关闭 `short_collection_answer` 和 `temporal_conflict`，因为离线估算显示它们会触发大量已正确样本。
- 该 repair 只读 prediction-time question、draft answer JSON 和 Memory Context，不读 gold、judge、category、sample id 或 test feedback。

触发估算：

- LoCoMo：`uncertain_min1` 触发 `75` 条，其中 wrong `62`、correct `13`；`modal_abstention` 触发 `13` 条，全部是 wrong。
- LME：`uncertain_min1` 触发 `33` 条，其中 wrong `19`、correct `14`；`modal_abstention` 触发 `2` 条，全部是 wrong。

诊断 smoke：

- LoCoMo smoke `46` 条：v116 subset strict/lenient `13/13`，v117 subset `10/12`，delta strict/lenient `-3/-1`；lenient gain/loss `3/4`。
- LME smoke `31` 条：v116 subset strict/lenient `13/14`，v117 subset `12/13`，delta strict/lenient `-1/-1`；lenient gain/loss `0/1`。
- v117 确实修复了部分 over-abstention，例如 roadtrip / favorite movie trilogy / Hollywood Bowl；但也把已经正确的答案改成更保守或错误的答案，例如 `$270` 被改成无法计算、fashion internship 被改成不确定。

结论：

- v117 不进入 full，不保留为正式配置。
- 当前 repair prompt 仍容易把可接受的近似答案改成过度保守答案，或在实体归因上引入新错误。
- 下一步不要继续堆 answer-side repair；应先做 query-time evidence planner / source manifest：把候选证据组织成可核查的事实、时间线、集合和冲突表，再让 verifier 只检查 support/coverage，而不是自由改写答案。

## v118 smoke result: prompt-side source manifest rejected

候选思路：

- 继承 v116，不改 build cache、retrieval top-k、granularity profiles、selected context、modal grounded inference、mechanical finalizer 或 answer backbone。
- 新增可选 `Candidate Evidence Map` 的 source-linked build-memory hints；build memory 只作为 raw Memory Context rows 的组织标签，不作为独立证据。
- 为控制成本，最终 v118 只在通用 `list_count` route 启用；诊断输入由 clean prediction input 通过当前 `QuestionRouter` 选出，不使用 gold、judge、category、sample id 或 row index。

外部方法借鉴与取舍：

- 借鉴 MemOS / MemU / Nemori / SimpleMem / Graphiti 的共同点：派生 memory 应保留 source backpointer，用于组织、定位、冲突和召回，而不是替代 raw evidence。
- 取舍：不引入完整 graph / memory OS，也不让 typed memory 直接进入最终答案区；只在候选 evidence map 中显示短 source hint。

诊断结果：

- LME list-count smoke5：v116 strict/lenient `5/5` / `5/5`，v118 strict/lenient `5/5` / `5/5`；answer changed `1/5`，只是 `500 copies` -> `500`；avg query tokens 相比 v116 `+553.6`。
- LoCoMo list-count smoke5：v116 strict/lenient `2/5` / `4/5`，v118 strict/lenient `2/5` / `3/5`；answer changed `4/5`，其中一条 lenient-correct 被改错；avg query tokens 相比 v116 `+625.8`。

结论：

- v118 不进入 full。source manifest 作为额外 prompt block 是 clean 的，但成本高且会干扰 LoCoMo list/count 答案。
- 下一步不要继续“给 reader 追加一块候选表”的路线；更合理的是把 evidence planning 变成更紧凑的结构化中间层或检索/排序侧信号，或者替换已有 guide 中的冗余内容，而不是叠加新 prompt。

## v119 route-all result: inline memory hint rejected

候选思路：

- 继承 v116，不改 build cache、retrieval top-k、granularity profiles、selected context、modal grounded inference、mechanical finalizer 或 answer backbone。
- 不再新增 v118 的 `Candidate Evidence Map` block，而是在已有 `Structured Evidence Guide` row 上追加极短 `memory_hint=type:value`。
- 只在通用 `list_count` information need 启用；hint 必须来自 build memory 的 `source_ids`，且只能贴到同一个 raw Memory Context row 上，因此不是独立答案证据。

工程修复：

- 在 v119 route-all 诊断中发现 Qwen3.6 偶发 malformed JSON / long reasoning loop，旧 parser 会把整段 JSON/reasoning 当答案写入 prediction。
- 已将 `json_answer` parser 改为通用格式 guard：优先合法 JSON，其次只抢救 `"answer"` 字段或明确短 `Answer:` / `I will output ...` marker；无法安全抽取时返回统一 insufficient。
- 该修复不读 gold、judge、benchmark label、sample id 或 test feedback；只处理模型输出格式失败。

诊断范围：

- LME：由 clean prediction input 经当前 `QuestionRouter` 选出的全部 `list_count` route，119/500。
- LoCoMo：由 clean prediction input 经当前 `QuestionRouter` 选出的全部 `list_count` route，270/1540。
- v116 对照为同一批 record_key 的正式 full prediction 子集。

结果：

- LME route-all：v116 strict/lenient `0.848739 / 0.873950`；v119 strict/lenient `0.823529 / 0.857143`。answer changed `22/119`，strict gain/loss `3/6`，lenient gain/loss `3/5`。
- LoCoMo route-all：v116 strict/lenient `0.677778 / 0.729630`；v119 strict/lenient `0.670370 / 0.700000`。answer changed `121/270`，strict gain/loss `11/13`，lenient gain/loss `9/17`。
- Token：LME route-all avg build/query `84898.555 / 6064.235`；LoCoMo route-all avg build/query `62924.622 / 6401.967`。这些 query tokens 来自原始 cached API usage，parser reparse 只修输出文本，不回写模型实际消耗。
- 输出路径：`outputs/diagnostic/stage1_inline_memory_hint_v119_lme_list_count_all_reparse/`；`outputs/diagnostic/stage1_inline_memory_hint_v119_locomo_list_count_all_reparse/`。

结论：

- v119 不进入 full，也不作为 LTS。
- source-linked memory hint 本身 clean，但直接塞进 reader prompt 仍会改变大量答案并带来净负；这支持 v118 的判断：build memory 不应继续以额外 reader hint 的形式暴露。
- 下一步若继续解决“build memory 不只是 retrieval index”的问题，应转向检索/排序侧或更明确的 query-time planning 中间层，例如 rerank、evidence unit selection、conflict/state planner；不要继续简单增加 reader prompt 内容。

## v120 route-all result: rerank tail filter rejected

候选思路：

- 继承 v116，不改 build cache、granularity profiles、selected context、compiler、modal grounded inference、mechanical finalizer 或 answer backbone。
- 只对通用 `list_count` information need 启用 Qwen3-Reranker-0.6B。
- 与 v112 直接重排最终 raw rows 不同，v120 使用 `selection_mode=filter_preserve_order`：先取 60-row candidate pool，保留前 32 个 hybrid-retrieval anchor，再用 rerank score 选择 tail，最终 reader context 仍按原 hybrid retrieval 顺序输出，最终保留 52 rows。
- 设计参考 SimpleMem / Graphiti / MemOS 的 multi-view retrieval + rerank 思路，但取舍为：rerank 只做低置信 tail filtering，不让 cross-encoder 覆盖原 hybrid order。

诊断范围：

- LME：由 clean prediction input 经当前 `QuestionRouter` 选出的全部 `list_count` route，119/500。
- LoCoMo：由 clean prediction input 经当前 `QuestionRouter` 选出的全部 `list_count` route，270/1540。
- v116 对照为同一批 record_key 的正式 full prediction 子集。

结果：

- LME route-all：v116 strict/lenient `0.848739 / 0.873950`；v120 strict/lenient `0.831933 / 0.848739`。answer changed `24/119`，strict gain/loss `5/7`，lenient gain/loss `4/7`。
- LoCoMo route-all：v116 strict/lenient `0.677778 / 0.729630`；v120 strict/lenient `0.662963 / 0.711111`。answer changed `117/270`，strict gain/loss `14/18`，lenient gain/loss `15/20`。
- Token：LME route-all avg build/query `84898.555 / 5976.345`，avg rerank tokens `20669.042`；LoCoMo route-all avg build/query `62924.622 / 5985.081`，avg rerank tokens `14577.867`。rerank tokens 按协议单独记录，不计入 LLM build/query token。
- 形态：LoCoMo avg query tokens 比 v116 selected subset 约 `-390`，avg context chars 约 `-1154`；但 accuracy 净负。
- 输出路径：`outputs/diagnostic/stage1_rerank_filter_v120_lme_list_count_all/`；`outputs/diagnostic/stage1_rerank_filter_v120_locomo_list_count_all/`。

结论：

- v120 不进入 full，也不作为 LTS。
- 对 list/count 来说，减少 tail 虽可降 token，但会损失覆盖，cross-encoder relevance 不足以替代 broad evidence coverage。
- 后续 rerank 不能简单用于裁剪 list/count 集合；更合理的方向是 coverage-aware organization，例如保留 broad raw evidence，再用 build memory / rerank 生成 coverage groups、dedup/merge 或 conflict/state plan，而不是减少最终可见证据。

## v122 dry-run result: per-row selected context rejected for LME

配置：`configs/stage1_per_row_selected_context_v122_qwen36_no_think_build4k_cached.json`

设计目的：

- 继承 v121，只移除 long-turn profile 的 `selected_context.enabled=false`，检查 selected context 长/短 turn 规则能否改成更 general 的 per-row policy。
- 不调用 answer LLM，只做 full LME compile dry-run，避免在高风险 prompt 大改上浪费正式评估成本。

结果：

- selected_context applied `317/500`
- changed_context `317/500`
- avg context char delta `+528.594`
- avg evidence row delta `-2.738`
- changed evidence row count `308/500`

结论：拒绝，不跑 full answer。这个改动虽然比 benchmark-level profile 更 general，但在 LME 上会大范围改变 prompt，并因为固定 evidence budget 压缩 raw evidence rows。下一步应做 token-budget / evidence-density policy，而不是把 short-turn selected context 直接搬到 long-turn 场景。

## v123 route-all result: aggregation contract rejected

配置：`configs/stage1_aggregation_contract_v123_qwen36_no_think_build4k_cached.json`

设计目的：

- 继承 v121，只对 `list_count` information need 中的问题语义触发通用 `aggregation_report_contract`。
- 不改变 build/retrieval/top-k/selected context；只让 answer model 在 evidence report 中标记 include/exclude、canonical item、count increment/operand 和 calculation。
- 该设计不使用 gold、judge、benchmark 标签、sample id 或样本级规则。

结果：

- LME list_count route-all：v116 strict/lenient `0.848739 / 0.873950`，v123 `0.815126 / 0.840336`。
- Answer changed vs v116：`20/119`。
- Strict gain/loss：`4/8`；lenient gain/loss：`1/5`。
- Token：avg build/query `84898.555 / 6144.160`；build cache hit `797`，answer cache miss/write `119/119`。

诊断：

- v123 在 temporal-reasoning group strict 有小幅收益，但 knowledge-update 和 multi-session 下降更大。
- Reader-side aggregation schema 会增加模型过度排除或过度承诺的风险，不能稳定修复 list/count。

结论：拒绝，不跑 LoCoMo。后续不要继续给最终 answer prompt 叠加更重的 aggregation 指令；更应做 evidence planning / dedup / conflict organization / build-memory management，并保持 raw evidence 覆盖。

## v124 dry-run result: broad local evidence unit rejected

配置：`configs/stage1_local_evidence_unit_v124_qwen36_no_think_build4k_cached.json`

设计目的：

- 继承 v121，只改变短 turn selected-context policy：加入 `temporal_lookup`，并把 `max_rows` 从 `6` 提到 `10`。
- 不调用 answer LLM，只做 full LoCoMo compile dry-run，用于判断更宽 local evidence unit 是否会造成不可接受的 prompt churn。
- 该设计只使用 question text、raw Memory Context、same-session visible turn order 和 prediction-time route，不使用 gold、judge、benchmark 标签、sample id 或样本级规则。

结果：

- changed `1536/1540`
- selected_context applied `1536` vs v116 `1198`
- materialized selected-context rows `15360` vs v116 `7188`
- avg context char delta `+2101.65`
- avg evidence row delta `-5.008`
- temporal_lookup route avg context char delta `+6077.1`
- fact/list/profile routes也全部改变，并且平均减少约 6 条 raw evidence row

诊断：

- v124 捕捉到了“邻接证据补全”的方向，但策略过宽。
- 它不是直接泄漏或 benchmark shortcut，仍然 clean；问题是成本和 context-noise 过高，且会压缩非 temporal 路线的 raw evidence coverage。
- 更合理的下一步是保留 v116 fact/list/profile selected context 不变，只为 `temporal_lookup` 增加小窗口 route override。

结论：拒绝，不跑 full answer。继续 v125 route-scoped local evidence unit。

## v125 diagnostic result: route-scoped temporal local evidence unit pending judge

配置：`configs/stage1_route_scoped_local_evidence_unit_v125_qwen36_no_think_build4k_cached.json`

设计目的：

- 继承 v121/v116，只新增 `retrieval.selected_context.route_overrides.temporal_lookup`。
- temporal questions 可以围绕最多 4 个短、指代性中心 row 补同 session 前后各 1 个邻居；fact/list/profile selected context 保持 v116 不变。
- 该设计只使用 question text、raw Memory Context、same-session visible turn order 和 prediction-time route，不使用 gold、judge、benchmark 标签、sample id 或样本级规则。

dry-run 结果：

- LoCoMo full null-answer compile dry-run。
- route override applied `338/338` temporal samples。
- changed prompt：temporal `338/338`；current/fact/list/profile `0`。
- changed evidence row ids：`0/1540`。
- temporal avg context char delta `+1688.524`；非 temporal route 全部 `0.0`。
- selected-context materialized rows：v116 `7188`，v125 `8540`。

answer 诊断：

- LoCoMo temporal route-all `338` 条。
- Avg build/query tokens `60931.935 / 5395.908`。
- Build cache hit/miss/write `2680/0/0`；answer cache hit/miss/write `1/337/337`。
- Answer changed vs v116 temporal subset `127/338`；finalizer applied `0`。
- Fresh paired dual flash on the same 338 temporal keys：
  - V116 strict/lenient `0.772189 / 0.786982`，`261/338` strict correct、`266/338` lenient correct。
  - V125 strict/lenient `0.792899 / 0.813609`，`268/338` strict correct、`275/338` lenient correct。
  - Paired gain/loss：strict `19/12`，lenient `19/10`，净 strict `+7`、lenient `+9`。
- 辅助 lexical exact/F1/BLEU1：v116 temporal subset `0.186391 / 0.468985 / 0.436853`，v125 `0.215976 / 0.505710 / 0.471056`；exact gain/loss `13/3`。

full cached artifact：

- 预测路径：先用 `scripts/seed_answer_cache_from_traces.py` 从 v116 prediction traces seed 相同 prompt 到 v125 answer cache；再跑 full LoCoMo v125 config。
- 输出：`outputs/diagnostic/stage1_route_scoped_local_evidence_unit_v125_locomo_nonadv_full_cached/`。
- Avg build/query tokens `62015.574 / 6058.560`；answer cache hit/miss/write `1540/0/0`。
- Full lexical exact/F1/BLEU1：v116 `0.236364 / 0.527409 / 0.474098`，v125 full cached `0.242857 / 0.535751 / 0.481794`。
- 相对 v116 changed answer `131/1540`：其中 temporal `127`；非 temporal `4` 来自同一 dirty worktree 中通用 `json_answer` parser/cache-hit repair 对旧 malformed cached answer 的修复，不是 v125 selected-context route override 本身。

route-only full merge：

- 为隔离 parser-guard confound，另建 full prediction merge artifact。
- 输入：v116 full predictions for non-temporal records + v125 temporal route-all predictions for temporal records。
- 输出：`outputs/diagnostic/stage1_route_scoped_local_evidence_unit_v125_locomo_nonadv_full_route_only_merge/predictions.jsonl`。
- Merge counts：v116/base `1202`，v125 temporal `338`，route mismatch `0`。
- 相对 v116 changed answer `127/1540`，全部是 `temporal_lookup`。
- Exact gain/loss `13/3`。
- Full lexical exact/F1/BLEU1：v116 `0.236364 / 0.527409 / 0.474098`，v125 route-only merge `0.242857 / 0.535470 / 0.481605`。
- Full route-only dual judge：v116 current LTS strict/lenient `0.779221 / 0.807143`，v125 route-only merge `0.789610 / 0.807792`；strict `+16/1540`，lenient `+1/1540`。

结论：v125 通过 scope/cost 诊断，LoCoMo temporal paired judge 明确正向，full route-only strict 正向但 lenient 只小幅 `+1/1540`。它是当前更强的 promising diagnostic candidate，但不能直接升级 LTS；下一步必须做 LME compatibility 和 temporal gain/loss badcase 分析，确认风险点减少且 target benchmarks 不退步后再跑 clean formal full。

## v133/v134 diagnostic result: fact tail text budget

配置：

- `configs/stage1_fact_tail_snippet_budget_v133_qwen36_no_think_build4k_cached.json`
- `configs/stage1_fact_tail_snippet_budget_v134_qwen36_no_think_build4k_cached.json`

设计目的：

- 继承 v129 的 `fact_lookup/profile_preference/current_state` route-scoped `max_evidence_chars=17000`。
- 修复 v132 hard row pruning 的 coverage loss：不删除 `fact_lookup` low-rank raw rows，只压缩 direct retrieval rank `>40` 的 row text。
- Tail compression 只影响最终 prompt rendering；row selection 仍按未压缩文本预算执行，避免因为压缩而额外纳入 row。
- 该设计只使用 question text、prediction-time route、retrieval rank 和 raw row text，不使用 gold、judge、benchmark 标签、sample id、row index、test feedback 或样本级规则。

dry-run 结果：

- LME：v133/v134 均 `0/500` prompt change，row set 和 avg context 完全不变。
- v133：LoCoMo fact prompt changed `207/882`，row set changed `0`，fact avg context 只降 `8.552` chars，过保守，拒绝。
- v134：LoCoMo fact prompt changed `882/882`，row set changed `0`，fact avg context `17637.014 -> 17025.604`，full avg context `17113.901 -> 16763.730`，avg evidence rows 保持 `52.860`。

answer 诊断：

- LoCoMo fact changed subset `882` 条。
- V134 avg build/query tokens `62126.289 / 5910.726`，把 changed-subset query 降到 6K 内。
- Changed-subset lexical exact/F1/BLEU1：v129 `0.249433 / 0.550951 / 0.488438`，v134 `0.253968 / 0.550460 / 0.490170`，exact gain/loss `22/18`。
- Full route-only merge：v129 exact/F1/BLEU1 `0.245455 / 0.538048 / 0.483962`，v134 `0.248052 / 0.537767 / 0.484954`，merge counts 为 v134 fact override `882`、v129 non-fact `658`。

dual judge：

- 对同 882 个 LoCoMo fact changed keys 补跑 paired dual `deepseek-v4-flash` judge。
- V129 same-key strict/lenient：`0.819728 / 0.833333`，`723/882` strict correct、`735/882` lenient correct。
- V134 same-key strict/lenient：`0.807256 / 0.824263`，`712/882` strict correct、`727/882` lenient correct。
- Paired gain/loss：strict `19/30`，lenient `23/31`，净 strict `-11`、lenient `-8`。

结论：v133 拒绝。v134 虽然把 changed-subset query 降到 6K 内，但 paired dual judge 主指标负向，因此拒绝为 LTS 候选；不继续 full route-only judge，也不测试更强的 `tail_max_row_text_chars=80`。下一步应回到 source-backed evidence organization 和 badcase 分析，而不是继续压缩事实尾部 raw text。
