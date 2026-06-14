# v88 evidence answer detail 诊断

## 目的

在 v83 的 build、retrieval、compiler、answer prompt、answer cache 和 token 设置完全不变的前提下，验证一组零额外 LLM token 的机械 finalizer 是否能减少 answer JSON 已有证据但最终答案过短或未做简单算术的问题。

## Clean 检查

- 预测阶段只读取 question、draft answer 和 answer model 原始 JSON response。
- 不读取 gold answer、judge output、question_type、sample id、row index 或 test feedback。
- 规则来自通用 answer/evidence 形态：count detail、average、money difference、date endpoint duration，不包含具体实体或样本级条件。

## 外部参考与取舍

- 参考 `docs/method.md` 的 evidence-first / query-time evidence compiler / source-preserving verification 方向。
- 只借鉴 `external/creating001-agent-memory` 中 count/list 答案应保留 compact counted items、简单算术应与 structured evidence 对齐的通用思路。
- 没有迁移旧项目的 question_type/sample filter、benchmark 专门 route、样本实体规则或 gold/judge 相关逻辑。
- 没有采用 broad sum/count/duration finalizer，因为历史 v65 证明宽泛机械算术会回退；v88 只打开窄触发条件。

## 诊断结果

- run_id: `stage1_evidence_answer_detail_v88_natural_lme_s_full_diag`
- benchmark/subset: `LongMemEval-S / full`
- prediction changed vs v83: `17/500`
- changed-subset DeepSeek judge: `12/17 = 0.705882`
- controlled transition vs v83 changed subset: `WRONG->CORRECT 3`, `CORRECT->WRONG 0`, `WRONG->WRONG 5`, `CORRECT->CORRECT 9`
- controlled net: `+3`

主要修复：

- money difference: Hawaii vs Tokyo accommodation `$270`
- average: undergraduate/graduate GPA `3.83`
- date endpoint duration: rug usage duration `9 days`

count detail 当前没有稳定净增，但没有造成 changed-subset 回退；医生 count case 在重复 judge 中存在方差，因此不把它计为稳定收益。

## Token 与 cache

- avg_build_tokens: `80346.246`
- avg_query_tokens: `5912.794`
- build_memory_cache_hits/misses: `3341/0`
- answer_cache_hits/misses: `500/0`
- answer_finalizer_applied_count: `45/500`

build/query token 仍按 logical cold-run LLM token 记录；cache hit 只减少本地重复 API 调用，不改变方法的逻辑 token 成本。

## 输出路径

- predictions: `outputs/diagnostic/stage1_evidence_answer_detail_v88_natural_lme_s_full_diag/predictions.jsonl`
- traces: `outputs/diagnostic/stage1_evidence_answer_detail_v88_natural_lme_s_full_diag/traces.jsonl`
- metrics: `experiments/diagnostic/stage1_evidence_answer_detail_v88_natural_lme_s_full_diag/metrics.json`
- changed judge: `experiments/diagnostic/stage1_evidence_answer_detail_v88_natural_lme_s_full_diag/deepseek_judge_changed.json`

## 结论

v88 是 clean、低风险、零额外 LLM token 的小正向候选。它的 controlled net 为 `+3`，不足以单独保证 LongMemEval-S 达到 `0.80`，但值得提交后跑 formal full judge，检查 fresh full 是否达到或接近 `400/500`。
