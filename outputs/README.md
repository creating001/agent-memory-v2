# 输出目录

`outputs/` 只保留当前仍有用的运行产物和本地缓存。预测文件、trace、日志和中间产物不能替代 `experiments/` 下的人类可读记录。

当前保留：

- `prepare_longmemeval_s_cleaned/`：LongMemEval-S clean prediction input 和离线 labels。
- `prepare_locomo_non_adversarial/`：LoCoMo non-adversarial prediction input 和离线 labels。
- `cache/`：本地 embedding cache。
- `services/`：本地 vLLM 服务日志/状态。
- `stage1_session_bm25_temporal_p4_grounded_strict_*_100/`：strict baseline 100 条诊断输出。
- `stage1_route_guidance_*_100/`：route guidance 100 条诊断输出。
- `stage1_cached_strict_lme_s_100_*warm/`：cache 成本诊断输出。

正式 full run 会生成：

```text
outputs/<formal_run_id>/predictions.jsonl
outputs/<formal_run_id>/traces.jsonl
```

旧 smoke、小样本、负向 ablation 输出应及时删除；有价值的结论写入 `experiments/README.md` 或对应正式实验记录。
