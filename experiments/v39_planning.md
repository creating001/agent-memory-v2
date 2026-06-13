# v39 Memory-Aware Evidence Selector Planning

## 背景

当前 LongMemEval-S 最好结果是 v36：

- accuracy: `0.772`
- correct: `386/500`
- avg build tokens: `80346.246`
- avg query tokens: `5715.468`
- 距 `0.80` baseline target 还差 `14` correct

v37 和 v38 的结论：

- v37 row-linked typed memory prompt：accuracy `0.744`，证明 typed memory 直接进入 answer prompt 会干扰 reader。
- v38 route-scoped top60 + snippet：accuracy `0.752`，比 v36 净 `-10`。更宽 raw evidence 能修复部分漏项，但最终 60 条上下文让 `list_count` / `temporal_lookup` 引入更多相邻噪声。

因此 v39 不继续堆 prompt，也不让 typed memory 成为独立事实来源；目标是让 build-stage memory 参与 source selection，把更多候选先召回，再把更少、更准的 raw evidence 交给 answer model。

## 方法设计

新增 `configs/stage1_memory_aware_selector_v39_cached.json`。

核心改动：

- 底座保持 v36：answer format guard、evidence_report contract、structured guide、temporal aid、answer max `131072/16384` 不变。
- `list_count` 和 `temporal_lookup` 的 retrieval candidate pool 从 top40 扩到 top60。
- compiler 最终仍只保留 top40 raw evidence，不采用 v38 的 top60 final prompt。
- 新增 `compiler.evidence_order = memory_aware`：
  - 使用 question terms、retrieval rank、row timestamp/quantity signal。
  - 使用 build-memory BM25 命中的 `source_ids` 给 raw row 加 source-linked memory bonus。
  - `max_memory_records=0`，typed memory 不作为 prompt fact 出现。

## 外部代码借鉴和取舍

- HippoRAG：借鉴 fact/entity 先检索、再回到 passage/raw chunk 的思想；不迁移 gold_docs/gold_answers 评测入口，也不使用任务 demo 作为预测规则。
- EverOS / SimpleMem / xMemory：延续 atomic/typed memory 只做 source expansion 和 source selection 的方向，最终答案仍依赖 raw evidence。
- LightMem / MemZero：参考 memory search wrapper 和 metadata/user scope 的工程边界；不引入其外部存储依赖。
- Memary：参考 entity/count 聚合的轻量思想，但 v39 不写固定 entity 规则，只用通用 quantity/time signal。
- MIA：其中基于 correct/incorrect feedback 的 balanced memory retrieval 不 clean，不能迁移；只把“候选计划/证据选择要与最终生成分离”的工程思路作为负面边界参考。

## 预期收益

- 相比 v36：top60 candidate pool 有机会召回 v36 漏掉的 operands。
- 相比 v38：最终 prompt 回到 40 条，减少 list/temporal 的噪声暴露。
- 相比 v37：typed memory 不直接进入 answer prompt，避免派生事实与 raw evidence 竞争。

## 风险

- deterministic memory bonus 可能把错误或过宽 typed memory 的 source row 提前。
- question overlap 可能偏向含问题词但不含答案的泛化建议 row。
- top60 candidate pool 即使最终截到 40，也会改变 prompt 顺序，可能引入 answer variance。

## Gate 计划

先跑 LongMemEval-S route-stratified no-label diagnostic gate：

- input: `outputs/diagnostic/v35_lme_route_stratified_probe/prediction_input.jsonl`
- config: `configs/stage1_memory_aware_selector_v39_cached.json`
- samples: `20`
- 检查 avg query tokens 是否 `<= 6000`
- 检查 answer max input/output 是否 `131072/16384`
- 检查 `list_count` / `temporal_lookup` 是否 top60 candidate、最终 compiled evidence 是否仍约 40
- 检查 `compiled_memory_records` 是否仍为 `0`
- 检查 build tokens 仍按 logical cold-build usage 统计

Gate 通过后再跑 LongMemEval-S full。LoCoMo 只有在 LME 不明显负向后再安排。

## Clean 边界

- Prediction 阶段不读取 gold answer、judge output、benchmark label、question_type、category、sample id、row index、qid、test feedback 或样本级规则。
- `information_need` route 只来自问题文本和可见 question_time。
- `memory_aware` selector 只使用 raw dialogue、build-stage memory source links、retrieval rank 和 question text。
- DeepSeek judge、evidence recall 和 badcase 只用于离线诊断。
