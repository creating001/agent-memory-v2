# v31 Evidence Report Detail Planning

## 目标

v30 LoCoMo full 证明 build-side typed temporal memory 字段更 clean，但当前 config 降低了 source activation 覆盖，accuracy 低于 v29。因此 v31 不继续盲目重建 build memory，而是在 v29 的 source-preserving build memory 底座上改 query-side compiler。

核心目标：

- 保留 v29 的 build memory namespace，保持 source activation 覆盖。
- 不增加 build token，不重新做全量 build。
- 在 answer prompt 里加入可关闭的 detailed evidence_report discipline，主要解决 evidence-hit wrong。
- 方法必须通用，只基于 question text 和 retrieved context，不使用 gold/judge/category/sample id。

## 外部方法借鉴

- creating001-agent-memory：借鉴两阶段 evidence table 的通用 include/exclude 思路、精确 slot 匹配、列表/计数去重、assistant suggestion gating、current/previous 区分。舍弃其不 clean 或过强 benchmark 化的 route/template 分支、target phrase 规则、finalizer 和样本级逻辑。
- SimpleMem：借鉴 lossless memory 和 hybrid retrieval 的原则，即不要让派生 memory 替代原始 evidence，query 阶段要保留所有可能影响答案的候选。舍弃其 benchmark/category prompt adapter。
- Graphiti/Zep：保留 temporal/provenance 的工程启发，但 v31 不引入图数据库或新 temporal KG。
- MIRIX：保留 episodic/source schema 的启发，但 v31 不做新的多类型 memory build。

## 方法设计

新增 `compiler.evidence_report_detail`，默认关闭。打开后，在已有 `evidence_report_contract` 中加入通用 evidence discipline：

- include every candidate row that may change the answer
- preserve exact names, dates, numbers, places, titles, units
- support/exclude 必须匹配 action/object/relation/time/scope
- discussing/planning/liking/asking/recommending 不等于实际 doing/buying/attending/reading
- assistant suggestions 只有在问题问 suggestion/plan 或用户确认时才算事实支持
- missing evidence 不当作 zero/false；只能输出 supported lower bound
- current/latest 和 previous/initial/original 分开处理
- list-style what/which 问题保留所有 distinct in-scope values

这些规则都来自真实 memory QA 的通用 evidence use，不包含具体测试实体、答案、category、sample id 或 row index。

## 配置

`configs/stage1_evidence_report_detail_v31_cached.json`：

- build_memory 复用 v29 namespace: `stage1_agent_memory_v1_qwen3_30b_cold`
- retrieval 与 v29 保持一致
- compiler:
  - `evidence_report_detail=true`
  - `evidence_report_max_items=12`
  - 其他 v29 temporal event contract 设置保持一致
- answer cache: `outputs/cache/qwen3_answer_v31.sqlite`
- answer max input/output: `131072/16384`

## Gate

先跑 no-label diagnostic：

- 使用 route-stratified prediction input，不读 label/gold/judge/category/sample id。
- 检查 answer 16K、query token 预算、build token logical accounting、build cache hit、prompt 中 detail rules 是否出现。
- evidence recall 只能在 prediction 后离线算，不能作为 prediction 输入。

如果 gate 正常，v31 是 query-side 改动，可以直接跑 LoCoMo non-adversarial full；若 accuracy 有收益，再补 LongMemEval-S full。

## 2026-06-14 Gate 结果

`v31_evidence_report_detail_probe_b913567` 已完成 no-label route-stratified diagnostic。

- samples: `20/20`
- avg build tokens: `63177.1`
- avg query tokens: `5152.6`
- answer max input/output: `131072/16384`
- `evidence_report_detail`: `true`
- detailed evidence rules present: `20/20` prompts
- plural/list slot rules present: `7/20` prompts
- build_memory_temporal_fields: `false`
- build memory records: avg `116.75`
- build memory source hits: avg `13.7`

Gate 通过。该诊断不读取 labels/gold/judge/category/sample id，不计算 accuracy。下一步可以跑 LoCoMo non-adversarial full v31 prediction，并在完成后离线 DeepSeek judge。
