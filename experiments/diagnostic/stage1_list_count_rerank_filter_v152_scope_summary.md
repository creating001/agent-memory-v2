# v152 List-Count Rerank Filter Scope Summary

## 目的

v152 测试风险 #2：能否在不破坏 clean setting 的前提下，用 rerank 降低 list/count 题的 top-k 噪声和 reader context 成本。

## 方法

- 配置：`configs/stage1_list_count_rerank_filter_v152_qwen36_no_think_build4k_cached.json`。
- 父版本：当前 LTS `v151`。
- 唯一预测侧改动：仅对 `list_count` 启用 Qwen3-Reranker-0.6B tail filter。先取 60 条候选，保留前 32 条 hybrid retrieval anchor，用 rerank 选择尾部候选，最终 reader context 仍保持原 retrieval 顺序并返回 52 条。
- v151 的 build memory、source-backed current-state repair、source-grounded finalizer 和 compiler 主体保持不变。
- Clean 边界：prediction 只使用 question text、raw Memory Context、同会话可见 turn order 和 query 前已经构建的 source-linked build memory；不使用 gold、judge、benchmark 标签、sample id、row id、test feedback 或样本级规则。

## 指标

| Benchmark | changed subset judge | derived full v152 | 成本 |
|---|---:|---:|---|
| LongMemEval-S full | v151 strict/lenient `10/15` / `11/15`；v152 `9/15` / `10/15`；delta `-1/-1` | strict/lenient `410/500` / `416/500` = `0.820000 / 0.832000` | avg query tokens `6164.606`；rerank `119/500`，avg rerank tokens when applied `20669.042`，total rerank tokens `2459616` |
| LoCoMo non-adversarial full | v151 strict/lenient `75/120` / `80/120`；v152 `69/120` / `79/120`；delta `-6/-1` | strict/lenient `1210/1540` / `1255/1540` = `0.785714 / 0.814935` | avg query tokens `5968.031`；rerank `270/1540`，avg rerank tokens when applied `14577.867`，total rerank tokens `3936024` |

## 诊断

- v152 的 query token 有下降，尤其 LoCoMo 从 v151 的 `6047.909` 降到 `5968.031`。
- 但 list/count 是 coverage-sensitive route。tail filter 会把部分枚举支撑行挤出 reader context，表现为少列、多列、裸数字化、或过度拒答。
- rerank 额外 token 较高：LME `2.46M`，LoCoMo `3.94M`。在 accuracy 负向时，这个成本不可接受。

## 决策

v152 不升 LTS。当前 LTS 仍为 v151。

下一步 #2 不应继续做简单 top-k pruning 或 tail compression；更合理的方向是 coverage-preserving context organization：先保留 list/count coverage anchors，再做 entity/session/topic grouping、dedup ledger 和 compact aggregation table，让 rerank 只提供候选标注或优先级，不直接删除覆盖证据。

## Artifacts

- Full prediction traces:
  - `outputs/diagnostic/stage1_list_count_rerank_filter_v152_lme_s_full/`
  - `outputs/diagnostic/stage1_list_count_rerank_filter_v152_locomo_nonadv_full/`
- Changed subset judge:
  - `experiments/diagnostic/stage1_list_count_rerank_filter_v152_lme_changed_vs_v151/`
  - `experiments/diagnostic/stage1_list_count_rerank_filter_v152_locomo_changed_vs_v151/`
- Aggregate:
  - `experiments/diagnostic/stage1_list_count_rerank_filter_v152_results.json`
