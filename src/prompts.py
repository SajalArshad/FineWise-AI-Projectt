"""
prompts.py
----------
Prompt engineering layer: PromptTemplate, ChatPromptTemplate, the system
safety instructions, and the exact JSON schema the LLM must return.
"""

from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.messages import SystemMessage

# ---------------------------------------------------------------------
# JSON schema the model must return (kept as a string to embed in prompts)
# ---------------------------------------------------------------------
JSON_SCHEMA_TEXT = """{
  "financial_summary": "",
  "financial_health_score": 0,
  "spending_analysis": [
    { "category": "", "observation": "", "recommendation": "" }
  ],
  "risk_level": "",
  "top_priorities": [],
  "budget_recommendations": [],
  "savings_strategy": [],
  "next_month_action_plan": []
}"""

# ---------------------------------------------------------------------
# System instructions: role + mandatory safety rules
# ---------------------------------------------------------------------
SYSTEM_INSTRUCTIONS = """You are FinWise AI, an educational personal-finance assistant.

SAFETY RULES (must always be followed):
1. You provide EDUCATIONAL information only — never guaranteed investment
   advice, and you never claim any financial outcome is certain.
2. You do not recommend specific stocks, cryptocurrencies, or investment
   products, and you never suggest the user can get rich quickly.
3. You always remind the user, in the financial_summary field, that this
   is educational and they should consult a qualified financial
   professional for real decisions.
4. You never claim to execute transactions or access real bank accounts.
5. Base every observation strictly on the numeric data you are given —
   do not invent numbers.
6. financial_health_score must be an integer 0-100, and risk_level must
   be one of: "LOW", "MEDIUM", "HIGH".
7. Respond with ONLY valid JSON matching the exact schema you are given.
   No markdown code fences, no commentary before or after the JSON.
"""

# ---------------------------------------------------------------------
# PromptTemplate: reusable single-string template with financial variables
# ---------------------------------------------------------------------
# BUG FIX (LangChain 1.x): PromptTemplate's default "f-string" formatter
# parses the raw template text with Python's str.format() rules, where
# every "{...}" is treated as a variable placeholder unless the braces
# are doubled ("{{" / "}}") to escape them as literal characters.
#
# JSON_SCHEMA_TEXT contains literal JSON object braces (e.g.
# `{ "financial_summary": "", ... }`). Embedding it into the template
# string UNESCAPED -- as this file previously did via
# `.replace("{json_schema}", JSON_SCHEMA_TEXT)` -- makes every JSON key
# ("financial_summary", "category", "observation", "recommendation",
# "risk_level", "top_priorities", "budget_recommendations",
# "savings_strategy", "next_month_action_plan") look like an undeclared
# template variable to PromptTemplate's constructor, which raises a
# validation error immediately on import.
#
# Fix: double every literal brace in the JSON schema ONLY for this raw
# PromptTemplate embedding, so PromptTemplate's parser treats them as
# escaped literal text, not variables. At render time, str.format()
# un-escapes "{{" -> "{" and "}}" -> "}", producing correct JSON.
# The real template variables below (e.g. {monthly_income}) are plain
# single braces and are NOT touched.
_JSON_SCHEMA_ESCAPED_FOR_PROMPT_TEMPLATE = (
    JSON_SCHEMA_TEXT.replace("{", "{{").replace("}", "}}")
)

FINANCIAL_ANALYSIS_PROMPT = PromptTemplate(
    input_variables=[
        "monthly_income",
        "total_expenses",
        "remaining_income",
        "savings",
        "savings_ratio",
        "expense_ratio",
        "financial_goal",
        "expense_breakdown",
    ],
    template="""
Analyse the following personal financial snapshot and produce educational
budgeting insights.

Monthly income: {monthly_income}
Total expenses: {total_expenses}
Remaining income: {remaining_income}
Current savings: {savings}
Savings ratio: {savings_ratio}%
Expense ratio: {expense_ratio}%
Financial goal: {financial_goal}
Expense breakdown by category: {expense_breakdown}

Return your analysis strictly as JSON matching this schema:
{json_schema}
""".replace("{json_schema}", _JSON_SCHEMA_ESCAPED_FOR_PROMPT_TEMPLATE),
)

# ---------------------------------------------------------------------
# ChatPromptTemplate: System + Human messages, safety rules + dynamic data
# ---------------------------------------------------------------------
# NOTE on brace safety: unlike FINANCIAL_ANALYSIS_PROMPT above, the raw
# message text below contains ONLY the clean placeholder "{json_schema}"
# -- the literal JSON_SCHEMA_TEXT braces are never embedded into the raw
# template string here. They are supplied afterwards via `.partial(
# json_schema=JSON_SCHEMA_TEXT)`, which fills in a template VARIABLE'S
# VALUE at render time; Python's str.format() does not re-parse a
# substituted value for further "{...}" patterns, so this is already
# 100% safe and requires no brace-escaping.
ANALYSIS_CHAT_TEMPLATE = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_INSTRUCTIONS),
        (
            "human",
            """Here is my financial snapshot for this month:

- Monthly income: {monthly_income}
- Total expenses: {total_expenses}
- Remaining income: {remaining_income}
- Current savings: {savings}
- Savings ratio: {savings_ratio}%
- Expense ratio: {expense_ratio}%
- Preliminary rule-based score (Python, 0-100): {preliminary_score}
- Financial goal: {financial_goal}
- Expense breakdown: {expense_breakdown}

Analyse this and respond with ONLY valid JSON matching this exact schema
(no markdown fences, no extra text):

{json_schema}""",
        ),
    ]
).partial(json_schema=JSON_SCHEMA_TEXT)

# ---------------------------------------------------------------------
# Narrative/streaming template: a plain-language written recommendation,
# used with llm.stream() for the "typing" effect in the UI.
# ---------------------------------------------------------------------
# NOTE on brace safety: this template contains no JSON schema at all --
# no literal "{" or "}" characters anywhere in the raw text below other
# than the intended single-brace variable placeholders (e.g.
# {financial_goal}, {monthly_income}). Nothing to escape here.
NARRATIVE_CHAT_TEMPLATE = ChatPromptTemplate.from_messages(
    [
        SystemMessage(content=SYSTEM_INSTRUCTIONS),
        (
            "human",
            """Based on this financial snapshot, write a short, warm,
plain-language narrative recommendation (4-6 sentences, no JSON, no
markdown headers) for a person whose goal is "{financial_goal}":

- Monthly income: {monthly_income}
- Total expenses: {total_expenses}
- Remaining income: {remaining_income}
- Savings ratio: {savings_ratio}%
- Expense ratio: {expense_ratio}%
- Preliminary score: {preliminary_score}/100

End with one sentence reminding the reader this is educational, not
professional financial advice.""",
        ),
    ]
)
