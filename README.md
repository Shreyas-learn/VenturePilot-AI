# 🚀 VenturePilot AI — Gemini Edition

> **Your AI Co-Founder** · Build • Validate • Fund • Launch

VenturePilot AI is an AI-powered startup consulting and business blueprint generation platform. Enter your startup idea and receive a comprehensive, investor-ready business blueprint — powered by **Google Gemini** and grounded in a curated knowledge base via **RAG (Retrieval-Augmented Generation)**.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 📄 **Business Blueprint** | Executive Summary, Problem, Solution, Vision, Customers, Value Prop, BMC, Revenue Model |
| 📊 **Market Intelligence** | Competitor Analysis, SWOT Analysis, Go-To-Market Strategy |
| 💰 **Funding Advisor** | Budget Breakdown, Funding Opportunities, Government Schemes, Incubators |
| 🗓️ **Business Planning** | 12-Month Roadmap, Risks & Mitigation |
| 🎤 **Investor Pitch** | Elevator Pitch, Final Recommendation, Immediate Next Steps |
| ⭐ **Readiness Score** | Six-dimensional startup readiness scoring (0–100) |
| 📥 **Export** | Download full blueprint as **Markdown** or **PDF** |

---

## 🏗️ Architecture

```
User Input (Streamlit Form)
         │
         ▼
  Startup Input Validation
         │
         ▼
   Core Orchestrator  ◄──── 5 prompt templates
         │
    ┌────┴────┐
    ▼         ▼
RAG Retrieval   Prompt Builder
(ChromaDB)     (template + context)
    │               │
    └───────┬────────┘
            ▼
      Google Gemini API
            │
            ▼
    Response Parser / Score Parser
            │
            ▼
      Report Builder
            │
       ┌────┴─────┐
       ▼          ▼
   Markdown     PDF (ReportLab)
```

### Technology Stack

| Component | Technology |
|-----------|-----------|
| **LLM (Generation)** | Google Gemini (`gemini-2.0-flash` or configurable) |
| **Embeddings** | sentence-transformers (`all-MiniLM-L6-v2`) — local, no API key needed |
| **Vector Store** | ChromaDB (persistent, file-backed) |
| **RAG Pipeline** | Custom retriever + ChromaDB similarity search |
| **Frontend** | Streamlit |
| **PDF Export** | ReportLab |
| **Knowledge Base** | ~53 curated PDFs across 5 categories |

---

## 📁 Project Structure

```
VenturePilot-AI/
│
├── app.py                        # Streamlit entry point
│
├── config/
│   ├── settings.py               # Centralised configuration (Gemini + RAG)
│   └── constants.py              # App constants, dropdowns, report sections
│
├── core/
│   ├── orchestrator.py           # Blueprint generation coordinator
│   ├── startup_input.py          # Startup input data model
│   ├── prompt_loader.py          # Prompt template loading & assembly
│   ├── report_builder.py         # Assembles Report from generated sections
│   └── score_parser.py           # Parses readiness score table
│
├── gemini/
│   ├── __init__.py
│   └── gemini_client.py          # Google Gemini API client (isolated)
│
├── rag/
│   ├── document_loader.py        # PDF loading and chunking
│   ├── embedding_manager.py      # sentence-transformers embedding (ChromaDB-compatible)
│   ├── vector_store.py           # ChromaDB client and indexing
│   ├── retriever.py              # Semantic context retrieval
│   └── rag_pipeline.py           # RAG pipeline public interface
│
├── frontend/
│   ├── layout.py                 # Page config, sidebar, header
│   ├── input_form.py             # Startup input form
│   ├── report_view.py            # Report display (tabs + expanders)
│   └── score_view.py             # Readiness score visualisation
│
├── prompts/
│   ├── business_blueprint.md     # Executive Summary → Revenue Model
│   ├── market_analysis.md        # Competitor Analysis, SWOT, GTM
│   ├── funding.md                # Budget, Funding, Government Schemes, Incubators
│   ├── startup_score.md          # Roadmap, Risks, Readiness Score
│   └── investor_pitch.md         # Final Recommendation, Pitch, Next Steps
│
├── knowledge_base/               # Curated PDF corpus (5 categories)
│   ├── business/
│   ├── funding/
│   ├── government/
│   ├── legal/
│   └── market/
│
├── chroma_db/                    # Persistent ChromaDB vector index (auto-generated)
├── exports/                      # Generated PDF / Markdown reports
├── logs/                         # Application logs
│
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## 🚀 Quick Start (Local)

### Prerequisites

- Python 3.11+
- A **Google Gemini API key** — get one free at [Google AI Studio](https://aistudio.google.com/app/apikey)

### 1. Clone the repository

```bash
git clone https://github.com/your-username/VenturePilot-AI.git
cd VenturePilot-AI
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your Gemini API key:

