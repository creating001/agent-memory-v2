# Diagnosis for stage1_dense_protect2_k12_locomo_20

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 20
- avg_compiled_evidence_items: 34.55
- avg_context_chars: 8944.85
- avg_query_tokens: 2796.55
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 256.
- offline_exact: 0.0
- offline_f1: 0.13776068080452944
- offline_bleu_unigram: 0.08851153985817861
- evidence_recall: 0.7
- avg_embedding_tokens: 13489.55

## Interpretation

- Wider source coverage helps slightly but does not solve LoCoMo category 1.
- Query-token budget remains acceptable, but evidence recall gain is too small to justify making k12 the default without stronger judge results.
- Profile/entity/session-level views are the next clean retrieval direction.

## Next Steps

- Use offline lexical, judge, and evidence-recall scripts to diagnose quality after prediction is complete.
- Improve retrieval and compiler recall before adding more expensive answer-time reasoning.
- Keep each new method behind explicit config toggles for ablation.
