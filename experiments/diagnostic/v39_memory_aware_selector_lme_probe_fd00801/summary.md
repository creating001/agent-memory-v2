# v39 memory-aware selector LME gate

## 目的

这是 `configs/stage1_memory_aware_selector_v39_cached.json` 的 LongMemEval-S route-stratified 20 条诊断 gate，不计算 accuracy。目标是确认 v39 在进入 full run 前满足 clean、token、route override 和 trace 记录要求。

v39 的方法假设是：不把 typed memory 直接塞进 answer prompt，而是让 build-stage memory 的 `source_ids` 只参与 list/temporal 候选 evidence 排序。最终 answer 仍读取 raw evidence rows。

## 结论

Gate 通过，可以进入 LongMemEval-S full。

- `answer_max_input_tokens`: `131072`
- `answer_max_output_tokens`: `16384`
- `avg_build_tokens`: `81690.45`
- `avg_query_tokens`: `5607.8`
- 按 LME full route 分布估算 avg query tokens: `5566.583`
- `avg_compiled_evidence_items`: `34.65`
- `avg_compiled_memory_records`: `0.0`
- prediction lines: `20`
- trace lines: `20`

主要风险：`temporal_lookup` gate 平均 query tokens 为 `6081.2`，略高于单 route 6K；但 full 分布加权估计仍低于 6K。full run 需要重点观察 list/temporal accuracy 是否真正收益，而不是只改变答案方差。

## Scope

- benchmark: `longmemeval_s`
- subset: `route_stratified_20`
- experiment_kind: `diagnostic`
- workers: `4`
- input: `outputs/diagnostic/v35_lme_route_stratified_probe/prediction_input.jsonl`
- config: `configs/stage1_memory_aware_selector_v39_cached.json`
- run_id: `v39_memory_aware_selector_lme_probe_fd00801`

## Git

- commit: `fd00801b76f9e3fc686f61e222ece71eec563c27`
- dirty: `true`
- dirty files: `docs/architecture.md`, `docs/clean_protocol.md`
- 说明：dirty 文件是用户修改的文档；本次 prediction pipeline、config 和代码来自上述 commit。

## Route Audit

| information_need | n | retrieval top_k | evidence_order | row_text_mode | avg query tokens | max query tokens | avg rows |
|---|---:|---:|---|---|---:|---:|---:|
| current_state | 4 | 40 | retrieval | full | 6092.0 | 6282 | 28.8 |
| fact_lookup | 4 | 40 | retrieval | full | 5073.5 | 5237 | 37.0 |
| list_count | 4 | 60 | memory_aware | role_query_snippet | 5575.5 | 5931 | 36.0 |
| profile_preference | 4 | 40 | retrieval | full | 5216.8 | 5571 | 36.0 |
| temporal_lookup | 4 | 60 | memory_aware | role_query_snippet | 6081.2 | 6407 | 35.5 |

Gate 检查点：

- 非目标 route 保持 v36 的 retrieval order 和 top40。
- `list_count` / `temporal_lookup` 使用 top60 candidate pool，但 compiler 仍最多保留 40 条 raw rows。
- `list_count` / `temporal_lookup` 使用 `role_query_snippet` 控制 prompt 长度。
- typed memory 不作为 answer prompt fact 出现，`avg_compiled_memory_records=0.0`。
- build cache 全命中，但 build tokens 按 logical cold-build usage 计入，不记为 0。

## Outputs

- predictions: `outputs/diagnostic/v39_memory_aware_selector_lme_probe_fd00801/predictions.jsonl`
- traces: `outputs/diagnostic/v39_memory_aware_selector_lme_probe_fd00801/traces.jsonl`
- metrics: `experiments/diagnostic/v39_memory_aware_selector_lme_probe_fd00801/metrics.json`
- manifest: `experiments/diagnostic/v39_memory_aware_selector_lme_probe_fd00801/manifest.json`
- config snapshot: `experiments/diagnostic/v39_memory_aware_selector_lme_probe_fd00801/config_snapshot.json`

## Clean Notes

- Prediction 阶段不读取 gold answer、judge output、benchmark label、question_type、category、sample id、row index、qid 或 test feedback。
- `information_need` route 只来自 question text 和可见 question time。
- `memory_aware` selector 只使用 raw dialogue、build-stage memory source links、retrieval rank 和 question text。
- DeepSeek judge 只允许在 full prediction 之后离线使用。
