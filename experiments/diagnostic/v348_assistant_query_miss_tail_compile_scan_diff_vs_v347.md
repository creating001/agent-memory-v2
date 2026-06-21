# v348 assistant-query-miss tail scan vs v347

## Purpose

Test a conservative query-token reduction policy: keep raw evidence row set/order unchanged, keep top evidence rows unchanged, keep user rows unchanged, and truncate only low-rank `assistant` rows that do not contain content terms from the question.

This is a diagnostic only. It does not use gold answers, judge output, benchmark labels, sample ids, test feedback, or sample-level rules.

## Configs

- Candidate: `configs/stage1_assistant_query_miss_tail_v348_seeded_qwen36_no_think_build4k_cached.json`
- Compile scan: `configs/stage1_assistant_query_miss_tail_v348_compile_scan.json`
- Baseline: `configs/stage1_guard_only_short_packet_v347_seeded_qwen36_no_think_build4k_cached.json`

## Compile-Scan Results

| Scope | Prompt changed | Row set changed | Row order changed | Avg prompt char delta | Notes |
|---|---:|---:|---:|---:|---|
| LongMemEval-S probe50 | `3/50` | `0/50` | `0/50` | `-57.84` | Only `0.04` truncated assistant rows per sample on average. |
| LoCoMo non-adversarial probe50 | `2/50` | `0/50` | `0/50` | `-0.96` | Nearly no effect because LoCoMo row roles are usually participant names, not literal `assistant`. |

Context block attribution on v347 showed `Memory Context` is the dominant query-token source: LME `14858.1` avg chars and LoCoMo `12639.3` avg chars, while v348 only reduced the LME memory-context block to `14802.6` avg chars and left LoCoMo unchanged.

## Decision

Do not promote v348 and do not spend judge budget on it. The policy is clean and low-risk, but the measured query-token reduction is too small to matter. The next query-token pass should target lossless prompt presentation such as compact row headers or build-owned workspace component replacement, not ultra-conservative assistant-tail truncation.

