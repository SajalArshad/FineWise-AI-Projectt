"""
app.py
------
FinWise AI — Streamlit entry point.

KEY CHANGE FOR THIS ASSIGNMENT VARIANT:
This app does NOT require a server-side OPENAI_API_KEY. Instead, every
visitor pastes their OWN OpenAI API key into a password-style input box
in the sidebar before the app will do any AI work. The key lives only in
st.session_state for that browser session — it is never written to disk,
logged, or sent anywhere except directly to OpenAI's API to make the
call the visitor requested.

Run with:  streamlit run app.py
"""

import streamlit as st

from src import config
from src.financial_calculator import FinancialCalculation, score_band
from src.cache_manager import configure_cache
from src.chains import build_llm, run_financial_analysis, stream_recommendations, message_demo
from src.utils import format_currency

# ----------------------------------------------------------------------
# Page setup
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="FinWise AI — Smart Budget Assistant",
    page_icon="💰",
    layout="wide",
)

# ----------------------------------------------------------------------
# Session state defaults
# ----------------------------------------------------------------------
defaults = {
    "openai_api_key": config.ENV_DEFAULT_API_KEY,
    "cache_status": "Caching disabled — every request calls the API.",
    "analysis_result": None,
    "calc_result": None,
    "narrative_text": "",
    "submitted": False,
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def reset_session():
    for key, value in defaults.items():
        st.session_state[key] = value


# ----------------------------------------------------------------------
# SIDEBAR — logo/title, disclaimer, API key box, model + cache settings
# ----------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 💰 FinWise AI")
    st.caption("AI-Powered Personal Financial Analysis & Smart Budget Assistant")
    st.caption("Educational LangChain + Streamlit FinTech prototype")

    st.info(config.EDUCATIONAL_DISCLAIMER)

    st.markdown("### 🔑 Your OpenAI API Key")
    st.caption(
        "FinWise AI runs on **your own** OpenAI API key — it is used only "
        "for this session and is never stored or shared. Get a key at "
        "platform.openai.com."
    )
    api_key_input = st.text_input(
        "OpenAI API key",
        value=st.session_state.openai_api_key,
        type="password",
        placeholder="sk-...",
        help="Required to run any AI analysis in this app.",
    )
    st.session_state.openai_api_key = api_key_input

    if st.session_state.openai_api_key.strip():
        st.success("API key set for this session ✅")
    else:
        st.warning("Enter an OpenAI API key above to enable AI analysis.")

    st.markdown("### ⚙️ Model Settings")
    model_name = st.selectbox("Model", config.AVAILABLE_MODELS, index=0)
    temperature = st.slider("Creativity (temperature)", 0.0, 1.0, config.DEFAULT_TEMPERATURE, 0.05)

    st.markdown("### 🗄️ Caching")
    cache_choice = st.selectbox("Cache backend", config.CACHE_OPTIONS, index=0)
    if st.button("Apply cache setting", use_container_width=True):
        st.session_state.cache_status = configure_cache(cache_choice)
    st.caption(st.session_state.cache_status)

    st.markdown("---")
    if st.button("🔄 Reset session", use_container_width=True):
        reset_session()
        st.rerun()

# ----------------------------------------------------------------------
# MAIN PAGE — header + disclaimer
# ----------------------------------------------------------------------
st.title("💰 FinWise AI — Smart Budget Assistant")
st.warning(config.EDUCATIONAL_DISCLAIMER)

# ----------------------------------------------------------------------
# GATE: require the visitor's own OpenAI API key before showing the
# rest of the interface (form, dashboard, how-it-works tabs).
# The key box lives in the sidebar; this just blocks the main content
# until it's filled in, then reveals everything automatically.
# ----------------------------------------------------------------------
if not st.session_state.openai_api_key.strip():
    st.info(
        "👈 **Enter your OpenAI API key in the sidebar to unlock FinWise AI.**\n\n"
        "Your key is used only for this browser session, is never stored "
        "or sent anywhere except directly to OpenAI, and lets you run the "
        "financial form, AI dashboard, and streaming recommendations below."
    )
    st.caption(
        "Don't have a key? Create one for free at "
        "[platform.openai.com](https://platform.openai.com/api-keys)."
    )
    st.stop()

tab_form, tab_dashboard, tab_how = st.tabs(
    ["📝 Enter Your Finances", "📊 AI Dashboard", "🧠 How It Works"]
)

# ----------------------------------------------------------------------
# TAB 1 — Input form
# ----------------------------------------------------------------------
with tab_form:
    st.subheader("Tell us about your month")

    with st.form("financial_form"):
        col1, col2 = st.columns(2)
        with col1:
            currency = st.selectbox("Currency", config.CURRENCIES, index=0)
            monthly_income = st.number_input(
                "Monthly income", min_value=0.0, value=4000.0, step=50.0
            )
            savings = st.number_input(
                "Current monthly savings", min_value=0.0, value=400.0, step=25.0
            )
        with col2:
            financial_goal = st.selectbox("Financial goal", config.FINANCIAL_GOALS)

        st.markdown("#### Monthly expenses")
        expenses = {}
        with st.expander("Expand to enter all 9 expense categories", expanded=True):
            exp_cols = st.columns(3)
            for i, cat in enumerate(config.EXPENSE_CATEGORIES):
                with exp_cols[i % 3]:
                    expenses[cat] = st.number_input(
                        config.EXPENSE_LABELS[cat],
                        min_value=0.0,
                        value=0.0,
                        step=10.0,
                        key=f"exp_{cat}",
                    )

        submitted = st.form_submit_button("Analyze my finances", use_container_width=True)

    if submitted:
        st.session_state.submitted = True
        calc = FinancialCalculation(
            monthly_income=monthly_income, expenses=expenses, savings=savings
        )
        st.session_state.calc_result = calc.to_dict()
        st.session_state.calc_result["currency"] = currency
        st.session_state.calc_result["financial_goal"] = financial_goal
        st.session_state.analysis_result = None
        st.session_state.narrative_text = ""

        if not st.session_state.openai_api_key.strip():
            st.error(
                "Please enter your OpenAI API key in the sidebar before "
                "running the AI analysis."
            )
        else:
            try:
                with st.spinner("Running deterministic calculations and asking the AI..."):
                    llm = build_llm(
                        api_key=st.session_state.openai_api_key,
                        model_name=model_name,
                        temperature=temperature,
                    )
                    chain_inputs = {
                        "monthly_income": monthly_income,
                        "total_expenses": calc.total_expenses,
                        "remaining_income": calc.remaining_income,
                        "savings": savings,
                        "savings_ratio": round(calc.savings_ratio, 2),
                        "expense_ratio": round(calc.expense_ratio, 2),
                        "preliminary_score": calc.preliminary_score,
                        "financial_goal": financial_goal,
                        "expense_breakdown": {
                            config.EXPENSE_LABELS[k]: v for k, v in expenses.items()
                        },
                    }
                    st.session_state.analysis_result = run_financial_analysis(llm, chain_inputs)
                    st.session_state.chain_inputs = chain_inputs
                st.success("Analysis complete — see the 📊 AI Dashboard tab.")
            except ValueError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"Something went wrong calling the OpenAI API: {e}")

