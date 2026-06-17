# v102 generalization audit and v104 plan

## 目的

本诊断对应当前目标的五个问题：检查 v102 是否存在 design-for-benchmark 风险，尤其是 granularity/profile、selected context、mechanical finalizer、top-k/context noise，以及 build memory 只作为 retrieval index 的局限。

本文件只记录 prediction-time 可见信息、正式实验 trace 和外部方法代码调研结论；不使用 gold answer、judge output、benchmark 标签、sample id 或样本级规则来设计预测逻辑。

## 当前 v102 证据

同 backbone 口径使用 `agent-memory-other` 中的 qwen3.6 no-thinking v102 full 结果：

- LongMemEval-S full：strict `403/500 = 0.806`，lenient `422/500 = 0.844`。
- LoCoMo non-adversarial full：strict `1213/1540 = 0.787662`，lenient `1268/1540 = 0.823377`。
- LME avg query tokens `6174.112`，略高于 6K 目标；LoCoMo avg query tokens `5751.377`。

Trace 形态：

- LME `500/500` 全部选择 `long_turn_precision` profile。
- LoCoMo `1540/1540` 全部选择 `short_turn_v96_spacing` profile。
- selected context：LME `0/500`，LoCoMo `1198/1540 = 0.778`。
- finalizer：LME 主要是 `missing_detail_from_structured_answer=42`，LoCoMo 主要是 `evidence_report_relative_time_calculation=41`。
- top-k/context：LME effective top-k `40`，avg context chars `19759`；LoCoMo effective top-k avg `55.61`，avg context chars `16311`。

结论：v102 不使用隐藏标签，因此 clean；但平均 turn 长度阈值几乎等价于把两个 benchmark 的输入形态分开处理，general 风险较高。它可以解释为 context granularity adaptation，但当前实现把 route、retrieval、selected context、compiler、finalizer 一起切换，粒度太粗。

## 逐项诊断

1. Granularity/profile 风险

- 证据：qwen3.6 traces 显示 LME 全部 long profile，LoCoMo 全部 short profile。
- 风险：虽然触发条件是可见的 `avg_turn_chars`，不是 benchmark 标签，但行为上过度贴合两个数据集形态。
- 处理方向：把“全样本 profile 切换”拆成更小、更通用的 runtime signals，例如每条 retrieved turn 的长度、context budget、route 信息需求和证据支持状态。

2. 多路检索 top-k / context noise

- 证据：v102 LoCoMo 大量使用 top60；LME query token 超 6K。v103 尝试 Qwen3-Reranker-0.6B 单 turn rerank + context budget，LME 同 backbone 退步：strict/lenient `0.780/0.818`，低于 v102 `0.806/0.844`。
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
