# Diagnosis: stage1_temporal_source_link_v19_lme_s_full_42dca7d

## 结论

v19 不是主线：LongMemEval-S full 从 v18 的 `0.732` 降到 `0.714`，净 `-9`，同时 avg query tokens 从 `5117.622` 增到 `5203.986`。这说明 temporal source-linked memory guide 会干扰 LME 的 answer selection，不能直接作为 v18 的统一增强。

## 分题型

| type | v19 | v18 | delta |
|---|---:|---:|---:|
| knowledge-update | 62 / 78 | 64 / 78 | -2 |
| multi-session | 71 / 133 | 74 / 133 | -3 |
| single-session-assistant | 51 / 56 | 52 / 56 | -1 |
| single-session-preference | 11 / 30 | 11 / 30 | 0 |
| single-session-user | 66 / 70 | 66 / 70 | 0 |
| temporal-reasoning | 96 / 133 | 99 / 133 | -3 |

目标本来是帮 temporal/source-linked 组织，但 temporal-reasoning 反而低 3 条，multi-session 也低 3 条。

## Prompt 诊断

- structured guide prompts：`492/500`
- row index prompts：`492/500`
- activated build memory prompts：`154/500`
- activated build memory prompts by route：`temporal_lookup=154`
- temporal_lookup route count：`161`
- temporal aid prompts：`198/500`
- avg selected memory records：`1.612`
- max selected memory records：`6`

触发逻辑符合设计，没有越界到 fact/list/profile route；负向主要来自方法本身的 source-map 噪声，而不是触发失控。

## 对照

| compare | net | v19-only | other-only |
|---|---:|---:|---:|
| v18 | -9 | 17 | 26 |
| v17 | -4 | 20 | 24 |
| v14 | +5 | 31 | 26 |
| v13 | 0 | 31 | 31 |
| clean naive RAG | +13 | 40 | 27 |

v19 比 v14 高，是因为继承了 v18 的 hybrid retrieval；但相对 v18 的 source-linked temporal guide 是负收益。

## 取舍

- 不继续跑 LoCoMo full，避免把明显不统一的 LME 负向方法扩展成昂贵正式实验。
- 保留 compiler 的 route override 能力，因为它是通用框架能力，后续可以用于更谨慎的 compiler ablation。
- 删除 `configs/stage1_temporal_source_link_v19_cached.json` 当前主配置入口，只在本实验目录保留 config snapshot。

## 下一步

下一轮不要再把 build memory 文本/字段直接放进 prompt 作为 guide。更值得尝试的是 evidence-level 组织而非 memory-line 组织：例如对 retrieved rows 做 session/time/entity grouping、source diversity 或 conflict-aware ordering，让 answer model 更好使用 raw rows，但不要额外暴露二手 memory 摘要。