# ----------------------------------------------------------------------
# TAB 2 — Dashboard
# ----------------------------------------------------------------------
with tab_dashboard:
    calc_result = st.session_state.calc_result

    if not calc_result:
        st.info("Fill in the form in the first tab and click **Analyze my finances**.")
    else:
        currency = calc_result.get("currency", "USD")

        st.subheader("📈 Financial Overview (Python-calculated, deterministic)")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Monthly Income", format_currency(calc_result["monthly_income"], currency))
        m2.metric("Total Expenses", format_currency(calc_result["total_expenses"], currency))
        m3.metric(
            "Remaining Income",
            format_currency(calc_result["remaining_income"], currency),
            delta=f"{calc_result['expense_ratio']}% of income spent",
            delta_color="inverse",
        )
        m4.metric("Current Savings", format_currency(calc_result["savings"], currency))

        c1, c2 = st.columns(2)
        c1.progress(min(int(calc_result["savings_ratio"]), 100), text=f"Savings ratio: {calc_result['savings_ratio']}%")
        c2.progress(min(int(calc_result["expense_ratio"]), 100), text=f"Expense ratio: {calc_result['expense_ratio']}%")

        st.caption(
            f"Preliminary rule-based score (Python heuristic, before AI review): "
            f"**{calc_result['preliminary_score']}/100** — {score_band(calc_result['preliminary_score'])}"
        )

        st.markdown("---")
        st.subheader("🤖 AI Financial Analysis")

        result = st.session_state.analysis_result
        if not result:
            st.info("No AI analysis yet. Submit the form with a valid API key first.")
        else:
            score = result["financial_health_score"]
            risk = result["risk_level"]

            colA, colB = st.columns([2, 1])
            with colA:
                st.markdown(f"**Financial summary:** {result['financial_summary']}")
                st.progress(score / 100, text=f"AI Financial Health Score: {score}/100 ({score_band(score)})")
            with colB:
                risk_box = {"LOW": st.success, "MEDIUM": st.warning, "HIGH": st.error}
                risk_box.get(risk, st.warning)(f"Risk level: **{risk}**")

            dash_tabs = st.tabs(
                ["Spending Analysis", "Priorities & Budget", "Savings Strategy", "Action Plan"]
            )

            with dash_tabs[0]:
                if result["spending_analysis"]:
                    for item in result["spending_analysis"]:
                        with st.expander(f"📂 {item.get('category', 'Category')}"):
                            st.write(f"**Observation:** {item.get('observation', '')}")
                            st.write(f"**Recommendation:** {item.get('recommendation', '')}")
                else:
                    st.write("No category-level analysis returned.")

            with dash_tabs[1]:
                st.markdown("**Top priorities**")
                for p in result["top_priorities"]:
                    st.write(f"- {p}")
                st.markdown("**Budget recommendations**")
                for b in result["budget_recommendations"]:
                    st.write(f"- {b}")

            with dash_tabs[2]:
                for s in result["savings_strategy"]:
                    st.write(f"- {s}")

            with dash_tabs[3]:
                for a in result["next_month_action_plan"]:
                    st.write(f"- {a}")

            st.markdown("---")
            st.subheader("✍️ Streamed Narrative Recommendation")
            if st.button("Generate streaming recommendation"):
                if not st.session_state.openai_api_key.strip():
                    st.error("Enter your OpenAI API key in the sidebar first.")
                else:
                    try:
                        stream_llm = build_llm(
                            api_key=st.session_state.openai_api_key,
                            model_name=model_name,
                            temperature=temperature,
                            streaming=True,
                        )
                        st.session_state.narrative_text = st.write_stream(
                            stream_recommendations(stream_llm, st.session_state.chain_inputs)
                        )
                    except Exception as e:
                        st.error(f"Streaming failed: {e}")

            st.caption(config.EDUCATIONAL_DISCLAIMER)

