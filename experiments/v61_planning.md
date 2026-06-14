# v61 规划：Fact Operation Workpad Gate

## 背景

v42 的 operation workpad 是当前 LongMemEval-S full 最好结果的唯一正向增量，但它只作用于 `list_count` 和 `temporal_lookup`。v42 full badcase 抽查显示，部分 `fact_lookup` 问题其实是通用运算/聚合问题，例如 total、difference、how much more、combined count。这些问题不需要改变 retrieval 或 build，只需要 answer reader 在已有证据上做 operand/scope/arithmetic 检查。

离线统计 v42 full：

- `fact_lookup` operation-pattern 子集：`33` 条，v42 `27/33` 正确，`6` 错误。
- 这些错误包括 accommodation price difference、road-trip total distance、online courses total、gift total、video views total、siblings total。
- 直接把这类问题改 route 到 `list_count` 风险大，因为同类已有 `27/33` 正确；因此 v61 不改 route，只给这类 fact question 加短 operation workpad。

## 外部代码依据

- `creating001-agent-memory`：参考 query-time evidence organization 和让模型在回答前核对证据的做法；不迁移任何不 clean 的 category/sample/answer 逻辑。
- LongMemEval 官方 generation baseline：说明 raw conversation context + 简洁 answer prompt 是强底座；v61 保持 raw evidence first，不引入隐藏字段。
- SimpleMem / xMemory / MemoryOS：共同启发是不要让 summary 替代 raw evidence，而是在 query-time 组织出更适合任务的 view；v61 是最小化的 operation view。
- agentmemory：参考 token budget 思路；v61 用 question gate 避免对普通 fact lookup 增加 prompt。

## 方法设计

新增可消融配置：

- `operation_workpad_question_gate`: 默认 false，保持 v42 完全不变。
- 当 gate 为 true 时：
  - `list_count` / `temporal_lookup` 保持 v42 行为。
  - 其他 route 只有当 question text 命中通用 operation / temporal calculation pattern 时才启用 operation workpad。

v61 配置：

- 基于 v42。
- `operation_workpad_information_needs`: `["fact_lookup", "list_count", "temporal_lookup"]`
- `operation_workpad_question_gate`: `true`
- 不改 build memory、retrieval、route、structured guide、evidence budget、answer finalizer。
- `max_memory_records=0` 保持 v42。
- answer max input/output 固定 `131072 / 16384`。

## Clean 检查

- gate 只看 question text 和现有 question-derived route。
- 不使用 gold answer、judge output、benchmark hidden label、sample id、row index、test feedback 或样本级规则。
- operation patterns 是通用数学/聚合意图，不包含具体测试实体或答案。

## 成本预期

v61 只影响 `fact_lookup` 中 question text 是 operation 的小子集；full avg query token 预计略高于 v42，但应明显低于 v60，目标仍是 `<= 6000`。

build 侧完全复用 v42 方法，`avg_build_tokens` 仍按新环境 cold build 逻辑 token 统计，cache hit 不把方法成本记为 0。

## 实验门禁

1. 单元测试、JSON 校验、diff check 通过。
2. 先构造 question-derived LongMemEval-S `fact_operation_33` 诊断子集，不使用 gold/judge/sample id 参与 prediction。
3. 诊断对比 v42 same33：
   - DeepSeek judge correct 必须高于 v42 same33，且 loss 不能明显多于 gain。
   - avg query tokens 需接近 v42 same33；若超过 6K 但无强正向，不扩 full。
4. 只有在 fact_operation_33 明确正向且 badcase 不显示系统性 over-count，才考虑 LongMemEval-S full。

## 风险

- Workpad 可能让原本正确的 simple total answer 变得过度保守。
- 一些 operation words 出现在普通 fact question 中，可能让模型错误地聚合无关证据。
- 这类子集最多 33 条，单独收益上限有限；如果只是小正向，也需要和更大的 build/query memory 方法组合。
