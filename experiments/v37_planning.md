# v37 Row-Linked Memory Bundle Planning

## 背景

v36 是当前 LongMemEval-S full 最好结果，但只达到：

- accuracy: `0.772`
- correct: `386/500`
- 距 `0.80` target 还差 `14` correct
- avg query tokens: `5715.468`
- avg build tokens: `80346.246`

v36 badcase digest 显示，剩余 `114` 个 wrong 里：

- `count_or_quantity`: `59`
- `temporal`: `57`
- `large_context`: `70`
- `gold_string_in_rows`: `20`
- `over_abstain`: `19`
- `should_abstain`: `10`

LME 的 `answer_session_ids` 级 evidence recall 为 `1.0`，说明很多问题不是完全没召回到 session，而是 evidence rows 已经很多、answer 阶段仍然用错、漏算或过度拒答。下一步不应继续盲目扩大 top-k，也不应只做 answer-format 微调。

## 方法设计

新增 `configs/stage1_row_memory_bundle_v37_cached.json`。

核心改动：

- 新增 `compiler.memory_record_source`：
  - `retrieval`: 旧行为，只把 memory BM25 命中的 typed memory records 交给 compiler。
  - `evidence_rows`: 新行为，只把 source_id 已经出现在 raw evidence rows 里的 typed memory records 交给 compiler。
  - `retrieval_and_evidence_rows`: 两者合并，去重。
- v37 使用 `evidence_rows`。
- raw evidence 仍是最终事实源；typed memory 只作为 Structured Evidence Guide 里的 compact index。
- 不扩大 retrieval top-k：仍使用 v36 top40。
- 为控制 token，把 compiler `max_evidence_chars` 从 `18000` 降到 `16500`，route override 中降到 `16000`。
- 只按 question-text route 的 `information_need` 控制 memory bundle 数量：
  - current_state: `6`
  - fact_lookup: `6`
  - list_count: `10`
  - profile_preference: `6`
  - temporal_lookup: `8`
- answer 继续使用 `128K/16K`、`json_answer` 和 v35 duration rounding guard。

这个设计的关键是“typed memory -> raw evidence row 回链”：build-stage LLM 参与生成原子 typed records，但 query-time 只展示与当前可见 raw rows 绑定的 records，避免 summary/profile 变成独立事实来源。

## 外部代码借鉴和取舍

- `external/creating001-agent-memory/src/agent_memory/baseline/context.py`：参考 turn-pair retrieval 后 materialize 到 source turns，以及 neighbor expansion 只围绕已命中的 raw chunks；不迁移 financial sum 等 task-specific routing。
- `external/SimpleMem/simplemem/core/hybrid_retriever.py`、`answer_generator.py`：参考 semantic/lexical/structured 多视角检索和 structured context；不引入额外 LLM query planner，避免 query token 失控。
- `external/xMemory/evaluation/locomo/xMemory_search_framework.py`：参考 semantic memory / episodic memory 双通道，以及返回 original messages 作为最终上下文；不迁移其 benchmark pipeline。
- `external/EverOS/src/everos/memory/search/hierarchy.py`：参考 atomic fact child -> episode parent 的层级回链思想；v37 不引入图数据库，只做轻量 row-linked typed record。
- `external/Mnemis/global_selection/global_selector.py`：参考 top-down node selection 后回到 one-hop episodes/relations；v37 不做 LLM node selection，避免额外 query 成本。
- `external/graphiti/graphiti_core/prompts/extract_edges.py`、`external/MIRIX/mirix/schemas/episodic_memory.py`：参考 temporal/provenance schema，但 v37 不重建 temporal KG。

## Clean 边界

- Prediction 阶段不读取 gold answer、judge output、benchmark label、question_type、category、sample id、row index、qid、test feedback 或样本级规则。
- `memory_record_source=evidence_rows` 只使用当前样本 raw turns、build-stage typed records、retrieved raw evidence rows 和 question-text route。
- Route override 使用已有的 generic `information_need`，来自 question text，不来自 benchmark hidden label。
- badcase digest 只用于离线分析和方法设计，不进入 prediction pipeline。

## 预期收益和风险

预期收益：

- 对 `gold_string_in_rows` 和 `over_abstain`：typed record 可以把隐藏在长 turn 里的 slot/value 显式暴露，减少“信息不足”误判。
- 对 `list_count`：row-linked typed facts 可以辅助去重和聚合同类实体。
- 对 `temporal_lookup`：typed record 中 timestamp/entities/value 可以帮助 answer model 在多个相似 rows 里选择目标事件。
- 对 `profile_preference`：profile/preference records 只在对应 raw rows 可见时作为索引，降低 profile hallucination 风险。

