# ⚖️ LegalRAG - Intelligent Legal Assistant

![CI/CD Pipeline](https://github.com/Iyed0092/LegalRAG/actions/workflows/ci_pipeline.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.10-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Enabled-blue.svg)
![Status](https://img.shields.io/badge/Status-Prototype-orange.svg)

**LegalRAG** is an advanced Retrieval-Augmented Generation (RAG) system designed to analyze complex legislative documents with high precision.

Unlike standard RAG systems that rely solely on vector similarity, LegalRAG implements a **Hybrid Architecture**:
1.  **Dense Retrieval (ChromaDB):** Finds semantically similar text chunks.
2.  **Knowledge Graph (Neo4j):** Maps and traverses legal dependencies (e.g., "Article 14 refers to Section 3").

This dual approach significantly reduces hallucinations and ensures that answers are grounded in the actual statutory context.

---

## 🚀 Key Features

* **🕸️ Hybrid Search Engine:** Combines **Vector Embeddings** (Sentence-Transformers) for semantic nuances and **Graph Traversal** (Cypher queries) for structural context.
* **🛡️ Hallucination Guardrails:** Implements a strict prompt engineering strategy ("Strict Mode") to prevent the LLM from inventing facts.
* **📄 Automated Ingestion:** Robust PDF processing pipeline that extracts text, chunks it intelligently, and indexes it into both databases simultaneously.
* **🐳 Microservices Architecture:** Fully containerized using **Docker Compose** (Django API, Neo4j, ChromaDB, Streamlit).
* **⚡ Interactive Dashboard:** User-friendly **Streamlit** interface for uploading documents and chatting with the legal assistant.

## 🏗️ System Architecture

The system follows a modular ETL (Extract, Transform, Load) and RAG pipeline:

1.  **Ingestion:** PDFs are parsed, cleaned, and split into chunks (LangChain).
2.  **Indexing:**
    * **Vector Store (ChromaDB):** Stores embeddings for similarity search.
    * **Graph Store (Neo4j):** Creates nodes for articles and relationships (`REFERS_TO`) for references.
3.  **Retrieval:** The engine performs a parallel search (Vector + Graph) to gather the most relevant context.
4.  **Generation:** The **FLAN-T5** model synthesizes the answer based *strictly* on the retrieved context.



## 📂 Project Structure

```bash
legal_rag_project/
├── .env                       # Environment variables (API Keys, Neo4j/Chroma URLs)
├── .gitignore
├── README.md
├── docker-compose.yml         # Orchestration (Django + Neo4j + Chroma + Redis)
├── Dockerfile                 # Django Backend Image
├── requirements.txt           # Python Dependencies (Django, DRF, ChromaDB, Neo4j, etc.)
├── manage.py                  # Django CLI
│
├── config/                    # Global Project Config
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py            # Project Settings
│   ├── urls.py                # Main URL Router
│   └── wsgi.py
│
├── apps/                      # Functional Modules (Domain Services)
│   ├── __init__.py
│   │
│   ├── ingestion/             # MODULE 1: ETL & Indexing
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py          # SQL Model for file tracking (DocumentMetadata)
│   │   ├── services/
│   │   │   ├── pdf_parser.py  # Text Extraction (PyPDF/LangChain)
│   │   │   ├── chunker.py     # Semantic Chunking
│   │   │   └── loader.py      # Orchestrator sending data to Chroma & Neo4j
│   │   └── views.py           # File Upload API
│   │
│   ├── rag_engine/            # MODULE 2: The Brain (Retrieval + LLM)
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── connectors/        # Database Connectors
│   │   │   ├── vector_store.py # ChromaDB Wrapper + SentenceTransformers
│   │   │   └── graph_store.py  # Neo4j Wrapper (Cypher queries)
│   │   ├── llm/
│   │   │   └── flan_t5.py      # Inference Logic (HuggingFace Pipeline)
│   │   ├── logic/
│   │   │   └── hybrid_search.py # Hybrid Fusion Logic (Vector + Graph)
│   │   └── views.py            # Q&A API (/ask)
│   │
│   └── evaluation/            # MODULE 3: Benchmarking (Recall@5)
│       ├── __init__.py
│       ├── scripts/
│       │   ├── generate_ground_truth.py
│       │   └── calculate_recall.py
│       └── metrics.py
│
└── data/                      # Local Storage (Git Ignored)
    ├── raw_pdfs/              # Raw legislative PDFs
    └── chroma_db/             # ChromaDB Persistence


```

## 🛠️ Installation & Getting Started

### Prerequisites
* **Docker Desktop** (running)
* **Python 3.10+** (for local model downloading)
* **Git**

### 1. Clone the Repository
```bash
git clone [https://github.com/Iyed0092/LegalRAG.git](https://github.com/Iyed0092/LegalRAG.git)
cd LegalRAG
```

2. Download AI Models (Important)
Since Large Language Models (LLMs) are too heavy for GitHub, you need to download them locally first. A script is provided to automate this:

```bash
# Install utils for the download script
pip install transformers torch sentence-transformers

# Run the downloader
python download_models.py
```
This will fetch FLAN-T5 and MiniLM and place them in the data/ai_models/ directory, which is mounted into the Docker containers.

3. Run with Docker
Once models are ready, launch the full stack:

```bash
docker-compose up --build
```
🖥️ Usage
User Interface (Streamlit): Open http://localhost:8501

Backend API (Django): Open http://localhost:8000/api/v1/

Neo4j Browser: Open http://localhost:7474 (User: neo4j, Password: password)

## 🔧 Tech Stack

| Category | Technologies |
| :--- | :--- |
| **Backend** | Python, Django REST Framework |
| **AI / ML** | PyTorch, HuggingFace Transformers, LangChain, FLAN-T5 |
| **Databases** | Neo4j (Graph), ChromaDB (Vector) |
| **Frontend** | Streamlit |
| **DevOps** | Docker, Docker Compose, GitHub Actions (CI/CD) |

## 📜 License

This project is intended for educational purposes as a personal project done by me.
Distributed under the **MIT License**.

## 👤 Author

**Iyed Mekki**
* **LinkedIn:** [linkedin.com/in/iyed-mekki](https://www.linkedin.com/in/iyed-mekki-265002384/)
* **GitHub:** [github.com/Iyed0092](https://github.com/Iyed0092)
















