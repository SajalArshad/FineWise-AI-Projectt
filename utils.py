"""
utils.py
--------
Small helpers: safe JSON parsing of LLM output, formatting helpers.
"""

import json
import re
from typing import Optional


REQUIRED_KEYS = [
    "financial_summary",
    "financial_health_score",
    "spending_analysis",
    "risk_level",
    "top_priorities",
    "budget_recommendations",
    "savings_strategy",
    "next_month_action_plan",
]

FALLBACK_RESPONSE = {
    "financial_summary": (
        "We couldn't generate a full analysis this time. Please try "
        "again. This tool is educational only and not financial advice."
    ),
    "financial_health_score": 0,
    "spending_analysis": [],
    "risk_level": "MEDIUM",
    "top_priorities": ["Retry the analysis"],
    "budget_recommendations": [],
    "savings_strategy": [],
    "next_month_action_plan": [],
}


def _strip_code_fences(text: str) -> str:
    """Remove ```json ... ``` or ``` ... ``` wrappers if the model added them."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _extract_json_block(text: str) -> Optional[str]:
    """Best-effort extraction of the first {...} block in a string."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group(0) if match else None


def safe_parse_json(raw_text: str) -> dict:
    """
    Safely parse LLM output into the expected JSON schema.

    Falls back to a safe default structure (with an explanatory message)
    if the model returns invalid or incomplete JSON, so the Streamlit UI
    never crashes on a bad LLM response.
    """
    if not raw_text or not raw_text.strip():
        return dict(FALLBACK_RESPONSE)

    cleaned = _strip_code_fences(raw_text)

    parsed = None
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        block = _extract_json_block(cleaned)
        if block:
            try:
                parsed = json.loads(block)
            except json.JSONDecodeError:
                parsed = None

    if not isinstance(parsed, dict):
        return dict(FALLBACK_RESPONSE)

    # Fill in any missing keys with safe defaults so the UI can render.
    result = dict(FALLBACK_RESPONSE)
    result.update(parsed)
    for key in REQUIRED_KEYS:
        if key not in result:
            result[key] = FALLBACK_RESPONSE[key]

    # Clamp score and normalize risk_level.
    try:
        result["financial_health_score"] = int(
            max(0, min(100, float(result["financial_health_score"])))
        )
    except (TypeError, ValueError):
        result["financial_health_score"] = 0

    risk = str(result.get("risk_level", "MEDIUM")).strip().upper()
    result["risk_level"] = risk if risk in ("LOW", "MEDIUM", "HIGH") else "MEDIUM"

    return result


def format_currency(value: float, currency: str = "USD") -> str:
    """Simple currency formatter for dashboard display."""
    symbols = {
        "USD": "$", "EUR": "€", "GBP": "£", "PKR": "PKR ",
        "INR": "₹", "AED": "AED ", "CAD": "C$", "AUD": "A$",
    }
    symbol = symbols.get(currency, currency + " ")
    return f"{symbol}{value:,.2f}"
