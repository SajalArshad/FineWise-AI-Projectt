## 🚀 Live Demo

[View FineWise AI App](https://sajal-finewise-ai-projectt.streamlit.app/)

# FinWise AI — AI-Powered Personal Financial Analysis & Smart Budget Assistant

An educational LangChain + Streamlit prototype. Users enter their monthly
income, expenses, and savings; Python computes deterministic financial
ratios; a LangChain-powered LLM turns those numbers into a structured,
educational budgeting dashboard with a streamed narrative recommendation.

> ⚠️ **Educational prototype only.** This app does not provide guaranteed
> investment advice, does not execute financial transactions, and is not
> connected to any real bank account. Consult a qualified, licensed
> financial professional before making real financial decisions.

## What's different in this build: bring-your-own API key

Instead of one operator's `OPENAI_API_KEY` powering every user, **each
visitor pastes their own OpenAI API key** into a password-style box in
the sidebar before any AI feature will run. The key:

- lives only in `st.session_state` for that browser session,
- is never written to disk, logged, or committed,
- is sent only directly to OpenAI's API for the calls that visitor
  requests.

A `.env` file is still supported for local development (see
`.env.example`) purely as a convenience default that pre-fills the
sidebar box — it is never required.

## Project structure

```
finwise_ai/
├── app.py                     # Streamlit UI — run this
├── requirements.txt
├── .env.example
├── README.md
├── src/
│   ├── __init__.py
│   ├── config.py               # settings + form options
│   ├── prompts.py               # PromptTemplate + ChatPromptTemplate + JSON schema
│   ├── financial_calculator.py  # deterministic maths — no AI
│   ├── chains.py                 # ChatOpenAI, reusable chain, streaming
│   ├── cache_manager.py           # in-memory + SQLite caching
│   └── utils.py                    # safe JSON parsing + helpers
└── docs/
    └── FinTech_AI_Assignment.pdf
```

## Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. (Optional, local dev only) copy `.env.example` to `.env` and set a
   default key — never commit a real key. `.env` is already in
   `.gitignore`.
4. Run the app:
   ```bash
   streamlit run app.py
   ```
5. In the running app's sidebar, paste your own OpenAI API key (get one
   at platform.openai.com) — the app is unusable for AI features until
   a key is entered.

## Python calculations vs. AI insight

The assignment deliberately separates deterministic math from
AI-generated interpretation:

| Layer | Where | What it does |
|---|---|---|
| **Python** | `financial_calculator.py` | `total_expenses`, `remaining_income`, `savings_ratio`, `expense_ratio`, and a rule-based `preliminary_score` (0-100) — the same inputs always produce the same outputs, with divide-by-zero guarded when income is 0. |
| **LangChain / LLM** | `prompts.py`, `chains.py` | Takes those Python-computed numbers (never invents its own) plus the user's stated goal, and produces qualitative, structured JSON: a summary, a health score, risk level, spending analysis, priorities, and action plan. |

Keeping these separate means the numeric ratios are always trustworthy
and reproducible, while the AI is used only for the qualitative,
educational interpretation layer on top.

## Caching: InMemoryCache vs. SQLiteCache

LangChain's `set_llm_cache(...)` registers **one global cache**; before
every model call, LangChain checks whether an identical prompt has
already been answered. If so, it returns the cached response instantly
and makes **no new API call** — saving both time and cost when a user
resubmits the same inputs.

| | InMemoryCache | SQLiteCache |
|---|---|---|
| Stored in | RAM | A `.db` file on disk |
| Speed | Fastest | Fast, slightly slower |
| Survives app restart? | No | Yes |
| Best for | A single session / demo | Reusing results across sessions |

Switch between them (or turn caching off) from the sidebar's **Caching**
section; the choice is applied via `cache_manager.configure_cache()`.

## Testing scenarios

Use the five scenarios below (from the assignment brief) to sanity-check
behavior:

| # | Input | Expected calculation | Expected AI response |
|---|---|---|---|
| 1 | Income 8000, expenses ~2000 | Large positive remaining; high savings ratio | High score; LOW risk; growth-focused tips |
| 2 | Income 2000, expenses ~2600 | Negative remaining; expense ratio >100% | Low score; HIGH risk; urgent cost-cutting |
| 3 | Income 5000, debt 2500 | High debt share of income | MEDIUM/HIGH risk; debt-reduction priorities |
| 4 | Income 4000, savings 1200 | Savings ratio ~30% | High score; LOW risk; reinforce good habits |
| 5 | Income 3000, expenses 3000 | Remaining = 0 | MEDIUM/HIGH risk; find room to save |

## Notes

- Uses LangChain Expression Language (`prompt | llm | parser`) as the
  modern equivalent of the legacy `LLMChain` class, wired through
  `chains.build_analysis_chain()`.
- All AI output is safely parsed in `utils.safe_parse_json()`, falling
  back to a safe default structure if the model ever returns invalid
  JSON, so the dashboard never crashes.
- This project is for education only. It is not financial advice and
  must not be used to make real investment or money decisions.

## LangChain 1.x compatibility

This project targets **LangChain 1.x** (developed against LangChain
1.3.16 on Python 3.12) and avoids all deprecated 0.x-era APIs:

- **No `LLMChain`.** `src/chains.py` uses LangChain Expression Language
  (`ANALYSIS_CHAT_TEMPLATE | llm | StrOutputParser()`), which is the
  1.x-native way to build a reusable chain — `LLMChain` is deprecated
  and was removed from the modern `langchain` package.
- **Caching moved to `langchain_core`.** In 1.x, `set_llm_cache` and
  `InMemoryCache` live in `langchain_core.globals` /
  `langchain_core.caches` instead of `langchain.globals` /
  `langchain_community.cache`. `src/cache_manager.py` imports from the
  new `langchain_core` locations first and only falls back to the old
  `langchain` / `langchain_community` paths if you happen to be on an
  older installation — so it works either way without edits.
- **`SQLiteCache`** remains a `langchain_community.cache` integration
  in both 0.x and 1.x, so that import is unchanged.
- **Prompts, messages, and parsers** (`PromptTemplate`,
  `ChatPromptTemplate`, `SystemMessage`/`HumanMessage`/`AIMessage`,
  `StrOutputParser`) already live in `langchain_core` and required no
  changes.

### Verifying your installation

Run the included compatibility checker after installing dependencies —
it imports everything this project uses (no API key or network call
required) and reports which import path each piece resolved to:

```bash
pip install -r requirements.txt
python check_compat.py
```

If it prints `✅ All compatibility checks passed.`, `streamlit run
app.py` will run cleanly. If any line prints `FAIL`, it tells you
exactly which import needs attention for your installed version.
