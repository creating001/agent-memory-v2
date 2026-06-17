# Dual judge 正式口径重算记录

- 时间：2026-06-17
- 性质：judge-only reassessment；复用已完成 prediction，不重新运行 build/query。
- 新口径：每个正式结果同时使用 `deepseek-v4-flash` 和 `deepseek-v4-pro` 离线 judge。
- `strict_accuracy`：两个 judge 都判为 `CORRECT` 才算正确。
- `lenient_accuracy`：任一 judge 判为 `CORRECT` 即算正确。
- clean 说明：dual judge 只在预测完成后读取 gold labels；不得进入 prediction、retrieval、compiler、answer、verifier 或 cache build。

## 主仓库 LTS v102

算法：`configs/stage1_spacing_profile_v102_cached.json`

| benchmark | flash accuracy | pro accuracy | strict accuracy | lenient accuracy | judge agreement | n |
|---|---:|---:|---:|---:|---:|---:|
| LongMemEval-S full | 0.800000 | 0.778000 | 0.772000 | 0.806000 | 0.966000 | 500 |
| LoCoMo non-adversarial full | 0.800000 | 0.798701 | 0.775974 | 0.822727 | 0.953247 | 1540 |

输出：

- LME dual judge：`experiments/formal/stage1_spacing_profile_v102_lme_s_full_f844921/deepseek_dual_judge.json`
- LoCoMo dual judge：`experiments/formal/stage1_spacing_profile_v102_locomo_nonadv_full_f844921/deepseek_dual_judge.json`

## Qwen3.6 no-thinking V102 embedding 对比

这些结果在 `/data/home_new/wujinqi/agent-memory-other` 中，算法保持 V102，answer backbone 为 Qwen3.6 no-thinking，build 为 4k+20；只改变 embedding 模型。

| embedding | benchmark | flash accuracy | pro accuracy | strict accuracy | lenient accuracy | judge agreement | n |
|---|---|---:|---:|---:|---:|---:|---:|
| Qwen3-Embedding-0.6B | LME | 0.836000 | 0.814000 | 0.806000 | 0.844000 | 0.962000 | 500 |
| Qwen3-Embedding-0.6B | LoCoMo | 0.807143 | 0.804418 | 0.787662 | 0.823377 | 0.964912 | 1540 |
| Qwen3-Embedding-8B | LME | 0.848000 | 0.834000 | 0.820000 | 0.862000 | 0.958000 | 500 |
| Qwen3-Embedding-8B | LoCoMo | 0.798701 | 0.798959 | 0.779870 | 0.816234 | 0.965517 | 1540 |
| KaLM-Embedding-Gemma3-12B | LME | 0.814000 | 0.804000 | 0.794000 | 0.824000 | 0.970000 | 500 |
| KaLM-Embedding-Gemma3-12B | LoCoMo | 0.808442 | 0.809617 | 0.789610 | 0.827922 | 0.962313 | 1540 |

诊断：

- LME 上 Qwen3-Embedding-8B 最强：strict 0.820000，lenient 0.862000。
- LoCoMo 上 KaLM lenient 最高 0.827922，strict 也略高于 0.6B；但差距很小。
- Qwen3-Embedding-0.6B 仍然是速度/成本更稳的默认选择；如果只追 LME 分数，8B embedding 更有吸引力。

## 其他 backbone 诊断

这些不是完全同一算法配置，只作为历史 backbone 诊断参考。

| config | benchmark | flash accuracy | pro accuracy | strict accuracy | lenient accuracy | judge agreement | n |
|---|---|---:|---:|---:|---:|---:|---:|
| Qwen3.6 default-thinking v98 diagnostic | LME | 0.852000 | 0.848000 | 0.830000 | 0.870000 | 0.960000 | 500 |
| Qwen3.6 default-thinking v98 diagnostic | LoCoMo | 0.819363 | 0.826511 | 0.803247 | 0.841558 | 0.962289 | 1540 |
| GPT-4.1-mini v42 diagnostic | LME | 0.816000 | 0.804000 | 0.794000 | 0.826000 | 0.968000 | 500 |