# ----------------------------------------------------------------------
# TAB 3 — How it works (message demo, educational)
# ----------------------------------------------------------------------
with tab_how:
    st.subheader("How FinWise AI is built")
    st.markdown(
        """
1. **Python does the math** (`financial_calculator.py`) — total expenses,
   remaining income, savings ratio, expense ratio, and a preliminary
   0-100 score are all computed deterministically, with no AI involved.
2. **LangChain builds the prompts** (`prompts.py`) — a `PromptTemplate`
   and a `ChatPromptTemplate` carry the numbers and safety rules into
   the model call.
3. **ChatOpenAI + a reusable chain** (`chains.py`) sends the data to
   OpenAI and asks for strict JSON back.
4. **Safe JSON parsing** (`utils.py`) guards the UI against malformed
   model output.
5. **Streaming** turns the final written recommendation into a live
   typing effect using `.stream()` and `st.write_stream()`.
6. **Caching** (`cache_manager.py`) can store repeated results in
   memory or on disk (SQLite) so identical requests don't re-call the
   API.
        """
    )

    st.markdown("#### Message roles demo (SystemMessage / HumanMessage / AIMessage)")
    if st.session_state.calc_result:
        demo_inputs = {
            "monthly_income": st.session_state.calc_result["monthly_income"],
            "total_expenses": st.session_state.calc_result["total_expenses"],
            "financial_goal": st.session_state.calc_result.get("financial_goal", ""),
        }
    else:
        demo_inputs = {"monthly_income": 4000, "total_expenses": 2500, "financial_goal": "Save money"}

    demo = message_demo(demo_inputs)
    st.markdown("**SystemMessage** *(role + safety rules)*")
    st.code(demo["system"], language="text")
    st.markdown("**HumanMessage** *(dynamic user data)*")
    st.code(demo["human"], language="text")
    st.markdown("**AIMessage** *(illustrative shape of a reply)*")
    st.code(demo["ai"], language="text")

    st.caption(config.EDUCATIONAL_DISCLAIMER)
