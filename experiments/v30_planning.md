# v30 typed event/state memory planning

## 当前事实

- v28 是当前 LongMemEval-S full 最好：`0.766`。
- v29 是当前 LoCoMo non-adversarial full 最好：`0.761688`，但 LME 回退到 `0.762`。
- v29 的 LoCoMo 净收益主要来自 `temporal_lookup`：`0.647929 -> 0.754438`，净 `+36`。
- v29 的 LME 回退主要来自 `current_state`、`list_count` 和部分 insufficient-evidence case。

## 结论

event-time 组织是有效方向，但不能继续只靠 query prompt。下一步应把有效部分前移到 build-stage memory management：

- build LLM 抽取 `mention_time`、`event_time`、`valid_from`、`valid_to`。
- memory manager 保留 event/state/profile 分通道，支持 dedup、supersede、source provenance。
- query 侧只把 typed memory 当作候选组织和 raw-source 回链线索，最终答案仍由 raw evidence 定案。

## 外部方法依据

- Graphiti/Zep：temporal validity (`valid_at` / `invalid_at`) 与 episode provenance。
- SimpleMem：lossless temporal memory unit 和多视角 retrieval。
- LangMem：profile schema、namespace、update-in-place。
- Memobase：event summary、profile delta、created time 的 event/profile 双通道。
- MIRIX：episodic event schema，包括 `event_type`、`summary`、`details`、`actor`、`occurred_at`。
- xMemory/EverOS：typed/semantic child memory 回链原始 episode。

舍弃：

- 不引入 benchmark category、question_type、source_sample_id、gold evidence、judge feedback。
- 不迁移 MemMachine/LongMemEval evaluator 中含 answer/session 标注的逻辑。
- 不继续堆针对具体 LoCoMo 表达的样本级 prompt 规则。

## 已实现 skeleton

Commit `0eb44da` 增加：

- `MemoryRecord.mention_time`
- `MemoryRecord.event_time`
- `build_memory.temporal_fields` 显式开关，默认关闭，避免污染 v28/v29 cache 与 prompt。
- `configs/stage1_typed_event_memory_v30_cached.json`
- compiler build-memory guide 中显示 `mention_time` / `event_time`
- runner metrics/summary 记录 `build_memory_temporal_fields`
- 单元测试覆盖 opt-in、字段保留和 compiler 可见性。

## 下一步诊断

先做 stratified diagnostic，不直接 full run：

- LoCoMo：优先抽 temporal_lookup、list_count、profile_preference、fact_lookup。
- LongMemEval：优先抽 temporal_lookup、current_state、list_count、profile_preference。
- 抽样必须来自 question text route 或离线诊断分组，不能使用 gold answer 选择具体样本。
- 检查 build 输出是否真的产生 `event_time`、`mention_time`、`valid_from`、`valid_to`。
- 检查 avg build/query token 是否仍满足预算趋势。
- 检查 v30 是否保留 v29 的 LoCoMo temporal 收益，同时不继续伤害 LME list/current。

## Full Run Gate

只有同时满足以下条件，才跑 full：

- 小样本 build cache miss 成功，字段非空率合理，且没有明显格式崩坏。
- temporal_lookup 有正向迹象，list_count/current_state 没有系统性回退。
- avg query tokens 仍明显低于 6K；build tokens 预计仍低于 LME 300K / LoCoMo 100K。
- 方案能解释为通用 agent memory management，不是 benchmark prompt tuning。

## 2026-06-13 诊断更新

`v30_stateful_validity_probe_3525934` 是当前有效的字段门禁：

- samples: `20`，来自 route-stratified prediction input，不使用 label/gold/judge/category/sample id/evidence。
- avg build tokens: `65592.3`
- avg query tokens: `4984.55`
- build cache: `128/0/0` hit/miss/write，token 成本仍按 cold-start logical usage 记录。
- build records: `1711`
- `mention_time`: `1711/1711`
- `event_time`: `424/1711`
- `valid_from`: `458/1711`
- `valid_to`: `97/1711`
- non-stateful validity records: `0`
- answer max input/output: `131072/16384`

本次诊断发现并修正了一个重要问题：LLM 会把 `valid_from/valid_to` 过度填到一次性 event/fact/plan 上。当前代码在 `build_memory.temporal_fields=true` 时只让 `state/profile/preference/relationship` 参与 validity/supersede 管理；`event/fact/plan` 使用 `event_time` 表达事件时间，不再被当作持续状态。

字段质量与 token gate 已通过。下一步建议先提交 v30 validity 修正，再跑 LoCoMo non-adversarial full 验证是否保留 v29 temporal 收益；随后必须跑 LongMemEval-S full，因为 v29 在 LME 回退。
