import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.config import (
    OPENAI_API_KEY,
    PINECONE_API_KEY,
    PINECONE_INDEX,
    EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP
)

import requests
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone, ServerlessSpec
import time

K8S_DOCS_URLS = [
    "https://kubernetes.io/docs/concepts/overview/",
    "https://kubernetes.io/docs/concepts/workloads/pods/",
    "https://kubernetes.io/docs/concepts/workloads/controllers/deployment/",
    "https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/",
    "https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/",
    "https://kubernetes.io/docs/concepts/services-networking/service/",
    "https://kubernetes.io/docs/concepts/services-networking/ingress/",
    "https://kubernetes.io/docs/concepts/storage/persistent-volumes/",
    "https://kubernetes.io/docs/concepts/configuration/configmap/",
    "https://kubernetes.io/docs/concepts/configuration/secret/",
    "https://kubernetes.io/docs/concepts/security/rbac-good-practices/",
    "https://kubernetes.io/docs/concepts/scheduling-eviction/",
    "https://kubernetes.io/docs/tasks/debug/debug-application/",
    "https://kubernetes.io/docs/tasks/debug/debug-cluster/",
    "https://kubernetes.io/docs/concepts/cluster-administration/logging/",
]

def scrape_page(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        main = soup.find("main") or soup.find("article") or soup.find("body")
        for tag in main(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = main.get_text(separator="\n", strip=True)
        return text
    except Exception as e:
        print(f"  Failed to scrape {url}: {e}")
        return None
    
def chunk_text(text, url):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " "]
    )
    chunks = splitter.split_text(text)
    docs = []
    for i, chunk in enumerate(chunks):
        docs.append({
            "text": chunk,
            "metadata": {"source": url, "chunk_id": i}
        })
    return docs


def setup_pinecone_index(pc):
    existing = [idx.name for idx in pc.list_indexes()]
    if PINECONE_INDEX not in existing:
        print(f"Creating Pinecone index: {PINECONE_INDEX}")
        pc.create_index(
            name=PINECONE_INDEX,
            dimension=1536,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
        time.sleep(5)
    else:
        print(f"Index '{PINECONE_INDEX}' already exists, skipping creation.")
    return pc.Index(PINECONE_INDEX)

def embed_and_upload(docs, embeddings, index):
    batch_size = 50
    for i in range(0, len(docs), batch_size):
        batch = docs[i:i + batch_size]
        texts = [d["text"] for d in batch]
        vectors = embeddings.embed_documents(texts)
        to_upsert = [
            (
                f"chunk-{i+j}",
                vectors[j],
                {"text": batch[j]["text"], "source": batch[j]["metadata"]["source"]}
            )
            for j in range(len(batch))
        ]
        index.upsert(vectors=to_upsert)
        print(f"  Uploaded batch {i//batch_size + 1} ({len(batch)} chunks)")
        
def main():
    print("=== K8s RAG Ingestion Pipeline ===\n")

    print("Step 1: Initializing embeddings and Pinecone...")
    embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        openai_api_key=OPENAI_API_KEY
    )
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = setup_pinecone_index(pc)

    print("\nStep 2: Scraping Kubernetes docs...")
    all_docs = []
    for url in K8S_DOCS_URLS:
        print(f"  Scraping: {url}")
        text = scrape_page(url)
        if text:
            chunks = chunk_text(text, url)
            all_docs.extend(chunks)
            print(f"  -> {len(chunks)} chunks")
        time.sleep(1)

    print(f"\nTotal chunks to embed: {len(all_docs)}")

    print("\nStep 3: Embedding and uploading to Pinecone...")
    embed_and_upload(all_docs, embeddings, index)

    print("\n=== Ingestion complete! ===")
    print(f"Total vectors in index: {index.describe_index_stats()['total_vector_count']}")

if __name__ == "__main__":
    main()
