# v48 Candidate Evidence Map 诊断

## 结论

v48 不进入 LongMemEval-S full，也不保留顶层候选配置。

同 87 条 question-derived weak-route 诊断集上，v48 DeepSeek judge accuracy 为 `56/87 = 0.643678`，低于 v42 same-87 的 `59/87 = 0.678161`。净变化 `+6 / -9`，answer changed `32/87`。按 v42 full route mix 估算，full avg query tokens 会到 `6250.456`，超过 6K 主线预算。

v48 的局部正向只出现在 `current_state`：v42 `12/22` -> v48 `14/22`。但 `temporal_lookup`、`profile_preference`、`list_count` 都回退，不能作为全弱路由主线。

## 范围

- run_id: `v48_candidate_map_lme_weakroute_265e07d`
- benchmark: `longmemeval_s`
- subset: `weak_route_87`
- experiment_kind: `diagnostic`
- input: `outputs/diagnostic/v48_lme_weak_route_input/prediction_input.jsonl`
- outputs: `outputs/diagnostic/v48_candidate_map_lme_weakroute_265e07d/`
- experiment dir: `experiments/diagnostic/v48_candidate_map_lme_weakroute_265e07d/`
- workers: `4`

## 方法

底座是 v42 operation workpad。v48 新增 `Candidate Evidence Map`，在 `current_state`、`list_count`、`profile_preference`、`temporal_lookup` 上把已召回 raw rows 压成短候选图：

- Memory 局部编号
- date / role
- matched question terms
- quantity mentions
- time phrase mentions
- query-focused snippet

该 map 只作为 Memory Context 的索引，不是独立事实源。

## Git

- commit: `265e07d`
- dirty: `true`
- dirty note: 运行时用户修改的 `docs/architecture.md`、`docs/clean_protocol.md` 未纳入本次方法代码；v48 诊断目录为新增 artifact。

## 预测指标

- n_samples: `87`
- avg_build_tokens: `80991.862069`
- total_build_tokens: `7046292`
- avg_query_tokens: `6618.068966`
- total_query_tokens: `575772`
- answer max input/output: `131072 / 16384`
- build cache hits/misses/writes: `585 / 0 / 0`
- answer cache hits/misses/writes: `0 / 87 / 87`
- avg_build_memory_records: `130.988506`
- avg_active_build_memory_records: `117.413793`
- avg_compiled_evidence_items: `33.919540`
- avg_context_chars: `22129.908046`
- answer_finalizer_applied_count: `0`

Token 口径：build tokens 是新环境冷构建 memory 的逻辑 LLM token，即使本机 cache 命中，也按 cached usage 计入方法成本；query tokens 是 answer/query LLM token。

## Judge 结果

- current accuracy: `0.643678` (`56/87`)
- v42 same-87 accuracy: `0.678161` (`59/87`)
- gain/loss: `6 / 9`
- same correct / same wrong: `50 / 22`
- answer changed: `32`
- DeepSeek judge usage: `22806` total tokens

按 information_need：

- current_state: v42 `12/22` -> v48 `14/22`
- list_count: v42 `15/20` -> v48 `14/20`
- profile_preference: v42 `10/15` -> v48 `8/15`
- temporal_lookup: v42 `22/30` -> v48 `20/30`

## Token Gate

文件：`full_query_token_estimate.json`

- v42 full avg query tokens: `5865.644`
- weighted full avg delta: `+384.812`
- estimated full avg query tokens: `6250.456`
- budget pass: `false`

即使 current_state 有局部正向，全弱路由开启 candidate map 也超预算，不能 full。

## Clean 检查

- 诊断输入按 clean `QuestionRouter` 和 question text 稳定 hash 分层采样，不按 gold/judge/question_type 选样本。
- prediction pipeline 未使用 gold/reference answer、judge output、benchmark label、sample id、qid、row index 或 test feedback。
- prompt clean scan findings: `0`
- judge、gold 和 benchmark question_type 只在预测完成后用于离线比较。

## 输出文件

- `metrics.json`
- `deepseek_judge.json`
- `judge_comparison_vs_v42_same87.json`
- `full_query_token_estimate.json`
- `prompt_clean_scan.json`
- `config_snapshot.json`
- predictions: `outputs/diagnostic/v48_candidate_map_lme_weakroute_265e07d/predictions.jsonl`
- traces: `outputs/diagnostic/v48_candidate_map_lme_weakroute_265e07d/traces.jsonl`

顶层候选配置 `configs/stage1_candidate_evidence_map_v48_cached.json` 已删除，只保留本目录 `config_snapshot.json` 供复盘。

## 下一步

不要把 Candidate Evidence Map 扩到全部弱 route。下一步只保留它在 `current_state` 上的局部正向，设计 v49 current-state-only/token-safe 版本；同时进一步压缩 max rows/snippet，先 gate 再决定是否 full。
