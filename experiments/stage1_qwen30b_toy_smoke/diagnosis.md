# Diagnosis for stage1_qwen30b_toy_smoke

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 1
- avg_compiled_evidence_items: 3.0
- avg_context_chars: 867.0
- avg_query_tokens: 314.0
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 256.

## Next Steps

- Use offline lexical, judge, and evidence-recall scripts to diagnose quality after prediction is complete.
- Improve retrieval and compiler recall before adding more expensive answer-time reasoning.
- Keep each new method behind explicit config toggles for ablation.
