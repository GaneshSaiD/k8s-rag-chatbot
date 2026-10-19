from functools import lru_cache

from langchain_core.messages import SystemMessage, HumanMessage
from backend.config import OPENAI_API_KEY, LLM_MODEL
from backend.rag.prompt_templates import SYSTEM_PROMPT, HUMAN_PROMPT


@lru_cache(maxsize=1)
def _get_llm():
    # Imported lazily so the app (and tests) can start without API keys.
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(model=LLM_MODEL, openai_api_key=OPENAI_API_KEY, temperature=0)


@lru_cache(maxsize=1)
def _get_retriever():
    from backend.rag.retriever import get_retriever
    return get_retriever()


def build_context(chunks: list[dict]) -> str:
    return "\n\n".join(f"Source: {c['source']}\n{c['text']}" for c in chunks)


def unique_sources(chunks: list[dict]) -> list[str]:
    # Preserve retrieval order (most relevant first) while removing duplicates.
    return list(dict.fromkeys(c["source"] for c in chunks))


def ask(question: str):
    chunks = _get_retriever()(question)

    messages = [
        SystemMessage(content=SYSTEM_PROMPT.format(context=build_context(chunks))),
        HumanMessage(content=HUMAN_PROMPT.format(question=question)),
    ]

    response = _get_llm().invoke(messages)

    return {"answer": response.content, "sources": unique_sources(chunks)}
