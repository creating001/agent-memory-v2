# stage1_evidence_report_contract_v28_locomo_nonadv_full_ee13e22

## 目的

验证 v28 `evidence_report_contract` 在 LoCoMo non-adversarial full 上的 clean 正式结果。该方法在 answer prompt 中要求模型从已检索的 Memory Context 内部构造简短的 support / exclude / missing 证据报告，再输出最终答案；不使用 gold answer、judge 输出、benchmark 标签、sample id、qid 或离线 evidence。

## 运行范围

- benchmark: LoCoMo
- subset: non-adversarial-full
- samples: 1540
- experiment_kind: formal
- run_id: `stage1_evidence_report_contract_v28_locomo_nonadv_full_ee13e22`
- config: `configs/stage1_evidence_report_contract_v28_cached.json`
- prediction input: `outputs/prepare_locomo_non_adversarial/prediction_input.jsonl`
- labels: `outputs/prepare_locomo_non_adversarial/labels.jsonl`，仅用于离线 judge / evidence recall / badcase 诊断

## Git

- commit: `ee13e22570285cc70e0a429a9f9ade060d8d28fe`
- dirty: false

## 配置摘要

- answer model: `Qwen/Qwen3-30B-A3B-Instruct-2507`
- answer base_url: `http://127.0.0.1:8000/v1`
- answer temperature: 0
- answer max_input_tokens: 131072
- answer max_output_tokens: 16384
- answer timeout: 600
- build memory: enabled，Qwen3 build-stage typed memory
- retrieval: lexical + dense hybrid, `top_k=40`, `dense_protect_top_n=32`, `neighbor_window=0`
- compiler: `external_naive` prompt mode, `structured_guide=true`, `temporal_workpad=true`, `evidence_report_contract=true`

## 主结果

- DeepSeek judge accuracy: 0.7376623377，1136 / 1540
- LoCoMo target: 0.78
- target_met: false
- invalid judgments: 0
- DeepSeek judge tokens: 647530

对比已完成的正式/诊断基线：

- naive RAG: 0.6985055231，1075 / 1540
- v18 hybrid BM25: 0.7370129870，1135 / 1540
- v26 structured answer contract: 0.7298701299，1124 / 1540
- v28 evidence report contract: 0.7376623377，1136 / 1540

v28 在 LoCoMo 上只比 v18 多 1 个正确样本，属于基本持平，不是有效突破；但比 v26 多 12 个正确样本。

## Token 成本

- avg_build_tokens: 58386.0078
- total_build_tokens: 89914452
- avg_query_tokens: 3864.5370
- total_query_tokens: 5951387
- token accounting: build token 是冷启动构建 memory 的逻辑 LLM 成本；cache hit 只避免重复本地 API 调用，不把该方法的冷启动成本记成 0。
- LoCoMo budget: avg build <= 100K，avg query <= 6K
- budget status: within budget

## 离线 evidence recall

- evidence_recall: 0.8893229167，1536 个带 evidence 标签样本
- category 1: 0.8936170213
- category 2: 0.8909657321
- category 3: 0.6739130435
- category 4: 0.9108204518

该指标只用于离线诊断。LoCoMo 标签侧 `evidence` 是数据集给出的评估信息，没有进入 prediction pipeline。

## 输出路径

- predictions: `outputs/formal/stage1_evidence_report_contract_v28_locomo_nonadv_full_ee13e22/predictions.jsonl`
- traces: `outputs/formal/stage1_evidence_report_contract_v28_locomo_nonadv_full_ee13e22/traces.jsonl`
- metrics: `experiments/formal/stage1_evidence_report_contract_v28_locomo_nonadv_full_ee13e22/metrics.json`
- judge: `experiments/formal/stage1_evidence_report_contract_v28_locomo_nonadv_full_ee13e22/deepseek_judge.json`
- evidence recall: `experiments/formal/stage1_evidence_report_contract_v28_locomo_nonadv_full_ee13e22/evidence_recall.json`
- offline comparison: `experiments/formal/stage1_evidence_report_contract_v28_locomo_nonadv_full_ee13e22/offline_comparison.json`

## 结论

v28 是 LME 有效、LoCoMo 基本持平的方法：它提升了 LoCoMo temporal_lookup 和 profile_preference，但损失了一部分 fact_lookup / category 3 反事实类问题。当前统一目标仍未达到，下一阶段应重点解决 LoCoMo 的 source coverage、跨轮上下文组织、相对时间还原和反事实/隐含问题推理，而不是继续只加 answer prompt 约束。
