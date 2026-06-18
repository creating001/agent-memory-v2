# v172 changed-answer judge vs v171

## 范围

- benchmark：LoCoMo non-adversarial full
- changed answers：`1/1540`
- record_key：`6658015006384a53816e150c`
- question：`What is Evan's favorite food?`
- v171 answer：`The provided information is not enough.`
- v172 answer：`ginger snaps`

## Judge

Dual `deepseek-v4-flash`，temperature `0`，default thinking。Gold answer 只在离线 judge 阶段读取，不进入 prediction、retrieval、compiler、answer、repair、cache 或配置构造。

| Version | strict | lenient |
|---|---:|---:|
| v171 | `0/1` | `0/1` |
| v172 | `1/1` | `1/1` |

Judge artifacts：

- `v171_dual_judge.json`
- `v172_dual_judge.json`
- `v171_flash1.json`
- `v171_flash2.json`
- `v172_flash1.json`
- `v172_flash2.json`
