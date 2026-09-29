# Knowledge Base

Place PDF documents in the appropriate category subfolder to enhance VenturePilot AI's RAG pipeline.

## Folder Structure

```
knowledge_base/
├── government/     ← Government schemes and policy documents
├── funding/        ← Funding guides, VC/angel references, grant brochures
├── business/       ← Business model, strategy, and pitch guides
├── legal/          ← Legal compliance, GST, company registration, IP
└── market/         ← Market research, sector reports, ecosystem overviews
```

## Recommended Documents

### government/
- Startup India Policy Document
- DPIIT Startup Recognition Guide
- Startup India Seed Fund Scheme (SISFS) Guidelines
- Atal Innovation Mission Overview

### funding/
- SIDBI SMILE Fund Brochure
- MSME Loan Scheme Guidelines
- Indian Angel Network Overview
- Sequoia Surge / Y Combinator Application Guide

### business/
- Business Model Canvas Guide (Osterwalder)
- Startup Pitch Deck Template Guide
- Lean Startup Methodology Overview

### legal/
- Company Registration in India (MCA)
- GST Registration Guide
- Intellectual Property Rights for Startups
- Startup India Legal Compliance Checklist

### market/
- Indian Startup Ecosystem Report (NASSCOM / Inc42)
- Sector-specific market research relevant to your domain

## Notes

- **Only PDF files** are processed. Other formats are ignored.
- The application automatically scans and indexes new files on startup.
- **No documents are required** — the app works without them, but adding
  relevant PDFs significantly improves the quality of funding and scheme recommendations.
- Do not commit large PDF files to version control. Add `knowledge_base/**/*.pdf`
  to `.gitignore` if needed.
