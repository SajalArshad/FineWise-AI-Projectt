"""
chains.py
---------
Builds the ChatOpenAI model, a reusable analysis chain, a raw
System/Human/AI message demo, and the streaming narrative generator.

The OpenAI API key is NEVER read from a hardcoded value here. It is
passed in explicitly by the caller (app.py), which sources it from the
visitor's own input box in the Streamlit sidebar. This keeps the app
usable by any visitor with their own key, without a server-side secret.
"""

from typing import Dict, Generator, Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser

from . import config
from .prompts import ANALYSIS_CHAT_TEMPLATE, NARRATIVE_CHAT_TEMPLATE, SYSTEM_INSTRUCTIONS
from .utils import safe_parse_json


def build_llm(
    api_key: str,
    model_name: str = config.DEFAULT_MODEL_NAME,
    temperature: float = config.DEFAULT_TEMPERATURE,
    streaming: bool = False,
) -> ChatOpenAI:
    """
    Construct a ChatOpenAI instance using the visitor-supplied API key.

    Raises:
        ValueError: if no API key was provided.
    """
    if not api_key or not api_key.strip():
        raise ValueError(
            "No OpenAI API key provided. Enter your API key in the "
            "sidebar to use FinWise AI."
        )
    return ChatOpenAI(
        api_key=api_key,
        model=model_name,
        temperature=temperature,
        streaming=streaming,
    )


def build_analysis_chain(llm: ChatOpenAI):
    """
    A reusable chain (LangChain Expression Language, the modern
    successor to the legacy LLMChain class) that takes the financial
    inputs dict and returns the raw string response from the model.

    prompt -> llm -> string parser
    """
    return ANALYSIS_CHAT_TEMPLATE | llm | StrOutputParser()


def run_financial_analysis(llm: ChatOpenAI, inputs: Dict) -> dict:
    """
    Runs the analysis chain and safely parses the JSON result.

    `inputs` must contain: monthly_income, total_expenses,
    remaining_income, savings, savings_ratio, expense_ratio,
    preliminary_score, financial_goal, expense_breakdown.
    """
    chain = build_analysis_chain(llm)
    raw_output = chain.invoke(inputs)
    return safe_parse_json(raw_output)


def message_demo(inputs: Dict) -> Dict[str, str]:
    """
    Demonstrates how a conversation is represented using
    SystemMessage, HumanMessage, and AIMessage — purely illustrative,
    does not call the API. Useful for the UI's "how it works" tab.
    """
    system_msg = SystemMessage(content=SYSTEM_INSTRUCTIONS.strip())
    human_msg = HumanMessage(
        content=(
            f"My income is {inputs.get('monthly_income')} and my total "
            f"expenses are {inputs.get('total_expenses')}. My goal is "
            f"'{inputs.get('financial_goal')}'."
        )
    )
    ai_msg = AIMessage(
        content=(
            "Here is a structured, educational breakdown of your budget "
            "based on the numbers you shared... (this is where the real "
            "AIMessage reply would appear once the model responds)."
        )
    )
    return {
        "system": system_msg.content,
        "human": human_msg.content,
        "ai": ai_msg.content,
    }


def stream_recommendations(llm: ChatOpenAI, inputs: Dict) -> Generator[str, None, None]:
    """
    Streams a short narrative recommendation chunk-by-chunk, for use
    with st.write_stream() to create a natural typing effect.
    """
    messages = NARRATIVE_CHAT_TEMPLATE.format_messages(**inputs)
    for chunk in llm.stream(messages):
        if chunk.content:
            yield chunk.content
