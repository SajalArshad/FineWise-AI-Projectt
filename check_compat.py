"""
check_compat.py
----------------
Run this after `pip install -r requirements.txt` to verify your installed
LangChain / langchain-core / langchain-openai / langchain-community
versions are wired up correctly with this project's imports — WITHOUT
needing an OpenAI API key or making any network call.

Usage:
    python check_compat.py
"""

import sys


def main() -> int:
    ok = True

    # 1. Report installed versions
    print("Installed package versions:")
    for pkg in ("langchain", "langchain_core", "langchain_openai", "langchain_community"):
        try:
            mod = __import__(pkg)
            print(f"  {pkg:20s} {getattr(mod, '__version__', 'unknown')}")
        except ImportError as e:
            print(f"  {pkg:20s} NOT INSTALLED ({e})")
            ok = False

    print()

    # 2. Exercise every import this project relies on
    checks = [
        ("langchain_openai.ChatOpenAI", lambda: __import__("langchain_openai", fromlist=["ChatOpenAI"])),
        ("langchain_core.messages (System/Human/AIMessage)",
         lambda: __import__("langchain_core.messages", fromlist=["SystemMessage", "HumanMessage", "AIMessage"])),
        ("langchain_core.output_parsers.StrOutputParser",
         lambda: __import__("langchain_core.output_parsers", fromlist=["StrOutputParser"])),
        ("langchain_core.prompts (PromptTemplate, ChatPromptTemplate)",
         lambda: __import__("langchain_core.prompts", fromlist=["PromptTemplate", "ChatPromptTemplate"])),
    ]
    for label, fn in checks:
        try:
            fn()
            print(f"  OK   {label}")
        except Exception as e:
            print(f"  FAIL {label}: {e}")
            ok = False

    # 3. Cache imports (with the same fallback logic as cache_manager.py)
    try:
        try:
            from langchain_core.globals import set_llm_cache  # noqa: F401
            print("  OK   set_llm_cache from langchain_core.globals")
        except ImportError:
            from langchain.globals import set_llm_cache  # noqa: F401
            print("  OK   set_llm_cache from langchain.globals (legacy fallback)")
    except Exception as e:
        print(f"  FAIL set_llm_cache: {e}")
        ok = False

    try:
        try:
            from langchain_core.caches import InMemoryCache  # noqa: F401
            print("  OK   InMemoryCache from langchain_core.caches")
        except ImportError:
            from langchain_community.cache import InMemoryCache  # noqa: F401
            print("  OK   InMemoryCache from langchain_community.cache (legacy fallback)")
    except Exception as e:
        print(f"  FAIL InMemoryCache: {e}")
        ok = False

    try:
        from langchain_community.cache import SQLiteCache  # noqa: F401
        print("  OK   SQLiteCache from langchain_community.cache")
    except Exception as e:
        print(f"  FAIL SQLiteCache: {e}")
        ok = False

    # 4. Import this project's own modules end-to-end
    try:
        sys.path.insert(0, ".")
        from src import config, financial_calculator, prompts, chains, cache_manager, utils  # noqa: F401
        print("  OK   All src/ modules import cleanly")
    except Exception as e:
        print(f"  FAIL project modules: {e}")
        ok = False

    print()
    if ok:
        print("✅ All compatibility checks passed.")
        return 0
    else:
        print("❌ Some checks failed — see FAIL lines above.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
