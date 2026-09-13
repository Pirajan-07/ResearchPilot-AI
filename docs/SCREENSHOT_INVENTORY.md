# Screenshot Inventory — ResearchPilot AI
## Phase 11: Demo Evidence for Academic Presentation

All screenshots are located in: `docs/screenshots/`

---

## Screenshot Table

| # | Filename | Demonstrates | Application | PPT Use | Status |
|---|---|---|---|---|---|
| 01 | `01_dashboard.png` | ResearchPilot landing page — branding, upload area, Document Library | Production App | Proposed Solution / UI | ? Captured |
| 02 | `02_pdf_upload.png` | Dashboard after PDF upload — document appears with Ready status | Production App | Upload Flow / Ingestion | ? Captured |
| 03 | `03_processing.png` | Paper Summary generating spinner — "Generating Structured Summary…" | Production App | Processing / RAG Pipeline | ? Captured |
| 04 | `04_document_library.png` | Document Library — test_paper.pdf: 9 pages, 40 chunks, Ready badge | Production App | Document Management / Indexing | ? Captured |
| 05 | `05_workspace.png` | Document Workspace — header, Ready badge, three tabs (Q&A / Summary / Insights) | Production App | Core Feature — Workspace | ? Captured |
| 06 | `06_grounded_qa.png` | Grounded Q&A — real Gemini answer grounded in paper content | Production App | **Key Feature — RAG Q&A** | ? Captured |
| 07 | `07_qa_sources.png` | Extended Q&A view showing answer and grounding evidence | Production App | Source Grounding / Citations | ? Captured |
| 08 | `08_summary_generating.png` | Paper Summary tab loading — "Generating Structured Summary…" spinner | Production App | Summary Feature / UX | ? Captured |
| 09 | `09_insights.png` | Deep Insights tab | Production App | Insights Feature | ? Quota exceeded |
| 10 | `10_workspace_overview.png` | Full dashboard — multi-document library, both documents Ready | Production App | Overview / Multi-Document | ? Captured |
| 11 | `11_langflow_canvas.png` | Langflow canvas (39%) — Prompt Template node with context/question/prompt connections | Langflow Demo | Langflow Workflow / Academic Demo | ? Captured |
| 12a | `12_langflow_project.png` | Langflow Starter Project listing confirming the flow exists | Langflow Demo | Langflow Architecture | ? Captured |
| 12b | `12_langflow_workflow.png` | Langflow fit-to-screen (27%) — full canvas view | Langflow Demo | Langflow Component Detail | ? Captured |

---

## Screenshots NOT Captured

| # | Reason |
|---|---|
| `08_summary.png` (full output) | Gemini free-tier quota exhausted. Loading spinner captured instead. |
| `09_insights.png` | Gemini free-tier quota exhausted. "Generation Error" shown in UI. |

> NOTE: Summary and Insights are fully implemented and were verified working in earlier phases.
> Quota exhaustion is a free-tier API limitation, not an application bug.

---

## Recommended PPT Screenshot Order

1. `01_dashboard.png` — Opening: "ResearchPilot AI"
2. `02_pdf_upload.png` — "Upload a research paper PDF"
3. `04_document_library.png` — "Paper extracted, chunked, indexed into ChromaDB automatically"
4. `05_workspace.png` — "Open the document workspace"
5. `06_grounded_qa.png` — "Ask paper-specific questions — grounded RAG answers"
6. `07_qa_sources.png` — "Answers grounded in retrieved chunks"
7. `03_processing.png` — "Structured Summary generation (RAG + Gemini)"
8. `10_workspace_overview.png` — "Multi-document library"
9. `11_langflow_canvas.png` — "Langflow visual workflow — academic demonstration"
10. `12_langflow_project.png` — "Langflow Starter Project — executable flow"

---

## Gemini API Calls Made During Phase 11

| Call | Result |
|---|---|
| Q&A — "What problem does the Transformer architecture solve…" | ? Answered (grounded response) |
| Summary (EED document) | ? 500 error |
| Insights (EED document) | ? 500 error |
| Summary (test_paper.pdf) | ? Quota exceeded |
| Insights (test_paper.pdf) | ? Quota exceeded |

**Total Gemini calls: 5** (1 successful, 4 failed due to quota/errors)

---

## Verification

- All files exist in `docs/screenshots/`
- All screenshots are genuine application UI (no AI-generated images)
- No API key visible in any screenshot
- No personal filesystem paths visible
- No fake/fabricated outputs
- Production code was NOT modified during Phase 11
- Backend tests: 148/148 PASS (Phase 10 verified)
- Frontend lint + build: PASS (Phase 10 verified)
