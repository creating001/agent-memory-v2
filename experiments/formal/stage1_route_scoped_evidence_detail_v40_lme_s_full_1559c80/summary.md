# v40 route-scoped evidence detail LME full

## 结论

v40 是负向 ablation，不进入 LoCoMo full，不作为当前主线保留。

- DeepSeek judge accuracy: `0.742` (`371/500`)
- invalid judgments: `0`
- v36 current best: `0.772` (`386/500`)
- v39 negative baseline: `0.724` (`362/500`)
- v40 vs v36: 净 `-15`
- v40 vs v39: 净 `+9`
- 距 LongMemEval `0.80` baseline target: 差 `29` correct

核心判断：route-scoped detailed evidence_report 对 `list_count` 有一定恢复，但仍损伤 `temporal_lookup`、`list_count` 和 `current_state`，整体低于 v36。evidence recall 仍为 `1.0`，说明瓶颈不是 gold evidence 是否进入 context，而是 answer 阶段如何可靠组织和使用证据。

## Scope

- benchmark: `longmemeval_s`
- subset: `longmemeval_s_full`
- experiment_kind: `formal`
- samples: `500`
- workers: `4`
- input: `outputs/prepare_longmemeval_s_cleaned/prediction_input.jsonl`
- config at run time: `configs/stage1_route_scoped_evidence_detail_v40_cached.json`
- config snapshot: `experiments/formal/stage1_route_scoped_evidence_detail_v40_lme_s_full_1559c80/config_snapshot.json`
- run_id: `stage1_route_scoped_evidence_detail_v40_lme_s_full_1559c80`

## Git

- prediction commit: `1559c80d278bad9da8249171f5ea38416056c907`
- prediction dirty: `true`
- dirty files at prediction time: `docs/architecture.md`, `docs/clean_protocol.md`
- 说明：dirty 文件是用户修改的文档；prediction pipeline、config 和代码来自上述 commit。

## Token Cost

| item | value |
|---|---:|
| avg_build_tokens | `80346.246` |
| total_build_tokens | `40173123` |
| avg_query_tokens | `5910.438` |
| total_query_tokens | `2955219` |
| max_query_tokens | `8776` |
| query_tokens > 8000 | `2` |
| avg_compiled_evidence_items | `34.062` |
| avg_context_chars | `19789.358` |
| avg_compiled_memory_records | `0.0` |
| answer max input/output | `131072/16384` |

Cache 和 build memory：

- build memory cache hits/misses/writes: `3341/0/0`
- embedding cache hits/misses/writes: `247238/0/0`
- answer cache hits/misses/writes: `20/480/480`
- avg build memory records: `129.662`
- avg active build memory records: `116.456`

DeepSeek judge token:

- prompt_tokens: `78152`
- completion_tokens: `43064`
- total_tokens: `121216`

## Accuracy Breakdown

| information_need | correct / n | accuracy |
|---|---:|---:|
| current_state | `12/22` | `0.5455` |
| fact_lookup | `146/183` | `0.7978` |
| list_count | `90/119` | `0.7563` |
| profile_preference | `9/15` | `0.6000` |
| temporal_lookup | `114/161` | `0.7081` |

| question_type | correct / n | accuracy |
|---|---:|---:|
| knowledge-update | `63/78` | `0.8077` |
| multi-session | `79/133` | `0.5940` |
| single-session-assistant | `52/56` | `0.9286` |
| single-session-preference | `11/30` | `0.3667` |
| single-session-user | `66/70` | `0.9429` |
| temporal-reasoning | `100/133` | `0.7519` |

## Route Audit

| information_need | n | avg query tokens | p90 query tokens | max query tokens | avg rows | detail prompts |
|---|---:|---:|---:|---:|---:|---:|
| current_state | 22 | 6191.682 | 6637 | 7138 | 33.773 | 0/22 |
| fact_lookup | 183 | 5359.978 | 5789 | 6873 | 34.262 | 0/183 |
| list_count | 119 | 5817.118 | 6165 | 6873 | 32.807 | 119/119 |
| profile_preference | 15 | 5139.533 | 5575 | 5784 | 35.800 | 0/15 |
| temporal_lookup | 161 | 6638.484 | 7390 | 8776 | 34.640 | 161/161 |

Clean prompt scan：

- `question_type` / `sample_id` / `qid` / `row index` / `gold answer` / `judge output`: `0`
- v40 detail rule does not contain the word `category`; remaining raw-context occurrences are user dialogue text.

## Comparison

vs v36:

- both_correct: `349`
- both_wrong: `92`
- gained: `22`
- lost: `37`
- delta_correct: `-15`
- lost_by_information_need: `temporal_lookup 13`, `list_count 10`, `fact_lookup 10`, `current_state 4`
- gained_by_information_need: `fact_lookup 9`, `temporal_lookup 7`, `list_count 4`, `current_state 1`, `profile_preference 1`

vs v39:

- both_correct: `334`
- both_wrong: `101`
- gained: `37`
- lost: `28`
- delta_correct: `+9`

## Outputs

- predictions: `outputs/formal/stage1_route_scoped_evidence_detail_v40_lme_s_full_1559c80/predictions.jsonl`
- traces: `outputs/formal/stage1_route_scoped_evidence_detail_v40_lme_s_full_1559c80/traces.jsonl`
- metrics: `experiments/formal/stage1_route_scoped_evidence_detail_v40_lme_s_full_1559c80/metrics.json`
- judge metrics summary: `experiments/formal/stage1_route_scoped_evidence_detail_v40_lme_s_full_1559c80/judge_metrics_summary.json`
- manifest: `experiments/formal/stage1_route_scoped_evidence_detail_v40_lme_s_full_1559c80/manifest.json`
- config snapshot: `experiments/formal/stage1_route_scoped_evidence_detail_v40_lme_s_full_1559c80/config_snapshot.json`
- DeepSeek judge: `experiments/formal/stage1_route_scoped_evidence_detail_v40_lme_s_full_1559c80/deepseek_judge.json`
- comparison: `experiments/formal/stage1_route_scoped_evidence_detail_v40_lme_s_full_1559c80/judge_comparison_vs_v36_v39_v38.json`
- badcase digest: `experiments/formal/stage1_route_scoped_evidence_detail_v40_lme_s_full_1559c80/badcase_digest.json`
- evidence recall: `experiments/formal/stage1_route_scoped_evidence_detail_v40_lme_s_full_1559c80/evidence_recall.json`

## Clean Notes

- Prediction 阶段不读取 gold answer、judge output、benchmark label、question_type、category、sample id、row index、qid 或 test feedback。
- `information_need` route 只来自 question text 和可见 question time。
- `evidence_report_detail` 只通过 question-derived route 对 `list_count` / `temporal_lookup` 生效。
- DeepSeek judge、comparison、badcase digest 和 evidence recall 都是离线诊断，不能被 prediction/retrieval/compiler/answer/verifier 读取。
