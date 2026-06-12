# Agent-Memory

本项目目标是搭建一套通用、clean、可消融、可持续迭代的 Agent-Memory 框架。LongMemEval 和 LoCoMo 是用于验证的 benchmark，用于检验框架在长期对话记忆任务中的有效性。核心目标不是为某个 benchmark 写专门规则，而是在 clean 和成本约束下沉淀一套更高性能、更可靠、更可解释、更具泛化能力的 Agent-Memory 方法。

## 目录结构

```text
.
├── AGENTS.md                    # Codex 开发协作规则
├── README.md                    # 项目入口说明
├── docs/
│   ├── clean_protocol.md        # clean setting 和泄漏红线
│   ├── constraints.md           # token、调用次数和成本约束
│   ├── experiment_protocol.md   # 模型、judge prompt 和指标协议
│   ├── architecture.md          # 项目探索框架
│   ├── method.md                # 外部方法总览和推荐主线
│   └── method_cards.md          # 详细方法 card
├── src/                         # 本项目自己的核心方法代码
├── configs/                     # 模型、检索、路由、实验配置
├── scripts/                     # 运行、评测、分析、数据准备脚本
├── experiments/                 # 面向人工查看的实验看板、ablation、诊断报告
├── outputs/                     # 预测结果、日志、中间产物，默认不作为方法代码
├── data/                        # 本地数据入口或软链接说明，不提交大数据
└── external/                    # 外部 repo、baseline 和参考实现
```

## 重要文档

- `docs/clean_protocol.md`：所有方法、代码和实验必须遵守的 clean 规则。
- `docs/constraints.md`：token、LLM 调用次数、build/query 成本等技术指标约束。
- `docs/experiment_protocol.md`：模型配置、judge prompt、指标和公共实验口径。
- `docs/architecture.md`：项目主框架和可探索模块。
- `docs/method.md`：外部方法总览、推荐主线和方法索引。
- `docs/method_cards.md`：详细方法 card，需要深入参考具体方法时再读。

## 实验可追溯

实验可追溯主要依赖本地 git。正式实验和结果汇报应记录对应的 commit、是否存在未提交改动、关键配置、运行命令和输出路径。方法迭代应尽量保持改动小而清晰，方便用 git diff 回看每次增益来自哪里。

`experiments/` 是主要观察入口，不只是日志 dump。每个正式实验应在 `experiments/` 下留下一个可读目录，至少包含实验目的、方法改动、配置摘要、指标结果、token 成本、关键诊断、输出路径和下一步判断。用户主要通过这个目录观察 Codex 的实验结果和方法迭代过程。

## 本地运行

当前项目使用独立 conda 环境：

```bash
conda activate agent-memory
python -m pip install -e .
python -m unittest discover -s tests
```

本地 answer model 使用协议指定的 Qwen vLLM 服务。启动和停止脚本如下：

```bash
bash scripts/start_answer_vllm.sh
curl --noproxy '*' http://127.0.0.1:8000/v1/models
bash scripts/stop_answer_vllm.sh
```

当前 answer 配置在 `configs/stage1_vllm_answer.json`，指向 `Qwen/Qwen3-30B-A3B-Instruct-2507` 的本地 OpenAI-compatible endpoint。DeepSeek judge 只允许在离线评测脚本中使用，API key 通过 `DEEPSEEK_API_KEY` 环境变量读取，不写入仓库。

## 数据和诊断入口

原始 benchmark 数据放在 `data/raw/` 或外部软链接中，不提交到 git。clean 预测输入和离线 labels 分离生成：

```bash
conda run -n agent-memory python scripts/prepare_dataset.py \
  --benchmark longmemeval \
  --subset s_cleaned \
  --input data/raw/longmemeval/longmemeval_s_cleaned.json \
  --output-dir outputs/prepare_longmemeval_s_cleaned

conda run -n agent-memory python scripts/prepare_dataset.py \
  --benchmark locomo \
  --subset non-adversarial \
  --input data/raw/locomo/locomo10.json \
  --output-dir outputs/prepare_locomo_non_adversarial
```

Stage-1 vLLM 诊断示例：

```bash
conda run -n agent-memory python scripts/run_stage1.py \
  --input outputs/prepare_longmemeval_s_cleaned/prediction_input.jsonl \
  --config configs/stage1_vllm_answer.json \
  --run-id stage1_qwen30b_lme_s_3 \
  --benchmark longmemeval \
  --subset s_cleaned \
  --experiment-kind diagnostic \
  --limit 3
```

预测完成后才运行离线评测和诊断：

```bash
conda run -n agent-memory python scripts/evaluate_predictions.py \
  --predictions outputs/stage1_qwen30b_lme_s_3/predictions.jsonl \
  --labels outputs/prepare_longmemeval_s_cleaned/labels.jsonl \
  --output experiments/stage1_qwen30b_lme_s_3/offline_lexical_eval.json

conda run -n agent-memory python scripts/analyze_evidence_recall.py \
  --traces outputs/stage1_qwen30b_lme_s_3/traces.jsonl \
  --labels outputs/prepare_longmemeval_s_cleaned/labels.jsonl \
  --output experiments/stage1_qwen30b_lme_s_3/evidence_recall.json
```

## 外部方法参考

本项目不是从零拍脑袋设计 memory 方法。`docs/method.md` 和 `docs/method_cards.md` 是重要设计输入：提出新 memory、retrieval、compiler、verifier 或 ablation 时，应先参考外部方法，总结可迁移机制、舍弃原因和预期收益，再落到本项目的 clean、成本和可消融约束下实现。
