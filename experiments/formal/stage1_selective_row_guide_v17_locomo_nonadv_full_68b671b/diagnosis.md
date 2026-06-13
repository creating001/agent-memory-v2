# Diagnosis for stage1_selective_row_guide_v17_locomo_nonadv_full_68b671b

## 结论

v17 在 LoCoMo non-adversarial full 上为 1110/1540 = 0.720779。该结果高于 v12/naive，但低于 v16、v14 和略低于 v13；因此 v17 不能作为 LoCoMo 主线，只能作为 LME-positive 方法的 cross-benchmark 验证。

## 关键观察

- prediction gate 通过：1540/1540 predictions 和 traces 完整。
- commit：`68b671b`；dirty 只来自未提交的 LME v17 实验目录。
- token gate 通过：avg_build_tokens 58386.008，avg_query_tokens 3303.915。
- answer max input/output 正确：131072 / 16384。
- build cache 全命中：hits 12411，misses 0；但 avg_build_tokens 按 logical cold-build cost 计入。
- structured guide 触发 1540/1540，row_index 1540/1540，activated memory source map 0/1540。
- personalized_recommendation 触发 0/1540，所以 v17 的 selective 逻辑没有真正改变 LoCoMo prompt 形态。
- evidence recall 为 0.871745，与 v16/v14 一致；瓶颈主要在证据组织/答案使用，而不是 gold evidence 是否进入 trace。

## 错误与收益形态

- category 2 为 188/321，低于 v14 的 195/321，但略高于 v16 的 186/321。
- category 4 为 682/841，低于 v16 的 691/841 和 v14 的 696/841，是本轮主要回退来源。
- 与 v16 相比净 -14；与 v14 相比净 -23；与 v13 相比净 -1。
- 尽管配置上 LoCoMo 没触发 v17 新 signal，prediction 字符串与 v16 有 345 条差异，说明当前 answer 服务温度 0 不等价于完全可复现。

## 下一步

- LoCoMo 主线仍应以 v14 为当前最好方法。
- 设计 v18 前先分析 v14/v17 的正负样本差异，重点看 typed memory source map 何时帮助 category 2/3/4。
- 优先考虑 general hybrid retrieval 或 selective source-map/source expansion；避免写 category/sample 级规则。
