# Diagnosis for stage1_dense_k12_concise_locomo_100

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 100
- avg_compiled_evidence_items: 34.14
- avg_context_chars: 8893.15
- avg_query_tokens: 2758.74
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.
- answer_style: concise
- offline_exact: 0.04
- offline_f1: 0.27571269917466834
- offline_bleu_unigram: 0.21255678202477424
- evidence_recall: 0.7653061224489796
- avg_embedding_tokens: 13489.47

## Interpretation

- Dense hybrid retrieval provides useful coverage but still misses too much category 1/3 evidence.
- The answerer often has enough evidence for semantically close answers, but temporal normalization and profile/entity grounding are not reliable.
- Next clean steps: add temporal normalization/verifier and a profile/entity typed view with source back-links.

## Next Steps

- Use offline lexical, judge, and evidence-recall scripts to diagnose quality after prediction is complete.
- Improve retrieval and compiler recall before adding more expensive answer-time reasoning.
- Keep each new method behind explicit config toggles for ablation.
