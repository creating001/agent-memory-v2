# Diagnosis for stage1_dense_protect2_locomo_20

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 20
- avg_compiled_evidence_items: 19.8
- avg_context_chars: 5282.8
- avg_query_tokens: 1647.25
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 256.
- offline_exact: 0.0
- offline_f1: 0.11995047751106505
- offline_bleu_unigram: 0.07782635632864467
- evidence_recall: 0.65
- avg_embedding_tokens: 13489.55

## Interpretation

- Dense retrieval improves semantic evidence coverage but does not yet reach a reliable LoCoMo baseline.
- Category 1 misses need profile/entity/session views or answer-time verification; dense turn retrieval alone is insufficient.
- Judge dry-run is available, but real judge accuracy is blocked until the DeepSeek key is exported to the environment.

## Next Steps

- Use offline lexical, judge, and evidence-recall scripts to diagnose quality after prediction is complete.
- Improve retrieval and compiler recall before adding more expensive answer-time reasoning.
- Keep each new method behind explicit config toggles for ablation.
