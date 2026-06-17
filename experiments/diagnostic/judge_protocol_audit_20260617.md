# Judge protocol audit 2026-06-17

## 目的

记录当前正式 judge 口径：`deepseek-v4-flash` 独立跑两遍，使用 strict/lenient 聚合。

本诊断只读取 prediction 后的 offline judge 结果、labels 和 predictions；不进入 prediction、retrieval、compiler、answer、verifier 或 cache build 流程。

## 当前协议

- judge run 1：`deepseek-v4-flash`，temperature `0`，thinking default。
- judge run 2：`deepseek-v4-flash`，temperature `0`，thinking default。
- LoCoMo judge prompt：只输出单个 label，`CORRECT` 或 `WRONG`，不输出 reasoning / JSON。
- Dual metrics：strict 表示两遍 flash 都判 `CORRECT`；lenient 表示任一遍 flash 判 `CORRECT`。
- 单次 flash accuracy 只作为诊断指标，不作为唯一主指标。

## 已有稳定性观察

### LoCoMo v102 qwen3.6 no-thinking

Run: `formal/stage1_spacing_profile_v102_qwen36_no_think_build4k_locomo_nonadv_full_1526d1c`

- flash run 1 accuracy：`1212/1540 = 0.787013`
- flash run 2 accuracy：`1213/1540 = 0.787662`
- 两遍分歧：`33/1540`
- run 1 WRONG / run 2 CORRECT：`17`
- run 1 CORRECT / run 2 WRONG：`16`

结论：两遍 flash 的总体 accuracy 基本一致，分歧方向近似对称。正式结果应使用 dual flash strict/lenient，而不是单次 flash。

## 结论

- 当前正式 judge 协议为 dual flash：`deepseek-v4-flash` 跑两遍。
- strict 是保守下界，lenient 是当前 target 判断口径。
- 这不影响 prediction clean，因为 judge 仍是 offline-only。
