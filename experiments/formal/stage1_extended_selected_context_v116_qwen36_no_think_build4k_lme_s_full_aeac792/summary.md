# v116 LongMemEval-S Full

## 目的

验证 LoCoMo 上正向的 v116 selected-context 邻域扩展是否破坏 LongMemEval-S full。LongMemEval-S 的长 turn 路径不会触发 selected context，因此本 run 主要做同算法兼容性检查。

## 配置

- benchmark/subset: LongMemEval-S full
- 样本数: 500
- config: `configs/stage1_extended_selected_context_v116_qwen36_no_think_build4k_cached.json`
- input: `outputs/prepare_longmemeval_s_cleaned/prediction_input.jsonl`
- predictions: `outputs/formal/stage1_extended_selected_context_v116_qwen36_no_think_build4k_lme_s_full_aeac792/predictions.jsonl`
- traces: `outputs/formal/stage1_extended_selected_context_v116_qwen36_no_think_build4k_lme_s_full_aeac792/traces.jsonl`
- compatibility: `experiments/formal/stage1_extended_selected_context_v116_qwen36_no_think_build4k_lme_s_full_aeac792/prediction_compatibility_vs_v110.json`
- git commit: `aeac79271c357b66e0ce0cda838c6b0aefbeeb9d`
- dirty at prediction time: `true`，仅因为 LoCoMo v116 formal 目录已经生成但尚未提交；prediction pipeline code/config 无未提交改动。
- answer/build model: `Qwen/Qwen3.6-35B-A3B`, `chat_template_kwargs.enable_thinking=false`
- answer max input/output: `131072 / 16384`
- workers: 8

## 指标

v116 的 LongMemEval-S predictions 与 v110 完全一致：`answer_text_changed = 0/500`。因此不重复跑 judge，继承 v110 dual flash judge 指标：

| 指标 | 数值 |
|---|---:|
| strict accuracy | `406/500 = 0.812000` |
| lenient accuracy | `417/500 = 0.834000` |
| judge flash_1 correct | `410/500` |
| judge flash_2 correct | `413/500` |
| judge agreement | `0.978000` |
| avg build tokens | `85393.566` |
| avg build think tokens | `0.000` |
| avg query tokens | `6140.218` |
| avg query think tokens | `0.000` |
| avg build memory records | `115.818` |
| avg active build memory records | `102.200` |
| avg compiled evidence items | `34.752` |
| selected context applied | `0/500` |
| answer finalizer applied | `8/500` |

## 结论

v116 不改变 LongMemEval-S 输出，继承 v110 的 `0.834000` lenient accuracy，达到当前 LME baseline target。avg query tokens `6140.218` 略高于 6K normal target，但低于 8K hard ceiling；后续如果继续优化，应在保持 LME accuracy 的前提下压缩长 turn context，而不是牺牲 LoCoMo 的 selected-context 收益。

clean 口径：预测阶段不读取 gold answer、judge 输出、benchmark label、sample id、row index 或 test feedback；本文件的 inherited judge 指标只用于离线结果汇报，不进入 prediction pipeline。
