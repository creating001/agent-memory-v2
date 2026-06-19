# V184 Seeded Strict Event-Time Candidate Map Probe

## Conclusion

V184 keeps the strict v183 prompt-map method and fixes the evaluation cache design: prompt-identical rows reuse v181 answers from a seeded answer cache, so answer changes are attributable to prompt changes rather than local model regeneration noise.

On the v182 likely-map probe set, v184 removes the v182 LoCoMo losses and is a valid full-run candidate. It is not promoted from probe alone.

## Method

- Method commit: `b56215b4b6d2a38036ac60533e744d0a96d35d26`.
- Config: `configs/stage1_strict_event_time_candidate_map_v184_seeded_qwen36_no_think_build4k_cached.json`.
- Cache seed source: v181 full prediction traces and predictions only.
- Cache seed clean note: no labels, gold answers, judge outputs, benchmark categories, sample ids, or test feedback were read.
- Strict map gate:
  - strip selected-context timestamp wrappers before event-time extraction;
  - allow only `exact_today` and `explicit_date` into the prompt map;
  - disable time-of-day question activation;
  - keep relative/vague candidates trace-only in the v181 grouped manifest.

## Probe Results

| Probe | n | map applied | prompt changed | answer diff vs v181 | answer cache hit/miss/write |
|---|---:|---:|---:|---:|---|
| LoCoMo likely-map probe | 40 | 1 | 1 | 1 | `39/1/1` |
| LongMemEval-S likely-map probe | 2 | 0 | 0 | 0 | `2/0/0` |

The single LoCoMo answer change is a date-format normalization:

- record `f32506eabf8b9384df950965`: v181 `June 20, 2023`; v184 `2023-06-20`.

Changed-answer dual `deepseek-v4-flash` judge is tied:

| Probe | v181 strict/lenient | v184 strict/lenient |
|---|---:|---:|
| LoCoMo changed subset | `1/1` / `1/1` | `1/1` / `1/1` |

## V183 Cache Lesson

V183 used the same strict map method but a fresh answer cache. On the same LoCoMo probe, only `1/40` prompts changed, yet `9/40` answers differed because prompt-identical rows were regenerated. Those differences are evaluation noise, not method effects. V184 fixes this with a seeded cache and should be used for full validation.

## Next

Run v184 on LongMemEval-S full and LoCoMo non-adversarial full with the seeded cache. If full answer diff is zero or changed-answer judge is non-negative, v184 can be considered for LTS because it lowers #5 prompt-map risk while preserving v181 performance.
