# Diagnosis for stage1_dense_k12_temporal_locomo_20

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 20
- avg_compiled_evidence_items: 34.55
- avg_context_chars: 9165.55
- avg_query_tokens: 2822.9
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.
- answer_style: concise
- temporal_grounding: True
- offline_exact: 0.05
- offline_f1: 0.1800437691989425
- offline_bleu_unigram: 0.1329007797757798
- evidence_recall: 0.7
- avg_embedding_tokens: 13489.55

## Interpretation

- Prompt-level temporal normalization helps when the right evidence is present.
- It does not solve retrieval misses, and can amplify wrong evidence into a plausible absolute date.
- The next temporal step should be a source-grounded verifier that checks date derivations against selected evidence rows.

## Next Steps

- Use offline lexical, judge, and evidence-recall scripts to diagnose quality after prediction is complete.
- Improve retrieval and compiler recall before adding more expensive answer-time reasoning.
- Keep each new method behind explicit config toggles for ablation.
