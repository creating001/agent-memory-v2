# v46 Temporal Session Thread 诊断

## 目的

v46 是 v45 的直接消融：保留 temporal route 的 `session_thread` raw evidence layout，关闭 typed memory guide，验证 v45 的 exact-date 收益是否来自同一 session 的原始顺序组织。

## 范围

- benchmark：LongMemEval-S
- subset：route_stratified_20
- experiment_kind：diagnostic
- run_id：`v46_temporal_session_thread_lme_probe_eb90c24`
- config snapshot：`experiments/diagnostic/v46_temporal_session_thread_lme_probe_eb90c24/config_snapshot.json`
- predictions：`outputs/diagnostic/v46_temporal_session_thread_lme_probe_eb90c24/predictions.jsonl`
- traces：`outputs/diagnostic/v46_temporal_session_thread_lme_probe_eb90c24/traces.jsonl`
- DeepSeek judge：`experiments/diagnostic/v46_temporal_session_thread_lme_probe_eb90c24/deepseek_judge.json`

## Git

- commit：`eb90c241ef65964c0b2efff9f5e6d19c9d4a37ac`
- dirty：是；dirty 内容为用户修改的 `docs/architecture.md`、`docs/clean_protocol.md`，未参与预测逻辑。

## 配置

- 底座：v42 operation workpad。
- 只对 `temporal_lookup` 开启：
  - `context_layout=session_thread`
  - `structured_guide_include_memory=false`
  - `max_memory_records=0`
- answer LLM：`Qwen/Qwen3-30B-A3B-Instruct-2507`
- answer max input/output：`131072/16384`
- workers：`4`
- answer cache：复用 v42 exact-prompt cache；cache hit 仍按 stored usage 计入 logical query tokens。

## 结果

- prediction：20/20 成功。
- DeepSeek judge accuracy：`15/20 = 0.750`。
- v42 same-20 accuracy：`15/20 = 0.750`。
- 相对 v42 raw judge：gain `1`，loss `1`，answer_changed `1`。
- changed-answer delta：唯一变化是 temporal exact-date；v42 回答 `February 2023`，v46 回答 `February 14, 2023`，judge 判为 correct。
- raw judge loss 是 same-answer variance：photography recommendation 的 v42/v46 answer 完全相同，但 v42 judge 为 correct、v46 judge 为 wrong。
- avg_build_tokens：`81690.45`；total_build_tokens：`1633809`。
- avg_query_tokens：`5722.5`；total_query_tokens：`114450`；max_query_tokens：`7274`。
- build cache：hits/misses/writes = `137/0/0`，但 build token 按冷启动逻辑成本计入。
- answer cache：hits/misses/writes = `16/4/4`，但 query token 按 stored usage 计入。
- avg build memory records：`130.95`；avg active records：`117.5`。
- avg compiled memory records：`0.0`。

## Gate 结论

v46 的 token gate 通过：

- base full avg query tokens：`5865.644`
- temporal_lookup probe delta：`+311.25`
- weighted full delta：`+100.2225`
- estimated full avg query tokens：`5965.8665`

但 strict DeepSeek same-20 没有净增，raw accuracy 与 v42 持平。虽然 changed-answer 分析显示没有预测级 regression，且唯一改变修复了 exact-date case，但按 accuracy-first gate 不能直接进入 LongMemEval-S full。

## Clean 审计

- `prompt_clean_scan.json`：实际 compiled prompt 中 forbidden counts 为 `{}`。
- `route_feature_audit.json`：session_thread 只在 `temporal_lookup` 生效；memory guide 和 compiled memory records 全部为 `0`。
- DeepSeek judge 和 gold labels 只在 prediction 完成后离线读取。

## 后续

v46 证明 session ordering 是有效线索，但 20 条 gate 不足以支撑 full。下一步不要继续加 prompt；应做更有信息量的 temporal-only 诊断或转向 build-side temporal/event memory，让 answer 阶段获得更明确的 event-time 表达，同时保持 query token 低于 6K。
