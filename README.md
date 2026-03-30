# 🤖 K8s Ops AI Assistant — RAG Chatbot

> An AI-powered chatbot that answers Kubernetes operational questions using Retrieval-Augmented Generation (RAG). Built with LangChain, Pinecone, FastAPI, and OpenAI.

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-teal)](https://fastapi.tiangolo.com)
[![LangChain](https://img.shields.io/badge/LangChain-0.2-purple)](https://langchain.com)
[![Docker](https://img.shields.io/badge/Docker-ready-blue)](https://docker.com)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-deployed-blue)](https://kubernetes.io)

---

## 📌 What This Project Does

Engineers spend hours searching Kubernetes documentation to debug pod crashes, misconfigured RBAC, networking issues, and resource limits. This chatbot ingests the entire Kubernetes official documentation and your internal runbooks into a vector database, and uses an LLM to answer questions with **cited, grounded answers** — not hallucinations.

**Example questions it can answer:**
- "Why is my pod stuck in CrashLoopBackOff?"
- "How do I configure resource limits for a namespace?"
- "What's the difference between a Deployment and a StatefulSet?"
- "How does Kubernetes handle pod scheduling with node affinity?"

---

## 🏗️ Architecture

```
User → Chat UI (React/Streamlit)
            ↓
       FastAPI Backend
       ↙      ↓       ↘
Embedding   Query       Context
 Model     Processor    Builder
  ↓                        ↑
Pinecone ────── retrieved chunks ──────┘
Vector DB

FastAPI → LLM (GPT-4o / Claude) → Response → User
```

**Two pipelines:**

| Pipeline | When | What it does |
|---|---|---|
| Ingestion | One-time / scheduled | Scrape docs → chunk → embed → store in Pinecone |
| Query | Every request | Embed query → retrieve top-k chunks → build prompt → LLM → answer |

---

## 🔧 Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | React / Streamlit | Chat interface |
| Backend | FastAPI | REST API, orchestration |
| RAG Framework | LangChain | Retrieval chain, prompt templates |
| Embedding Model | OpenAI `text-embedding-3-small` | Convert text to vectors |
| Vector Database | Pinecone | Store and search embeddings |
| LLM | GPT-4o / Claude Sonnet | Generate final answers |
| Document Loader | LangChain WebBaseLoader | Scrape Kubernetes docs |
| Chunking | RecursiveCharacterTextSplitter | 512-token chunks, 50 overlap |
| Containerization | Docker | Portable deployment |
| Orchestration | Kubernetes + Helm | Production deployment |
| CI/CD | GitHub Actions | Automated build and deploy |
| Monitoring | Prometheus + Grafana | Latency, query volume tracking |

---

## 📁 Project Structure

```
k8s-rag-chatbot/
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── api/
│   │   └── routes.py            # /query, /health endpoints
│   ├── rag/
│   │   ├── ingestion.py         # Document loading + chunking + embedding
│   │   ├── retriever.py         # Pinecone vector search
│   │   ├── chain.py             # LangChain RAG chain
│   │   └── prompt_templates.py  # System + user prompt templates
│   └── config.py                # Environment config
├── frontend/
│   └── app.py                   # Streamlit chat UI
├── ingestion/
│   └── ingest_k8s_docs.py       # One-time ingestion script
├── k8s/
│   ├── deployment.yaml          # K8s Deployment manifest
│   ├── service.yaml             # K8s Service manifest
│   └── helm/                    # Helm chart
├── .github/
│   └── workflows/
│       └── ci-cd.yaml           # GitHub Actions pipeline
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Docker
- Pinecone account (free tier works)
- OpenAI API key

### 1. Clone and Install

```bash
git clone https://github.com/yourusername/k8s-rag-chatbot.git
cd k8s-rag-chatbot
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
cp .env.example .env
# Fill in:
# OPENAI_API_KEY=sk-...
# PINECONE_API_KEY=...
# PINECONE_INDEX=k8s-ops-assistant
# PINECONE_ENV=us-east-1-aws
```

### 3. Run the Ingestion Pipeline

```bash
python ingestion/ingest_k8s_docs.py
```

This scrapes the Kubernetes documentation, chunks it into 512-token segments, generates embeddings, and uploads them to Pinecone. Runs once (or on update).

### 4. Start the Backend

```bash
uvicorn backend.main:app --reload --port 8000
```

### 5. Start the Frontend

```bash
streamlit run frontend/app.py
```

Open `http://localhost:8501` and start asking Kubernetes questions.

---

## 🐳 Docker

```bash
docker-compose up --build
```

Services started:
- `backend` on port 8000
- `frontend` on port 8501

---

## ☸️ Deploy to Kubernetes

```bash
# Build and push image
docker build -t your-dockerhub/k8s-rag-chatbot:latest .
docker push your-dockerhub/k8s-rag-chatbot:latest

# Deploy via Helm
helm install k8s-rag ./k8s/helm \
  --set image.repository=your-dockerhub/k8s-rag-chatbot \
  --set secrets.openaiKey=$OPENAI_API_KEY \
  --set secrets.pineconeKey=$PINECONE_API_KEY
```

---

## 🔑 Key Design Decisions

**Why RAG over fine-tuning?**
Kubernetes documentation is updated frequently. RAG lets us update the knowledge base by re-running ingestion — no retraining needed.

**Why Pinecone?**
Managed, serverless vector DB with excellent Python SDK. No ops overhead. For a fully self-hosted setup, swap for Weaviate or Qdrant.

**Why 512-token chunks?**
Balances semantic coherence (not too small to lose context) with retrieval precision (not so large that irrelevant content fills the context window).

**Why LangChain?**
Abstracts the retrieval chain, prompt templates, and LLM calls into composable pieces. Easy to swap the LLM (OpenAI ↔ Claude ↔ local Llama) without rewriting logic.

---

## 📊 Evaluation Metrics

| Metric | Target | Tool |
|---|---|---|
| Answer relevancy | > 0.85 | RAGAS |
| Context recall | > 0.80 | RAGAS |
| API p95 latency | < 3s | Prometheus |
| Query throughput | > 10 req/s | Locust load test |

---

## 🗺️ Roadmap

- [x] Document ingestion pipeline
- [x] RAG retrieval chain
- [x] FastAPI backend
- [x] Streamlit chat UI
- [x] Docker + Kubernetes deployment
- [ ] Slack bot integration (`/k8s-help` slash command)
- [ ] Feedback loop (thumbs up/down → RLHF dataset)
- [ ] Support for custom internal runbooks
- [ ] Conversation memory (multi-turn context)
- [ ] MLflow experiment tracking for retrieval evals

---

## 🤝 Contributing

Pull requests welcome. Please open an issue first to discuss what you'd like to change.

---

## 📄 License

MIT

---

## 👤 Author

**Ganesh Sai Dontineni**
DevOps / Cloud / Data Engineer
[LinkedIn](https://linkedin.com/in/yourprofile) · [GitHub](https://github.com/yourusername)