"""Offline judge prompt construction and result parsing."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from typing import Any


LOCOMO_TEMPLATE = """Your task is to label an answer to a question as 'CORRECT' or 'WRONG'. You will be given the following data:
    (1) a question (posed by one user to another user),
    (2) a 'gold' (ground truth) answer,
    (3) a generated answer
which you will score as CORRECT/WRONG.

The point of the question is to ask about something one user should know about the other user based on their prior conversations.
The gold answer will usually be a concise and short answer that includes the referenced topic, for example:
Question: Do you remember what I got the last time I went to Hawaii?
Gold answer: A shell necklace
The generated answer might be much longer, but you should be generous with your grading - as long as it touches on the same topic as the gold answer, it should be counted as CORRECT.

For time related questions, the gold answer will be a specific date, month, year, etc. The generated answer might be much longer or use relative time references (like "last Tuesday" or "next month"), but you should be generous with your grading - as long as it refers to the same date or time period as the gold answer, it should be counted as CORRECT. Even if the format differs (e.g., "May 7th" vs "7 May"), consider it CORRECT if it's the same date.

Now it's time for the real question:
Question: {question}
Gold answer: {gold_answer}
Generated answer: {generated_answer}

Return exactly one label: CORRECT or WRONG.
Do not include explanations, JSON, markdown, code fences, or any other text."""


LONGMEMEVAL_DEFAULT_TEMPLATE = """I will give you a question, a correct answer, and a response from a model. Please answer yes if the response contains the correct answer. Otherwise, answer no. If the response is equivalent to the correct answer or contains all the intermediate steps to get the correct answer, you should also answer yes. If the response only contains a subset of the information required by the answer, answer no.

Question: {question}

Correct Answer: {gold_answer}

Model Response: {generated_answer}

Is the model response correct? Answer yes or no only."""


LONGMEMEVAL_TEMPORAL_TEMPLATE = """I will give you a question, a correct answer, and a response from a model. Please answer yes if the response contains the correct answer. Otherwise, answer no. If the response is equivalent to the correct answer or contains all the intermediate steps to get the correct answer, you should also answer yes. If the response only contains a subset of the information required by the answer, answer no. In addition, do not penalize off-by-one errors for the number of days. If the question asks for the number of days/weeks/months, etc., and the model makes off-by-one errors (e.g., predicting 19 days when the answer is 18), the model's response is still correct.

Question: {question}

Correct Answer: {gold_answer}

Model Response: {generated_answer}

Is the model response correct? Answer yes or no only."""


LONGMEMEVAL_KNOWLEDGE_UPDATE_TEMPLATE = """I will give you a question, a correct answer, and a response from a model. Please answer yes if the response contains the correct answer. Otherwise, answer no. If the response contains some previous information along with an updated answer, the response should be considered as correct as long as the updated answer is the required answer.

Question: {question}

Correct Answer: {gold_answer}

Model Response: {generated_answer}

Is the model response correct? Answer yes or no only."""


LONGMEMEVAL_PREFERENCE_TEMPLATE = """I will give you a question, a rubric for desired personalized response, and a response from a model. Please answer yes if the response satisfies the desired response. Otherwise, answer no. The model does not need to reflect all the points in the rubric. The response is correct as long as it recalls and utilizes the user's personal information correctly.

Question: {question}

Rubric: {gold_answer}

Model Response: {generated_answer}

Is the model response correct? Answer yes or no only."""


LONGMEMEVAL_ABSTENTION_TEMPLATE = """I will give you an unanswerable question, an explanation, and a response from a model. Please answer yes if the model correctly identifies the question as unanswerable. The model could say that the information is incomplete, or some other information is given but the asked information is not.

Question: {question}

Explanation: {gold_answer}

Model Response: {generated_answer}

