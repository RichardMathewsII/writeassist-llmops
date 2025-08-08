"""Utility helpers used across the experiment package.

The original implementation relied on the third party ``tiktoken`` package to
estimate token counts for language models.  That dependency is optional and is
not available in the execution environment for these kata tests.  This module
now provides a graceful fallback that uses a very small approximation based on
whitespace tokenisation when ``tiktoken`` isn't installed.  The behaviour is
sufficient for the unit tests which only require deterministic, not exact,
counts.
"""

from __future__ import annotations

try:  # pragma: no cover - executed indirectly in tests
    import tiktoken
except ModuleNotFoundError:  # Provide a minimal stand-in when tiktoken is missing
    tiktoken = None  # type: ignore


def _simple_token_count(text: str) -> int:
    """Rudimentary token counter used when ``tiktoken`` is unavailable."""
    return len(text.split())


def num_tokens_for_llm(string: str, llm: str) -> int:
    """Return the number of tokens in ``string`` for a given ``llm``.

    When ``tiktoken`` is installed we delegate to it for accurate tokenisation;
    otherwise we fall back to a simple whitespace based approximation.
    """
    if tiktoken is None:
        return _simple_token_count(string)
    encoding = tiktoken.encoding_for_model(llm)
    return len(encoding.encode(string))


def trim_document_content(documents: list[dict], max_tokens: int, text_key: str) -> list[dict]:
    """Trim document contents so the total number of tokens stays below ``max_tokens``."""
    total_document_text = " ".join([context[text_key] for context in documents])
    total_document_tokens = num_tokens_for_llm(total_document_text, "gpt-3.5-turbo")
    if total_document_tokens > max_tokens:
        max_tokens_per_document = max_tokens // len(documents)
        for context in documents:
            context[text_key] = context[text_key][:max_tokens_per_document] + "..."
    return documents
