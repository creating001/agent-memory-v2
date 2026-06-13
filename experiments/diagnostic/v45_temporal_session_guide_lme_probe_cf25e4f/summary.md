# v45 Temporal Session Guide 诊断

## 目的

v44 的 temporal-only session guide 在 LongMemEval-S route-stratified 20 条上相对 v42 净增 1 条，但按 full route mix 估算 avg query tokens 超过 6K。v45 只做 token-safe 收窄：仅在 `temporal_lookup` 启用 `session_thread`，并把 row-linked build memory guide 限制为 `max_memory_records=1`。

## 范围

- benchmark：LongMemEval-S
- subset：route_stratified_20
- experiment_kind：diagnostic
- run_id：`v45_temporal_session_guide_lme_probe_cf25e4f`
- config snapshot：`experiments/diagnostic/v45_temporal_session_guide_lme_probe_cf25e4f/config_snapshot.json`
- predictions：`outputs/diagnostic/v45_temporal_session_guide_lme_probe_cf25e4f/predictions.jsonl`
- traces：`outputs/diagnostic/v45_temporal_session_guide_lme_probe_cf25e4f/traces.jsonl`
- DeepSeek judge：`experiments/diagnostic/v45_temporal_session_guide_lme_probe_cf25e4f/deepseek_judge.json`

## Git

- commit：`cf25e4fbf9066f829c74bb4d6063fca2a5502595`
- dirty：是；dirty 内容为用户修改的 `docs/architecture.md`、`docs/clean_protocol.md`，未参与预测逻辑。

## 配置

- 底座：v42 operation workpad。
- 只对 `temporal_lookup` 开启：
  - `context_layout=session_thread`
  - `structured_guide_include_memory=true`
  - `memory_record_source=evidence_rows`
  - `memory_order=question_overlap`
  - `max_memory_records=1`
- answer LLM：`Qwen/Qwen3-30B-A3B-Instruct-2507`
- answer max input/output：`131072/16384`
- workers：`4`
- answer cache：复用 v42 exact-prompt cache；cache hit 仍按 stored usage 计入 logical query tokens。

## 结果

- prediction：20/20 成功。
- DeepSeek judge accuracy：`16/20 = 0.800`。
- v42 same-20 accuracy：`15/20 = 0.750`。
- 相对 v42：gain `1`，loss `0`，answer_changed `1`。
- 修复类型：temporal exact-date；v42 回答 `February 2023`，v45 回答 `2023-02-14`。
- avg_build_tokens：`81690.45`；total_build_tokens：`1633809`。
- avg_query_tokens：`5744.5`；total_query_tokens：`114890`；max_query_tokens：`7352`。
- build cache：hits/misses/writes = `137/0/0`，但 build token 按冷启动逻辑成本计入。
- answer cache：hits/misses/writes = `17/3/3`，但 query token 按 stored usage 计入。
- avg build memory records：`130.95`；avg active records：`117.5`。
- avg compiled memory records：`0.2`；temporal_lookup 上为 `1.0`，其他 route 为 `0`。

## Gate 结论

v45 的质量信号为正：same-20 净增 1 条、无新增错误，且 exact-date case 仍被修复。但按 v42 full route mix 估算：

- base full avg query tokens：`5865.644`
- temporal_lookup probe delta：`+421.25`
- weighted full delta：`+135.6425`
- estimated full avg query tokens：`6001.2865`

该估算略高于 `6000` 主线预算，因此 v45 不进入 LongMemEval-S full。顶层 config 已删除，只保留本诊断目录和 config snapshot。

## Clean 审计

- `prompt_clean_scan.json`：实际 compiled prompt 中 forbidden counts 为 `{}`。
- config note 中出现 `sample id`、`judge output`、`reference answer` 等词，仅用于声明禁止使用，不是预测 prompt 或方法逻辑。
- DeepSeek judge 和 gold labels 只在 prediction 完成后离线读取。

## 后续

下一步不应直接 full。需要设计 v46：去掉 temporal memory guide 或进一步压缩 session-thread 表达，验证 exact-date 收益是否来自 session ordering 而不是额外 typed memory token；若 token 预算仍不稳，应转向 build-side temporal/event memory schema 或 retrieval-side source expansion，而不是继续加长 answer prompt。
