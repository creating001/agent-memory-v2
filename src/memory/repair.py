"""Selective answer repair for clean memory QA.

This module uses only prediction-time artifacts: the question, route, retrieved
memory context, and the draft answer/JSON. It must never read labels, judge
outputs, benchmark metadata, sample ids, or test feedback.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

from common.schemas import AnswerResult, CompiledContext
from memory.finalize import extract_json_object, raw_response_content


_INSUFFICIENT_ANSWER = re.compile(
    r"\b(not enough|insufficient|cannot determine|can't determine|not available|"
    r"unknown|do not know|don't know|not provided|not mentioned|not specified|"
    r"no information)\b",
    re.IGNORECASE,
)
_COLLECTION_QUESTION = re.compile(
    r"\b(?:what|which)\s+(?:items|events|activities|places|people|persons|"
    r"books|songs|movies|artists|bands|exercises|causes|foods|meals|"
    r"classes|workshops|projects|purchases|hobbies|sports|games|"
    r"restaurants|stores|services|organizations|groups|symbols|topics|"
    r"subjects|courses|awards|trips|visits|tools|apps|devices)\b|"
    r"\bwhat\s+kinds\s+of\b|"
    r"\bwhat\s+.+\b(?:has|have|had)\s+.+\b(?:done|bought|painted|visited|"
    r"attended|participated|read|seen|watched|tried|used|owned|made|created|"
    r"ordered|eaten|played|joined|taken)\b",
    re.IGNORECASE,
)
_COUNT_QUESTION = re.compile(r"\b(?:how many|number of|count of)\b", re.IGNORECASE)
_ORDER_CHOICE_QUESTION = re.compile(
    r"\b(?:which|what)\b[^?]{0,120}\b(?:first|earlier|later|before|after)\b",
    re.IGNORECASE,
)
_NUMERIC_ANSWER = re.compile(r"\b\d+(?:\.\d+)?\b")
_ITEM_SEPARATOR = re.compile(r"\s*(?:,|;|\band\b|\n|\|)\s*", re.IGNORECASE)
_MODAL_INFERENCE_QUESTION = re.compile(
    r"\b(?:would|might|could|likely|unlikely|probably|seem(?:s)?|"
    r"considered|what\s+might|how\s+would|still\s+want|be\s+considered)\b",
    re.IGNORECASE,
)
_SOURCE_GROUNDED_MODAL_YES_NO_QUESTION = re.compile(
    r"^\s*(?:would|could|might)\b[^?]{8,240}\?\s*$",
    re.IGNORECASE,
)
_SOURCE_GROUNDED_MODAL_BLOCKED_QUESTION = re.compile(
    r"\b(?:which|what|who|where|when|how\s+many|how\s+much)\b|"
    r"\b(?:recommend|recommendation|suggest|suggestion|advice|good\s+idea|"
    r"should|help\s+me\s+(?:choose|pick)|gift|shop|book|company|states?|"
    r"national\s+park|store|restaurant|venue|product|brand)\b",
    re.IGNORECASE,
)
_SOURCE_GROUNDED_MODAL_SENSITIVE_ATTRIBUTION = re.compile(
    r"\bbe\s+considered\s+(?:religious|political|conservative|liberal|"
    r"wealthy|poor|healthy|disabled|diagnosed|depressed|anxious)\b",
    re.IGNORECASE,
)
_SOURCE_GROUNDED_MODAL_SUPPORT_ANCHOR = re.compile(
    r"\b(?:because|why|motivat(?:e|ed|es|ing|ion|ional)?|motive|"
    r"driv(?:e|en)|therefore|so\s+(?:i|he|she|they)\s+could|"
    r"made\s+(?:me|him|her|them)|realiz(?:e|ed)|"
    r"want(?:s|ed)?|would\s+like|love(?:s|d)?|enjoy(?:s|ed)?|prefer(?:s|red)?|"
    r"dream|passion|interested|fuel(?:s|ed)?|alive|scary|trauma|afraid|fear|"
    r"accident|support(?:ed)?|help(?:ed|ful)?|important|connection)\b",
    re.IGNORECASE,
)
_SOURCE_GROUNDED_TEMPORAL_CALC_QUESTION = re.compile(
    r"\b(?:how\s+many\s+(?:days|weeks|months|years)|how\s+long|how\s+old)\b|"
    r"\b(?:days|weeks|months|years)\s+(?:ago|before|after|between)\b",
    re.IGNORECASE,
)
_SOURCE_GROUNDED_TEMPORAL_CALC_BLOCKED_QUESTION = re.compile(
    r"\band\s+how\s+many\b|"
    r"\bwhat\s+(?:schools?|items|events|activities|places|people|persons|"
    r"books|songs|movies|artists|bands|projects|purchases|trips|visits)\b|"
    r"\b(?:which|what)\b[^?]{0,120}\b(?:first|earlier|later|before|after)\b|"
    r"\bdid\b[^?]{0,160}\bor\s+not\b|"
    r"\b(?:recommend|recommendation|suggest|suggestion|advice|good\s+idea|"
    r"should|gift|shop|book|company|national\s+park|store|restaurant|"
    r"venue|product|brand)\b",
    re.IGNORECASE,
)
_SOURCE_GROUNDED_TEMPORAL_DATE = re.compile(
    r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b|"
    r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:t|tember)?|oct(?:ober)?|nov(?:ember)?|"
    r"dec(?:ember)?)\s+\d{1,2},?\s+\d{4}\b|"
    r"\b\d{1,2}\s+(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|"
    r"jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t|tember)?|oct(?:ober)?|"
    r"nov(?:ember)?|dec(?:ember)?),?\s+\d{4}\b|"
    r"\b(?:event_time|mention_time)\b[^,;|]{0,40}\b\d{4}\b|"
    r"\b(?:in|since|from|on|by|around|about|approx(?:imately)?)\s+\d{4}\b",
    re.IGNORECASE,
)
_SOURCE_GROUNDED_TEMPORAL_DURATION = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:days?|weeks?|months?|years?|yrs?|mos?)\b|"
    r"\b(?:few|couple|several|nearly|about|around|almost)\s+"
    r"(?:days?|weeks?|months?|years?)\b",
    re.IGNORECASE,
)
_SOURCE_GROUNDED_TEMPORAL_AGE = re.compile(
    r"\b(?:current_?age|age(?:d)?)\b[^,;|]{0,20}\b\d{1,3}\b|"
    r"\b\d{1,3}\s*(?:years?\s+old|yo)\b",
    re.IGNORECASE,
)
_CURRENT_STATE_LIFECYCLE_QUESTION = re.compile(
    r"\b(current|currently|now|still|latest|most\s+recent|previous|previously|"
    r"before|after|since|how\s+long|duration|tenure|status|changed|compared)\b",
    re.IGNORECASE,
)
_LIFECYCLE_STATE_SLOT_QUESTION = re.compile(
    r"\b(current|currently|now|still|previous|previously|status|goal|"
    r"feel(?:s|ing)?|working|living|lead|have|record)\b",
    re.IGNORECASE,
)
_LIFECYCLE_ADVICE_QUESTION = re.compile(
    r"\b(suggest|recommend|recommendation|advice|what\s+do\s+you\s+think|"
    r"trying\s+to\s+decide|should\s+i|should\s+we|complement)\b",
    re.IGNORECASE,
)
_PROFILE_ADVICE_ABSTENTION_QUESTION = re.compile(
    r"\b(recommend|recommendation|suggest|suggestion|advice|ideas?|options?|"
    r"resources?|activities|where\s+can\s+i|what\s+can\s+i|what\s+should|"
    r"should\s+i|should\s+we|help\s+me\s+(?:choose|pick|decide))\b",
    re.IGNORECASE,
)
_LIFECYCLE_ORDER_OR_COLLECTION_QUESTION = re.compile(
    r"\b(order\s+of|from\s+earliest\s+to\s+latest|earliest\s+to\s+latest|"
    r"which\b[^?]{0,120}\b(?:first|earlier|later)|"
    r"what\s+(?:items|events|activities|places|people|books|songs|movies|"
    r"artists|bands|projects|purchases|trips|visits))\b",
    re.IGNORECASE,
)
_LIFECYCLE_CALCULATION_QUESTION = re.compile(
    r"\b(percentage|percent|how\s+many\s+days|how\s+much\s+more|compared\s+to|"
    r"total\s+cost|difference|average)\b|"
    r"\bhow\s+long\b[^?]{0,120}\bbefore\b",
    re.IGNORECASE,
)
_LIFECYCLE_LATEST_EVENT_QUESTION = re.compile(
    r"\bwhat\s+did\b[^?]{0,160}\blatest\b[^?]{0,120}\b"
    r"(project|trip|visit|event|purchase|order|class|workshop)\b",
    re.IGNORECASE,
)
_TOKEN_PATTERN = re.compile(r"[\w]+", re.UNICODE)
_NUMERIC_DATE = re.compile(r"\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b")
_TEXT_DATE = re.compile(
    r"\b(\d{1,2})\s+"
    r"(January|February|March|April|May|June|July|August|September|October|"
    r"November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept|Sep|Oct|Nov|Dec)"
    r",?\s+(\d{4})\b",
    re.IGNORECASE,
)
_MONTH_BY_NAME = {
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sept": 9,
    "sep": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
}
_TERM_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "at",
    "been",
    "before",
    "being",
    "compared",
    "current",
    "currently",
    "did",
    "do",
    "does",
    "duration",
    "for",
    "from",
    "had",
    "has",
    "have",
    "how",
    "i",
    "in",
    "is",
    "it",
    "job",
    "latest",
    "long",
    "me",
    "my",
    "now",
    "of",
    "on",
    "or",
    "previous",
    "previously",
    "recent",
    "role",
    "since",
    "still",
    "the",
    "to",
    "was",
    "were",
    "what",
    "when",
    "where",
    "which",
    "who",
    "work",
    "worked",
    "working",
    "with",
    "you",
    "your",
}


@dataclass(frozen=True)
class AnswerRepair:
    """Traceable result for optional LLM answer repair."""

    answer: AnswerResult
    enabled: bool
    triggered: bool
    applied: bool
    reasons: tuple[str, ...]
    before: str
    after: str
    decision: str
    reason: str
    prompt_context_chars: int = 0
    response: AnswerResult | None = None

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["answer"] = self.answer.to_dict()
        result["response"] = self.response.to_dict() if self.response else None
        return result


def maybe_repair_answer(
    *,
    answerer: Any | None,
    compiled: CompiledContext,
    draft: AnswerResult,
    enabled: bool,
    information_needs: tuple[str, ...],
    enable_uncertain_trigger: bool,
    enable_short_list_trigger: bool,
    enable_temporal_conflict_trigger: bool,
    enable_profile_preference_trigger: bool,
    enable_profile_advice_abstention_trigger: bool,
    enable_modal_abstention_trigger: bool,
    enable_source_grounded_modal_inference_trigger: bool,
    enable_source_grounded_temporal_calculation_trigger: bool,
    uncertain_min_support_items: int,
    source_grounded_modal_min_support_items: int,
    source_grounded_temporal_calculation_min_support_items: int,
    max_context_chars: int,
    max_row_text_chars: int,
    enable_lifecycle_ledger: bool = False,
    enable_lifecycle_slot_trigger: bool = False,
) -> AnswerRepair:
    """Run a second LLM pass only when generic runtime signals show risk."""

    if not enabled:
        return _noop(draft, enabled=False, reason="disabled")
    if answerer is None:
        return _noop(draft, enabled=True, reason="no_repair_answerer")
    if information_needs and compiled.route.information_need not in information_needs:
        return _noop(draft, enabled=True, reason="information_need_not_enabled")

    reasons = repair_trigger_reasons(
        question=compiled.question,
        route_information_need=compiled.route.information_need,
        draft_answer=draft.answer,
        raw_response=draft.raw_response,
        enable_uncertain_trigger=enable_uncertain_trigger,
        enable_short_list_trigger=enable_short_list_trigger,
        enable_temporal_conflict_trigger=enable_temporal_conflict_trigger,
        enable_profile_preference_trigger=enable_profile_preference_trigger,
        enable_profile_advice_abstention_trigger=(
            enable_profile_advice_abstention_trigger
        ),
        enable_modal_abstention_trigger=enable_modal_abstention_trigger,
        enable_source_grounded_modal_inference_trigger=(
            enable_source_grounded_modal_inference_trigger
        ),
        enable_source_grounded_temporal_calculation_trigger=(
            enable_source_grounded_temporal_calculation_trigger
        ),
        uncertain_min_support_items=uncertain_min_support_items,
        source_grounded_modal_min_support_items=(
            source_grounded_modal_min_support_items
        ),
        source_grounded_temporal_calculation_min_support_items=(
            source_grounded_temporal_calculation_min_support_items
        ),
    )
    if enable_lifecycle_slot_trigger:
        reasons = (
            *reasons,
            *_lifecycle_slot_trigger_reasons(compiled=compiled, draft=draft),
        )
        reasons = tuple(dict.fromkeys(reasons))
    if not reasons:
        return _noop(draft, enabled=True, reason="no_trigger")

    prompt, prompt_context_chars = build_repair_prompt(
        compiled=compiled,
        draft=draft,
        reasons=reasons,
        enable_lifecycle_ledger=enable_lifecycle_ledger,
        max_context_chars=max_context_chars,
        max_row_text_chars=max_row_text_chars,
    )
    repair_context = CompiledContext(
        question=compiled.question,
        question_time=compiled.question_time,
        route=compiled.route,
        evidence_rows=compiled.evidence_rows,
        prompt=prompt,
        context_chars=prompt_context_chars,
        memory_records=compiled.memory_records,
    )
    response = answerer.answer(repair_context)
    decision = _repair_decision(response.raw_response)
    revised_answer = response.answer.strip()

    applied = False
    after = draft.answer
    if decision == "revise" and revised_answer:
        after = revised_answer
        applied = after != draft.answer
    elif decision not in {"keep", "revise"} and revised_answer:
        after = revised_answer
        applied = after != draft.answer

    final_token_usage = draft.token_usage + response.token_usage
    final = AnswerResult(
        answer=after,
        model=response.model if applied else draft.model,
        token_usage=final_token_usage,
        raw_response=response.raw_response if applied else draft.raw_response,
    )
    return AnswerRepair(
        answer=final,
        enabled=True,
        triggered=True,
        applied=applied,
        reasons=reasons,
        before=draft.answer,
        after=after,
        decision=decision or "unknown",
        reason="repair_called",
        prompt_context_chars=prompt_context_chars,
        response=response,
    )


def repair_trigger_reasons(
    *,
    question: str,
    route_information_need: str,
    draft_answer: str,
    raw_response: str | None,
    enable_uncertain_trigger: bool,
    enable_short_list_trigger: bool,
    enable_temporal_conflict_trigger: bool,
    enable_profile_preference_trigger: bool = False,
    enable_profile_advice_abstention_trigger: bool = False,
    enable_modal_abstention_trigger: bool = False,
    enable_source_grounded_modal_inference_trigger: bool = False,
    enable_source_grounded_temporal_calculation_trigger: bool = False,
    uncertain_min_support_items: int = 0,
    source_grounded_modal_min_support_items: int = 2,
    source_grounded_temporal_calculation_min_support_items: int = 1,
) -> tuple[str, ...]:
    payload = _draft_payload(raw_response)
    reasons: list[str] = []
    uncertain_signal = _has_uncertain_signal(draft_answer, payload)
    surface_refusal_signal = bool(_INSUFFICIENT_ANSWER.search(draft_answer or ""))

    if (
        enable_profile_preference_trigger
        and route_information_need == "profile_preference"
    ):
        reasons.append("profile_preference_review")

    if (
        enable_profile_advice_abstention_trigger
        and route_information_need == "profile_preference"
        and surface_refusal_signal
        and _PROFILE_ADVICE_ABSTENTION_QUESTION.search(question or "")
    ):
        reasons.append("profile_advice_abstention_review")

    if (
        enable_modal_abstention_trigger
        and _INSUFFICIENT_ANSWER.search(draft_answer or "")
        and _MODAL_INFERENCE_QUESTION.search(question or "")
    ):
        reasons.append("modal_abstention_review")

    if (
        enable_source_grounded_modal_inference_trigger
        and _source_grounded_modal_inference_applies(
            question=question,
            route_information_need=route_information_need,
            draft_answer=draft_answer,
            payload=payload,
            min_support_items=source_grounded_modal_min_support_items,
        )
    ):
        reasons.append("source_grounded_modal_inference_review")

    if (
        enable_source_grounded_temporal_calculation_trigger
        and _source_grounded_temporal_calculation_applies(
            question=question,
            route_information_need=route_information_need,
            draft_answer=draft_answer,
            payload=payload,
            min_support_items=(
                source_grounded_temporal_calculation_min_support_items
            ),
        )
    ):
        reasons.append("source_grounded_temporal_calculation_review")

    if enable_uncertain_trigger:
        if uncertain_signal and _support_item_count(payload) >= max(
            0, int(uncertain_min_support_items)
        ):
            reasons.append("uncertain_or_missing")

    if enable_short_list_trigger and _looks_like_short_collection_answer(
        question=question,
        route_information_need=route_information_need,
        draft_answer=draft_answer,
        payload=payload,
    ):
        reasons.append("short_collection_answer")

    if enable_temporal_conflict_trigger and route_information_need == "temporal_lookup":
        answer_type = str(payload.get("answer_type") or "").strip().lower()
        if answer_type in {"fact", "unknown", "list", "count", "preference"}:
            reasons.append("temporal_answer_type_mismatch")
        values = _support_values(payload)
        if len(values) > 1:
            reasons.append("temporal_multiple_support_values")

    return tuple(dict.fromkeys(reasons))


def build_repair_prompt(
    *,
    compiled: CompiledContext,
    draft: AnswerResult,
    reasons: tuple[str, ...],
    max_context_chars: int,
    max_row_text_chars: int,
    enable_lifecycle_ledger: bool = False,
) -> tuple[str, int]:
    draft_json = raw_response_content(draft.raw_response) or draft.answer
    memory_context, context_chars = _repair_memory_context(
        compiled,
        max_context_chars=max_context_chars,
        max_row_text_chars=max_row_text_chars,
    )
    lifecycle_ledger = _current_state_lifecycle_ledger(
        compiled,
        enabled=enable_lifecycle_ledger,
        max_rows=10,
        max_text_chars=min(max_row_text_chars, 360) if max_row_text_chars else 360,
    )
    question_time = compiled.question_time or ""
    reason_text = ", ".join(reasons)

    prompt = "\n".join(
        [
            "You are a clean memory-QA answer verifier and repairer.",
            "Use only the provided Memory Context and Draft Answer artifacts.",
            "",
            "Question:",
            compiled.question,
            "",
            "Question Time:",
            question_time,
            "",
            "Information Need:",
            compiled.route.information_need,
            "",
            "Repair Trigger Reasons:",
            reason_text,
            "",
            "Draft Answer:",
            draft.answer,
            "",
            "Draft Answer JSON:",
            draft_json,
            "",
            "Memory Context:",
            memory_context,
            *lifecycle_ledger,
            "",
            "Rules:",
            "1. Prefer decision=keep when the draft answer is directly supported and complete enough for the question.",
            "2. Use decision=revise only when Memory Context clearly supports a better answer or the draft refusal is contradicted by available evidence.",
            "3. Do not use labels, reference answers, judge feedback, benchmark categories, sample ids, or assumptions outside Memory Context.",
            "4. For list or count questions, include all distinct in-scope values supported by Memory Context; merge duplicates and do not narrow a supported broad answer unless evidence clearly excludes it.",
            "5. For temporal questions, separate Memory Date from event time; answer the event/state time requested by the question.",
            "6. For current/latest questions, compare older and newer directly relevant evidence before revising.",
            "7. If evidence remains insufficient, keep or revise to a concise insufficient-information answer.",
            *_current_state_repair_rules(compiled),
            *_profile_preference_repair_rules(compiled, reasons=reasons),
            *_modal_abstention_repair_rules(reasons),
            *_temporal_calculation_repair_rules(reasons),
            "Return only valid JSON.",
            "",
            "Output JSON:",
            "{",
            '  "decision": "keep|revise",',
            '  "reason": "one short evidence-based sentence",',
            '  "answer": "final concise answer"',
            "}",
        ]
    )
    return prompt, context_chars


def _current_state_repair_rules(compiled: CompiledContext) -> list[str]:
    if compiled.route.information_need != "current_state":
        return []
    return [
        "8. For current-state duration or tenure questions, you may compute a simple date or duration answer from directly relevant raw rows and Question Time; do not require the final duration to be stated verbatim.",
        "9. For current/previous state questions, revise only from raw rows that match the asked entity and state relation; do not use topically related but different state slots.",
        "10. If raw rows support both previous and current values and the question asks for both, include both instead of collapsing to one value.",
    ]


def _profile_preference_repair_rules(
    compiled: CompiledContext,
    *,
    reasons: tuple[str, ...],
) -> list[str]:
    if compiled.route.information_need != "profile_preference":
        return []
    lines = [
        "8. For preference, advice, or recommendation questions, extract user-specific anchors from Memory Context: preferences, dislikes, constraints, owned tools/resources, current setup, prior successful experiences, current problems, and stated goals.",
        "9. If the draft refused but Memory Context has relevant anchors, revise to a tailored answer using those anchors instead of generic advice.",
        "10. If the exact requested named option is not in Memory Context, answer with the type, criteria, or constraints the user would likely prefer; do not invent unsupported specific names.",
        "11. This no-new-names rule applies even when you know plausible real-world shows, conferences, hotels, products, publications, venues, or events; use only names present in Memory Context.",
        "12. The final answer must not contain a proper noun, title, organization, venue, platform, publication, conference, hotel, product, show, movie, restaurant, or event name unless that exact name appears verbatim in Memory Context.",
        "13. If no exact named option is present, answer with preference type, selection criteria, or constraints only.",
        "14. Include the key personalized constraint or reason in the final answer when needed for the answer to satisfy the request.",
    ]
    if "profile_advice_abstention_review" in reasons:
        lines.extend(
            [
                "15. For this surface-refusal review, do not require the exact target instance, city, date, or named option to appear when Memory Context gives same-domain anchors; provide preference-aligned criteria, option types, or search terms instead.",
                "16. Same-domain anchors may transfer across equivalent decision domains such as a prior hotel feature preference to another hotel search, a prior recipe or baking experiment to related baking advice, or a prior research-topic request to publication/conference search criteria.",
                "17. Do not transfer anchors across unrelated domains; a trivia topic, isolated game clue, or one-off unrelated event is not enough to personalize a show, product, venue, or activity recommendation.",
                "18. For recent, current, upcoming, or local requests, do not invent live facts; if no named current item is in Memory Context, give grounded search criteria or event/publication types and say that no specific current name is supported.",
                "19. Do not write parenthetical examples, 'such as ...', 'e.g.', or any named conference, journal, paper, venue, platform, product, show, movie, event, organization, or brand unless that exact name appears in the Question or Memory Context.",
                "20. For publication, conference, resource, venue, or event searches, use generic subfields, criteria, and search phrases only when no exact names are supported.",
                "21. Avoid leading with an insufficient-information refusal when a criteria/type answer is supported; lead with the supported preference-aligned answer and include uncertainty only as a qualifier.",
            ]
        )
    return lines


def _modal_abstention_repair_rules(reasons: tuple[str, ...]) -> list[str]:
    if (
        "modal_abstention_review" not in reasons
        and "source_grounded_modal_inference_review" not in reasons
    ):
        return []
    return [
        "15. For modal or inference questions, a calibrated answer such as likely, unlikely, yes, no, or somewhat is allowed when Memory Context has directly relevant anchors.",
        "16. Do not keep an insufficient-information refusal merely because the context lacks an exact verbatim answer; use the user's stated preferences, actions, constraints, outcomes, and self-descriptions as anchors.",
        "17. Keep or revise to insufficient information when anchors are absent, conflicting, or only topically related.",
        "18. For sensitive traits or statuses such as identity, religion, health, finances, or politics, do not infer from stereotypes; require explicit self-description or concrete behavior in Memory Context and use uncertainty qualifiers.",
    ]


def _temporal_calculation_repair_rules(reasons: tuple[str, ...]) -> list[str]:
    if "source_grounded_temporal_calculation_review" not in reasons:
        return []
    return [
        "15. For this temporal, age, or duration review, simple arithmetic is allowed only over directly supported dates, durations, ages, event_time, mention_time, time_phrase, and Question Time.",
        "16. Do not revise when any endpoint, age, duration, entity match, or requested event/state is missing, ambiguous, conflicting, or only topically related.",
        "17. Preserve the unit requested by the question when possible; use approximate wording only when Memory Context gives approximate dates, approximate durations, or incomplete date precision.",
        "18. For multi-part, list, choice, or external-name questions, keep or revise to insufficient information unless Memory Context fully supports every requested part.",
    ]


def _lifecycle_slot_trigger_reasons(
    *,
    compiled: CompiledContext,
    draft: AnswerResult,
) -> tuple[str, ...]:
    if compiled.route.information_need != "current_state":
        return ()
    if not _lifecycle_slot_question_applies(compiled.question):
        return ()
    payload = _draft_payload(draft.raw_response)
    if _has_uncertain_signal(draft.answer, payload):
        return ()
    answer_type = str(payload.get("answer_type") or "").strip().lower()
    if answer_type in {"list"}:
        return ()
    if len(_support_values(payload)) <= 1:
        return ()
    if len(_current_state_lifecycle_rows(compiled, max_rows=10)) < 2:
        return ()
    return ("current_state_lifecycle_review",)


def _lifecycle_slot_question_applies(question: str) -> bool:
    text = question or ""
    if not _CURRENT_STATE_LIFECYCLE_QUESTION.search(text):
        return False
    if not _LIFECYCLE_STATE_SLOT_QUESTION.search(text):
        return False
    if _LIFECYCLE_ADVICE_QUESTION.search(text):
        return False
    if _LIFECYCLE_ORDER_OR_COLLECTION_QUESTION.search(text):
        return False
    if _LIFECYCLE_CALCULATION_QUESTION.search(text):
        return False
    if _LIFECYCLE_LATEST_EVENT_QUESTION.search(text):
        return False
    return True


def _current_state_lifecycle_ledger(
    compiled: CompiledContext,
    *,
    enabled: bool,
    max_rows: int,
    max_text_chars: int,
) -> list[str]:
    if not enabled or compiled.route.information_need != "current_state":
        return []
    rows = _current_state_lifecycle_rows(compiled, max_rows=max_rows)
    if len(rows) < 2:
        return []

    newest_index = len(rows) - 1
    lines = [
        "",
        "Current-State Lifecycle Ledger:",
        "Use this as a compact source index for update/state reasoning; verify every claim against Memory Context rows.",
        "The ledger must not add a stricter evidence requirement than Memory Context; simple arithmetic over directly supported dates or durations is allowed.",
    ]
    for ledger_index, (row_index, row) in enumerate(rows, start=1):
        text = row.text
        if max_text_chars and len(text) > max_text_chars:
            text = (text[: max(0, max_text_chars - 3)].rstrip() + "...")[
                :max_text_chars
            ]
        status = (
            "newest_candidate"
            if ledger_index - 1 == newest_index
            else "older_candidate"
        )
        lines.append(
            " ".join(
                part
                for part in (
                    f"Ledger {ledger_index}:",
                    f"memory=Memory {row_index}",
                    f"source_id={row.source_id}",
                    f"date={row.timestamp or ''}",
                    f"role={row.role}",
                    f"status={status}",
                    f"text={text}",
                )
                if part
            )
        )
    return lines


def _current_state_lifecycle_rows(
    compiled: CompiledContext,
    *,
    max_rows: int,
) -> tuple[tuple[int, Any], ...]:
    question_terms = _content_terms(compiled.question)
    if not question_terms:
        return ()
    scored: list[tuple[int, int, tuple[int, int, int], int, Any]] = []
    for index, row in enumerate(compiled.evidence_rows, start=1):
        row_terms = _content_terms(" ".join((row.role, row.text)))
        overlap = len(question_terms.intersection(row_terms))
        if overlap <= 0:
            continue
        rank = row.retrieval_rank if row.retrieval_rank is not None else index
        scored.append((overlap, -rank, _date_key(row.timestamp), index, row))
    if len(scored) < 2:
        return ()
    selected = sorted(scored, key=lambda item: (-item[0], item[1], item[3]))[
        : max(2, max_rows)
    ]
    ordered = sorted(selected, key=lambda item: (item[2], item[3]))
    return tuple((index, row) for _score, _rank, _date, index, row in ordered)


def _content_terms(text: str) -> frozenset[str]:
    terms = []
    for token in _TOKEN_PATTERN.findall((text or "").lower()):
        if len(token) < 3 or token in _TERM_STOPWORDS:
            continue
        terms.append(token)
    return frozenset(terms)


def _date_key(value: str | None) -> tuple[int, int, int]:
    text = value or ""
    numeric = _NUMERIC_DATE.search(text)
    if numeric:
        year, month, day = numeric.groups()
        return (int(year), int(month), int(day))
    textual = _TEXT_DATE.search(text)
    if textual:
        day, month_name, year = textual.groups()
        month = _MONTH_BY_NAME.get(month_name.lower(), 0)
        if month:
            return (int(year), month, int(day))
    return (9999, 12, 31)


def _noop(draft: AnswerResult, *, enabled: bool, reason: str) -> AnswerRepair:
    return AnswerRepair(
        answer=draft,
        enabled=enabled,
        triggered=False,
        applied=False,
        reasons=(),
        before=draft.answer,
        after=draft.answer,
        decision="keep",
        reason=reason,
    )


def _draft_payload(raw_response: str | None) -> dict[str, Any]:
    content = raw_response_content(raw_response)
    if not content:
        return {}
    return extract_json_object(content) or {}


def _repair_decision(raw_response: str | None) -> str:
    payload = _draft_payload(raw_response)
    return str(payload.get("decision") or "").strip().lower()


def _has_uncertain_signal(draft_answer: str, payload: dict[str, Any]) -> bool:
    answer_type = str(payload.get("answer_type") or "").strip().lower()
    missing = str(payload.get("missing") or "").strip()
    return bool(
        _INSUFFICIENT_ANSWER.search(draft_answer or "")
        or payload.get("sufficient") is False
        or answer_type == "unknown"
        or missing
    )


def _looks_like_short_collection_answer(
    *,
    question: str,
    route_information_need: str,
    draft_answer: str,
    payload: dict[str, Any],
) -> bool:
    if route_information_need not in {"fact_lookup", "list_count"}:
        return False
    lowered_question = question.lower()
    answer_type = str(payload.get("answer_type") or "").strip().lower()
    if answer_type not in {"", "list", "count", "fact"}:
        return False
    if not _COLLECTION_QUESTION.search(lowered_question):
        return False
    if _ORDER_CHOICE_QUESTION.search(lowered_question):
        return False
    if _INSUFFICIENT_ANSWER.search(draft_answer or ""):
        return False
    answer = (draft_answer or "").strip()
    if not answer:
        return False
    if _COUNT_QUESTION.search(lowered_question) and _NUMERIC_ANSWER.search(answer):
        return False
    if len(answer.split()) > 10:
        return False
    return len(_answer_items(answer)) <= 2


def _answer_items(answer: str) -> tuple[str, ...]:
    normalized = answer.strip().strip("[](){}")
    if not normalized:
        return ()
    parts = [
        part.strip().strip("\"'")
        for part in _ITEM_SEPARATOR.split(normalized)
        if part.strip().strip("\"'")
    ]
    return tuple(parts or (normalized,))


def _support_values(payload: dict[str, Any]) -> set[str]:
    values: set[str] = set()
    report = payload.get("evidence_report")
    if not isinstance(report, list):
        return values
    for item in report:
        if not isinstance(item, dict):
            continue
        if str(item.get("status") or "").strip().lower() != "support":
            continue
        value = str(item.get("event_time") or item.get("value") or "").strip()
        if value:
            values.add(value)
    return values


def _support_item_count(payload: dict[str, Any]) -> int:
    report = payload.get("evidence_report")
    if not isinstance(report, list):
        return 0
    return sum(
        1
        for item in report
        if isinstance(item, dict)
        and str(item.get("status") or "").strip().lower() == "support"
    )


def _source_grounded_modal_inference_applies(
    *,
    question: str,
    route_information_need: str,
    draft_answer: str,
    payload: dict[str, Any],
    min_support_items: int,
) -> bool:
    if route_information_need not in {"fact_lookup", "profile_preference"}:
        return False
    text = question or ""
    if not _INSUFFICIENT_ANSWER.search(draft_answer or ""):
        return False
    if not _SOURCE_GROUNDED_MODAL_YES_NO_QUESTION.search(text):
        return False
    if _SOURCE_GROUNDED_MODAL_BLOCKED_QUESTION.search(text):
        return False
    if _SOURCE_GROUNDED_MODAL_SENSITIVE_ATTRIBUTION.search(text):
        return False
    support_items = _support_items(payload)
    if len(support_items) < max(0, int(min_support_items)):
        return False
    return _has_source_grounded_modal_anchor(support_items)


def _source_grounded_temporal_calculation_applies(
    *,
    question: str,
    route_information_need: str,
    draft_answer: str,
    payload: dict[str, Any],
    min_support_items: int,
) -> bool:
    if route_information_need not in {"current_state", "fact_lookup", "temporal_lookup"}:
        return False
    text = question or ""
    if not _INSUFFICIENT_ANSWER.search(draft_answer or ""):
        return False
    if not _SOURCE_GROUNDED_TEMPORAL_CALC_QUESTION.search(text):
        return False
    if _SOURCE_GROUNDED_TEMPORAL_CALC_BLOCKED_QUESTION.search(text):
        return False
    missing = str(payload.get("missing") or "")
    if re.search(r"\bnot\s+(?:yet\s+)?completed\b", missing, re.IGNORECASE):
        return False
    support_items = _support_items(payload)
    if len(support_items) < max(0, int(min_support_items)):
        return False
    counts = _source_grounded_temporal_operand_counts(support_items)
    if counts["items"] <= 0:
        return False
    lowered = text.lower()
    if "how old" in lowered:
        return counts["age"] >= 1 and counts["duration"] >= 1
    if re.search(r"\bhow\s+many\s+(?:days|weeks|months|years)\s+ago\b", lowered):
        return counts["endpoint_date"] >= 1
    return counts["items"] >= 2 and (
        counts["endpoint_date"] >= 2
        or (counts["endpoint_date"] >= 1 and counts["duration"] >= 1)
        or counts["duration"] >= 2
    )


def _source_grounded_temporal_operand_counts(
    support_items: tuple[dict[str, Any], ...],
) -> dict[str, int]:
    counts = {"items": 0, "date": 0, "endpoint_date": 0, "duration": 0, "age": 0}
    for item in support_items:
        text = " ".join(
            str(item.get(field) or "")
            for field in (
                "slot",
                "value",
                "reason",
                "event_time",
                "mention_time",
                "time_phrase",
            )
        )
        has_date = bool(_SOURCE_GROUNDED_TEMPORAL_DATE.search(text))
        has_endpoint_date = _has_source_grounded_temporal_endpoint_date(item)
        has_duration = bool(_SOURCE_GROUNDED_TEMPORAL_DURATION.search(text))
        has_age = bool(_SOURCE_GROUNDED_TEMPORAL_AGE.search(text))
        if has_date or has_duration or has_age:
            counts["items"] += 1
        if has_date:
            counts["date"] += 1
        if has_endpoint_date:
            counts["endpoint_date"] += 1
        if has_duration:
            counts["duration"] += 1
        if has_age:
            counts["age"] += 1
    return counts


def _has_source_grounded_temporal_endpoint_date(item: dict[str, Any]) -> bool:
    event_time = str(item.get("event_time") or "").strip()
    if event_time and not re.search(
        r"\b(?:unknown|empty|n/?a|not\s+provided|not\s+specified)\b",
        event_time,
        re.IGNORECASE,
    ):
        if _SOURCE_GROUNDED_TEMPORAL_DATE.search(event_time):
            return True
    for field in ("value", "reason"):
        text = str(item.get(field) or "")
        if _SOURCE_GROUNDED_TEMPORAL_DATE.search(text):
            return True
    return False


def _support_items(payload: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    report = payload.get("evidence_report")
    if not isinstance(report, list):
        return ()
    return tuple(
        item
        for item in report
        if isinstance(item, dict)
        and str(item.get("status") or "").strip().lower() == "support"
    )


def _has_source_grounded_modal_anchor(
    support_items: tuple[dict[str, Any], ...],
) -> bool:
    for item in support_items:
        text = " ".join(
            str(item.get(field) or "")
            for field in ("slot", "value", "reason")
        )
        if _SOURCE_GROUNDED_MODAL_SUPPORT_ANCHOR.search(text):
            return True
    return False


def _repair_memory_context(
    compiled: CompiledContext,
    *,
    max_context_chars: int,
    max_row_text_chars: int,
) -> tuple[str, int]:
    limit = max(0, int(max_context_chars))
    row_limit = max(0, int(max_row_text_chars))
    lines: list[str] = []
    total = 0
    for index, row in enumerate(compiled.evidence_rows, start=1):
        text = row.text
        if row_limit and len(text) > row_limit:
            text = (text[: max(0, row_limit - 3)].rstrip() + "...")[:row_limit]
        parts = [
            f"Memory {index}:",
            f"Date: {row.timestamp or ''}",
            f"Speaker: {row.role}",
            f"Text: {text}",
        ]
        row_text = "\n".join(parts)
        projected = total + len(row_text) + (2 if lines else 0)
        if limit and lines and projected > limit:
            break
        if limit and not lines and len(row_text) > limit:
            row_text = (row_text[: max(0, limit - 3)].rstrip() + "...")[:limit]
            projected = len(row_text)
        lines.append(row_text)
        total = projected
    return "\n\n".join(lines), total
