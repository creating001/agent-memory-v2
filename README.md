# Agent-Memory

本项目目标是构建一个通用、clean、可消融、可持续迭代的 Agent Memory 系统，并在 LongMemEval-S full 和 LoCoMo non-adversarial full 上用 judge accuracy 验证效果。

核心不是固定某个框架，而是在严格 clean setting 和成本约束下，持续提升长期记忆的 build、management、retrieval、context organization 和 answer 能力。方法可以迭代替换，但不能使用 gold answer、judge output、benchmark 标签、sample id、test feedback 或样本级规则。

## 当前默认配置

后续新实验默认使用 `configs/stage1_spacing_profile_v102_qwen36_no_think_build4k_cached.json`：

- Answer / build LLM：`Qwen/Qwen3.6-35B-A3B`。
- thinking：请求级 `chat_template_kwargs.enable_thinking=false`。
- Answer 上限：`max_input_tokens=131072`，`max_output_tokens=16384`。
- build 上限：`max_tokens=4096`，`max_records_per_chunk=20`。

当前默认 backbone 的已验证 v102 LTS 结果：

- Backbone：`Qwen/Qwen3.6-35B-A3B` no-thinking（build/answer 均使用 `chat_template_kwargs.enable_thinking=false`）。
- LongMemEval-S full：strict `403/500 = 0.806000`，lenient `422/500 = 0.844000`。
- LoCoMo non-adversarial full：strict `1213/1540 = 0.787662`，lenient `1268/1540 = 0.823377`。
- 两个 benchmark 使用同一套 clean raw-memory-granularity adaptive v102 算法；按 lenient dual judge 达到 baseline target，strict 是更保守的下界。V102 只把短 turn prompt spacing 显式纳入 profile；LongMemEval-S 长 turn 分支保持 v98，LoCoMo 短 turn 分支恢复 v96 行为。
- 结果入口见 `experiments/README.md`；预测和 trace 见 `outputs/formal/<run_id>/`。

## 目录

```text
docs/          规则、约束、架构和方法调研
src/           项目代码：common、data、memory、evaluation、tests
configs/       可消融配置
scripts/       数据准备、预测、评测、诊断脚本
experiments/   人类可读的 LTS / split best / 关键 baseline 实验记录
outputs/       保留实验的预测、trace、必要 cache 和数据准备产物
data/          本地数据入口，不提交大数据
external/      只读外部参考实现
```

## 必读文档

- `AGENTS.md`
- `docs/clean_protocol.md`
- `docs/constraints.md`
- `docs/experiment_protocol.md`
- `docs/architecture.md`
- `docs/method.md`

需要深入外部方法时再读 `docs/method_cards.md`。

## 本地检查

```bash
conda activate agent-memory
python -m pip install -e .
python -m unittest discover -s src/tests
```

正式实验必须在 `experiments/` 下留下 summary、metrics、diagnosis、配置快照、git commit/dirty 状态、token 成本和 outputs 路径。方法性能主要看 DeepSeek dual judge accuracy：strict 为 flash/pro 都判对，lenient 为任一 judge 判对。
