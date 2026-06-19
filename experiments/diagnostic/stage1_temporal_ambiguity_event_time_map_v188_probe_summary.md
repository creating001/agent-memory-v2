# V188 Temporal Ambiguity Event-Time Map Probe

## 结论

V188 不升 LTS，当前 LTS 仍为 v184。

V188 在 v187 的基础上新增窄的 Event-Time Candidate Map temporal ambiguity contract：只有当高置信 source-backed map 真正进入 prompt 时，才提醒 answer model 保留 `mention_time` 和 planned/future `event_time` 的区别。该设计比全局 temporal prompt 更低风险，但在三条 v184 risky activation probe 上没有恢复 v184 的 Nate 行收益，答案仍为 `2022-08-27 to 2022-08-28`。

## Clean Setting

- V188 config: `configs/stage1_temporal_ambiguity_event_time_map_v188_seeded_qwen36_no_think_build4k_cached.json`.
- Method commit: `8c3c95f` added the map-scoped temporal ambiguity contract.
- Probe input: the same three LoCoMo rows where v184 prompt map activated.
- Cache seed source: v187 activation prediction traces/predictions only; prompt-identical rows reused parent answers, and the changed Nate prompt missed/wrote once.
- No gold answers, judge outputs, benchmark labels, sample ids, test feedback, or sample-level rules are used by prediction, retrieval, compiler, answer, repair, finalizer, or cache construction.

## Probe Results

| Version | map applied | answer cache | answers | decision |
|---|---:|---|---|---|
| v184 | `3/3` | seeded from v181 full | `2023-06-20`; `2022-08-22`; insufficient | current LTS; LoCoMo full derived `+1/+1` vs v181 |
| v187 | `1/3` | `2/1/1` | `June 20, 2023`; `2022-08-27 to 2022-08-28`; insufficient | parses `this weekend` cleanly but loses v184 gain |
| v188 | `1/3` | `2/1/1` | `June 20, 2023`; `2022-08-27 to 2022-08-28`; insufficient | prompt contract did not change the answer; not LTS |

V188 has avg query tokens `5525.667`, no repair/finalizer application, and `event_time_candidate_map_temporal_ambiguity_contract=true`.

## 诊断

- A prompt-only ambiguity contract is too weak: the answer model still treats `this weekend` as the sole requested event_time even when `mention_time=2022-08-22` is available.
- The current v184 gain is tied to the risky `exact_today` activation that V185-V188 are intentionally trying to remove. Reintroducing that behavior would reduce clean/general quality.
- Next work should move away from this single event-time map branch and target broader #5 temporal organization or another risk area (#2 context noise / #3 selected-context) rather than keep tuning the same row.

## Outputs

- Probe run: `diagnostic/stage1_temporal_ambiguity_event_time_map_v188_activation_probe/`.
- Predictions: `outputs/diagnostic/stage1_temporal_ambiguity_event_time_map_v188_activation_probe/predictions.jsonl`.
- Traces: `outputs/diagnostic/stage1_temporal_ambiguity_event_time_map_v188_activation_probe/traces.jsonl`.
