# V185/V186 Event-Time Candidate Map Probe

## Conclusion

V185 and V186 are not promoted to LTS.

V185 fixes two v184 false-positive `exact_today` prompt-map activations by binding event-time phrases to the same local-context segment as the target slot, but it still allows a role-mismatch prompt-map candidate. V186 adds role matching and removes all three risky prompt-map activations in this probe, but it also reverts one v184 LoCoMo gain, so current LTS remains v184.

## Clean Setting

- V185 config: `configs/stage1_segment_local_event_time_candidate_map_v185_seeded_qwen36_no_think_build4k_cached.json`.
- V186 config: `configs/stage1_role_matched_event_time_candidate_map_v186_seeded_qwen36_no_think_build4k_cached.json`.
- Method commits:
  - `a55c3c7` added v185 segment-local, coverage-ranked event-time map.
  - `871a06a` added v186 role-matched event-time map.
- Cache seed source: v181 and v184 full prediction traces/predictions only.
- No gold answers, judge outputs, benchmark labels, sample ids, test feedback, or sample-level rules are used by prediction, retrieval, compiler, answer, repair, finalizer, or cache construction.

## Probe Results

Probe rows are the three LoCoMo rows where v184 prompt-map activated:

| Version | map applied | answers | decision |
|---|---:|---|---|
| v184 | `3/3` | `2023-06-20`; `2022-08-22`; insufficient | current LTS; LoCoMo full derived `+1/+1` vs v181 |
| v185 | `1/3` | `June 20, 2023`; `2022-08-27 to 2022-08-28`; insufficient | rejects two wrapper-time false positives, but still maps a James row for a John question |
| v186 | `0/3` | `June 20, 2023`; `2022-08-27 to 2022-08-28`; insufficient | risk lower than v184/v185, but loses the v184 gain on the Nate row |

V186 answer cache hits were `3/3`, showing all three prompts matched seeded parent prompts after the risky maps were removed.

## Diagnosis

- Segment-local binding is useful: it blocks `today` from a nearby turn from being attached to the selected target turn.
- Coverage-first ranking is useful: it prevents marker count from dominating target-slot specificity.
- Role matching is necessary: without it, a row can match a target name only because it addresses that person while describing the speaker's own dated event.
- The current v184 gain on the Nate row appears tied to a risky/noisy prompt-map perturbation rather than a cleaner source-backed target event-time activation. Removing the risk reverts that answer to v181.

## Outputs

- V185 probe: `diagnostic/stage1_segment_local_event_time_candidate_map_v185_activation_probe/`.
- V186 probe: `diagnostic/stage1_role_matched_event_time_candidate_map_v186_activation_probe/`.
