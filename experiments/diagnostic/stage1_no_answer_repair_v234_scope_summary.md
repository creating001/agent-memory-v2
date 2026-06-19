# v234 no answer repair scope summary

## 结论

v234 升为当前本地 LTS。它继承 v233 的 build-time `stateful_only` memory management，并关闭 v233 full run 中触发 `8` 次但 applied `0` 次的 answer repair。v234 与 v233 full predictions answer-identical，因此 judge accuracy 继承 v233；同时 query token 更低，query-time 补丁复杂度更少。

当前 LTS 配置：

```text
configs/stage1_no_answer_repair_v234_seeded_qwen36_no_think_build4k_cached.json
```

方法 commit：

```text
5ca31749dc64ad9d5416bcd0283a6c32c16514a6
```

## 方法改动

- 保留 v233 的 build memory policy：`management_policy = stateful_only`。
- 保留 retrieval、compiler prompt、source-grounded finalizer、guarded fact tail-exchange rerank。
- 设置 `answer.repair.enabled = false`。
- answer cache 使用 v234 独立 path/namespace，并从 v233 full traces 的 `answer_draft` 预种；不读取 labels、judge outputs、benchmark categories、sample ids、test feedback 或 gold answers。

这一步的目标是 query-time 简化：如果 verifier/repair 分支在 full run 中只触发但不产生 revision，它不应该留在默认 LTS path 里消耗 token 和增加 drift surface。

## Full run

| Benchmark | run | avg build/query tokens | answer cache | repair |
|---|---|---:|---:|---:|
| LongMemEval-S full | `stage1_no_answer_repair_v234_lme_s_full` | `85393.566 / 6579.782` | `500/0/0` | disabled, `0` triggered |
| LoCoMo non-adversarial full | `stage1_no_answer_repair_v234_locomo_nonadv_full` | `62015.57402597403 / 6094.017532467533` | `1540/0/0` | disabled, `0` triggered |

Outputs:

```text
outputs/diagnostic/stage1_no_answer_repair_v234_lme_s_full/
outputs/diagnostic/stage1_no_answer_repair_v234_locomo_nonadv_full/
experiments/diagnostic/stage1_no_answer_repair_v234_lme_s_full/
experiments/diagnostic/stage1_no_answer_repair_v234_locomo_nonadv_full/
```

## Answer diff and accuracy

v234 vs v233 prediction answer diff:

| Benchmark | diff |
|---|---:|
| LongMemEval-S full | `0/500` |
| LoCoMo non-adversarial full | `0/1540` |

因此 v234 继承 v233 的 paired-delta derived accuracy：

| Benchmark | strict | lenient |
|---|---:|---:|
| LongMemEval-S full | `0.832000` (`416/500`) | `0.844000` (`422/500`) |
| LoCoMo non-adversarial full | `0.794156` (`1223/1540`) | `0.819481` (`1262/1540`) |

v234 没有新增 changed answers，所以不重跑 judge。v233 的 changed-answer judge 记录仍是 accuracy 依据：

```text
experiments/diagnostic/stage1_build_memory_stateful_policy_v233_changed_vs_v231/
```

## Token and risk effect

| Benchmark | v233 avg query | v234 avg query | reduction |
|---|---:|---:|---:|
| LongMemEval-S full | `6637.416` | `6579.782` | `57.634` |
| LoCoMo non-adversarial full | `6100.013636363637` | `6094.017532467533` | `5.996103896104` |

The reduction is exactly the removed repair query budget:

- LME v233 repair query tokens: `28817` total, `57.634` average.
- LoCoMo v233 repair query tokens: `9234` total, `5.996103896104` average.

## LTS 决策

升 v234 为当前本地 LTS，理由：

- 相对 v233，answer diff `0`，accuracy 不变。
- query tokens 严格下降。
- 删除 full applied 为 `0` 的 repair branch，减少 query-time drift surface 和 pipeline patch 感。
- 保留 v233 的 build-time memory lifecycle policy，因此不牺牲当前系统化改进。

v233 保留为 build memory stateful policy 父锚点；v231 保留为 LongMemEval-S performance anchor。

## 下一步

1. 把 `management_policy`、operation counts、layer counts 聚合进 `metrics.json`，减少手工 trace 聚合。
2. 继续清理 query-time route/guide/ledger/finalizer 的兼容分支，保留有消融价值的能力。
3. 扩展 build-time memory operations，让 lifecycle/collection/source provenance 更直接影响 retrieval 和 context organization，而不是回到 benchmark-specific prompt rule。
