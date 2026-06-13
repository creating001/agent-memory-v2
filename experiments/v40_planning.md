# v40 Route-Scoped Evidence Detail Planning

## 背景

当前 LongMemEval-S 最好结果仍是 v36：

- accuracy: `0.772`
- correct: `386/500`
- avg build tokens: `80346.246`
- avg query tokens: `5715.468`
- 距 `0.80` baseline target 还差 `14` correct

v37-v39 都是负向探索：

- v37 把 row-linked typed memory 放进 answer prompt，accuracy `0.744`，说明派生 memory 直接作为 prompt fact 会干扰 reader。
- v38 扩大 `list_count` / `temporal_lookup` final context 到 top60，accuracy `0.752`，说明更宽上下文引入的噪声超过 coverage 收益。
- v39 用 build-memory source signal 重排 final raw rows，accuracy `0.724`，说明轻量 memory-aware row score 会破坏 list/temporal operand coverage。

v36 wrong-case 主要集中在：

- `multi-session`
- `temporal-reasoning`
- `single-session-preference`
- `temporal_lookup`
- `list_count`
- `fact_lookup`

已有诊断显示，很多 wrong case 并不是简单检索不到证据，而是 evidence 已进入 context 后，answer 阶段没有稳定区分事件动作、列表边界、时间点、旧事实和最新状态。因此 v40 不继续扩大 top-k，也不把 typed memory 塞进 prompt；只尝试让 reader 在高风险 question-derived route 上更明确地整理 include / exclude / missing evidence。

## 方法设计

新增 `configs/stage1_route_scoped_evidence_detail_v40_cached.json`。

核心改动：

- 底座保持 v36：top40 raw-turn dense+BM25 retrieval、evidence_report contract、structured guide、temporal aid、answer format guard、answer max `131072/16384` 不变。
- 全局 `compiler.evidence_report_detail=false`，保持 v36 对 `current_state` / `fact_lookup` / `profile_preference` 的稳定 prompt。
- 仅对 question-derived `list_count` 和 `temporal_lookup` route override：
  - `evidence_report_detail=true`
  - 不改变 retrieval top-k。
  - 不改变 final evidence row 数量。
  - 不启用 build-memory prompt records。
  - 不启用 sample-level、benchmark-label 或 judge-based 逻辑。

这是一组单调用 reader/compiler ablation。它不会新增 build LLM 调用，也不会新增 query-side LLM stage；主要成本是 list/temporal prompt 中多几行通用 evidence 操作规则。

## 外部代码借鉴和取舍

本次设计参考了以下外部方向：

- `creating001-agent-memory` 的 query/answer pipeline、retrieve prompt、answer template、evidence finalizer：借鉴“先整理 support/exclude/missing evidence，再输出最终答案”的 reader 组织方式；不迁移其中任何 `sample_id`、`question_type`、gold answer、benchmark rule、sample-level guardrail 或 test feedback 逻辑。
- HippoRAG / Graphiti / Zep：继续保留 source-linked raw evidence 是最终事实依据，派生结构只能帮助组织或检索。
- SimpleMem / LightMem / Memary：借鉴轻量 memory organization 和列表/实体聚合的思路，但不引入固定实体规则或 benchmark 专门 pattern。
- v26 structured answer contract：它在 LME 有一定收益但整体低于 v36，说明强 JSON evidence_items contract 会带来回退；v40 只打开更轻的 evidence_report detail，且只作用于 list/temporal route。

## 预期收益

- `list_count`：减少把“拥有/讨论/计划/喜欢/询问/推荐/考虑”误当成真实发生或应计入列表的问题。
- `temporal_lookup`：提醒 reader 区分 mention time、event time、状态有效时间和相对时间。
- 保持 v36 的 retrieval、token 和非目标 route 稳定性，降低 full run 风险。

## 风险

- v31 detailed evidence_report 在 LoCoMo full 负向，原因之一是 answer 更保守；v40 虽然只 route-scoped，但仍可能增加 over-abstain。
- 更细规则可能让模型输出更长 JSON reasoning，推高 query tokens。
- 如果 v36 错误根因是 evidence 排序或缺失，v40 这种 reader-side 小改不会解决。

## Gate 计划

先跑 LongMemEval-S route-stratified no-label diagnostic gate：

- input: `outputs/diagnostic/v35_lme_route_stratified_probe/prediction_input.jsonl`
- config: `configs/stage1_route_scoped_evidence_detail_v40_cached.json`
- samples: `20`
- workers: `4`

必须检查：

- answer max input/output 为 `131072/16384`
- avg query tokens `<= 6000`
- avg build tokens 按 logical cold-build usage 统计，即使 cache hit 也不能记为 0
- `evidence_report_detail` 只出现在 `list_count` / `temporal_lookup` prompt 中
- retrieval top-k、compiled evidence rows 和 compiled memory records 不偏离 v36
- build cache、embedding cache、answer cache 状态完整记录

Gate 不通过就停止，不跑 full。Gate 通过后，也只先跑 LongMemEval-S full；只有 LME full 相对 v36 不明显负向，才考虑 LoCoMo full。

## Clean 边界

- Prediction 阶段不读取 gold answer、judge output、benchmark label、question_type、category、sample id、row index、qid、test feedback 或样本级规则。
- `list_count` / `temporal_lookup` 来自项目内部 question-text router，不来自 benchmark 隐藏标签。
- prompt 中不写具体测试答案、测试实体或测试样本编号。
- DeepSeek judge、evidence recall、badcase digest 只用于离线诊断，不能进入同一轮 prediction pipeline。
