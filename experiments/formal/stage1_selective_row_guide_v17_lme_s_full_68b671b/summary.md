# stage1_selective_row_guide_v17_lme_s_full_68b671b

## 目的

验证 v17 selective row guide 在 LongMemEval-S full 上的效果。v17 基于 v16 row-guide-only：普通 fact/list/temporal/current/profile 问题继续使用 retrieved raw rows 的 compact row overview；对通用 personalized recommendation 信号关闭 row overview，让回答阶段直接使用 raw Memory Context，避免 row-level overview 干扰偏好/推荐类问题。

该方法是 general 的 profile-safe compiler 设计，不使用 gold answer、judge output、benchmark question_type、sample id、qid、row index 或样本级规则。

## 外部方法借鉴

- LangMem：借鉴 profile/preference memory 与普通事实 memory 分层的思路。
- Mem0：借鉴从用户请求和助手建议中保留偏好/推荐线索的思路。
- Graphiti：借鉴不要把弱单次提及过度固化成稳定偏好的约束。

取舍：本轮只改 query/compiler 侧的通用路由与 guide 开关，不新增重型 graph、reflection 或 query planning，避免额外 query token 和不稳定性。

## 配置

- benchmark: LongMemEval-S
- subset: full
- n_samples: 500
- config: `/data/home_new/wujinqi/agent-memory/configs/stage1_selective_row_guide_v17_cached.json`
- prediction workers: 8
- judge workers: 16
- answer model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer base_url: `http://127.0.0.1:8000/v1`
- answer max input/output: 131072 / 16384
- dense raw-turn retrieval: top-40, external_naive text format
- lexical retrieval: disabled
- temporal aid: enabled
- structured_guide_include_rows: true
- structured_guide_include_memory: false
- structured_guide_disabled_signals: `personalized_recommendation`
- enable_recommendation_profile_patterns: true
- max_memory_records: 0

## Git

- commit: `68b671be00e5882b46834c87a16f2c3481702c1b`
- dirty at prediction: false

## Prediction Metrics

- avg_build_tokens: 80346.246
- build_token_accounting: logical cold-build LLM tokens；cache 命中也按 stored usage 计入方法成本，cache 只减少本机重复 API 调用。
- avg_query_tokens: 5022.590
- avg_compiled_evidence_items: 35.318
- avg_context_chars: 16945.686
- avg_build_memory_records: 129.662
- avg_memory_hits: 8.208
- build_memory_cache: hits 3341, misses 0, writes 0
- structured_guide_prompts: 492/500
- row_index_prompts: 492/500
- activated_build_memory_prompts: 0/500
- temporal_aid_prompts: 198/500
- personalized_recommendation_prompts: 8/500
- personalized_recommendation_with_structured_guide: 0/8
- avg_selected_memory_records: 0.0

## Offline Judge Results

- judge: DeepSeek `deepseek-v4-flash`, prediction 完成后离线使用。
- accuracy: 361/500 = 0.722
- invalid_judgments: 0
- judge_tokens: prompt 78132, completion 38451, total 116583
- evidence_recall: 500/500 = 1.000, diagnostic only.
- token_gate: avg_build_tokens 80346.246 <= 300000；avg_query_tokens 5022.590 <= 6000。

By question type:

- knowledge-update: 62/78 = 0.795
- multi-session: 75/133 = 0.564
- single-session-assistant: 52/56 = 0.929
- single-session-preference: 11/30 = 0.367
- single-session-user: 66/70 = 0.943
- temporal-reasoning: 95/133 = 0.714

Comparisons:

- vs v16 row-guide-only: v17-only 21, v16-only 14, net +7.
- vs v15 source-map-only: net +18.
- vs v14 full structured guide: net +9.
- vs v13 temporal aid: v17-only 33, v13-only 29, net +4.
- vs v12 source expansion: net +4.
- vs clean naive external top-40: net +17.

结论：v17 是当前 LongMemEval-S full 最好结果。主要收益来自 preference/recommendation 类不再无条件吃 row overview，同时保留 row guide 对 fact/list/temporal 的组织能力。temporal-reasoning 从 v16 的 97/133 降到 95/133，但 knowledge-update、multi-session 和 preference 的净收益抵消了回退。

## Outputs

- predictions: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_selective_row_guide_v17_lme_s_full_68b671b/predictions.jsonl`
- traces: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_selective_row_guide_v17_lme_s_full_68b671b/traces.jsonl`
- metrics: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_selective_row_guide_v17_lme_s_full_68b671b/metrics.json`
- judge: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_selective_row_guide_v17_lme_s_full_68b671b/deepseek_judge.json`
- evidence_recall: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_selective_row_guide_v17_lme_s_full_68b671b/evidence_recall.json`
- manifest: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_selective_row_guide_v17_lme_s_full_68b671b/manifest.json`

## Clean Notes

- Prediction loader rejects gold/reference/target answers, judge outputs, benchmark labels, sample ids, qids, and hidden row indices.
- Personalized recommendation signal is derived only from question text by generic route patterns.
- Row guide only reorganizes retrieved raw rows already visible in Memory Context；disabled signal only removes prompt organization, not evidence.
- DeepSeek judge and evidence labels are offline-only diagnostics and must not feed prediction, retrieval, compiler, answer, verifier, or route logic.
