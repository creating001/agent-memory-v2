# stage1_profile_memory_contract_v24_lme_s_full_bc7983d

## 目的

验证在 v18 hybrid BM25+dense 主线之上，仅对 question-text router 判定为 `profile_preference` 的请求重新启用 source-linked build-stage typed memory guide，并加入个性化推荐题的偏好约束式回答契约，是否能提升 LongMemEval-S full accuracy。

## 方法

- 基线：`configs/stage1_hybrid_bm25_v18_cached.json`
- 本轮配置：`configs/stage1_profile_memory_contract_v24_cached.json`
- 改动范围：只改变 `profile_preference` prompt；非 profile prompt 与 v18 完全一致。
- build 阶段：继续使用本地 Qwen 从 raw dialogue 构建 typed memory，cache hit 仍按 cached usage 计入 build tokens。
- query 阶段：不新增 LLM 调用，不改 retrieval top-k，不改 answer max input/output。
- 借鉴：LangMem 的 profile/collection 分层、Mem0 的 preference memory 个性化、SimpleMem 的 structured memory entry。
- clean 约束：不使用 gold、judge、benchmark label、sample id、qid、row index 或测试反馈。

## 范围

- benchmark：LongMemEval-S
- subset：full
- samples：500
- workers：8
- answer model：`Qwen/Qwen3-30B-A3B-Instruct-2507`
- answer max input：131072
- answer max output：16384
- judge：`deepseek-v4-flash`

## Git

- prediction commit：`bc7983d3ded910fef695dd1c59a9cd5835c42e50`
- prediction dirty：false
- evidence recall 和 judge 均为预测完成后的离线诊断，不进入预测链路。

## 主指标

- DeepSeek judge accuracy：0.714, 357/500
- v18 baseline accuracy：0.732, 366/500
- 相对 v18：fixed 15, hurt 24, net -9
- 结论：v24 full accuracy 负向，不跑 LoCoMo full，不作为主线配置保留。

## 分题型

| type | v18 | v24 | delta |
|---|---:|---:|---:|
| knowledge-update | 64/78 | 62/78 | -2 |
| multi-session | 74/133 | 70/133 | -4 |
| single-session-assistant | 52/56 | 52/56 | 0 |
| single-session-preference | 11/30 | 13/30 | +2 |
| single-session-user | 66/70 | 64/70 | -2 |
| temporal-reasoning | 99/133 | 96/133 | -3 |

## Token 成本

- avg_build_tokens：80346.246
- total_build_tokens：40173123
- avg_query_tokens：5133.588
- total_query_tokens：2566794
- avg_context_chars：17608.414
- build cache：hits 3341, misses 0, writes 0
- judge total_tokens：119726

## 诊断

- evidence recall：1.0，分题型也均为 1.0。
- prompt_changed_total：15/500；prompt_changed_nonprofile：0。
- v24 只改动 profile route，但 full-run 非 profile 仍出现 fixed/hurt 波动；正式 full accuracy 低于 v18，不能作为主线。
- 局部信号：single-session-preference 从 11/30 提到 13/30，说明 profile/preference memory contract 方向可能有价值。
- 主要问题：局部收益太小，且没有带来可稳定验证的 full benchmark 提升。

## 输出

- predictions：`outputs/formal/stage1_profile_memory_contract_v24_lme_s_full_bc7983d/predictions.jsonl`
- traces：`outputs/formal/stage1_profile_memory_contract_v24_lme_s_full_bc7983d/traces.jsonl`
- metrics：`experiments/formal/stage1_profile_memory_contract_v24_lme_s_full_bc7983d/metrics.json`
- manifest：`experiments/formal/stage1_profile_memory_contract_v24_lme_s_full_bc7983d/manifest.json`
- evidence recall：`experiments/formal/stage1_profile_memory_contract_v24_lme_s_full_bc7983d/evidence_recall.json`
- judge：`experiments/formal/stage1_profile_memory_contract_v24_lme_s_full_bc7983d/deepseek_judge.json`

## 下一步

- 不保留 v24 作为主线配置。
- 可以把 preference 局部 +2 作为后续线索，但下一轮必须让 full accuracy 明确超过 v18。
- 更优先的方向是减少 answer nondeterminism / 建立 prompt-keyed answer cache，或做 build-stage profile/event 管理改进，而不是继续扩大 prompt 规则。
