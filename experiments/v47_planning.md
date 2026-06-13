# v47 规划：Temporal Aggregation Contract

## 背景

v46 证明 temporal session ordering 能修复一个 exact-date badcase，并且 full query token 估算低于 6K，但 strict DeepSeek same-20 与 v42 持平，没有直接 full 的把握。

重新分析 v42 LongMemEval-S full 的 `temporal_lookup` wrong cases 后，发现错误主体不是日期 lookup：

- temporal wrong 总数：`41`
- `count_in_time_scope`：约 `22`
- `date_or_time_lookup`：约 `5`
- `duration_calc`：约 `3`
- `numeric_sum_or_amount`：约 `1`
- 其他 temporal / preference / order：约 `10`

典型 count/sum wrong 不是 retrieval miss。v42 full evidence recall 为 `1.0`，错误更多发生在 answer 阶段：模型能列出 evidence_report，但最终 answer 和它自己的 evidence_report/计算不一致，或者把 count、operand、页数、星数、尺寸等数字混在一起。

## 方法设计

底座：v42 operation workpad。

配置：`configs/stage1_temporal_aggregation_contract_v47_cached.json`

新增：

- `compiler.aggregation_report_contract=true`
- `compiler.aggregation_report_information_needs=["temporal_lookup"]`
- 仅当 question text 命中通用 aggregation pattern 时启用，包括 `how many`、`how much`、`total`、`sum`、`difference`、`percentage`、`order` 等。
- aggregation evidence_report schema 增加：
  - `canonical_item`
  - `count_increment`
  - `operand_value`
  - `calculation`
- `answer.finalizer.enable_evidence_report_count_correction=true`

finalizer 极窄触发：

- 只读取 answer model 当前 raw_response 里的 JSON。
- 只处理 `answer_type=count`。
- 只认新 schema 的 `count_increment`，不从旧 `value` 猜 count。
- 所有 support item 都必须给出正整数 `count_increment`，且不能有 `operand_value`。
- draft answer 必须与 `sum(count_increment)` 数值不一致。

不启用：

- 不打开旧的宽 `enable_count_correction`。
- 不启用 session_thread，避免和 v46 混合变量。
- 不新增 build LLM call。

## 外部方法参考

- `creating001-agent-memory`：参考 scoped aggregation 的 include/exclude/canonical_item/operand 思路；舍弃两阶段 LLM、target phrase、category、sample-level guardrail 和 finalizer 中不 clean/过强的部分。
- `SimpleMem`：参考 structured context 和 typed evidence，但 v47 不让 summary/typed memory 替代 raw evidence。
- `Memary`：参考 entity/count/date 聚合思想，但不做固定 entity 规则。
- `Graphiti/Zep`：保留 provenance/temporal 区分思想，不引入图数据库。

## Clean 边界

- prediction 只用 question text、visible question_time、raw dialogue、retrieval result 和 build-stage memory source links。
- aggregation trigger 是通用 question-derived information need，不读 benchmark `question_type` 或 label。
- finalizer 只读当前 answer raw_response，不读 gold、judge、offline evidence label、sample id 或 test feedback。
- badcase 只用于离线设计，不进入 config/prompt 里的样本实体或答案。

## Gate 计划

先做一个 question-type diagnostic，而不是 full：

- 从 LongMemEval-S full prediction input 中按 question text 和 clean router 选出 `temporal_lookup + aggregation question`。
- 不按 gold/judge 选样本。
- 跑 v47 与 v42 同输入对比，重点看 DeepSeek judge accuracy、changed-answer delta、finalizer applied cases 和 token。

通过条件：

- prediction 全成功。
- answer max input/output = `131072/16384`。
- avg query tokens 估算仍可控，若 full route-mix 预计超过 6K，则不能作为主线。
- finalizer applied cases 必须逐条检查，不能出现明显机械误修。
- DeepSeek judge 在该 diagnostic 上相对 v42 净正向，且 changed-answer regression 可解释。

## 预期决策

如果 temporal aggregation diagnostic 正向，再考虑 v48：把 v46 的 session ordering 与 v47 的 aggregation contract 组合，并先做 token gate。若 v47 对 aggregation 无收益或 finalizer 误修，则回退，转向 build-side event/temporal schema 或 retrieval-side coverage，而不是扩大 finalizer。
