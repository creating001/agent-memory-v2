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
- compiler 最终仍只保留 top40 source rows，不采用 v38 的 top60 final prompt。
- `list_count` 和 `temporal_lookup` 使用 `role_query_snippet` 控制 prompt token；trace 中仍保留完整 raw row，answer prompt 中只放 query-focused raw snippet。
- 默认保持 v36 的 `compiler.evidence_order = retrieval`，只对 `list_count` 和 `temporal_lookup` route override 为 `memory_aware`：
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
- 检查 route override 是否只让 list/temporal 使用 `role_query_snippet`
- 检查 `compiled_memory_records` 是否仍为 `0`
- 检查 build tokens 仍按 logical cold-build usage 统计

Gate 通过后再跑 LongMemEval-S full。LoCoMo 只有在 LME 不明显负向后再安排。

## Clean 边界

- Prediction 阶段不读取 gold answer、judge output、benchmark label、question_type、category、sample id、row index、qid、test feedback 或样本级规则。
- `information_need` route 只来自问题文本和可见 question_time。
- `memory_aware` selector 只使用 raw dialogue、build-stage memory source links、retrieval rank 和 question text。
- DeepSeek judge、evidence recall 和 badcase 只用于离线诊断。

## 2026-06-14 Gate 修正记录

第一次 gate run `v39_memory_aware_selector_lme_probe_6a44f23` 没有进入 full：

- avg query tokens: `5288.1`
- avg compiled evidence items: `20.6`
- `list_count` avg rows: `13.5`
- `temporal_lookup` avg rows: `12.5`
- compiled memory records: `0`

问题：`memory_aware` 把高重叠但很长的 rows 提前，`max_evidence_chars=18000` 很快耗尽，虽然 token 低，但最终证据覆盖不足。该 run 只作为 transient gate 失败记录，输出目录不长期保留。

修正：保留 top60 candidate -> top40 source row 的 selector 设计，但对 `list_count` / `temporal_lookup` 在 prompt 中使用 `role_query_snippet`，避免长 row 吃掉证据预算。下一次 gate 需要确认最终 rows 回到接近 40，且 avg query tokens 仍 `<=6000`。

第二次 gate run `v39_memory_aware_selector_lme_probe_760bbb3` 仍不进入 full：

- avg query tokens: `5482.25`
- avg compiled evidence items: `29.7`
- `list_count` avg rows: `36.0`
- `temporal_lookup` avg rows: `35.5`
- compiled memory records: `0`

它解决了 list/temporal row coverage 和 token 问题，但因为 `evidence_order=memory_aware` 是全局设置，current/fact/profile route 也被重排，偏离 v36 稳定底座。为降低 full run 风险，继续修正为 route-scoped evidence order：默认 retrieval order，只对 `list_count` / `temporal_lookup` 使用 `memory_aware`。

第三次 gate run `v39_memory_aware_selector_lme_probe_fd00801` 通过，可以进入 LongMemEval-S full：

- commit: `fd00801b76f9e3fc686f61e222ece71eec563c27`
- dirty: `true`，仅包含用户修改的 `docs/architecture.md` 和 `docs/clean_protocol.md`
- answer max input/output: `131072/16384`
- avg build tokens: `81690.45`
- total build tokens: `1633809`
- avg query tokens: `5607.8`
- total query tokens: `112156`
- 按 LME full route 分布估算 avg query tokens: `5566.583`
- avg compiled evidence items: `34.65`
- avg compiled memory records: `0.0`
- build cache hits/misses/writes: `137/0/0`
- embedding cache hits/misses/writes: `10079/0/0`
- answer cache hits/misses/writes: `8/12/12`

route audit：

| information_need | n | top_k | evidence_order | row_text_mode | avg query tokens | avg rows |
|---|---:|---:|---|---|---:|---:|
| current_state | 4 | 40 | retrieval | full | 6092.0 | 28.8 |
| fact_lookup | 4 | 40 | retrieval | full | 5073.5 | 37.0 |
| list_count | 4 | 60 | memory_aware | role_query_snippet | 5575.5 | 36.0 |
| profile_preference | 4 | 40 | retrieval | full | 5216.8 | 36.0 |
| temporal_lookup | 4 | 60 | memory_aware | role_query_snippet | 6081.2 | 35.5 |

结论：

- v39 的 route-scoped override 已按设计生效：非目标 route 保持 v36，`list_count` / `temporal_lookup` 才启用 memory-aware selector。
- 第一次 gate 的 row coverage 过低问题和第二次 gate 的全局重排问题已修正。
- `temporal_lookup` 单 route query token 略高，但 full 分布加权估计仍在 6K 内。
- 下一步跑 LongMemEval-S full；只有 LME full 不明显负向，才安排 LoCoMo full。
