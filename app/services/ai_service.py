import json
import logging
import re

from langchain_openai import ChatOpenAI

from app.core.config import settings


log = logging.getLogger(__name__)


async def classify_text(email_text: str) -> dict:
    if not settings.openai_api_key:
        return _heuristic_classify(email_text)

    llm = ChatOpenAI(model=settings.openai_model, api_key=settings.openai_api_key, temperature=0)
    prompt = (
        "Analyze this email and return JSON ONLY with keys: "
        "category (one of: Requires Attention, Interview Opportunity, Rejection, Spam, Follow-up Needed, Important Client/Work), "
        "urgency (1-10 integer), requires_attention (true/false), short_summary (string), suggested_reply (string or null), confidence (0-100 integer).\n\n"
        f"EMAIL:\n{email_text}"
    )
    msg = await llm.ainvoke(prompt)
    content = getattr(msg, "content", "") or ""
    parsed = _parse_json_best_effort(content)
    if parsed is None:
        log.warning("Failed to parse model JSON output; falling back to heuristic.")
        return _heuristic_classify(email_text)
    return parsed


def _parse_json_best_effort(text: str) -> dict | None:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def _heuristic_classify(email_text: str) -> dict:
    lowered = email_text.lower()
    category = "Requires Attention"
    urgency = 5
    requires_attention = True
    confidence = 55

    if any(k in lowered for k in ["interview", "phone screen", "onsite", "schedule", "availability"]):
        category = "Interview Opportunity"
        urgency = 9
        requires_attention = True
        confidence = 75
    elif any(k in lowered for k in ["unfortunately", "we have decided", "not moving forward", "rejection"]):
        category = "Rejection"
        urgency = 2
        requires_attention = False
        confidence = 70
    elif any(k in lowered for k in ["follow up", "following up", "checking in", "circling back", "any updates"]):
        category = "Follow-up Needed"
        urgency = 6
        requires_attention = True
        confidence = 65
    elif any(k in lowered for k in ["invoice", "contract", "client", "statement of work", "sow"]):
        category = "Important Client/Work"
        urgency = 7
        requires_attention = True
        confidence = 60
    elif any(k in lowered for k in ["unsubscribe", "promotion", "deal", "discount", "buy now"]):
        category = "Spam"
        urgency = 1
        requires_attention = False
        confidence = 60

    short_summary = (email_text.strip().splitlines() or [""])[0][:280]
    return {
        "category": category,
        "urgency": urgency,
        "requires_attention": requires_attention,
        "short_summary": short_summary or "No content",
        "suggested_reply": None,
        "confidence": confidence,
    }