Does the model correctly identify the question as unanswerable? Answer yes or no only."""


@dataclass(frozen=True)
class JudgeExample:
    record_key: str
    question: str
    gold_answer: str
    generated_answer: str
    benchmark: str
    question_type: str | None = None


def build_judge_prompt(example: JudgeExample) -> str:
    benchmark = example.benchmark.lower()
    template = LOCOMO_TEMPLATE if benchmark == "locomo" else _longmemeval_template(example)
    return template.format(
        question=example.question,
        gold_answer=example.gold_answer,
        generated_answer=example.generated_answer,
    )


def parse_judge_label(benchmark: str, response_text: str) -> str:
    text = response_text.strip()
    if benchmark.lower() == "locomo":
        label = text.upper().strip(" .\n\t\"'")
        if label in {"CORRECT", "WRONG"}:
            return label
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return "INVALID"
        label = str(payload.get("label", "")).upper()
        return label if label in {"CORRECT", "WRONG"} else "INVALID"

    normalized = text.lower().strip(" .\n\t")
    if normalized == "yes":
        return "CORRECT"
    if normalized == "no":
        return "WRONG"
    return "INVALID"


def normalize_judge_label(label: str) -> str:
    normalized = label.upper()
    if normalized in {"YES", "CORRECT"}:
        return "CORRECT"
    if normalized in {"NO", "WRONG"}:
        return "WRONG"
    return "INVALID"


def accuracy_from_judgments(judgments: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [
        item
        for item in judgments
        if normalize_judge_label(str(item.get("label"))) in {"CORRECT", "WRONG"}
    ]
    correct = [
        item for item in valid if normalize_judge_label(str(item.get("label"))) == "CORRECT"
    ]
    return {
        "n_judgments": len(judgments),
        "n_valid": len(valid),
        "n_invalid": len(judgments) - len(valid),
        "accuracy": len(correct) / len(valid) if valid else None,
    }


def dual_accuracy_from_judgments(
    flash_judgments: list[dict[str, Any]],
    pro_judgments: list[dict[str, Any]],
    *,
    labels_by_key: dict[str, dict[str, Any]] | None = None,
    group_field: str | None = None,
) -> dict[str, Any]:
    """Aggregate strict/lenient accuracy from two offline judge outputs.

    Invalid labels count as not-correct for strict/lenient accuracy. This keeps the
    headline denominator equal to the shared prediction set instead of silently
    dropping difficult judge responses.
    """

    flash_by_key = _judgments_by_key(flash_judgments)
    pro_by_key = _judgments_by_key(pro_judgments)
    flash_keys = set(flash_by_key)
    pro_keys = set(pro_by_key)
    shared_keys = _ordered_shared_keys(
        flash_judgments, pro_judgments, flash_keys & pro_keys
    )

    rows: list[dict[str, Any]] = []
    for key in shared_keys:
        flash_label = normalize_judge_label(str(flash_by_key[key].get("label")))
        pro_label = normalize_judge_label(str(pro_by_key[key].get("label")))
        row = {
            "record_key": key,
            "flash_label": flash_label,
            "pro_label": pro_label,
            "flash_correct": flash_label == "CORRECT",
            "pro_correct": pro_label == "CORRECT",
            "flash_valid": flash_label in {"CORRECT", "WRONG"},
            "pro_valid": pro_label in {"CORRECT", "WRONG"},
        }
        row["both_valid"] = bool(row["flash_valid"] and row["pro_valid"])
        row["strict_correct"] = bool(row["flash_correct"] and row["pro_correct"])
        row["lenient_correct"] = bool(row["flash_correct"] or row["pro_correct"])
        group_value = _group_value(key, labels_by_key, group_field)
        if group_value is not None:
            row["group"] = group_value
        rows.append(row)

    metrics = _dual_summary(rows)
    metrics.update(
        {
            "n_flash_judgments": len(flash_judgments),
            "n_pro_judgments": len(pro_judgments),
            "n_missing_flash": len(pro_keys - flash_keys),
            "n_missing_pro": len(flash_keys - pro_keys),
        }
    )

    by_group: dict[str, Any] = {}
    if group_field:
        grouped_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped_rows[str(row.get("group", "unknown"))].append(row)
        by_group = {
            group: _dual_summary(items) for group, items in sorted(grouped_rows.items())
        }

    return {
        "metrics": metrics,
        "by_group": by_group,
        "records": rows,
    }


def _longmemeval_template(example: JudgeExample) -> str:
    question_type = (example.question_type or "").lower()
    if question_type == "temporal-reasoning":
        return LONGMEMEVAL_TEMPORAL_TEMPLATE
    if question_type == "knowledge-update":
        return LONGMEMEVAL_KNOWLEDGE_UPDATE_TEMPLATE
    if question_type == "single-session-preference":
        return LONGMEMEVAL_PREFERENCE_TEMPLATE
    if question_type == "abstention":
        return LONGMEMEVAL_ABSTENTION_TEMPLATE
    return LONGMEMEVAL_DEFAULT_TEMPLATE


def _judgments_by_key(judgments: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("record_key")): item
        for item in judgments
        if item.get("record_key") is not None
    }


def _ordered_shared_keys(
    flash_judgments: list[dict[str, Any]],
    pro_judgments: list[dict[str, Any]],
    shared_keys: set[str],
) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for judgment in flash_judgments + pro_judgments:
        key = str(judgment.get("record_key"))
        if key in shared_keys and key not in seen:
            ordered.append(key)
            seen.add(key)
    return ordered


def _dual_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    strict_correct = sum(1 for row in rows if row["strict_correct"])
    lenient_correct = sum(1 for row in rows if row["lenient_correct"])
    both_valid = [row for row in rows if row["both_valid"]]
    both_valid_n = len(both_valid)
    agreement = sum(1 for row in both_valid if row["flash_label"] == row["pro_label"])
    return {
        "n_joined": n,
        "n_both_valid": both_valid_n,
        "n_any_invalid": n - both_valid_n,
        "flash_correct": sum(1 for row in rows if row["flash_correct"]),
        "pro_correct": sum(1 for row in rows if row["pro_correct"]),
        "strict_correct": strict_correct,
        "lenient_correct": lenient_correct,
        "strict_accuracy": strict_correct / n if n else None,
        "lenient_accuracy": lenient_correct / n if n else None,
        "strict_accuracy_both_valid": strict_correct / both_valid_n
        if both_valid_n
        else None,
        "lenient_accuracy_both_valid": lenient_correct / both_valid_n
        if both_valid_n
        else None,
        "judge_agreement": agreement / both_valid_n if both_valid_n else None,
    }


def _group_value(
    key: str,
    labels_by_key: dict[str, dict[str, Any]] | None,
    group_field: str | None,
) -> str | None:
    if not labels_by_key or not group_field:
        return None
    value = labels_by_key.get(key, {}).get(group_field)
    if value is None or str(value).strip() == "":
        return "unknown"
    return str(value)
