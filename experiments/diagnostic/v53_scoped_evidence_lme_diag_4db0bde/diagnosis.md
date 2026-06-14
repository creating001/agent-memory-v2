# v53 Scoped Evidence 失败诊断

## 诊断结论

v53 的两阶段 scoped evidence 路线当前失败，不能扩到 full。

它确实证明了一点：先抽 operands 再回答可以修复部分 coverage 型错误，例如：

- `e3b12960136041241dc62c39`: bike expenses，v42 `65` -> v53 `185`
- `9ae27974136200033b2aac40`: feed weight，v42 `50 pounds` -> v53 `70 pounds`
- `6778983aaf41f9823f490730`: plants，v42 `2` -> v53 `3`
- `982d8ba42d8afeef9f5749fb`: fitness class days，v42 `3` -> v53 `4`
- `38395512ed74d379096ac16f`: sculpting duration，v42 abstain -> v53 `3`

但整体是强负向：相对 v42 same-106 只有 `+5` gains，却有 `23` losses。说明 scoped extraction 的少量 coverage gain 远远抵不过压缩、误纳入和 calculation 错误。

## 失败机制

### 1. Extractor 过度自信

v53 的 extraction 几乎总是认为证据充分：

- `sufficient=True`: `103/106`
- `sufficient=False`: `3/106`

这对 unknown / incomplete-information 题非常危险。典型 regression：

- `45ccdf8947da04d80402bb2e`: Hawaii + Seattle travel days。v42 正确拒答；v53 只看到 Hawaii 的 `10` 天，就回答 `10`，漏掉 Seattle 缺失。
- `71c309443747c6d8faf4a7d2`: iPad purchase not mentioned。v42 正确拒答；v53 用相邻 Apple device 事件算出 `7`。
- `7aca5175762d0438ea896589`: football vs baseball collection。v42 正确拒答；v53 把 baseball collection 当 football，答 `20`。

结论：如果 extracted JSON 是唯一事实输入，extractor 的 false sufficient 会直接变成错误答案。

### 2. Duration / temporal calculation 容易压缩错

v53 的 answer_type 分布里 `duration=65/106`，loss 里 duration 占比很高。问题不是 token 不够，而是 extractor 把时间点压成错误 calculation，第二阶段没有 raw context 可复核。

典型 regression：

- `243572a249c3fec8e125aade`: museum visit，v42 `5` months 正确；v53 `1 month`。
- `2baf3826b072fa512434bb50`: remote shutter release arrival，v42 `5 days` 正确；v53 `20`。
- `57cc985e29edc5e617c3cfac`: Holi vs Sunday mass，v42 `21` 正确；v53 `28 days`。
- `73cce53c811c1938bfc16964`: running shoes vs shoelaces，v42 `14` 正确；v53 `0 days`。

结论：duration 题不能只靠 LLM 抽取 JSON 后再让另一个 LLM算；需要 source-level event pair selection 和可验证日期规范化，最好保留 raw evidence fallback。

### 3. Included/excluded 边界不稳

v53 能列 included/excluded，但并不等于边界正确。它会把 social event 当 dinner party，把 repeated mention 当新事件，把 assistant suggestion 当 attended event，或者把 close-but-wrong item 纳入。

示例：

- `040a4510206229039b25c860`: concerts order。v53 把 Billie Eilish、music festival、free outdoor concert 反复纳入，且顺序 calculation 自相矛盾；仍漏/错关键边界。
- `cdde2a2cdd99eb2b49880db5`: dinner parties。v53 把 birthday party 和 BBQ party 扩成 dinner party，答 `4`，虽然此题相对 v42 可能是 gain/loss 边界，但说明 inclusion 语义过宽。
- `3327f6bb9f2b962d1187cd6b`: baking count。v42 `4` 正确；v53 `3`，漏掉 in-scope event。

结论：included/excluded 不能只作为自由文本 JSON，需要更强的 evidence provenance 和 conflict/duplicate management。

### 4. Raw evidence 兜底被移除

v42 虽然 prompt 长，但 answer model 能直接看到 raw rows。v53 第二阶段只看 extraction JSON，一旦 JSON 丢掉关键 row 或把 value 写错，就没有办法恢复。这个设计与 `docs/method.md` 的 evidence-first 原则相冲突：派生结构应辅助 raw evidence，而不应替代 raw evidence。

## Token 与工程结论

v53 token gate 通过：

- avg_build_tokens: `79953.094340`
- avg_query_tokens: `5113.226415`
- scoped extraction avg query tokens: `4025.603774`
- scoped answer avg query tokens: `1087.622642`

这说明失败不是“预算太小导致输出差”，而是结构设计不稳。继续扩大 max rows 或 extraction schema 可能只会增加噪声，不应作为下一步主线。

## Clean 结论

clean scan 没有发现真实泄漏：

- prediction 输入不含 gold/judge/label/sample id/qid/row index。
- scoped prompt 已去掉会污染 literal scan 的泛化 forbidden-term 句子。
- 仅有 `correct answer` 的 raw dialogue false positive。

因此 v53 是 clean 但性能失败，不是 clean 问题。

## 保留价值

可以保留代码里的 `scoped_evidence` 模块作为后续 ablation 工具，但当前配置应删除。可能的可复用方向：

- 把 scoped extraction 作为 advisory evidence table，而不是唯一 answer input。
- 只在 high-confidence arithmetic/sum 题上使用 extracted operands，并让 answer stage 同时看到 raw supporting rows。
- 用 extraction 结果做 verifier，对 draft answer 做一致性检查，而不是替换 draft answer。
- 把 evidence extraction 前移到 build-side typed event/state/entity memory，并保留 source_ids 和 raw row fallback。

## 下一步建议

下一轮不要再做“二阶段抽取 JSON 后直接回答”的变体。更有价值的方向：

1. 深入外部代码的 memory manager / graph / temporal provenance 实现，优先看 Graphiti/Zep、Memobase、LangMem、MIRIX、xMemory、SimpleMem 的 source-linked update/merge 机制。
2. 设计 build-side event/entity/state memory v54：LLM build 阶段抽取 event/state records，显式 source_ids、event_time、validity、entity、relation、supersedes；query 阶段用它扩展 raw evidence，而不是直接回答。
3. 对 v42/v53 gain/loss 做更细 badcase 分类，尤其区分 retrieval miss、wrong inclusion、duplicate count、duration pair error 和 should-abstain。
4. 先跑 question-derived diagnostic，不直接 full；只有 same-set accuracy 净正且 token <= 6K 时才扩 LongMemEval-S full。
