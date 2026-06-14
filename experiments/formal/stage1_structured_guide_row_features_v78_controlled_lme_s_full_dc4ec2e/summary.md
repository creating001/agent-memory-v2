# stage1_structured_guide_row_features_v78_controlled_lme_s_full_dc4ec2e

## 结论

v78 controlled LongMemEval-S full 为负向，不进入主线，不跑 LoCoMo。

- DeepSeek judge accuracy: `0.758` (`379/500`)
- v73 baseline: `0.778` (`389/500`)
- delta: `-10` correct
- gain/loss vs v73: `12` / `22`
- answer_changed: `66/500`
- changed-answer gain/loss: `9` / `14`
- evidence_recall: `1.0`
- invalid judgments: `0`

## 方法

基于 v73，只在已有 `Structured Evidence Guide` 里为 question-derived `list_count` / `temporal_lookup` 增加 raw row 的 `quantities` 和 `time_phrases` 短特征。该设计参考 creating001 的 evidence-first query 组织和 SimpleMem structured context，同时吸取 v40/v31/v48 负向经验：不加长 evidence_report 规则，不让 candidate map 替代 raw evidence。

本 run 使用 controlled cache：从 v73 prediction traces seed 旧 prompt answer cache；cache key 包含完整 prompt，因此只有 v78 未改变 prompt 的样本会命中，真正加入 row features 的 prompt 会重新调用 answer LLM。

## Token Cost

| item | value |
|---|---:|
| avg_build_tokens | `80346.246` |
| total_build_tokens | `40173123` |
| avg_query_tokens | `5891.06` |
| total_query_tokens | `2945530` |
| answer max input/output | `131072/16384` |
| answer cache hits/misses/writes | `231/269/269` |
| build cache hits/misses/writes | `3341/0/0` |

## 配置与 Git

- prediction commit: `dc4ec2ef657d381e478a570fee83f9d0d7146ac7`
- prediction dirty: `False`
- config: `configs/stage1_structured_guide_row_features_v78_cached.json`
- row feature needs: `['list_count', 'temporal_lookup']`
- build memory avg records / active: `129.662` / `116.456`

## Outputs

- predictions: `outputs/formal/stage1_structured_guide_row_features_v78_controlled_lme_s_full_dc4ec2e/predictions.jsonl`
- traces: `outputs/formal/stage1_structured_guide_row_features_v78_controlled_lme_s_full_dc4ec2e/traces.jsonl`
- metrics: `experiments/formal/stage1_structured_guide_row_features_v78_controlled_lme_s_full_dc4ec2e/metrics.json`
- judge: `experiments/formal/stage1_structured_guide_row_features_v78_controlled_lme_s_full_dc4ec2e/deepseek_judge.json`
- evidence_recall: `experiments/formal/stage1_structured_guide_row_features_v78_controlled_lme_s_full_dc4ec2e/evidence_recall.json`
- comparison_vs_v73: `experiments/formal/stage1_structured_guide_row_features_v78_controlled_lme_s_full_dc4ec2e/judge_comparison_vs_v73.json`
- delta_badcases: `experiments/formal/stage1_structured_guide_row_features_v78_controlled_lme_s_full_dc4ec2e/delta_badcases.md`
- cache_seed: `experiments/formal/stage1_structured_guide_row_features_v78_controlled_lme_s_full_dc4ec2e/cache_seed.json`
