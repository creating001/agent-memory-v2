# Diagnosis for stage1_concise_lme_s_20

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 20
- avg_compiled_evidence_items: 9.85
- avg_context_chars: 11278.6
- avg_query_tokens: 2841.85
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.
- answer_style: concise
- offline_exact: 0.5
- offline_f1: 0.7513194444444445
- offline_bleu_unigram: 0.6910081585081584
- evidence_recall: 1.0

## Interpretation

- Answer style, not retrieval, was the dominant LongMemEval issue on this slice.
- Concise prompting substantially improves lexical metrics without increasing retrieval breadth or token cost.
- Real DeepSeek judge accuracy is still needed before claiming benchmark accuracy.

## Next Steps

- Use offline lexical, judge, and evidence-recall scripts to diagnose quality after prediction is complete.
- Improve retrieval and compiler recall before adding more expensive answer-time reasoning.
- Keep each new method behind explicit config toggles for ablation.