主要风险：

- v14/v30 说明直接把 typed memory 放进 prompt 可能伤害 LME 或 LoCoMo；v37 必须验证是否只是增加噪声。
- v36 avg query tokens 已接近 6K；即使降 evidence chars，也必须先做 LME token gate。
- LLM build memory 可能抽错 typed record；因此 prompt 必须继续声明 Structured Evidence Guide 不是独立证据，最终事实以 Memory Context raw rows 为准。

## Gate 计划

先跑 LongMemEval-S route-stratified no-label diagnostic gate：

- input: `outputs/diagnostic/v35_lme_route_stratified_probe/prediction_input.jsonl`
- config: `configs/stage1_row_memory_bundle_v37_cached.json`
- samples: `20`
- 检查 avg query tokens 是否 `<= 6000`
- 检查 answer max input/output 是否 `131072/16384`
- 检查 avg compiled memory records 是否符合 route budget
- 检查 build tokens 仍按 logical cold-build usage 统计

如果 LME token gate 失败，不跑 full。

如果 gate 合格，再决定 full：

- LongMemEval-S full：优先，因为 v36 仍差 14 条，且 v37 直接针对 LME badcase。
- LoCoMo full：只有 LME 不明显负向，或 LoCoMo gate 显示 token/trace 合格后再跑；不能只看 LoCoMo。

## 记录要求

正式实验必须在 `experiments/formal/<run_id>/` 下记录：

- git commit 和 dirty 状态
- config snapshot
- benchmark/subset
- build/query tokens
- avg compiled memory records
- build memory cache stats
- answer cache stats
- DeepSeek judge accuracy
- diagnosis、summary、outputs 路径

## 2026-06-14 LME Gate 结果

run: `v37_row_memory_bundle_lme_probe_3d3cd07`

- samples: `20`
- source: `outputs/diagnostic/v35_lme_route_stratified_probe/prediction_input.jsonl`
- commit: `3d3cd072d69883f717de87f219c1553191d7d69b`
- dirty: 仅用户修改的 `docs/architecture.md`、`docs/clean_protocol.md`
- answer max input/output: `131072/16384`
- avg build tokens: `81690.45`
- avg query tokens: `5564.5`
- query token distribution: min `4489`, p50 `5477.5`, p90 `6820.5`, p95 `6967.65`, max `6972`
- avg compiled evidence items: `32.1`
- avg compiled memory records: `7.1`
- compiled memory records min/max: `4/10`
- build cache hits/misses/writes: `137/0/0`
- embedding cache hits/misses/writes: `10079/0/0`
- answer cache hits/misses/writes: `0/20/20`

结论：v37 通过 LongMemEval-S no-label average query token gate。row-linked build memory bundle 已生效，且通过降低 raw evidence char budget，把 avg query tokens 控制在 `6000` 内。下一步可以跑 LongMemEval-S full；正式记录必须同时报告 avg compiled memory records，避免只看 accuracy。

## 2026-06-14 LME Full 结果

run: `stage1_row_memory_bundle_v37_lme_s_full_7f1fea6`

- samples: `500`
- commit: `7f1fea62934d33252a01f0fe2000abdb483b2be8`
- dirty: 主要为用户修改的 `docs/architecture.md`、`docs/clean_protocol.md` 和预测后新增实验记录
- answer max input/output: `131072/16384`
- DeepSeek judge accuracy: `0.744`
- correct/valid/samples: `372/500/500`
- current best v36: `0.772`, `386/500`
- delta_vs_v36: `-14`
- v28: `0.766`, `383/500`
- delta_vs_v28: `-11`
- avg build tokens: `80346.246`
- avg query tokens: `5790.57`
- avg compiled evidence items: `32.348`
- avg compiled memory records: `7.478`
- build cache hits/misses/writes: `3341/0/0`
- embedding cache hits/misses/writes: `247238/0/0`
- answer cache hits/misses/writes: `20/480/480`
- evidence_recall: `1.0`
- comparison_vs_v36: gained `29`, lost `43`, changed-answer net `-11`, same-answer judge flip net `-3`

结论：v37 是负向消融。row-linked typed memory 作为 prompt 内 Structured Evidence Guide 的思路虽然 clean、general，也确实修复了一些 fact/temporal 个案，但整体让 temporal_lookup、list_count 和 current_state 回退更多。后续不继续沿着“增加 answer prompt 中 typed memory”推进；typed memory 更适合作为 retrieval/ranking/source selection/control signal，最终 answer prompt 应保留更少、更准的 raw evidence。
