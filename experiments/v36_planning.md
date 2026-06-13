# v36 LME Token-Safe Format Guard Planning

## 背景

v35 在 LoCoMo non-adversarial full 上达到 valid-only `0.7803768680961664`，但直接用于 LongMemEval-S 的 token gate 失败：

- `v35_lme_route_probe_e6de8c5`
- avg query tokens: `7109.2`
- p95 query tokens: `8059`
- max query tokens: `8371`

因此不能直接跑 LME full。当前 LME 最好仍是 v28：

- `stage1_evidence_report_contract_v28_lme_s_full_9917c22`
- accuracy `0.766`
- avg query tokens `5736.928`
- avg build tokens `80346.246`

## 方法设计

新增 `configs/stage1_lme_token_safe_format_guard_v36_cached.json`：

- build memory 沿用 v28/v35。
- retrieval 回到 v28 top40：
  - retrieval `top_k=40`
  - dense `top_k=40`
  - dense protect `32`
  - compiler `max_evidence_items=40`
  - compiler `max_evidence_chars=18000`
- compiler 沿用 v28 evidence_report contract，不启用 v29/v35 temporal_event_contract。
- answer 使用 v35 的 format guard：
  - robust `json_answer` salvage / cache reparse
  - `enable_duration_rounding_correction=true`
  - answer max input/output `131072/16384`

这不是 benchmark-label route。v36 是通用 token-safe long-context variant：当 long-context task 无法承受 top60 时，使用 top40 evidence budget，并保留 answer formatting bugfix。

## 外部方法借鉴和取舍

- `docs/method.md`：坚持 evidence-first 和 query-time compiler，但必须受 token budget 约束。
- creating001-agent-memory：借鉴最终短答案抽取的重要性，不迁移 benchmark-specific guardrails。
- SimpleMem/Hindsight：借鉴 structured context + final answer stability；v36 不做额外 LLM planner 或多轮 search。

## Gate 计划

先复用 `outputs/diagnostic/v35_lme_route_stratified_probe/prediction_input.jsonl`：

- 20 条 LME-only route-stratified no-label sample。
- 不读取 labels/gold/judge/question_type/sample id。
- 检查 avg query tokens 是否回到 <= 6K。
- 检查 answer max input/output `131072/16384`。
- 检查 build/embedding cache 和 logical build token accounting。

如果 gate 合格，再用 v28 LME full traces 预热 v36 answer cache，并跑 LongMemEval-S full prediction + DeepSeek judge。

## 2026-06-14 Gate 结果

run: `v36_lme_token_safe_probe_e7ca9e5`

- samples: `20`
- source: `outputs/diagnostic/v35_lme_route_stratified_probe/prediction_input.jsonl`
- commit: `e7ca9e5bba5b279592e0a11b9c156025a148ed62`
- dirty: 仅用户修改的 `docs/architecture.md`、`docs/clean_protocol.md`
- answer max input/output: `131072/16384`
- avg build tokens: `81690.45`
- avg query tokens: `5579.7`
- query token distribution: min `4810`, p50 `5484`, p90 `6463`, p95 `6528`, max `6622`
- avg compiled evidence items: `33.9`
- build cache hits/misses/writes: `137/0/0`
- embedding cache hits/misses/writes: `10079/0/0`

结论：v36 通过 LongMemEval-S no-label average query token gate，可以跑 LME full。下一步使用 v28 LME traces 预热 v36 answer cache，然后跑 LongMemEval-S full prediction + DeepSeek judge。

## 2026-06-14 Full 结果

run: `stage1_lme_token_safe_format_guard_v36_lme_s_full_4af3244`

- benchmark/subset: LongMemEval-S full
- samples: `500`
- commit: `4af32444a58fff4e7b86c44906ec7da448a68e7c`
- dirty: 仅用户修改的 `docs/architecture.md`、`docs/clean_protocol.md`
- answer max input/output: `131072/16384`
- avg build tokens: `80346.246`
- total build tokens: `40173123`
- avg query tokens: `5715.468`
- total query tokens: `2857734`
- build cache hits/misses/writes: `3341/0/0`
- embedding cache hits/misses/writes: `247238/0/0`
- answer cache hits/misses/writes: `412/88/88`
- avg build memory records: `129.662`
- avg active build memory records: `116.456`
- avg compiled evidence items: `34.062`
- DeepSeek judge accuracy: `0.772`
- correct/valid/samples: `386/500/500`
- judge invalid: `0`
- judge total tokens: `119844`

对比 v28:

- v28 accuracy: `0.766`, `383/500`
- v36 accuracy: `0.772`, `386/500`
- net: `+3`
- gained/lost: `15/12`
- answer_changed: `24/500`
- changed-answer net: `+2`
- same-answer judge flip net: `+1`

结论：v36 是当前 LME 最好 full formal 结果，且 token 合格；但收益只有 `+3` correct，距 0.80 还差 `14` correct。下一步不能继续做零散 answer formatting，应基于 v36 badcase 和外部方法代码，设计 build/query memory organization 的通用改进。

输出:

- summary: `experiments/formal/stage1_lme_token_safe_format_guard_v36_lme_s_full_4af3244/summary.md`
- diagnosis: `experiments/formal/stage1_lme_token_safe_format_guard_v36_lme_s_full_4af3244/diagnosis.md`
- judge: `experiments/formal/stage1_lme_token_safe_format_guard_v36_lme_s_full_4af3244/deepseek_judge.json`
- comparison: `experiments/formal/stage1_lme_token_safe_format_guard_v36_lme_s_full_4af3244/judge_comparison_vs_v28.json`
- predictions: `outputs/formal/stage1_lme_token_safe_format_guard_v36_lme_s_full_4af3244/predictions.jsonl`
- traces: `outputs/formal/stage1_lme_token_safe_format_guard_v36_lme_s_full_4af3244/traces.jsonl`
