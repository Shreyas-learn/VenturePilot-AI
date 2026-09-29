# VenturePilot AI — Architecture

## Overview

VenturePilot AI follows **Clean Architecture** principles. Each layer has a
single responsibility and depends only on layers below it. The UI never
touches the database or AI directly; all cross-cutting concerns (config,
logging, error handling) are isolated in dedicated modules.

---

## Layer Diagram

```
┌──────────────────────────────────────────────┐
│                  app.py                      │  Entry point only
├──────────────────────────────────────────────┤
│              frontend/                       │  UI rendering
│   layout.py  │  input_form.py  │ report_view │
├──────────────────────────────────────────────┤
│               core/                          │  Business logic
│  orchestrator.py  │  report_builder.py       │
│  startup_input.py                            │
├──────────────────────────────────────────────┤
│      ibm/                  rag/              │
│  authentication.py     document_loader.py    │
│  granite_client.py     vector_store.py       │
│                         retriever.py         │
├──────────────────────────────────────────────┤
│  config/          utils/          prompts/   │
│  settings.py      logger.py      *.md        │
│  constants.py     file_utils.py             │
│                   export.py                  │
├──────────────────────────────────────────────┤
│  knowledge_base/           chroma_db/        │  Storage
│  government/ funding/      (auto-generated)  │
│  business/ legal/ market/                    │
└──────────────────────────────────────────────┘
```

---

## Module Responsibilities

| Module | File(s) | Responsibility |
|--------|---------|----------------|
| Entry point | `app.py` | Page config, session state, coordinate flow |
| UI layout | `frontend/layout.py` | Page config, sidebar, header |
| Input form | `frontend/input_form.py` | Form rendering, input validation |
| Report view | `frontend/report_view.py` | Tabs, expanders, download buttons |
| Orchestrator | `core/orchestrator.py` | Coordinates RAG + IBM Granite + builder |
| Report builder | `core/report_builder.py` | Assembles `Report` from section content |
| Input model | `core/startup_input.py` | Typed, immutable user input container |
| Authentication | `ibm/authentication.py` | IBM IAM auth, cached API client |
| Granite client | `ibm/granite_client.py` | Prompt execution, retry, error handling |
| Doc loader | `rag/document_loader.py` | PDF scanning, text extraction, chunking |
| Vector store | `rag/vector_store.py` | ChromaDB indexing, embedding selection |
| Retriever | `rag/retriever.py` | Semantic search, context formatting |
| Settings | `config/settings.py` | Environment variable resolution |
| Constants | `config/constants.py` | Static lists, score weights, section names |
| Logger | `utils/logger.py` | Root logger setup, rotating file handler |
| File utils | `utils/file_utils.py` | Text/prompt file I/O |
| Export | `utils/export.py` | PDF (ReportLab) and Markdown generation |
| Prompts | `prompts/*.md` | Editable prompt templates |

---

## Data Flow

```
User submits form
      │
      ▼
StartupInput (dataclass)
      │
      ▼
orchestrator.generate_blueprint(startup_input)
      │
      ├──► retriever.retrieve_context(query)
      │         └──► ChromaDB vector store
      │                   └──► PDF knowledge base
      │
      ├──► prompts/*.md  (template loading)
      │
      ├──► granite_client.generate(prompt)
      │         └──► IBM watsonx API
      │                   └──► IBM Granite model
      │
      └──► ReportBuilder.build()
                └──► Report (dataclass)
                          │
                          ▼
                    render_report(report)
                          │
                          ├──► Streamlit tabs + expanders
                          └──► Download (PDF / Markdown)
```

---

## Embedding Strategy

| Condition | Embedding Provider |
|-----------|-------------------|
| `IBM_WATSONX_API_KEY`, `IBM_WATSONX_PROJECT_ID`, `IBM_WATSONX_URL` all set | IBM watsonx `slate-125m-english-rtrvr` |
| Any credential missing | `sentence-transformers/all-MiniLM-L6-v2` (local) |

The fallback ensures the RAG pipeline works during development without IBM credentials.

---

## Knowledge Base Structure

```
knowledge_base/
├── government/     ← DPIIT, Startup India, policy PDFs
├── funding/        ← VC guides, SISFS, SIDBI brochures
├── business/       ← BMC, pitch deck templates, strategy guides
├── legal/          ← GST, company registration, IP guides
└── market/         ← Sector reports, ecosystem overviews
```

The application scans all subfolders recursively at startup. New PDFs are
indexed automatically without any code changes.

---

## Startup Readiness Score

The score is calculated across 6 dimensions by IBM Granite based on the startup details.

| Dimension | Max Score | What Is Evaluated |
|-----------|-----------|-------------------|
| Innovation | 20 | Novelty of the idea, IP potential, technical differentiation |
| Market Need | 20 | Problem severity, market size, demand evidence |
| Revenue Model | 15 | Clarity of monetization, unit economics, path to profitability |
| Competition | 15 | Competitive moat, differentiation vs existing players |
| Scalability | 15 | Ability to grow without proportional cost increase |
| Funding Potential | 15 | Investor appeal, alignment with funding trends |
| **Total** | **100** | |

Score bands:
- 85–100: 🟢 Investor-ready
- 70–84:  🟡 Strong foundation — address key gaps
- 55–69:  🟠 Promising — significant work required
- Below 55: 🔴 Needs major rethinking

---

## Error Handling Strategy

| Scenario | Handling |
|----------|----------|
| Missing IBM credentials | User-friendly warning; app remains usable |
| Granite API timeout | Retry 3× with exponential back-off via `tenacity` |
| Empty knowledge base | RAG silently skipped; generation proceeds without context |
| Invalid user input | Form-level validation with clear error messages |
| PDF parse failure | Warning logged; file skipped; remaining docs indexed |
| Export failure | Error displayed inline; app does not crash |

---

## Session State Management

`st.session_state` keys used in `app.py`:

| Key | Type | Purpose |
|-----|------|---------|
| `report` | `Report \| None` | Stores last generated report |
| `startup_input` | `StartupInput \| None` | Tracks last submitted input to detect re-runs |

Reports are not regenerated unless the user submits a new form, avoiding
unnecessary API calls.
