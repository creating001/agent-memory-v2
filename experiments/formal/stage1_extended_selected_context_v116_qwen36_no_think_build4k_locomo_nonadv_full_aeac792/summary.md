# v116 LoCoMo Non-Adversarial Full

## 目的

验证 `stage1_extended_selected_context_v116_qwen36_no_think_build4k_cached.json` 在 LoCoMo non-adversarial full 上的正式效果。v116 继承 v110，仅把短 turn selected context 的后向邻域从 1 扩到 2、neighbor 文本预算从 120 提到 180，并增加 `max_center_chars=320`。目标是补足对话中“检索命中 anchor，但答案在相邻后一轮出现”的通用邻域证据，不增加 rerank、repair 或额外 answer LLM pass。

## 配置

- benchmark/subset: LoCoMo non-adversarial full
- 样本数: 1540
- config: `configs/stage1_extended_selected_context_v116_qwen36_no_think_build4k_cached.json`
- input: `outputs/prepare_locomo_non_adversarial/prediction_input.jsonl`
- predictions: `outputs/formal/stage1_extended_selected_context_v116_qwen36_no_think_build4k_locomo_nonadv_full_aeac792/predictions.jsonl`
- traces: `outputs/formal/stage1_extended_selected_context_v116_qwen36_no_think_build4k_locomo_nonadv_full_aeac792/traces.jsonl`
- judge: `experiments/formal/stage1_extended_selected_context_v116_qwen36_no_think_build4k_locomo_nonadv_full_aeac792/deepseek_dual_judge.json`
- comparison: `experiments/formal/stage1_extended_selected_context_v116_qwen36_no_think_build4k_locomo_nonadv_full_aeac792/judge_comparison_vs_v110.json`
- git commit: `aeac79271c357b66e0ce0cda838c6b0aefbeeb9d`
- dirty at prediction time: `false`
- answer/build model: `Qwen/Qwen3.6-35B-A3B`, `chat_template_kwargs.enable_thinking=false`
- answer max input/output: `131072 / 16384`
- workers: 12

## 指标

| 指标 | 数值 |
|---|---:|
| strict accuracy | `1200/1540 = 0.779221` |
| lenient accuracy | `1243/1540 = 0.807143` |
| judge flash_1 accuracy | `1219/1540 = 0.791558` |
| judge flash_2 accuracy | `1224/1540 = 0.794805` |
| judge agreement | `0.972078` |
| avg build tokens | `62015.574` |
| avg build think tokens | `0.000` |
| avg query tokens | `5956.221` |
| avg query think tokens | `0.000` |
| avg build memory records | `150.915` |
| avg active build memory records | `141.868` |
| avg compiled evidence items | `54.144` |
| selected context applied | `1198/1540 = 0.777922` |
| avg selected context rows | `4.668` |
| answer finalizer applied | `0/1540` |

## 对比 v110

| 项 | v110 | v116 | delta |
|---|---:|---:|---:|
| strict correct | `1200` | `1200` | `+0` |
| strict accuracy | `0.779221` | `0.779221` | `+0.000000` |
| lenient correct | `1231` | `1243` | `+12` |
| lenient accuracy | `0.799351` | `0.807143` | `+0.007792` |
| answer text changed | - | `575/1540` | - |

按 LoCoMo category：

| Category | 名称 | lenient correct / total | lenient accuracy | vs v110 |
|---:|---|---:|---:|---:|
| 1 | Multi-Hop | `197/282` | `0.698582` | `+5` |
| 2 | Temporal Reasoning | `248/321` | `0.772586` | `+0` |
| 3 | Open-Domain | `51/96` | `0.531250` | `-3` |
| 4 | Single-Hop | `747/841` | `0.888228` | `+10` |

## 结论

v116 在不改变 build、retrieval top-k、rerank、repair 和 answer backbone 的情况下，把 LoCoMo dual flash lenient 从 `0.799351` 提升到 `0.807143`，达到当前 baseline target `>=0.800000`。strict 不变，收益主要来自 Multi-Hop 和 Single-Hop；Open-Domain 有小幅回退，后续如继续提升应重点处理开放式推断和上下文噪声，而不是继续扩大邻域窗口。

clean 口径：预测阶段不读取 gold answer、judge 输出、benchmark label、sample id、row index 或 test feedback；v116 的 selected context 只基于 prediction-time question、retrieved raw turn、同 session 邻近 turn 和通用 information-need/anaphora gate。
