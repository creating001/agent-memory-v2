# Diagnosis for stage1_dense_k12_concise_locomo_20

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 20
- avg_compiled_evidence_items: 34.55
- avg_context_chars: 9038.65
- avg_query_tokens: 2795.35
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.
- answer_style: concise
- offline_exact: 0.05
- offline_f1: 0.1859956416132887
- offline_bleu_unigram: 0.1407515401265401
- evidence_recall: 0.7
- avg_embedding_tokens: 13489.55

## Interpretation

- Concise prompting helps LoCoMo lexical overlap but does not address evidence recall or temporal reasoning.
- The candidate needs a temporal verifier before it can be trusted on date questions.

## Next Steps

- Use offline lexical, judge, and evidence-recall scripts to diagnose quality after prediction is complete.
- Improve retrieval and compiler recall before adding more expensive answer-time reasoning.
- Keep each new method behind explicit config toggles for ablation.
