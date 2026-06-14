# v49 Current-State Candidate Map 诊断

## 目的

v48 Candidate Evidence Map 在弱路由整体失败，但 current_state 子集有局部正向。因此 v49 只在 question-derived `current_state` route 上打开一个短 Candidate Evidence Map，验证它是否值得扩展到 LongMemEval-S full。

方法参考：

- xMemory：借鉴 candidate 到 raw message 的回链思想。
- SimpleMem：借鉴多视角 structured context，但不引入 LLM planner。
- Graphiti/Zep：借鉴当前状态需要时间和 provenance 对比。
- Memobase/MIRIX：借鉴 state/profile 与 event 分开管理的思路。

舍弃部分：不做 benchmark 专门规则，不读取 gold/judge/question_type/sample id，不让 candidate map 直接替代 raw evidence。

## 范围

- benchmark: LongMemEval-S
- subset: question-derived current_state 全量 22 条
- experiment_kind: diagnostic
- run_id: `v49_current_state_candidate_map_lme_5993d30`
- commit: `5993d30808d9ce124f7e19ef43e1c77342575fc5`
- dirty: True。运行时存在用户修改的 `docs/architecture.md`、`docs/clean_protocol.md`，以及本实验新生成目录。
- workers: 4
- answer model: `Qwen/Qwen3-30B-A3B-Instruct-2507`
- answer max input/output: `131072 / 16384`

实际运行配置已保存在本目录 `config_snapshot.json`。顶层 v49 config 在诊断后删除，不作为长期候选配置保留。

## 主要结果

- DeepSeek judge accuracy: `13/22 = 0.590909`
- v42 same-22 baseline: `12/22 = 0.545455`
- gain/loss: `3/2`，净 `+1`
- answer_changed: `12/22`
- avg_build_tokens: `79065.818182`
- avg_query_tokens: `6628.409091`
- build cache: hits `143`，misses `0`，writes `0`
- answer cache: hits `0`，misses `22`，writes `22`
- prompt clean scan: `0` findings
- full query token estimate: `5884.492`，低于 6K 预算

token 口径：build tokens 是冷启动构建 memory 的逻辑 LLM token，即使本机 cache 命中也按缓存 usage 计入方法成本；query tokens 同理按实际 answer 调用 usage 统计。

## 结论

v49 不扩 LongMemEval-S full。虽然 same-22 净 `+1` 且 full token 估计过预算 gate，但收益太小、answer_changed 过多，并且两个 loss 都是有代表性的 temporal/order regression。这个结果只能说明短 candidate map 对部分当前状态问题有帮助，不能作为主线方法。

后续方向不应继续堆 reader-side prompt，而应转向更 general 的 build-side memory management：构建可追溯的 temporal state / event / profile typed view，用它们做 retrieval 和 compiler 组织线索，同时保留 raw evidence 回查。

## 文件

- predictions: `outputs/diagnostic/v49_current_state_candidate_map_lme_5993d30/predictions.jsonl`
- traces: `outputs/diagnostic/v49_current_state_candidate_map_lme_5993d30/traces.jsonl`
- metrics: `experiments/diagnostic/v49_current_state_candidate_map_lme_5993d30/metrics.json`
- judge: `experiments/diagnostic/v49_current_state_candidate_map_lme_5993d30/deepseek_judge.json`
- comparison: `experiments/diagnostic/v49_current_state_candidate_map_lme_5993d30/judge_comparison_vs_v42_same22.json`
- token estimate: `experiments/diagnostic/v49_current_state_candidate_map_lme_5993d30/full_query_token_estimate.json`
- prompt scan: `experiments/diagnostic/v49_current_state_candidate_map_lme_5993d30/prompt_clean_scan.json`