```env
GEMINI_API_KEY=your_gemini_api_key_here
# Optional — defaults shown below:
# GEMINI_MODEL=gemini-2.0-flash
# GEMINI_TEMPERATURE=0.2
# GEMINI_MAX_OUTPUT_TOKENS=8192
```

### 5. Run the application

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## ☁️ Streamlit Community Cloud Deployment

### 1. Push to GitHub

```bash
git add .
git commit -m "VenturePilot AI — Gemini Edition"
git push origin main
```

### 2. Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **New app** → select your repository
3. Set **Main file path** to `app.py`

### 3. Add secrets

In Streamlit Cloud, go to your app → **Settings** → **Secrets** and add:

```toml
GEMINI_API_KEY = "your_gemini_api_key_here"
GEMINI_MODEL = "gemini-2.0-flash"
```

> **Note:** The ChromaDB vector store is rebuilt automatically on Streamlit Cloud from the `knowledge_base/` PDFs committed to your repository. No manual indexing step is required.

---

## ⚙️ Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | ✅ Yes | — | Google Gemini API key |
| `GEMINI_MODEL` | No | `gemini-2.0-flash` | Gemini model ID |
| `GEMINI_TEMPERATURE` | No | `0.2` | Sampling temperature (0.0–1.0) |
| `GEMINI_TOP_P` | No | `0.9` | Top-p nucleus sampling |
| `GEMINI_MAX_OUTPUT_TOKENS` | No | `8192` | Max tokens per response |
| `PREFERRED_EMBEDDING_PROVIDER` | No | `sentence-transformers` | Embedding provider |
| `RAG_CHUNK_SIZE` | No | `800` | PDF chunk size (chars) |
| `RAG_CHUNK_OVERLAP` | No | `150` | Chunk overlap (chars) |
| `RAG_TOP_K` | No | `5` | Passages retrieved per query |
| `RAG_SIMILARITY_THRESHOLD` | No | `0.8` | Max cosine distance for relevance |
| `RAG_MAX_CONTEXT_CHARS` | No | `3000` | Max context chars per prompt |
| `APP_ENV` | No | `development` | `development` or `production` |
| `LOG_LEVEL` | No | `INFO` | Log level |
| `KNOWLEDGE_BASE_PATH` | No | `knowledge_base` | PDF knowledge base directory |
| `CHROMA_DB_PATH` | No | `chroma_db` | ChromaDB persistence path |
| `EXPORTS_DIR` | No | `exports` | Export output directory |

---

## 📚 Knowledge Base

The knowledge base contains ~53 curated PDFs across 5 categories:

| Category | Contents |
|----------|----------|
| `business/` | Business Model Canvas, Lean Startup, GTM strategy, value proposition |
| `funding/` | VC guides, angel investing, SIDBI schemes, state startup policies |
| `government/` | Startup India, DPIIT, SISFS, MSME, Udyam registration |
| `legal/` | Company registration, GST, IP basics, trademark |
| `market/` | Market research, competitor analysis, SWOT, pitch guidelines |

The RAG pipeline:
1. Scans `knowledge_base/` for PDFs at startup
2. Chunks new/changed PDFs (800 chars, 150 overlap)
3. Embeds with `all-MiniLM-L6-v2` (sentence-transformers)
4. Indexes into ChromaDB (`chroma_db/`)
5. Retrieves domain-specific passages for each of the 5 prompt calls

---

## 🧪 Testing

### Embedding & RAG smoke test (no API key required)

```bash
python _embed_test.py
```

### Run the full application

```bash
streamlit run app.py
```

Enter a startup idea and verify:
- [ ] Form submission works
- [ ] Generation completes (requires `GEMINI_API_KEY`)
- [ ] All report sections appear
- [ ] Readiness score is displayed
- [ ] Markdown download works
- [ ] PDF download works

---

## 📋 Report Sections Generated

1. Executive Summary
2. Problem Statement
3. Proposed Solution
4. Vision & Mission
5. Target Customers
6. Value Proposition
7. Business Model Canvas
8. Revenue Model
9. Competitor Analysis
10. SWOT Analysis
11. Go-To-Market Strategy
12. Estimated Budget
13. Funding Opportunities
14. Government Schemes
15. Incubator Recommendations
16. 12-Month Roadmap
17. Risks & Mitigation
18. Final Recommendation
19. Investor Elevator Pitch
20. Startup Readiness Score
21. Immediate Next Steps

---

## 🔒 Security

- API keys are **never hardcoded** — always loaded from environment variables or Streamlit secrets
- `.env` is in `.gitignore` and is never committed
- The `GEMINI_API_KEY` is only used in `gemini/gemini_client.py`

---

## 📄 License

MIT License. See `LICENSE` for details.

---

*VenturePilot AI — Gemini Edition · Powered by Google Gemini + RAG + ChromaDB + Streamlit*
