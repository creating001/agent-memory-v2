# v331 Inline Memory Header Probe

## Purpose

Test a low-risk query-token reduction that keeps v288 memory, retrieval, guide, answer contract, raw evidence rows, and verifier behavior unchanged, but renders Memory Context metadata inline.

## Method

- config: `configs/stage1_inline_memory_header_v331_seeded_qwen36_no_think_build4k_cached.json`
- commit: `15c2d6752f99af804942df45e7f0573030b021b8`
- code change: `memory_context_header_format=inline`
- unchanged: evidence selection, raw row text, compact query contract, guide semantics, answer JSON schema, verifier
- clean note: no labels, judge output, benchmark tags, sample ids, gold answers, or test feedback enter prediction

## Verification

- `python -m py_compile src/memory/compiler.py src/memory/pipeline.py scripts/run_stage1.py`
- `python -m unittest discover -s src/tests` -> 405 tests OK
- output integrity:
  - `outputs/diagnostic/v331_lme_probe50/predictions.jsonl`: 50 lines, 0 bad JSON, 0 duplicate keys
  - `outputs/diagnostic/v331_lme_probe50/traces.jsonl`: 50 lines, 0 bad JSON
  - `outputs/diagnostic/v331_locomo_probe50/predictions.jsonl`: 50 lines, 0 bad JSON, 0 duplicate keys
  - `outputs/diagnostic/v331_locomo_probe50/traces.jsonl`: 50 lines, 0 bad JSON

## Token Results

| Scope | avg build tokens | avg query tokens | Notes |
|---|---:|---:|---|
| LME smoke5 | 92386.0 | 5438.6 | changed answers vs v288 first/full match: 1/5, only insufficiency wording |
| LoCoMo smoke5 | 45868.0 | 5803.4 | changed answers vs v288 full first keys: 0/5 |
| LME probe50 | 86398.54 | 5525.84 | below 6K target |
| LoCoMo probe50 | 45868.0 | 5720.06 | below 6K target |

## Changed-Answer Judge

Changed answers were judged with offline dual `deepseek-v4-flash` only on changed subsets.

| Scope | changed answers | v288 strict/lenient correct | v331 strict/lenient correct | Decision |
|---|---:|---:|---:|---|
| LME probe50 changed vs v288 | 7/50 | 5/7, 5/7 | 4/7, 4/7 | regression by 1 changed item |
| LoCoMo probe50 changed vs v288 | 20/50 | 16/20, 18/20 | 16/20, 18/20 | neutral |

Judge paths:

```text
outputs/diagnostic/v331_lme_probe50_changed_vs_v288/base_dual_judge.json
outputs/diagnostic/v331_lme_probe50_changed_vs_v288/new_dual_judge.json
outputs/diagnostic/v331_locomo_probe50_changed_vs_v288/base_dual_judge.json
outputs/diagnostic/v331_locomo_probe50_changed_vs_v288/new_dual_judge.json
```

## Diagnosis

The formatting change reduced probe query tokens below the 6K target on both benchmarks, but it still changed answer behavior. Most LME changes were formatting or shorter insufficiency wording, but one LME changed item lost enough answer specificity to be judged wrong. LoCoMo changed-answer judge was neutral.

This suggests that even answer-visible Memory Context header compression can perturb the answer model. Do not promote v331 to LTS. The next token-reduction attempt should either preserve the explicit `Date:`/`Session:` semantics, move compression to non-answer-visible trace/guide blocks, or reduce query complexity by removing/downstreaming guide layers rather than changing raw evidence presentation.

