# Diagnosis for stage1_external_route_guidance_v21_lme_s_full_774be27

## 诊断结论

v21 不是可继续放大的方向。它只改变 external-naive prompt 的 route guidance，不改变 retrieval、build memory、row guide 或 evidence budget；但 LME full 从 v18 的 `0.732` 降到 `0.702`。

## 与 v18 对比

- fixed_vs_v18: `15`
- hurt_vs_v18: `30`
- net_correct_delta: `-15`

fixed by type：

| type | count |
|---|---:|
| multi-session | 5 |
| single-session-assistant | 1 |
| single-session-preference | 3 |
| single-session-user | 1 |
| temporal-reasoning | 5 |

hurt by type：

| type | count |
|---|---:|
| knowledge-update | 9 |
| multi-session | 9 |
| single-session-assistant | 1 |
| single-session-preference | 3 |
| single-session-user | 2 |
| temporal-reasoning | 6 |

## 失败模式

- evidence recall 仍为 `1.0`，说明本次退化不是离线 evidence label 覆盖率下降导致。
- avg compiled evidence items 为 `34.058`，和 v18 同量级；retrieval 结构没有变化。
- route guidance prompt 覆盖所有 500 个问题，增加了少量 query token：v18 `5117.622`，v21 `5165.882`。
- knowledge-update 从 v18 的 `64/78` 降到 `55/78`，说明短规则可能干扰了更新链判断和完整答案表述。
- multi-session 从 v18 的 `74/133` 降到 `70/133`，说明跨会话证据组织仍不能靠通用 answer rule 解决。
- preference 仍为 `11/30`，未解决主线弱项。

离线错例抽样显示，一些退化来自答案过短或丢掉限定细节，例如只答 `Main St` 而不是 `The music shop on Main St.`，或只答 `bluegrass band` 而丢掉 gold 需要的限定描述。该分析只用于离线诊断，不能进入 prediction pipeline。

## Clean 检查

- prediction loader 未读取 gold/reference/target、judge output、benchmark label、sample id、qid 或 row index。
- route guidance 只由问题文本和 runtime route signal 触发，不使用 LongMemEval question_type。
- DeepSeek judge 和 evidence recall 均在预测完成后离线运行，输出不得被 route、retrieval、compiler、answer 或 verifier 读取。
- manifest 记录 commit `774be27582abd0dcc3a1a70ea082260a69e5ebb9`，prediction dirty 为 `false`。

## 后续建议

- 不继续运行 LoCoMo full，避免在 LME 明确负向的 query-side prompt 规则上浪费成本。
- v18 仍是当前 unified best。
- 下一步应回到更 general 的 memory 系统能力：build-stage typed memory 管理、source-preserving multi-view retrieval、raw evidence compiler、conflict/update handling，而不是继续增加强指令式 route rules。
- 如果继续做 answer-side 改动，应优先尝试可消融的 evidence table / contradiction view / compact verifier，并确保 query token 不超过 6K。
