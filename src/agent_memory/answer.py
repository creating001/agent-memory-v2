"""Answer module interfaces."""

from __future__ import annotations

from agent_memory.schemas import AnswerResult, CompiledContext, TokenUsage


class NullAnswerer:
    """Clean no-LLM answerer used for pipeline smoke tests."""

    def __init__(self, fallback_answer: str):
        self._fallback_answer = fallback_answer

    def answer(self, context: CompiledContext) -> AnswerResult:
        del context
        return AnswerResult(
            answer=self._fallback_answer,
            model="null_answerer",
            token_usage=TokenUsage(build_tokens=0, query_tokens=0),
            raw_response=None,
        )
