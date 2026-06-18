# v153 Current-State Update Contract Scope Summary

## 目的

v153 测试风险 #5 的一个低风险子方向：不改变 retrieval、row ordering 或 typed-memory exposure，只在 `current_state` route 的 reader prompt 中加入通用 current-state update discipline，看能否减少旧状态覆盖新状态、近似状态被忽略、assistant acknowledgement 被误用等问题。

## 方法

- 配置：`configs/stage1_current_state_update_contract_v153_qwen36_no_think_build4k_cached.json`。
- 父版本：当前 LTS `v151`。
- 唯一预测侧改动：`compiler.route_overrides.current_state.current_state_update_contract=true`。
- 不改 build memory、retrieval、selected context、evidence row ordering、typed memory 暴露、answer model 或 repair scope。
- Clean 边界：新 contract 只使用 question text 和 raw Memory Context；不使用 gold、judge、benchmark 标签、sample id、row index、test feedback 或样本级规则。

## 指标

| Benchmark | changed subset judge | derived full v153 | 成本 |
|---|---:|---:|---|
| LongMemEval-S full | v151 strict/lenient `9/10` / `9/10`；v153 `5/10` / `5/10`；delta `-4/-4` | strict/lenient `407/500` / `413/500` = `0.814000 / 0.826000` | avg query tokens `6169.376`；contract prompts `22/500` |
| LoCoMo non-adversarial full | v151 strict/lenient `1/2` / `1/2`；v153 `1/2` / `1/2`；delta `0/0` | strict/lenient `1216/1540` / `1256/1540` = `0.789610 / 0.815584` | avg query tokens `6048.142`；contract prompts `4/1540` |

## 诊断

- v153 scope 很窄，但 LME 负向明显。
- 典型损失不是 retrieval 变坏，而是 prompt-side update discipline 让 answer model 过度偏向“newer/current”解释，改坏了已正确的 duration、most-recent trip 和 recommendation-style current-state 答案。
- LoCoMo 只有 2 条答案变化且持平，但不足以抵消 LME 负向。

## 决策

v153 不升 LTS。当前 LTS 仍为 v151。

下一步 #5 不应继续加宽 prompt-only current-state discipline。更合理的方向是 source-backed lifecycle ledger / answer-slot-aware verifier：先在 raw evidence 层识别 question 要求的 state slot、time scope、active/historical/change intent，再用 compact ledger 或 verifier 限制候选，而不是让 reader 自行从宽泛规则里重解释所有 current-state 证据。

## Artifacts

- Full prediction traces:
  - `outputs/diagnostic/stage1_current_state_update_contract_v153_lme_s_full/`
  - `outputs/diagnostic/stage1_current_state_update_contract_v153_locomo_nonadv_full/`
- Changed subset judge:
  - `experiments/diagnostic/stage1_current_state_update_contract_v153_lme_changed_vs_v151/`
  - `experiments/diagnostic/stage1_current_state_update_contract_v153_locomo_changed_vs_v151/`
- Aggregate:
  - `experiments/diagnostic/stage1_current_state_update_contract_v153_results.json`
