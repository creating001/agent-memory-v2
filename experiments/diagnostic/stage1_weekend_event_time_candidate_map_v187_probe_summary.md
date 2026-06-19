# V187 Weekend Event-Time Candidate Map Probe

## 结论

V187 不升 LTS，当前 LTS 仍为 v184。

V187 在 v186 的 segment-local、coverage-ranked、role-matched Event-Time Candidate Map 上补了 `this weekend` / `coming weekend` / `upcoming weekend` 解析，并在 prompt map 中同时暴露 `mention_time` 和 `event_time`，方法上比 v184 更 clean。但在三条 v184 risky activation probe 上，V187 仍把 Nate row 回答成 `2022-08-27 to 2022-08-28`，没有保住 v184 对该行的正确答案 `2022-08-22`。因此它降低了部分 activation 风险，但相对当前 LTS 会丢 LoCoMo `+1/+1`，不能替代 v184。

## Clean Setting

- V187 config: `configs/stage1_weekend_event_time_candidate_map_v187_seeded_qwen36_no_think_build4k_cached.json`.
- Method commit: `adf6275` added weekend relative-time parsing and mention/event time map output.
- Probe input: the same three LoCoMo rows where v184 prompt map activated.
- Cache seed source: v181 and v184 full prediction traces/predictions only.
- No gold answers, judge outputs, benchmark labels, sample ids, test feedback, or sample-level rules are used by prediction, retrieval, compiler, answer, repair, finalizer, or cache construction.

## Probe Results

| Version | map applied | answers | decision |
|---|---:|---|---|
| v184 | `3/3` | `2023-06-20`; `2022-08-22`; insufficient | current LTS; LoCoMo full derived `+1/+1` vs v181 |
| v186 | `0/3` | `June 20, 2023`; `2022-08-27 to 2022-08-28`; insufficient | cleaner activation, but loses the v184 Nate gain |
| v187 | `1/3` | `June 20, 2023`; `2022-08-27 to 2022-08-28`; insufficient | parses `this weekend` cleanly, but still loses the v184 Nate gain |

V187 answer cache was `2/1/1`: two rows reused seeded parent answers and only the Nate row missed/wrote because the clean `this weekend` map changed the prompt. The run has `event_time_candidate_map_applied_count=1/3`, avg query tokens `5478.667`, and no repair/finalizer application.

## 诊断

- `this weekend` 解析本身是通用且 clean 的：它只依赖 mention date 和 raw source phrase，不依赖 gold answer 或样本级信息。
- 同时展示 `mention_time=2022-08-22` 与 `event_time=2022-08-27 to 2022-08-28` 仍不足以让 answer model 在歧义问题中保留“说这件事的时间”。这说明问题不只是 event-time extraction，而是 temporal answer contract 还没有处理“mention time vs planned event time”的歧义。
- 下一步不应继续单纯扩大 Event-Time Candidate Map；更稳的方向是做 source-backed temporal ambiguity contract 或 query-time organization，让模型在计划/未来事件场景下显式区分 stated-at time 与 scheduled event time。

## Outputs

- Probe run: `diagnostic/stage1_weekend_event_time_candidate_map_v187_activation_probe/`.
- Predictions: `outputs/diagnostic/stage1_weekend_event_time_candidate_map_v187_activation_probe/predictions.jsonl`.
- Traces: `outputs/diagnostic/stage1_weekend_event_time_candidate_map_v187_activation_probe/traces.jsonl`.
