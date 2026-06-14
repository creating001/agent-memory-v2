# v57 规划：Target-Completeness Checklist

## 背景

v56 build-side lossless atomic memory 在 LongMemEval-S `weak_route_87` 上失败：

- v56: `57/87 = 0.655172`
- v42 same87: `59/87 = 0.678161`
- gain/loss: `4/6`
- avg build tokens: `107052.839`，比 v42 same87 增加约 `26060.977`
- avg query tokens: `6007.575`，略超 6K

结论是：继续加宽 build extraction 会增加 records、build 成本和 source activation 噪声，但没有稳定提升 answer 使用证据的能力。下一步不沿着 v56 扩 extraction 方向继续跑。

## 错误动机

v42/v56 的 weak-route 错误里有一类通用问题：

- 问题包含多个必须目标或比较对象，但 evidence 只支持其中一个，模型仍选择已支持的一边。
- 问题要求完整 slot，例如完整地点、标题、作者、店名，但模型输出过短 head noun 或部分名字。
- evidence_report 已有“match requested slot”规则，但在 answer 阶段仍会把相关证据误当成充分证据。

这类错误不是某个 benchmark 的样本规则，而是真实 agent memory QA 中常见的 target completeness / false premise 问题。

## 方法设计

配置：`configs/stage1_target_completeness_v57_cached.json`。

底座：v42 `stage1_operation_workpad_v42_cached`。

只改 query/compiler：

- 复用已有 `compiler.final_answer_checklist = true` 开关。
- 让 `final_answer_checklist` 也作用于 `prompt_mode = external_naive`。
- checklist 增加通用 target-completeness 纪律：
  - 必须目标、比较对象、required action/entity/time scope 都要被 Memory Context 直接支持。
  - 只支持其中一个 alternative 时，不可把它当作完整答案。
  - 证据包含完整名称、标题、地点、日期、item qualifier 时，最终答案要保留足够区分信息。

保持不变：

- build memory cache namespace、prompt、records 和 manager。
- raw-turn dense + BM25 top40 retrieval。
- structured guide、evidence_report、operation workpad。
- answer model、answer max input/output `131072/16384`。

这是 query-only ablation；build cache 命中仍按 logical cold-build token 记录 v42 build 成本。

## 外部方法依据

- creating001-agent-memory：重点参考其 query 侧 `target_support_required / required_target_phrases` 和 answer detail requirements。取舍：不迁移它的 dataset loader、question_type filter、sample_id、gold/judge 逻辑，也不引入 LLM router target phrases；只采用通用 target completeness 思想。
- SimpleMem / xMemory：它们都强调 retrieval 后还要保持 memory component 与原始 source 的匹配关系；v57 把这种思想落在 answer 前的“目标约束必须被原文支持”。
- Mem0 ADD-only linking：提供了“相关不等于重复/充分”的启发；v57 只在 query 阶段要求相关证据不能替代缺失目标。

## Clean 边界

- Prediction 不读取 gold answer、judge output、benchmark label、question_type、category、sample id、qid、row index 或 test feedback。
- 新 checklist 不包含测试实体、测试答案或样本级规则。
- Route 仍来自 question text；checklist 只看 question text 和 retrieved Memory Context。
- DeepSeek judge 和 v42/v56 badcase 只用于离线设计与 gate。

## 风险

- 更强 target completeness 可能增加 over-abstain，尤其是本来可由隐含上下文回答的问题。
- checklist 会增加少量 prompt tokens；需要确认 weak-route avg query 仍不超过 6K，至少不能超过 8K hard diagnostic。
- 如果主要错误来自 retrieval miss 或 answer arithmetic，而不是 target completeness，则不会提升。

## Gate 计划

先跑 LongMemEval-S question-derived `weak_route_87` diagnostic：

- input: `outputs/diagnostic/v48_lme_weak_route_input/prediction_input.jsonl`
- benchmark/subset: `longmemeval_s / weak_route_87`
- workers: 4
- prediction 完成后跑 DeepSeek judge，并与 v42 same87、v56 same87 比较

通过 full 的最低条件：

- DeepSeek judge same87 相比 v42 有明确净收益，目标至少 `+3` correct。
- avg query tokens `<= 6000`；若略超但 accuracy 明显正向，先做 token-safe 收窄，不直接 full。
- losses 不能主要来自 over-abstain。

如果 weak-route gate 持平或负向，不跑 full，删除顶层 v57 config，只保留诊断快照。
