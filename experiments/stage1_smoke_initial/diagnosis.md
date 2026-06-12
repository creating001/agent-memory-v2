# Diagnosis for stage1_smoke_initial

## Summary

The run validates pipeline shape and traceability, not benchmark quality. The null answerer makes zero LLM calls, so token cost is zero and answer accuracy is not meaningful.

## Observations

- samples_processed: 1
- avg_compiled_evidence_items: 3.0
- avg_context_chars: 867.0

## Next Steps

- Add dataset adapters that strip gold/judge/type/id fields before prediction.
- Add local answer-model client behind the existing answerer interface.
- Add offline evaluation scripts that consume predictions and gold after prediction is complete.
- Add dense/BM25 hybrid retrieval and source-grounded compiler ablations.
