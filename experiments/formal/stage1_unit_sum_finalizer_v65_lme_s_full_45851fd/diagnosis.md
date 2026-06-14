# Diagnosis for stage1_unit_sum_finalizer_v65_lme_s_full_45851fd

## 结论

负向。v65 的窄机械 finalizer 没有形成可用提升：LongMemEval-S full 为 `379/500 = 0.758000`，低于原 v42 `387/500 = 0.774000`。

## 诊断

- retrieval/evidence recall 仍为 `1.0`，不是召回失败。
- avg_build_tokens `80346.246`，avg_query_tokens `5924.318`，token gate 通过。
- build cache 全命中，answer cache 全命中；token 成本按逻辑 cold build/query 统计。
- finalizer 只 applied `16/500`，但最终 predictions 与原 v42 差 `120` 条。
- 根因是 v65 跑在当前 commit `45851fd`，原 v42 跑在 `f7eb076`，中间 compiler/answer 解析已有漂移；这使 v65 不是纯 finalizer 消融。
- 即使不做纯消融归因，最终 accuracy 也低于 v42，因此直接判定为失败候选。

## 有效信号

少量机械修正确实有局部收益：

- 距离单位：`3000 -> 3,000 miles`
- views 加法：`2,000 -> 1998`
- 一些 temporal / aggregation case 由当前解析漂移改对

但这些收益小于损失，且机械 finalizer 方向容易误触发、增加源码复杂度。

## 失败信号

- gain/loss 为 `20/28`，net `-8`。
- multi-session 损失最多：`CORRECT->WRONG 13`。
- temporal-reasoning 损失也明显：`CORRECT->WRONG 9`。
- 若继续沿机械 finalizer 扩展，很容易变成 fragile rule accumulation，不符合当前“性能优先但不作弊、不写样本级规则”的方法要求。

## 决策

- 不跑 LoCoMo。
- 删除顶层 v65 config。
- 撤掉 v65 finalizer 源码和测试，避免负向代码留在主线里。
- 只保留本 formal 实验目录作为负向记录。
