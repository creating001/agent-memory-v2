# formal/stage1_temporal_preference_v4_locomo_nonadv_full_edf05a5_cached

## 目的

用当前 LongMemEval 最优的 v4 temporal/preference clean 方法，在 LoCoMo non-adversarial full 1540 条上做正式验证。该 run 不引入任何 LoCoMo 专门规则，不使用 gold、judge、category、source_sample_id 或样本级反馈进入预测链路。

## 范围

- benchmark: LoCoMo
- subset: non-adversarial full
- samples: 1540
- workers: 8
- config: `configs/stage1_temporal_preference_v4_cached.json`
- prediction input: `outputs/prepare_locomo_non_adversarial/prediction_input.jsonl`
- labels: `outputs/prepare_locomo_non_adversarial/labels.jsonl`
- answer model: `Qwen/Qwen3-30B-A3B-Instruct-2507`
- answer max input: 131072
- answer max output: 16384
- judge model: `deepseek-v4-flash`

## Git

- prediction commit: `edf05a53bf5524ee67baf455ec35f2d82fc24146`
- prediction dirty: false
- judge/evidence dirty: true, only because this experiment directory was newly generated and untracked when offline analysis ran

## 主要结果

- DeepSeek judge accuracy: 1071/1539 = 0.695906
- invalid judge outputs: 1/1540
- invalid-as-wrong accuracy: 1071/1540 = 0.695455
- evidence recall: 0.831380 over 1536 rows with evidence labels
- avg build tokens: 2965.958
- avg query tokens: 4420.572
- total build tokens: 4567575
- total query tokens: 6807681
- judge tokens: 653224

## 分组结果

By category:

- category 1: 178/281 = 0.633452, invalid 1
- category 2: 135/321 = 0.420561
- category 3: 54/96 = 0.562500
- category 4: 704/841 = 0.837099

By route:

- fact_lookup: 821/1017 = 0.807276, invalid 1
- temporal_lookup: 146/338 = 0.431953
- list_count: 70/131 = 0.534351
- profile_preference: 32/49 = 0.653061
- current_state: 2/4 = 0.500000

## 成本与缓存

- build memory enabled: true
- build cache hits/misses/writes: 11779 / 632 / 632
- avg build memory records: 136.723
- avg active build memory records: 125.298
- avg memory hits: 19.835
- avg memory source hits: 22.594
- embedding cache hits/misses/writes: 912989 / 14709 / 14709
- session BM25 applied: 522/1540 = 0.338961
- avg context chars: 13917.845

## 输出

- predictions: `outputs/formal/stage1_temporal_preference_v4_locomo_nonadv_full_edf05a5_cached/predictions.jsonl`
- traces: `outputs/formal/stage1_temporal_preference_v4_locomo_nonadv_full_edf05a5_cached/traces.jsonl`
- metrics: `experiments/formal/stage1_temporal_preference_v4_locomo_nonadv_full_edf05a5_cached/metrics.json`
- manifest: `experiments/formal/stage1_temporal_preference_v4_locomo_nonadv_full_edf05a5_cached/manifest.json`
- judge: `experiments/formal/stage1_temporal_preference_v4_locomo_nonadv_full_edf05a5_cached/deepseek_judge.json`
- evidence recall: `experiments/formal/stage1_temporal_preference_v4_locomo_nonadv_full_edf05a5_cached/evidence_recall.json`

## Clean 说明

- prediction input 不含 gold answer、category、source_sample_id、sample id、qid、row index 或 judge 输出。
- prediction runner 只把 `record_key` 用于写输出对齐，不传入 route、retrieval、compiler、answer。
- build-stage typed memory 只由 raw dialogue 和可见 metadata 构建。
- judge 和 evidence recall 是离线分析结果，不能回流 prediction pipeline。
- 本 run 的方法参考 `docs/method.md` 中 evidence-first、typed memory、source expansion、profile/event 和 temporal organization 思路；具体实现没有迁移旧项目作弊逻辑，也没有写 LoCoMo 样本级规则。
