# V189 Temporal Question-Reference Selected Context Probe

## Purpose

Evaluate whether a generic question-reference gate can reduce temporal selected-context noise without changing the v184 LTS backbone.

V189 inherits v184 and only adds `require_question_reference: true` to the `temporal_lookup` selected-context route override. The gate uses question text only and does not use gold answers, judge output, benchmark labels, sample ids, test feedback, or sample-level rules during prediction.

## Run

- Config: `configs/stage1_temporal_question_ref_selected_context_v189_seeded_qwen36_no_think_build4k_cached.json`
- Method commit: `dd62084ba5839038c3988b71ebd92dc73f36a0a2`
- Output: `outputs/diagnostic/stage1_temporal_question_ref_selected_context_v189_activation_probe/`
- Experiment record: `experiments/diagnostic/stage1_temporal_question_ref_selected_context_v189_activation_probe/`
- Input: `outputs/diagnostic/stage1_segment_local_event_time_candidate_map_v185_activation_probe/input.jsonl`

Command:

```bash
python scripts/run_stage1.py \
  --input outputs/diagnostic/stage1_segment_local_event_time_candidate_map_v185_activation_probe/input.jsonl \
  --config configs/stage1_temporal_question_ref_selected_context_v189_seeded_qwen36_no_think_build4k_cached.json \
  --run-id stage1_temporal_question_ref_selected_context_v189_activation_probe \
  --benchmark locomo \
  --subset non_adversarial_activation3 \
  --experiment-kind diagnostic \
  --workers 1
```

## Results

| Item | Result |
|---|---:|
| Samples | `3` |
| selected-context applied | `0/3` |
| avg selected-context rows | `0.000` |
| avg query tokens | `4898.667` |
| answer cache | `0/3/3` hits/misses/writes |
| repair/finalizer applied | `0/3` / `0/3` |

Compared with the v186-v188 three-row probes, V189 reduces selected-context materialization from `3/3` to `0/3` and lowers avg query tokens from roughly `5423-5526` to `4898.667`. This is useful evidence for risk #2/#3: temporal neighbor expansion should not be route-only when the question has no local reference signal.

However, V189 answers the key current-LTS delta row as `2022-08-27 to 2022-08-28`, matching the already rejected v181/v186-v188 behavior rather than v184's `2022-08-22`. Existing v184-vs-v181 changed-answer dual judge records show that row is strict/lenient wrong for the v181-style answer and strict/lenient correct for v184. Therefore V189 would lose the v184 LoCoMo `+1/+1` paired-delta gain.

## Decision

Do not promote V189 to LTS.

Keep the finding: question-reference gating is a clean and general way to reduce selected-context risk and token cost, but applying it bluntly to all temporal selected-context removes useful local context on at least one current-LTS positive row. The next direction should be a source-backed evidence selector rather than a pure question-text gate: keep local context when it supports a high-confidence event/action/participant slot, and suppress it when it only contributes wrapper dates or unrelated nearby `today` signals.
