"""
config.py
---------
Central place for static settings and form options.

IMPORTANT CHANGE FOR THIS ASSIGNMENT VARIANT:
Instead of requiring every user to have an OPENAI_API_KEY set in a .env
file on the server, this app is designed to be used by *visitors* who each
bring their own OpenAI API key. The key is collected once via a text input
in the Streamlit sidebar (see app.py) and kept only in st.session_state
for the duration of that browser session. It is never written to disk,
logged, or committed to source control.

For local development you may still optionally set OPENAI_API_KEY in a
.env file (loaded via python-dotenv) as a convenience default that
pre-fills the input box — but the app never *requires* it, and the
sidebar value always takes priority.
"""

import os
from dotenv import load_dotenv

load_dotenv()  # optional convenience default for local dev only

# ---------------------------------------------------------------------
# Model settings
# ---------------------------------------------------------------------
DEFAULT_MODEL_NAME = "gpt-4o-mini"
AVAILABLE_MODELS = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"]
DEFAULT_TEMPERATURE = 0.3

# Optional local-dev fallback default (usually empty in production/demo).
# The sidebar input box is the primary and required source of the key.
ENV_DEFAULT_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ---------------------------------------------------------------------
# Form options
# ---------------------------------------------------------------------
EXPENSE_CATEGORIES = [
    "housing_rent",
    "food",
    "transportation",
    "utilities",
    "education",
    "healthcare",
    "entertainment",
    "loan_debt",
    "other",
]

EXPENSE_LABELS = {
    "housing_rent": "Housing / Rent",
    "food": "Food & Groceries",
    "transportation": "Transportation",
    "utilities": "Utilities",
    "education": "Education",
    "healthcare": "Healthcare",
    "entertainment": "Entertainment",
    "loan_debt": "Loan / Debt Payments",
    "other": "Other",
}

FINANCIAL_GOALS = [
    "Save money",
    "Build an emergency fund",
    "Pay off debt",
    "Save for a vacation",
    "Start a business",
    "Improve budgeting habits",
]

CURRENCIES = ["USD", "EUR", "GBP", "PKR", "INR", "AED", "CAD", "AUD"]

# ---------------------------------------------------------------------
# Caching
# ---------------------------------------------------------------------
CACHE_OPTIONS = ["None", "In-Memory", "SQLite"]
SQLITE_CACHE_PATH = ".langchain_cache.db"

# ---------------------------------------------------------------------
# Disclaimer text (shown on every relevant screen)
# ---------------------------------------------------------------------
EDUCATIONAL_DISCLAIMER = (
    "⚠️ **Educational Prototype Only.** FinWise AI does not provide "
    "guaranteed investment advice, does not execute financial "
    "transactions, and is not connected to any real bank account. "
    "Nothing shown here is a guarantee of any financial outcome. "
    "Please consult a qualified, licensed financial professional "
    "before making real financial decisions."
)
