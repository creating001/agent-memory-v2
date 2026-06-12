# Diagnosis for stage1_hit_priority_w2_locomo_3

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 3
- avg_compiled_evidence_items: 24.0
- avg_context_chars: 6620.666666666667
- avg_query_tokens: 2018.6666666666667
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 256.
- offline_exact: 0.0
- offline_f1: 0.10565476190476192
- offline_bleu_unigram: 0.06607054148037754
- evidence_recall: 0.6666666666666666

## Interpretation

- Wider source expansion recovers a nearby evidence turn for the Melanie sunrise question.
- It also increases context noise and can hurt temporal precision, so the mainline should prefer adaptive expansion over a fixed larger window.

## Next Steps

- Use offline lexical, judge, and evidence-recall scripts to diagnose quality after prediction is complete.
- Improve retrieval and compiler recall before adding more expensive answer-time reasoning.
- Keep each new method behind explicit config toggles for ablation.
