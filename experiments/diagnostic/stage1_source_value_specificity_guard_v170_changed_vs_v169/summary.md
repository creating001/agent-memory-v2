# v170 Changed-Answer Judge vs v169

Purpose: evaluate the narrow `source_value_specificity_preservation` finalizer
candidate on only the answers changed relative to v169.

Scope:

- LongMemEval-S full changed answers: `1`
- LoCoMo non-adversarial full changed answers: `8`

Dual `deepseek-v4-flash` judge, temperature `0`, default thinking:

| Benchmark | v169 strict/lenient | v170 strict/lenient | Decision |
|---|---:|---:|---|
| LongMemEval-S changed set | `1/1` / `1/1` | `1/1` / `1/1` | hold |
| LoCoMo changed set | `6/8` / `7/8` | `7/8` / `7/8` | positive strict, no lenient regression |

The only strict improvement is `aptitude test` -> `military aptitude test`.
No changed-set strict or lenient regressions were observed.