说明：

- GPT-4.1-mini 目录当前只有完整 LME prediction/judge，未发现完整 LoCoMo prediction，因此未重算 GPT LoCoMo。
- Qwen3.6 default-thinking v98 分数较强，但它不是当前主仓库 LTS V102 配置，不能直接替代 V102 的正式成绩。

## 输出路径

- Qwen3.6 0.6B LME：`/data/home_new/wujinqi/agent-memory-other/experiments/formal/stage1_spacing_profile_v102_qwen36_no_think_build4k_lme_s_full/deepseek_dual_judge.json`
- Qwen3.6 0.6B LoCoMo：`/data/home_new/wujinqi/agent-memory-other/experiments/formal/stage1_spacing_profile_v102_qwen36_no_think_build4k_locomo_nonadv_full/deepseek_dual_judge.json`
- Qwen3.6 8B LME：`/data/home_new/wujinqi/agent-memory-other/experiments/formal/stage1_spacing_profile_v102_qwen36_no_think_build4k_qwen3emb8b_lme_s_full/deepseek_dual_judge.json`
- Qwen3.6 8B LoCoMo：`/data/home_new/wujinqi/agent-memory-other/experiments/formal/stage1_spacing_profile_v102_qwen36_no_think_build4k_qwen3emb8b_locomo_nonadv_full/deepseek_dual_judge.json`
- Qwen3.6 KaLM LME：`/data/home_new/wujinqi/agent-memory-other/experiments/formal/stage1_spacing_profile_v102_qwen36_no_think_build4k_kalm_lme_s_full/deepseek_dual_judge.json`
- Qwen3.6 KaLM LoCoMo：`/data/home_new/wujinqi/agent-memory-other/experiments/formal/stage1_spacing_profile_v102_qwen36_no_think_build4k_kalm_locomo_nonadv_full/deepseek_dual_judge.json`
- Qwen3.6 default-thinking LME：`/data/home_new/wujinqi/agent-memory-other/experiments/formal/stage1_granularity_adaptive_v98_qwen36_35b_build16k_lme_s_full/deepseek_dual_judge.json`
- Qwen3.6 default-thinking LoCoMo：`/data/home_new/wujinqi/agent-memory-other/experiments/formal/stage1_granularity_adaptive_v98_qwen36_35b_locomo_build32k_locomo_nonadv_full/deepseek_dual_judge.json`
- GPT-4.1-mini LME：`/data/home_new/wujinqi/agent-memory-gpt/experiments/formal/stage1_operation_workpad_v42_gpt41mini_build16k_lme_s_full_w8_retry/deepseek_dual_judge.json`

## Judge token 成本

本次是 judge-only reassessment，build/query token 沿用原 prediction 记录；下面只统计本次 dual judge 的 API token 成本。

| result | flash judge tokens | pro judge tokens | total judge tokens |
|---|---:|---:|---:|
| main LTS v102 LME | 116682 | 157841 | 274523 |
| main LTS v102 LoCoMo | 649050 | 761827 | 1410877 |
| Qwen3.6 0.6B LME | 157460 | 205116 | 362576 |
| Qwen3.6 0.6B LoCoMo | 728169 | 843498 | 1571667 |
| Qwen3.6 8B LME | 186148 | 226922 | 413070 |
| Qwen3.6 8B LoCoMo | 745610 | 863617 | 1609227 |
| Qwen3.6 KaLM LME | 137253 | 176640 | 313893 |
| Qwen3.6 KaLM LoCoMo | 793431 | 900765 | 1694196 |
| Qwen3.6 thinking v98 LME | 117222 | 155361 | 272583 |
| Qwen3.6 thinking v98 LoCoMo | 670638 | 776815 | 1447453 |
| GPT-4.1-mini v42 LME | 128193 | 169502 | 297695 |
