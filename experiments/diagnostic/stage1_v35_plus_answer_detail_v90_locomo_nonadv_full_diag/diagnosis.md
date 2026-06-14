# v90 v35 plus answer detail 诊断

## 目的

隔离测试 v88 窄 evidence-json finalizer 是否能直接提升 v35 LoCoMo 强底座。v90 保持 v35 的 retrieval、compiler、prompt、answer cache namespace 和 duration format guard，不改 context 组织，只加入 v88 的 missing_detail、count detail、average、money difference 和 date endpoint duration finalizer。

## Clean 检查

- 预测阶段不读取 gold answer、judge output、benchmark category、sample id、row index 或 test feedback。
- 新增 finalizer 只读取 question、draft answer 和 answer model raw JSON response。
- 本次配置文件位于 `/tmp/stage1_v35_plus_answer_detail_v90_cached.json`，因此作为 diagnostic 记录，不作为 formal 主线。

## 结果

- benchmark/subset: `LoCoMo / non-adversarial full`
- DeepSeek judge accuracy: `0.775033`
- valid/correct: `1192/1538`
- invalid judgments: `2`
- avg_build_tokens: `58386.008`
- avg_query_tokens: `4914.036`
- build_memory_cache_hits/misses: `12411/0`
- answer_cache_hits/misses: `11/1529`
- answer_finalizer_applied_count: `30/1540`

相对 v35：`WRONG->CORRECT 47`、`CORRECT->WRONG 57`、`WRONG->INVALID 2`、`INVALID->CORRECT 1`，净 `-10`。

## 结论

v90 低于 v35，不进入主线。LoCoMo 当前问题不能靠 v88 finalizer 直接修复；下一步应回到 v35 badcase，重点分析 evidence organization、answer prompt 稳定性和 LoCoMo category 1/2/4 的回退，而不是继续叠加 query-side finalizer。

## 输出路径

- predictions: `outputs/diagnostic/stage1_v35_plus_answer_detail_v90_locomo_nonadv_full_diag/predictions.jsonl`
- traces: `outputs/diagnostic/stage1_v35_plus_answer_detail_v90_locomo_nonadv_full_diag/traces.jsonl`
- metrics: `experiments/diagnostic/stage1_v35_plus_answer_detail_v90_locomo_nonadv_full_diag/metrics.json`
- judge: `experiments/diagnostic/stage1_v35_plus_answer_detail_v90_locomo_nonadv_full_diag/deepseek_judge.json`
