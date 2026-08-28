"""
cache_manager.py
-----------------
Configures LangChain's global LLM cache. Two backends are supported:

  - InMemoryCache : lives only in RAM; fastest; lost on app restart;
                    best for a single user session.
  - SQLiteCache   : persisted to a .db file on disk; slightly slower
                    than in-memory but survives restarts; best for
                    reusing results across sessions/demos.

set_llm_cache(...) registers ONE global cache. LangChain checks it before
every model call — an identical prompt (same model + same messages) is
served from the cache instead of making a new, billable API call.

LANGCHAIN 1.x COMPATIBILITY NOTE
---------------------------------
In LangChain 1.0+, the legacy top-level `langchain` package was slimmed
down considerably. Global cache configuration (`set_llm_cache`) and the
pure-Python `InMemoryCache` implementation now live in `langchain_core`
instead of `langchain`/`langchain_community`. `SQLiteCache` is a
provider-style integration and still lives in `langchain_community`.

The imports below try the current `langchain_core` locations first and
fall back to the older `langchain` / `langchain_community` locations,
so this file works unmodified whether you're on LangChain 1.x or an
older 0.2/0.3 installation.
"""

# --- set_llm_cache: langchain_core (1.x) with legacy fallback ---------
try:
    from langchain_core.globals import set_llm_cache
except ImportError:  # pragma: no cover - only hit on very old versions
    from langchain.globals import set_llm_cache  # type: ignore

# --- InMemoryCache: langchain_core (1.x) with legacy fallback ---------
try:
    from langchain_core.caches import InMemoryCache
except ImportError:  # pragma: no cover
    from langchain_community.cache import InMemoryCache  # type: ignore

# --- SQLiteCache: still a langchain_community integration -------------
from langchain_community.cache import SQLiteCache

from . import config


def configure_cache(cache_type: str) -> str:
    """
    Register the requested cache backend as LangChain's global cache.

    Args:
        cache_type: one of "None", "In-Memory", "SQLite"

    Returns:
        A short human-readable status string for display in the UI.
    """
    if cache_type == "In-Memory":
        set_llm_cache(InMemoryCache())
        return "In-Memory cache active (cleared on restart)."

    if cache_type == "SQLite":
        set_llm_cache(SQLiteCache(database_path=config.SQLITE_CACHE_PATH))
        return f"SQLite cache active ({config.SQLITE_CACHE_PATH})."

    set_llm_cache(None)
    return "Caching disabled — every request calls the API."
