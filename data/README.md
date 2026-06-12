# Data

Large benchmark files should live outside git or be linked into this directory.

Prediction JSONL for `scripts/run_stage1.py` must contain only clean runtime fields:

```json
{
  "record_key": "optional-runner-only-key",
  "question": "What does Alex prefer to drink?",
  "question_time": "2025-01-03",
  "sessions": [
    {
      "session_id": "session_0001",
      "date": "2025-01-01",
      "turns": [
        {"role": "user", "text": "I prefer jasmine tea.", "timestamp": "2025-01-01T09:00:00"}
      ]
    }
  ]
}
```

Do not include gold answers, judge outputs, benchmark labels, sample ids, qids, or row indices in prediction input files. Dataset adapters should strip those fields before calling the prediction pipeline.

Use `scripts/prepare_dataset.py` to split raw benchmark rows into:

- `prediction_input.jsonl`: clean runtime input for prediction.
- `labels.jsonl`: offline-only answers/types/categories for evaluation.
