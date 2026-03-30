from pinecone import Pinecone
from langchain_openai import OpenAIEmbeddings
from backend.config import (
    OPENAI_API_KEY,
    PINECONE_API_KEY,
    PINECONE_INDEX,
    EMBEDDING_MODEL,
    TOP_K_RESULTS
)

def get_retriever():
    embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        openai_api_key=OPENAI_API_KEY
    )

    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX)

    def retrieve(query: str):
        query_vector = embeddings.embed_query(query)
        results = index.query(
            vector=query_vector,
            top_k=TOP_K_RESULTS,
            include_metadata=True
        )
        chunks = []
        for match in results["matches"]:
            chunks.append({
                "text": match["metadata"]["text"],
                "source": match["metadata"]["source"],
                "score": match["score"]
            })
        return chunks

    return retrieve