"""Offline metrics that run only after prediction is complete."""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable, Mapping
from typing import Any


TOKEN_PATTERN = re.compile(r"[\w]+", re.UNICODE)


def evaluate_offline(
    predictions: Iterable[Mapping[str, Any]],
    labels: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    prediction_by_key = {str(item.get("record_key")): item for item in predictions}
    label_by_key = {str(item.get("record_key")): item for item in labels}
    shared_keys = [key for key in label_by_key if key in prediction_by_key]

    exact_scores = []
    f1_scores = []
    bleu_scores = []
    by_type: dict[str, list[float]] = {}
    missing_gold = 0

    for key in shared_keys:
        prediction = str(prediction_by_key[key].get("answer", ""))
        gold = label_by_key[key].get("gold_answer")
        if gold is None:
            missing_gold += 1
            continue
        gold_text = _stringify_gold(gold)
        exact = float(_normalize_text(prediction) == _normalize_text(gold_text))
        f1 = token_f1(prediction, gold_text)
        bleu = unigram_bleu(prediction, gold_text)
        exact_scores.append(exact)
        f1_scores.append(f1)
        bleu_scores.append(bleu)

        group = _group_name(label_by_key[key])
        by_type.setdefault(group, []).append(exact)

    return {
        "n_predictions": len(prediction_by_key),
        "n_labels": len(label_by_key),
        "n_joined": len(shared_keys),
        "n_missing_gold": missing_gold,
        "accuracy_exact": _average(exact_scores),
        "f1": _average(f1_scores),
        "bleu_unigram": _average(bleu_scores),
        "by_type": {
            group: {"accuracy_exact": _average(scores), "n": len(scores)}
            for group, scores in sorted(by_type.items())
        },
        "metrics_note": (
            "Offline lexical metrics only. Judge-based benchmark accuracy should be "
            "computed in a separate offline step and must not feed prediction."
        ),
    }


def token_f1(prediction: str, gold: str) -> float:
    prediction_tokens = _tokens(prediction)
    gold_tokens = _tokens(gold)
    if not prediction_tokens and not gold_tokens:
        return 1.0
    if not prediction_tokens or not gold_tokens:
        return 0.0
    common = Counter(prediction_tokens) & Counter(gold_tokens)
    overlap = sum(common.values())
    if overlap == 0:
        return 0.0
    precision = overlap / len(prediction_tokens)
    recall = overlap / len(gold_tokens)
    return 2 * precision * recall / (precision + recall)


def unigram_bleu(prediction: str, gold: str) -> float:
    prediction_tokens = _tokens(prediction)
    gold_tokens = _tokens(gold)
    if not prediction_tokens and not gold_tokens:
        return 1.0
    if not prediction_tokens or not gold_tokens:
        return 0.0
    common = Counter(prediction_tokens) & Counter(gold_tokens)
    precision = sum(common.values()) / len(prediction_tokens)
    brevity_penalty = min(1.0, len(prediction_tokens) / len(gold_tokens))
    return precision * brevity_penalty


def _stringify_gold(gold: Any) -> str:
    if isinstance(gold, list):
        return " / ".join(str(item) for item in gold)
    return str(gold)


def _group_name(label: Mapping[str, Any]) -> str:
    value = label.get("question_type") or label.get("category") or "unknown"
    return str(value)


def _tokens(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(_normalize_text(text))


def _normalize_text(text: str) -> str:
    return " ".join(TOKEN_PATTERN.findall(text.lower()))


def _average(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)
