"""Answer module interfaces."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from common.schemas import AnswerResult, CompiledContext, TokenUsage


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


class OpenAICompatibleAnswerer:
    """Answerer for local vLLM/OpenAI-compatible chat completion services."""

    def __init__(
        self,
        base_url: str,
        model: str,
        temperature: float,
        max_tokens: int,
        timeout: float,
        max_input_tokens: int | None = None,
        api_key_env: str | None = None,
        output_format: str = "text",
    ):
        if output_format not in {"text", "json_answer"}:
            raise ValueError(f"Unsupported answer output_format: {output_format}")
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._timeout = timeout
        self._max_input_tokens = max_input_tokens
        self._api_key_env = api_key_env
        self._output_format = output_format

    def answer(self, context: CompiledContext) -> AnswerResult:
        response = self._chat_completion(context.prompt)
        message = response["choices"][0]["message"]
        raw_content = _message_text(message).strip()
        content = _parse_answer_content(raw_content, output_format=self._output_format)
        usage = response.get("usage") or {}
        prompt_tokens = int(usage.get("prompt_tokens") or 0)
        completion_tokens = int(usage.get("completion_tokens") or 0)
        total_tokens = int(usage.get("total_tokens") or prompt_tokens + completion_tokens)
        if (
            self._max_input_tokens is not None
            and prompt_tokens > self._max_input_tokens
        ):
            raise RuntimeError(
                "Answer prompt exceeded configured max_input_tokens: "
                f"{prompt_tokens} > {self._max_input_tokens}"
            )
        return AnswerResult(
            answer=content,
            model=self._model,
            token_usage=TokenUsage(build_tokens=0, query_tokens=total_tokens),
            raw_response=json.dumps(
                {
                    "id": response.get("id"),
                    "model": response.get("model"),
                    "usage": usage,
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
        )

    def _chat_completion(self, prompt: str) -> dict[str, Any]:
        endpoint = self._base_url + "/chat/completions"
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
        }
        if self._output_format == "json_answer":
            payload["response_format"] = {"type": "json_object"}
        request_body = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self._api_key_env:
            api_key = os.environ.get(self._api_key_env)
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
        request = urllib.request.Request(
            endpoint,
            data=request_body,
            headers=headers,
            method="POST",
        )
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            with opener.open(request, timeout=self._timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Answer request failed: {error.code} {body}") from error


def _message_text(message: dict[str, Any]) -> str:
    for key in ("content", "reasoning", "reasoning_content"):
        value = message.get(key)
        if value is not None:
            return str(value)
    return ""


def _parse_answer_content(raw_content: str, *, output_format: str) -> str:
    if output_format == "text":
        return raw_content
    if output_format != "json_answer":
        raise ValueError(f"Unsupported answer output_format: {output_format}")
    parsed = _extract_json_object(raw_content)
    if isinstance(parsed, dict) and parsed.get("answer") is not None:
        return str(parsed["answer"]).strip()
    return raw_content


def _extract_json_object(text: str) -> dict[str, Any] | None:
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            return None
        try:
            value = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
    return value if isinstance(value, dict) else None
