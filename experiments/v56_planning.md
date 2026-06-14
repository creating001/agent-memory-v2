# v56 规划：Lossless Atomic Build Memory

## 背景

当前 LongMemEval-S 最好是 v42：

- accuracy: `387/500 = 0.774`
- avg build tokens: `80346.246`
- avg query tokens: `5865.644`
- 距 `0.80` baseline target 还差 `13` 条

v42 的问题不是单纯 target session recall。LME evidence session recall 已经是 `1.0`，但 badcase 仍集中在：

- `multi-session`、`temporal_lookup`、`list_count`
- 关键字符串已经在 top rows，却被 answer 过度拒答或漏聚合
- build memory 对并列事实覆盖不稳定，例如 clothing/project/bike expense 这类 list/count 场景

最近负向结果也给出边界：

- v37：row-linked typed memory 进入 prompt，LME full 降到 `0.744`，说明派生 memory 不能直接和 raw evidence 抢事实源。
- v39：memory-aware row order，LME full 降到 `0.724`，说明 build-memory signal 不能直接重排最终 evidence rows。
- v54/v55：邻近窗口 retrieval 在 weak-route 87 上持平或负向，说明继续扩大 raw context 不是主线。

因此 v56 不再扩 answer prompt，也不改最终 row order；只改 build-stage memory 的抽取与管理质量，让 typed memory 继续只作为 source activation signal。

## 方法设计

配置：`configs/stage1_lossless_atomic_memory_v56_cached.json`。

底座：v42 `stage1_operation_workpad_v42_cached`。

只改 build memory：

- `prompt_profile = lossless_atomic`
- `max_turns_per_chunk = 72`
- `overlap_turns = 8`
- `max_chars_per_turn = 600`
- `max_records_per_chunk = 30`
- `max_tokens = 3072`
- `manage_facts = false`
- `build_memory.top_k = 24`

保持不变：

- raw-turn dense + BM25 hybrid retrieval
- top-40 final evidence budget
- `structured_guide_include_memory = false`
- `max_memory_records = 0`
- v42 `operation_workpad`
- answer max input/output `131072/16384`

核心假设：

- 更自包含、细粒度的 build memory 能提升 memory BM25 source activation，尤其是低显著并列事实、数量、价格、时间、实体名。
- `manage_facts=false` 只对 state/profile/preference/relationship 做 supersede，避免普通 fact 被最新同 predicate 事实覆盖；这更适合 list/count 和历史事实查询。
- overlap window 借鉴 SimpleMem 的局部连续性，但仍保留 raw source ids，避免摘要替代原文。

## 外部方法依据

- SimpleMem：借鉴 build 侧 self-contained memory units、时间归一化、指代消解、三路索引思想；本次只采用 lossless atomic extraction 和 overlap，不引入 query LLM planner。
- EverOS：借鉴 raw episode + atomic facts + 可重建索引；本次 raw turns 仍是最终证据，atomic memory 只做召回入口。
- HippoRAG / EverOS hierarchy：借鉴 fact/entity child -> passage/episode parent 回链；本次 typed memory hit 仍投影回 raw source turn。
- Graphiti/Zep：借鉴 temporal/provenance 和非破坏性失效思想；本次不构建重型图，只保留 source ids 和可选时间字段。
- LangMem / Memobase：借鉴 collection/profile 分层和 profile/event 双通道；本次先解决 collection/fact 覆盖，不把 profile 作为唯一事实。
- creating001-agent-memory：参考其 evidence-first query 和 source-turn materialization，但不迁移 target phrase、category、sample rule、gold/judge 或任何 benchmark-specific 逻辑。

## Clean 边界

- Prediction 不读取 gold answer、judge output、benchmark label、question_type、category、sample id、qid、row index 或 test feedback。
- v56 prompt 是通用 extraction prompt，不含测试实体、测试答案或样本规则。
- route 仍只来自 question text。
- typed memory 只来自 raw dialogue 和可见 timestamp/source metadata。
- DeepSeek judge、badcase、evidence recall 只用于离线分析和 gate。

## 预期收益

- list/count：减少低显著 item、价格、数量、并列事实漏抽；避免普通 fact supersede。
- temporal：overlap 和 lossless text 保留相对时间、日期、持续时间。
- current_state/profile：stable memory 仍允许 supersede，不破坏当前状态管理。
- over-abstain：memory source activation 可能把 assistant turn 或相邻 support row 带入 top40。

## 风险

- 更多 records 会提高 build tokens；需要确认 LME <=300K、LoCoMo <=100K。
- 更宽 build memory 可能带来 RRF 噪声，替换原 v42 的有用 raw rows。
- 如果错误主要来自 answer 聚合，即使 source activation 变好也可能不涨分。
- 新 build cache 需要冷构建，诊断前必须明确成本。

## Gate 计划

先跑 LongMemEval-S question-derived `weak_route_87` diagnostic：

- input: `outputs/diagnostic/v48_lme_weak_route_input/prediction_input.jsonl`
- benchmark/subset: `longmemeval_s / weak_route_87`
- workers: 4
- prediction 完成后跑 DeepSeek judge，并与 v42 same87 比较

通过 full 的最低条件：

- DeepSeek judge same87 相比 v42 有明确净收益，目标至少 `+3` correct。
- avg query tokens `<= 6000`，单样本不能系统性超过 `8000`。
- avg build tokens 合理，按 cold-build logical token 记录。
- avg memory records / active records 上升但不异常膨胀。
- memory source hits 增加时不能伴随大量 evidence row 替换噪声。

如果 weak-route gate 只是持平或负向，不跑 full，删除顶层 v56 config，只保留诊断快照。

如果 weak-route gate 正向，再按 question-derived route 做更大诊断或直接 LME full；LoCoMo 只有在 LME 不负向后再迁移到 v35/v34 底座。
