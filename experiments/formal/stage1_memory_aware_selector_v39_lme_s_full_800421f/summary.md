# v39 memory-aware selector LME full

## 结论

v39 是负向 ablation，不进入 LoCoMo full，不作为当前主线保留。

- DeepSeek judge accuracy: `0.724` (`362/500`)
- invalid judgments: `0`
- v36 current best: `0.772` (`386/500`)
- v38 negative baseline: `0.752` (`376/500`)
- v39 vs v36: 净 `-24`
- v39 vs v38: 净 `-14`
- 距 LongMemEval `0.80` baseline target: 差 `38` correct

核心原因：build-memory source signal 用于 list/temporal evidence selection 后，没有带来净收益，反而让 `list_count` 和 `temporal_lookup` 的 evidence order 更容易选错或漏掉关键 operand。v39 保持了 evidence recall `1.0`，但 accuracy 明显下降，说明主要问题不是 gold evidence 是否出现过，而是 selector/context organization/reader 使用证据不稳定。

## Scope

- benchmark: `longmemeval_s`
- subset: `longmemeval_s_full`
- experiment_kind: `formal`
- samples: `500`
- workers: `4`
- input: `outputs/prepare_longmemeval_s_cleaned/prediction_input.jsonl`
- config: `configs/stage1_memory_aware_selector_v39_cached.json`
- run_id: `stage1_memory_aware_selector_v39_lme_s_full_800421f`

## Git

- prediction commit: `800421fcab10338f13c456145f0c38d8ca1a452a`
- prediction dirty: `true`
- dirty files at prediction time: `docs/architecture.md`, `docs/clean_protocol.md`
- 说明：dirty 文件是用户修改的文档；prediction pipeline、config 和代码来自上述 commit。

## Token Cost

| item | value |
|---|---:|
| avg_build_tokens | `80346.246` |
| total_build_tokens | `40173123` |
| avg_query_tokens | `5861.556` |
| total_query_tokens | `2930778` |
| avg_compiled_evidence_items | `34.754` |
| avg_context_chars | `19161.898` |
| avg_compiled_memory_records | `0.0` |
| answer max input/output | `131072/16384` |

Cache 和 build memory：

- build memory cache hits/misses/writes: `3341/0/0`
- embedding cache hits/misses/writes: `247238/0/0`
- answer cache hits/misses/writes: `20/480/480`
- avg build memory records: `129.662`
- avg active build memory records: `116.456`

DeepSeek judge token:

- prompt_tokens: `108739`
- completion_tokens: `38190`
- total_tokens: `146929`

## Accuracy Breakdown

| information_need | correct / n | accuracy |
|---|---:|---:|
| current_state | `12/22` | `0.5455` |
| fact_lookup | `149/183` | `0.8142` |
| list_count | `81/119` | `0.6807` |
| profile_preference | `9/15` | `0.6000` |
| temporal_lookup | `111/161` | `0.6894` |

| question_type | correct / n | accuracy |
|---|---:|---:|
| knowledge-update | `61/78` | `0.7821` |
| multi-session | `76/133` | `0.5714` |
| single-session-assistant | `47/56` | `0.8393` |
| single-session-preference | `13/30` | `0.4333` |
| single-session-user | `66/70` | `0.9429` |
| temporal-reasoning | `99/133` | `0.7444` |

## Outputs

- predictions: `outputs/formal/stage1_memory_aware_selector_v39_lme_s_full_800421f/predictions.jsonl`
- traces: `outputs/formal/stage1_memory_aware_selector_v39_lme_s_full_800421f/traces.jsonl`
- metrics: `experiments/formal/stage1_memory_aware_selector_v39_lme_s_full_800421f/metrics.json`
- manifest: `experiments/formal/stage1_memory_aware_selector_v39_lme_s_full_800421f/manifest.json`
- config snapshot: `experiments/formal/stage1_memory_aware_selector_v39_lme_s_full_800421f/config_snapshot.json`
- DeepSeek judge: `experiments/formal/stage1_memory_aware_selector_v39_lme_s_full_800421f/deepseek_judge.json`
- comparison: `experiments/formal/stage1_memory_aware_selector_v39_lme_s_full_800421f/judge_comparison_vs_v36_v38.json`
- badcase digest: `experiments/formal/stage1_memory_aware_selector_v39_lme_s_full_800421f/badcase_digest.json`
- evidence recall: `experiments/formal/stage1_memory_aware_selector_v39_lme_s_full_800421f/evidence_recall.json`

## Clean Notes

- Prediction 阶段不读取 gold answer、judge output、benchmark label、question_type、category、sample id、row index、qid 或 test feedback。
- `information_need` route 只来自 question text 和可见 question time。
- `memory_aware` selector 只使用 raw dialogue、build-stage memory source links、retrieval rank 和 question text。
- DeepSeek judge、comparison、badcase digest 和 evidence recall 都是离线诊断，不能被 prediction/retrieval/compiler/answer/verifier 读取。
