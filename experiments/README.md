# 实验入口

`experiments/` 是人工查看结果的入口，不再平铺所有历史小实验。这里只保留当前仍有用的记录；早期 smoke、小样本、负向 ablation 和旧配置结果已清理。

## 看什么指标

方法性能主要看离线 DeepSeek judge accuracy。

- LongMemEval-S full：`outputs/prepare_longmemeval_s_cleaned/prediction_input.jsonl`，共 500 条。
- LoCoMo non-adversarial full：`outputs/prepare_locomo_non_adversarial/prediction_input.jsonl`，共 1540 条。

`offline_lexical_eval.json` 里的 exact/F1/BLEU 只作为低成本诊断，不作为方法好坏判断。evidence recall 也只用于定位 retrieval 问题。

## 当前目录结构

```text
experiments/
├── README.md
├── candidates/
│   ├── strict/                  # 当前 strict baseline 100 条诊断记录
│   └── route_guidance/          # 当前 route guidance 候选 100 条诊断记录
└── diagnostics/
    └── cache/                   # embedding cache 成本诊断
```

正式全量实验跑完后再创建：

```text
experiments/formal/<run_id>/
```

## 当前候选

### Strict Baseline

目录：

- `candidates/strict/stage1_session_bm25_temporal_p4_grounded_strict_lme_s_100`
- `candidates/strict/stage1_session_bm25_temporal_p4_grounded_strict_locomo_100`

配置：

- `configs/stage1_strict_cached.json`

说明：

- raw evidence 是唯一事实来源。
- retrieval 使用 dense + turn BM25 + gated session BM25。
- compiler 使用 retrieval order、concise answer、temporal grounding。
- embedding cache 只减少重复 embedding 调用，不改变预测输入。

### Route Guidance Candidate

目录：

- `candidates/route_guidance/stage1_route_guidance_lme_s_100`
- `candidates/route_guidance/stage1_route_guidance_locomo_100`

配置：

- `configs/stage1_route_guidance_cached.json`

说明：

- 在 strict baseline 上增加通用 question-route guidance。
- guidance 只来自 question text 和 question-derived route。
- 不使用 benchmark label、sample id、gold answer、judge output 或 test feedback。
- `stage1_route_guidance_locomo_100/deepseek_judge.json` 是 100 条诊断 judge 结果，accuracy 为 0.51；这不是正式全量结果。

## 正式实验要求

正式实验必须满足：

- 使用 full benchmark scope，不用前 N 条当正式结果。
- 同时报告 LongMemEval-S full 和 LoCoMo non-adversarial full。
- 主要指标为 DeepSeek judge accuracy。
- 记录 git commit、dirty 状态、配置、benchmark/subset、token 成本和输出路径。
- 保留 `summary.md`、`metrics.json`、`diagnosis.md`、`manifest.json`、`config_snapshot.json`。
- `summary.md` 和 `diagnosis.md` 必须用 accuracy-first 的方式解释结果。

如果因为成本或调试必须做子集，应使用按问题类型或 question-derived information need 的分层采样，并明确标成 diagnostic。

## 已清理的历史记录

以下内容已从 `experiments/` 顶层删除，只保留结论：

- early smoke / 3-row / 20-row 小样本。
- question-overlap compiler ordering：负向。
- query snippet compiler mode：100 条诊断负向。
- turn-level stopword filtering：LongMemEval 诊断有正向，但 LoCoMo 100 负向，不作为通用默认。
- temporal hints / broad list route：负向。

需要恢复旧结果时应从 git 历史查找，不在当前工作目录保留无用目录。
