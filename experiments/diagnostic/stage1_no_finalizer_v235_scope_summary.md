# v235 no finalizer scope summary

## 结论

v235 升为当前本地 LTS。它继承 v234 的 build-time `stateful_only` memory management 和 no-repair query path，并关闭 v234 full run 中 applied `0` 次的 deterministic answer finalizer。v235 与 v234 full predictions answer-identical，因此 judge accuracy 继承 v234；query token 不变，但默认 query path 少一个 post-hoc rewrite branch。

当前 LTS 配置：

```text
configs/stage1_no_finalizer_v235_seeded_qwen36_no_think_build4k_cached.json
```

方法 commit：

```text
a61b45b65f4acbec0f2565a0334f0ec2d2895dbb
```

## 方法改动

- 保留 v234 的 build memory policy：`management_policy = stateful_only`。
- 保留 retrieval、compiler prompt、guarded fact tail-exchange rerank。
- 保持 `answer.repair.enabled = false`。
- 设置 `answer.finalizer.enabled = false`。
- answer cache 使用 v235 独立 path/namespace，并从 v234 full traces 的 `answer_draft` 预种；不读取 labels、judge outputs、benchmark categories、sample ids、test feedback 或 gold answers。

这一步的目标是 query-time 简化：如果 finalizer 在 full run 中没有产生 revision，它不应该留在默认 LTS path 里增加 rewrite surface。

## Full run

| Benchmark | run | avg build/query tokens | answer cache | finalizer / repair |
|---|---|---:|---:|---:|
| LongMemEval-S full | `stage1_no_finalizer_v235_lme_s_full` | `85393.566 / 6579.782` | `500/0/0` | finalizer disabled, repair disabled |
| LoCoMo non-adversarial full | `stage1_no_finalizer_v235_locomo_nonadv_full` | `62015.57402597403 / 6094.017532467533` | `1540/0/0` | finalizer disabled, repair disabled |

Outputs:

```text
outputs/diagnostic/stage1_no_finalizer_v235_lme_s_full/
outputs/diagnostic/stage1_no_finalizer_v235_locomo_nonadv_full/
experiments/diagnostic/stage1_no_finalizer_v235_lme_s_full/
experiments/diagnostic/stage1_no_finalizer_v235_locomo_nonadv_full/
```

LoCoMo run manifest is dirty only because the LME experiment directory already existed before the LoCoMo run:

```text
status_short: ?? experiments/diagnostic/stage1_no_finalizer_v235_lme_s_full/
```

## Answer diff and accuracy

v235 vs v234 prediction answer diff:

| Benchmark | diff |
|---|---:|
| LongMemEval-S full | `0/500` |
| LoCoMo non-adversarial full | `0/1540` |

因此 v235 继承 v234/v233 的 paired-delta derived accuracy：

| Benchmark | strict | lenient |
|---|---:|---:|
| LongMemEval-S full | `0.832000` (`416/500`) | `0.844000` (`422/500`) |
| LoCoMo non-adversarial full | `0.794156` (`1223/1540`) | `0.819481` (`1262/1540`) |

v235 没有新增 changed answers，所以不重跑 judge。v233 的 changed-answer judge 记录仍是 accuracy 依据：

```text
experiments/diagnostic/stage1_build_memory_stateful_policy_v233_changed_vs_v231/
```

## Memory management diagnostics

| Benchmark | policy rows | operation counts |
|---|---:|---|
| LongMemEval-S | `stateful_only: 500` | create `57909`, retain_active `52410`, retain_collection_multi_value_slot `3806`, supersede `5499` |
| LoCoMo | `stateful_only: 1540` | create `232409`, retain_active `218787`, retain_collection_multi_value_slot `13470`, supersede `13622` |

## LTS 决策

升 v235 为当前本地 LTS，理由：

- 相对 v234，answer diff `0`，accuracy 和 token 不变。
- 删除 full applied 为 `0` 的 finalizer branch，减少 query-time rewrite surface。
- 保留 v233/v234 的 build-time memory lifecycle policy 和 no-repair simplification。
- 不使用任何 benchmark-specific、label、judge、sample-id 或样本级信息。

v234 保留为 no-repair 父锚点；v233 保留为 build memory stateful policy 父锚点；v231 保留为 LongMemEval-S performance anchor。

## 下一步

1. 继续清理 query-time route/guide/ledger 的兼容分支，保留仍有消融价值的能力。
2. 扩展 build-time memory operations，让 lifecycle/collection/source provenance 更直接影响 retrieval 和 context organization。
3. 探索通用 candidate pooling + source expansion + evidence utility selection，减少固定 top-k / route override 的 benchmark-oriented 感。
