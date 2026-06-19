# V182 Prompt-Safe Event-Time Candidate Map Probe

## Conclusion

V182 is not promoted to LTS. It adds a narrow prompt-side Event-Time Candidate Map, but changed-answer dual judge shows a net negative on the LoCoMo probe despite one LME probe gain.

Current LTS remains v181.

## Method

- Code/config commit: `f09e9fbbb82c16762c45e840caa28dfc82a2856c`.
- Config: `configs/stage1_prompt_safe_event_time_candidate_map_v182_qwen36_no_think_build4k_cached.json`.
- Clean selection: probe inputs were selected from question text, route, and v181 trace-only source-backed `event_time_candidate_manifest`; no gold answers, judge outputs, labels, sample ids, or test feedback were used by prediction or probe selection.
- Prompt map gate: temporal when/date questions only; high-confidence q-slot groups; no conflict; strong question-term coverage; at most one event-time group.

## Probe Results

| Probe | n | map applied | answer changed vs v181 | avg query tokens |
|---|---:|---:|---:|---:|
| LoCoMo likely-map probe | 40 | 39 | 17 | 5459.425 |
| LongMemEval-S likely-map probe | 2 | 2 | 1 | 14809.000 |

Changed-answer dual `deepseek-v4-flash` judge:

| Probe | v181 strict/lenient | v182 strict/lenient | Decision |
|---|---:|---:|---|
| LoCoMo changed subset | `17/17` / `17/17` | `15/17` / `15/17` | negative |
| LongMemEval-S changed subset | `0/1` / `0/1` | `1/1` / `1/1` | positive but too small |

Valid judge artifacts are in `diagnostic/stage1_prompt_safe_event_time_candidate_map_v182_changed_vs_v181/`. An earlier parallel judge attempt used the default flash output filenames and is ignored; the valid rerun uses version-specific `locomo_v181_*`, `locomo_v182_*`, `lme_v181_*`, and `lme_v182_*` files.

## Badcase Lessons

- Selected-context rows can contain wrapper timestamps such as `selected turn (4:04 pm on 20 January, 2023)`. V182 allowed the map extractor to treat those wrapper dates as event dates, producing an over-specific wrong answer for a festival question whose source text only supported `February 2023`.
- Relative or vague time phrases such as `a few years ago` are useful for trace organization but too risky to promote into a prompt-side event-time candidate without a stricter verifier.
- `what time` habitual questions are not event-date lookup questions; V182's map can add irrelevant date candidates even when the answer is a clock time from another row.

## Next

V183 should keep the trace-only v181 grouped manifest, but make prompt map activation more conservative:

- Strip selected-context timestamp wrappers before extracting prompt-map candidates.
- Allow only `explicit_date` and `exact_today` time kinds into the prompt map; keep `relative_phrase` in diagnostics only.
- Disable time-of-day question activation for the event-date map.
