# V102 judge v4 pro 对比记录

- 时间：2026-06-16
- 性质：judge-only diagnostic；复用 v102 已完成 prediction，不重新运行 build/query。
- 算法配置：`configs/stage1_spacing_profile_v102_cached.json`
- git commit：`cd61130`
- dirty 状态：是，仅包含本次新增的 v4 pro judge 输出和本记录。
- clean 说明：judge 离线读取 gold labels，只用于评测对比；不进入 prediction、retrieval、compiler、answer 或 verifier。

## 输出路径

- LME predictions：`outputs/formal/stage1_spacing_profile_v102_lme_s_full_f844921/predictions.jsonl`
- LME v4 flash judge：`experiments/formal/stage1_spacing_profile_v102_lme_s_full_f844921/deepseek_judge.json`
- LME v4 pro judge：`experiments/formal/stage1_spacing_profile_v102_lme_s_full_f844921/deepseek_judge_v4_pro.json`
- LoCoMo predictions：`outputs/formal/stage1_spacing_profile_v102_locomo_nonadv_full_f844921/predictions.jsonl`
- LoCoMo v4 flash judge：`experiments/formal/stage1_spacing_profile_v102_locomo_nonadv_full_f844921/deepseek_judge.json`
- LoCoMo v4 pro judge：`experiments/formal/stage1_spacing_profile_v102_locomo_nonadv_full_f844921/deepseek_judge_v4_pro.json`

## 总体指标

| benchmark | judge model | correct / total | accuracy | invalid | judge tokens |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S full | deepseek-v4-flash | 400/500 | 0.800000 | 0 | 116682 |
| LongMemEval-S full | deepseek-v4-pro | 389/500 | 0.778000 | 0 | 157841 |
| LoCoMo non-adversarial full | deepseek-v4-flash | 1232/1540 | 0.800000 | 0 | 649050 |
| LoCoMo non-adversarial full | deepseek-v4-pro | 1230/1540 | 0.798701 | 0 | 761827 |

## 判定差异

- LME：17 个样本判定不同；flash 正确/pro 错误 14 个，flash 错误/pro 正确 3 个。
- LoCoMo：72 个样本判定不同；flash 正确/pro 错误 37 个，flash 错误/pro 正确 35 个。

## LoCoMo 分类 accuracy

| category | 名称 | v4 flash | v4 pro |
|---:|---|---:|---:|
| 1 | Multi-Hop | 201/282 = 0.712766 | 216/282 = 0.765957 |
| 2 | Temporal Reasoning | 239/321 = 0.744548 | 238/321 = 0.741433 |
| 3 | Open-Domain | 58/96 = 0.604167 | 58/96 = 0.604167 |
| 4 | Single-Hop | 734/841 = 0.872771 | 718/841 = 0.853746 |

## LME 问题类型 accuracy

| question_type | v4 flash | v4 pro |
|---|---:|---:|
| knowledge-update | 69/78 = 0.884615 | 67/78 = 0.858974 |
| multi-session | 92/133 = 0.691729 | 90/133 = 0.676692 |
| single-session-assistant | 52/56 = 0.928571 | 51/56 = 0.910714 |
| single-session-preference | 13/30 = 0.433333 | 10/30 = 0.333333 |
| single-session-user | 67/70 = 0.957143 | 66/70 = 0.942857 |
| temporal-reasoning | 107/133 = 0.804511 | 105/133 = 0.789474 |

## 诊断结论

v4 pro 没有提升当前 v102 的总体 judge accuracy。LME 上 v4 pro 明显更严格，accuracy 从 0.800 降到 0.778；LoCoMo 总体几乎持平，从 0.800 降到 0.798701，但 multi-hop 更高、single-hop 更低。后续主线仍应以固定 judge 口径比较方法，不建议把不同 judge 的绝对分数混在同一排行榜里。
