# 输出目录

`outputs/` 是本地运行产物目录，默认不纳入 git。人工查看实验结论时先看 `experiments/`；这里只保留当前 LTS、split best、关键 baseline 的预测/trace、clean 数据输入和必要缓存。

## 目录职责

- `prepare_longmemeval_s_cleaned/`：LongMemEval-S 的 clean prediction input 和离线 labels。
- `prepare_locomo_non_adversarial/`：LoCoMo non-adversarial 的 clean prediction input 和离线 labels。
- `formal/`：保留正式 full run 的 `predictions.jsonl` 和 `traces.jsonl`，目录名与 `experiments/formal/<run_id>/` 对齐。
- `diagnostic/`：只保留仍有诊断价值的 run 输出，目前主要是 v99 short-answer negative diagnostic。
- `cache/`：只保留近期复现 LTS / split best / 关键 baseline 所需的 embedding、build memory 和主线 answer cache。cache 命中只减少重复 API 调用；实验 token 成本仍按逻辑冷启动记录。若某个保留历史配置指向的旧 answer cache 已清理，正式实验记录仍以 `experiments/` 和 `outputs/formal/` 为准，重新运行会冷启动重填。
- `services/`：本地 vLLM 服务日志和状态文件。

## 清理规则

- 只生成子集输入、没有对应 `experiments/diagnostic/<run_id>/` 的临时目录不长期保留。
- partial judge、临时下载、失败候选的过期 answer/repair/scoped evidence cache 可以删除。
- 删除 cache 前先确认不会影响近期 LTS 复现；embedding cache 和 build memory cache 默认保留。
- 正式汇报不能只依赖 `outputs/`，必须在 `experiments/` 留下 summary、metrics、diagnosis、config snapshot、git 状态、token 成本和 outputs 路径。
