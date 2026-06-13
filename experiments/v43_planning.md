# v43 规划：Session Thread + Row-Linked Memory Guide

## 背景

v42 LongMemEval-S full 是当前最好结果，但只比 v36 多 `1/500`：

- v42：`387/500 = 0.774`
- v36：`386/500 = 0.772`
- gained：`26`
- lost：`25`
- changed_answer_count：`150`

这说明短 operation workpad 比 v40 detailed reader rules 稳，但不是突破。继续堆 answer prompt 不划算。

v42 badcase 显示，很多错误不是完全 retrieval miss：

- wrong total：`113`
- temporal：`59`
- large_context：`56`
- count_or_quantity：`54`
- gold_string_in_rows：`33`
- over_abstain：`22`
- update_or_state：`19`

具体错案里有三类共性：

- exact build memory 已经存在，但对应 raw row 排在 context 后面，answer 选了更靠前但更粗的证据。例如 animal shelter dinner 的 build memory 抽到了 Valentine's Day，但 answer 只答 February。
- 关键 raw row 已进 context，但 answer 没有把同一 session 的相邻 turns 合并理解。例如 pick up/return clothing 漏掉 dry cleaning blazer。
- 相关但不匹配的实体被误当作 support。例如 vintage cameras 被当成 vintage films。

## 外部方法参考

- `creating001-agent-memory`：参考 query 侧 evidence-first 和同一 conversation thread 的组织价值；不迁移 target phrase、category、sample rule、gold/judge 相关逻辑。
- SimpleMem：参考 self-contained memory units 与 structured context；v43 只把 build memory 作为 row-linked guide，不把 summary 当最终事实源。
- xMemory：参考 semantic/episodic 双通道和 raw message 回链；v43 把 selected raw rows 按 session thread 排列，帮助 episode-level reasoning。
- Mnemis：参考先选候选节点再回链 episode 的思路；v43 的 build memory guide 只指向已进入 context 的 raw rows。
- Graphiti/Zep：参考 temporal/provenance schema；v43 不新增图数据库，只保留 source-linked memory hints。

## 方法设计

底座：v42 `stage1_operation_workpad_v42_cached`。

新增代码开关：

- `compiler.context_layout`
  - `flat`：默认旧行为。
  - `session_thread`：把已选 raw evidence 按 session 分组，并在每个 session 内按 `turn_index` 排列。
- `compiler.route_overrides.<information_need>.context_layout`
  - 允许只对 question-derived information need 打开，不使用 benchmark label。

v43 配置：

- `configs/stage1_session_thread_memory_guide_v43_cached.json`
- retrieval/build/top-k 与 v42 完全相同。
- 对 `list_count` / `temporal_lookup`：
  - `context_layout=session_thread`
  - `structured_guide_include_memory=true`
  - `memory_record_source=evidence_rows`
  - `memory_order=question_overlap`
  - `max_memory_records=6`
- 对其他 information need 保持 v42 的 flat context 和无 memory guide。

设计意图：

- session thread 让 answer model 看到同一 episode 的前后文，而不是只看到按 retrieval 排列的孤立 turns。
- row-linked memory guide 只指向已召回 raw rows，提示 subject/predicate/value/time/status，不作为独立证据。
- max memory records 设为 6，避免 v42 已接近 `6000` avg query token 预算时继续膨胀 prompt。

## Clean 边界

- 只使用 question text、question_time、raw dialogue、build-stage memory records 和 retrieval 结果。
- 不使用 gold/reference answer、judge output、benchmark hidden labels、sample id、qid、row index、test feedback 或样本级规则。
- `list_count` / `temporal_lookup` 是 question-derived route，不是 LongMemEval question_type 或 LoCoMo category。
- build memory 由 raw dialogue 预先构建，cache hit 只节省本地 API 调用；build token 仍按 cold-build logical usage 统计。
- DeepSeek judge 仅用于预测完成后的离线评测。

## 风险

- v37 证明 typed memory 直接进入 prompt 会明显伤害 accuracy；v43 必须保持 row-linked guide，而不是 summary-as-fact。
- session thread 会改变 evidence row 顺序，可能让原本靠 retrieval rank 解决的 fact 被打乱；因此先只对 list/temporal 开启。
- memory guide 增加 query token，必须先 gate，不能直接 full。
- 如果错误来自 answer model 不服从 exact-slot 约束，session thread 不一定能解决。

## Gate 计划

先跑 LongMemEval-S route-stratified 20 条 diagnostic：

- input：`outputs/diagnostic/v35_lme_route_stratified_probe/prediction_input.jsonl`
- config：`configs/stage1_session_thread_memory_guide_v43_cached.json`
- workers：`4`

通过条件：

- 20/20 prediction 成功。
- answer max input/output = `131072/16384`。
- avg query tokens <= `6000`，max query tokens < `8000`。
- avg build tokens 按 logical cold-build usage 记录。
- `session_thread` 和 `activated_build_memory` 只在 `list_count` / `temporal_lookup` prompts 出现。
- prompt clean scan 无 hidden metadata；`category` 若出现只能来自 raw dialogue 普通词。
- 同子集 DeepSeek judge 相对 v42 或 v36 有净收益，或至少修复明确的 list/temporal badcase 且无明显 regression。否则不跑 full。

## 预期决策

如果 gate 只是持平或 token 超预算，不跑 full，保留为负向/中性诊断。若 gate 正向，再跑 LongMemEval-S full；LoCoMo 需要基于 v35/v34 底座单独做迁移版本，不能直接把 LME top40 配置当 LoCoMo 主线。
