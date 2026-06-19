# v233 build memory stateful policy scope summary

## 结论

v233 升为当前本地 LTS。它不是单纯提分版本：LongMemEval-S full 比 v231 少 `1` 个 strict/lenient 正确，LoCoMo non-adversarial full 多 `1` 个 strict/lenient 正确，合并 strict/lenient 数量持平。但 v233 明确减少了当前新 goal 中最关键的系统风险：build memory 不再把普通 fact/list collection 当作 current-state lifecycle update 去覆盖，lifecycle 只管理 `preference/profile/relationship/state` 这类状态型 memory。

当前 LTS 配置：

```text
configs/stage1_build_memory_stateful_policy_v233_seeded_qwen36_no_think_build4k_cached.json
```

方法 commit：

```text
875b002a5b269714d59e807bb9c330a83c360f74
```

## 方法改动

- `build_memory.management_policy = stateful_only`。
- lifecycle managed types 固定为 `preference/profile/relationship/state`。
- `fact/event/plan` 不参与 supersede/update lifecycle；同一 slot 的多个 fact/list value 保留为 active collection memory。
- trace 中新增 `build_memory.management_policy`、`managed_memory_types` 和 `management`，记录 create/retain/supersede/collection-retain、memory layer 和 clean note。
- query/retrieval/compiler/answer/finalizer/repair 继承 v231；本版本聚焦 build-time memory management。

这一步借鉴的是 memory OS / temporal graph / episodic-semantic-profile memory 的通用思想：memory 应该有 build-time lifecycle 和 operation trace，而不是只作为 typed retrieval hint。实现仍保持 source-backed：typed memory 只来自 raw turns 和 visible metadata，不使用 gold answer、judge output、sample id 或 test feedback。

## Full run

| Benchmark | run | avg build/query tokens | answer cache | repair |
|---|---|---:|---:|---:|
| LongMemEval-S full | `stage1_build_memory_stateful_policy_v233_lme_s_full` | `85393.566 / 6637.416` | `491/9/9` | `6` triggered, `0` applied |
| LoCoMo non-adversarial full | `stage1_build_memory_stateful_policy_v233_locomo_nonadv_full` | `62015.57402597403 / 6100.013636363637` | `1532/8/8` | `2` triggered, `0` applied |

Outputs:

```text
outputs/diagnostic/stage1_build_memory_stateful_policy_v233_lme_s_full/
outputs/diagnostic/stage1_build_memory_stateful_policy_v233_locomo_nonadv_full/
experiments/diagnostic/stage1_build_memory_stateful_policy_v233_lme_s_full/
experiments/diagnostic/stage1_build_memory_stateful_policy_v233_locomo_nonadv_full/
```

LoCoMo run manifest is dirty only because the LME experiment directory already existed before the LoCoMo run:

```text
status_short: ?? experiments/diagnostic/stage1_build_memory_stateful_policy_v233_lme_s_full/
```

## Build memory management diagnostics

| Benchmark | policy rows | total/active/superseded records | collection-retain | layer counts |
|---|---:|---:|---:|---|
| LongMemEval-S | `stateful_only: 500` | `57909 / 52410 / 5499` | `3806` | episodic `7468`, semantic `12204`, profile_state `23369`, prospective `14736`, unknown `132` |
| LoCoMo | `stateful_only: 1540` | `232409 / 218787 / 13622` | `13470` | episodic `79615`, semantic `21861`, profile_state `109005`, prospective `21928` |

`collection-retain` 是 v233 的关键安全信号：多值 fact/list 不再被 lifecycle 误判为互相覆盖的 current-state slot。

## Judge accuracy

因为 v233 只有少量答案变化，性能采用 paired-delta derived 口径：先生成 full predictions，再对 v231/v233 的 changed answers 单独跑 DeepSeek dual flash judge，未变化答案沿用 v231 full judge records。

Changed-answer judge:

| Benchmark | changed rows | v231 changed strict/lenient | v233 changed strict/lenient |
|---|---:|---:|---:|
| LongMemEval-S | `4` | `4/4` | `3/4` |
| LoCoMo | `5` | `2/5` | `3/5` |

Derived full accuracy:

| Benchmark | strict | lenient |
|---|---:|---:|
| LongMemEval-S full | `0.832000` (`416/500`) | `0.844000` (`422/500`) |
| LoCoMo non-adversarial full | `0.794156` (`1223/1540`) | `0.819481` (`1262/1540`) |

Judge outputs:

```text
experiments/diagnostic/stage1_build_memory_stateful_policy_v233_changed_vs_v231/lme_v231_dual_judge.json
experiments/diagnostic/stage1_build_memory_stateful_policy_v233_changed_vs_v231/lme_v233_dual_judge.json
experiments/diagnostic/stage1_build_memory_stateful_policy_v233_changed_vs_v231/locomo_v231_dual_judge.json
experiments/diagnostic/stage1_build_memory_stateful_policy_v233_changed_vs_v231/locomo_v233_dual_judge.json
```

## Badcase notes

- LME 负向来自 `Where did I buy my new tennis racket from?`：v231 `sports store downtown` 被判对，v233 `a sports store downtown` 被双 judge 判错；语义接近，但按 judge 结果记为回退。
- LME 另有拒答和 paraphrase 变化，未改变 judge 正误。
- LoCoMo 正向主要来自 Melanie painting answer 覆盖 `horse/sunset/sunrise` 更完整。
- LoCoMo 仍有一个 bowl reminder 问题从异常字符串变成标准拒答，但 gold 需要 `art and self-expression`，仍错。

## LTS 决策

升 v233 为当前本地 LTS，理由：

- 风险收益明确：把 build memory 从 typed retrieval hint 推进到带 lifecycle policy 和 operation trace 的 memory management。
- 降低 #1 build naive 风险和 #5 memory source-backed activation 风险：memory 是否覆盖只由 source-backed typed record 的通用类型和 slot 决定，不依赖 benchmark、question、judge 或样本级规则。
- 性能没有整体数量回退：LME `-1`、LoCoMo `+1`，合并 strict/lenient counts 持平；query tokens 也小幅低于 v231。
- 局限仍在：query-time repair 还会触发但 applied 为 `0`，route/guide/ledger/finalizer 仍偏复杂；下一版应优先剪掉或统一这些无收益 query-time 补丁。

v231 保留为 LME split-best / parent anchor；v233 作为系统目标下的新 LTS。

## 下一步

1. v234：禁用或统一当前 applied 为 `0` 的 answer repair，降低 query-time 复杂度和 token 成本。
2. 补 metrics 聚合：把 `management_policy`、operation counts、layer counts 写入 `metrics.json`，减少后续手工 trace 聚合。
3. 继续把 memory operation 用到 compiler/retrieval 的通用 context organization，而不是增加 benchmark-specific prompt rule。
