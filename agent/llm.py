"""
Local LLM configuration using Ollama.

Ollama runs the local model.
LangChain communicates with Ollama through ChatOllama.
"""

from functools import lru_cache

from langchain_ollama import ChatOllama

from agent.config import OLLAMA_MODEL, OLLAMA_BASE_URL

@lru_cache(maxsize=1)
def get_llm() -> ChatOllama:
    """
    Create and return the local Ollama chat model.
    """

    return ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0
    )