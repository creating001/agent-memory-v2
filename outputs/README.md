# 输出目录

`outputs/` 只保留当前仍有用的运行产物和本地缓存。预测文件、trace、日志和中间产物不能替代 `experiments/` 下的人类可读记录。

## 当前保留

- `prepare_longmemeval_s_cleaned/`：LongMemEval-S clean prediction input 和离线 labels。
- `prepare_locomo_non_adversarial/`：LoCoMo non-adversarial prediction input 和离线 labels。
- `formal/`：只保留 `experiments/README.md` 中列出的 key full runs 的 `predictions.jsonl` 和 `traces.jsonl`。
- `cache/qwen3_embedding.sqlite`：embedding cache，保留以减少全量实验重复成本。
- `cache/qwen3_build_memory.sqlite`：build-stage memory cache，保留；正式 token 统计仍按冷启动逻辑成本记录。
- `cache/qwen3_answer_v28.sqlite`：当前主线 answer cache，保留用于复查 v28。
- `services/`：本地 vLLM 服务日志/状态。

## 清理规则

- 旧 smoke、小样本、负向 ablation 输出及时删除。
- 旧 partial judge、过期 answer cache、query planner cache 不长期保留。
- 如果某个 ignored 输出对正式结果有价值，必须把 summary、metrics、diagnosis、config snapshot 和输出路径写入 `experiments/`，不能只依赖 `outputs/`。
