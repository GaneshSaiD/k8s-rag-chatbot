from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from backend.config import OPENAI_API_KEY, LLM_MODEL
from backend.rag.retriever import get_retriever
from backend.rag.prompt_templates import SYSTEM_PROMPT, HUMAN_PROMPT

llm = ChatOpenAI(
    model=LLM_MODEL,
    openai_api_key=OPENAI_API_KEY,
    temperature=0
)

retrieve = get_retriever()

def ask(question: str):
    chunks = retrieve(question)

    context = "\n\n".join([
        f"Source: {c['source']}\n{c['text']}"
        for c in chunks
    ])

    messages = [
        SystemMessage(content=SYSTEM_PROMPT.format(context=context)),
        HumanMessage(content=HUMAN_PROMPT.format(question=question))
    ]

    response = llm.invoke(messages)

    return {
        "answer": response.content,
        "sources": list(set([c["source"] for c in chunks]))
    }