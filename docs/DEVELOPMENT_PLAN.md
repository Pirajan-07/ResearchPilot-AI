# ResearchPilot AI — Development Plan

**Version:** 1.1 (Revised — Free-Tier Gemini + Local Embeddings)
**Status:** Architecture Phase — Approved for Phase 1
**Last Revised:** 2026-09-11
**MVP Deadline:** September 15, 2026

---

## Overview

This plan covers Phase 0 (complete) through Phase 10 (submission readiness). Each phase has a clear objective, task list, dependencies, and acceptance criteria. Phases are designed to be completed sequentially.

**Critical path for deadline:** Phases 1 → 2 → 3 → 4 → 5 → 6 → 7 in sequence. Phases 8, 9, 10 may overlap.

---

## Phase 0 — Architecture & Product Specification ✅

**Objective:** Produce a coherent, implementation-ready blueprint before writing any code.

**Status:** COMPLETE (revised in v1.1 to adopt Gemini Free Tier + local embeddings)

**Deliverables:**
- `docs/PRODUCT_SPEC.md` ✅
- `docs/ARCHITECTURE.md` ✅ (revised v1.1)
- `docs/TECH_STACK.md` ✅ (revised v1.1)
- `docs/UI_UX_SPEC.md` ✅
- `docs/API_SPEC.md` ✅ (revised v1.1)
- `docs/RAG_DESIGN.md` ✅ (revised v1.1)
- `docs/DEVELOPMENT_PLAN.md` ✅ (this file, revised v1.1)
- `docs/DECISIONS.md` ✅ (new in v1.1)

---

## Phase 1 — Project Foundation & Configuration

**Objective:** Create the project scaffold, install and verify all dependencies, establish the working development environment.

**Dependencies:** Phase 0 approval ✅

**Critical:** Verify ALL packages install cleanly on Python 3.11.9 / Windows before proceeding.

### 1.1 Environment Setup

- [ ] Create `.gitignore` covering: `.env`, `.env.local`, `.venv`, `node_modules/`, `storage/`, `__pycache__/`, `*.pyc`, `.next/`, `dist/`
- [ ] Create `backend/` directory structure as per ARCHITECTURE.md
- [ ] Create virtual environment: `py -3.11 -m venv .venv`
- [ ] Activate: `.venv\Scripts\Activate.ps1`
- [ ] Install CPU-only PyTorch first: `pip install torch --index-url https://download.pytorch.org/whl/cpu`
- [ ] Install remaining backend dependencies: `pip install -r requirements.txt`
- [ ] Verify all imports work: `python -c "import fastapi, fitz, langchain, langchain_google_genai, langchain_huggingface, chromadb, sentence_transformers; print('OK')"`

### 1.2 Backend Foundation

- [ ] Create `backend/requirements.txt` (pinned versions per TECH_STACK.md)
- [ ] Create `backend/.env.example` (all keys documented, no real values)
- [ ] Create `backend/.env` (with real `GEMINI_API_KEY`, gitignored)
- [ ] Create `backend/app/config.py` (Pydantic BaseSettings reading from .env)
- [ ] Create `backend/app/utils/logging_config.py` (Loguru setup)
- [ ] Create `backend/main.py` (FastAPI app, CORS, health endpoint, startup validation)
- [ ] Create `backend/storage/uploads/` and `backend/storage/chroma_db/` directories
- [ ] Run: `uvicorn app.main:app --reload` → no errors
- [ ] Verify: `GET http://localhost:8000/health` returns 200 with providers info

### 1.3 Configuration Validation Tests

- [ ] Test: Start server without `GEMINI_API_KEY` → clear error message (not silent crash)
- [ ] Test: `MAX_UPLOAD_SIZE_MB` reads from env correctly
- [ ] Test: `GEMINI_MODEL` env var is used (log model name on startup)

### 1.4 Frontend Foundation

- [ ] Scaffold: `npx create-next-app@"^15" frontend --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"` (specify 15.x explicitly)
- [ ] Install shadcn/ui: `cd frontend && npx shadcn@latest init` (dark theme, neutral base)
- [ ] Install dependencies: `npm install @tanstack/react-query axios lucide-react react-hot-toast class-variance-authority clsx tailwind-merge`
- [ ] Create `frontend/.env.local.example` and `frontend/.env.local`
- [ ] Configure Tailwind with design tokens from UI_UX_SPEC.md
- [ ] Configure Inter font (via `next/font/google`)
- [ ] Set up TanStack Query provider in `src/app/layout.tsx`
- [ ] Set up toast provider in `src/app/layout.tsx`
- [ ] Run: `npm run dev` → no errors, loads at localhost:3000

**Acceptance Criteria — Phase 1:**
- `GET /health` returns 200 ✅
- All Python imports succeed ✅
- Frontend dev server starts without errors ✅
- Config validation catches missing `GEMINI_API_KEY` ✅
- `.gitignore` prevents committing secrets ✅

---

## Phase 2 — Premium Frontend Shell & UI System

**Objective:** Build the complete application shell and all reusable UI components with correct design token usage. No real data — static props only.

**Dependencies:** Phase 1 complete

- [ ] Implement `AppShell.tsx` — sidebar + main content layout
- [ ] Implement `Sidebar.tsx` — brand, navigation items with active/disabled states
- [ ] Implement `WorkspaceEmpty.tsx` — upload CTA, 3-step workflow, product description
- [ ] Implement `UploadZone.tsx` — drag-and-drop: idle / dragging / uploading states
- [ ] Implement `ProcessingStatus.tsx` — 5-stage pipeline visualizer (all stage states)
- [ ] Implement `PaperMetaCard.tsx` — filename, page count, chunk count, ready badge
- [ ] Implement tab navigation (Summary | Paper Insights | Assistant)
- [ ] Implement `SummaryPanel.tsx` + `SummaryDimensionCard.tsx` (skeleton + populated states)
- [ ] Implement `InsightsPanel.tsx` + `InsightCard.tsx` (skeleton + populated states)
- [ ] Implement `ResearchAssistant.tsx` — chat UI with suggested queries shown when empty
- [ ] Implement `MessageBubble.tsx` — user and assistant styles
- [ ] Implement `SourceReferences.tsx` — source chips with page label + excerpt
- [ ] Implement `QueryInput.tsx` — textarea + send button + char limit indicator
- [ ] Implement error state components (generic + specific: scanned PDF, processing failed)
- [ ] Verify all states render with static mock data
- [ ] Verify responsive behavior at 768px (tablet)
- [ ] Verify keyboard navigation (Tab key through all interactive elements)
- [ ] Design review against UI_UX_SPEC.md — no token violations

**Acceptance Criteria — Phase 2:**
- All workspace states render correctly with static data ✅
- Design tokens consistent across all components ✅
- No TypeScript compilation errors ✅
- Keyboard navigation functional ✅

---

## Phase 3 — PDF Ingestion & Document Processing

**Objective:** Build the backend document processing pipeline: validate → extract → chunk → metadata. No embeddings yet.

**Dependencies:** Phase 1 complete

- [ ] Implement `file_utils.py` — validation, safe save, path management
- [ ] Implement `parser_service.py` — PyMuPDF extraction returning `List[Document]`
- [ ] Implement `chunking_service.py` — LangChain RecursiveCharacterTextSplitter
- [ ] Implement `document_service.py` — state registry + pipeline orchestration skeleton
- [ ] Implement `documents.py` router — upload endpoint (background task)
- [ ] Implement status endpoint in `documents.py`
- [ ] Write Pydantic schemas: `DocumentUploadResponse`, `DocumentStatusResponse`, `StageStatus`
- [ ] Add stage progression updates to document state during processing
- [ ] Test: Upload "Attention Is All You Need" PDF → inspect extracted pages
- [ ] Test: Upload a 2-page PDF → verify chunks are correct size
- [ ] Test: Upload non-PDF → 415 error
- [ ] Test: Upload >50MB file → 413 error
- [ ] Test: Corrupt PDF → PROCESSING_FAILED with useful message
- [ ] Test: Scanned (image-only) PDF → SCANNED_PDF error with explanation

**Acceptance Criteria — Phase 3:**
- Upload → extraction → chunking completes for a real research paper ✅
- Status polling shows correct stage progression ✅
- Chunk sizes within configured bounds ✅
- All metadata fields (document_id, page_number, chunk_id) present on chunks ✅
- All error cases return correct HTTP status + error code ✅

---

## Phase 4 — Embeddings, Vector Store & Retrieval

**Objective:** Add the embedding generation and vector indexing layer. Verify retrieval quality.

**Dependencies:** Phase 3 complete

- [ ] Implement `providers/base.py` — `BaseEmbeddingProvider` ABC
- [ ] Implement `providers/huggingface_provider.py` — `LocalHuggingFaceEmbeddingProvider`
- [ ] Implement `embedding_service.py` — wraps provider; handles model loading + caching
- [ ] Implement `vector_store_service.py` — ChromaDB operations via `langchain-chroma`
- [ ] Implement `retrieval_service.py` — similarity search interface
- [ ] Integrate embedding + indexing stages into `document_service.py`
- [ ] Test: First run → model downloads (~90 MB) → embedding succeeds
- [ ] Test: Second run → uses cached model → faster startup
- [ ] Test: ChromaDB collection `doc_{id}` exists after processing
- [ ] Test: `retrieval_service.retrieve(doc_id, "self-attention mechanism")` returns relevant chunks
- [ ] Test: Metadata (page_number, chunk_id) present in retrieval results
- [ ] Test: ChromaDB data persists after server restart
- [ ] Test: Document DELETE removes ChromaDB collection

**Acceptance Criteria — Phase 4:**
- Embedding generation completes for a 20-page paper in <90 seconds ✅
- ChromaDB collection persists across server restarts ✅
- Retrieval returns semantically relevant chunks for research-domain queries ✅
- Retrieval metadata is complete and accurate ✅

---

## Phase 5 — Research Assistant & Grounded Q&A

**Objective:** Implement the core RAG Q&A capability end-to-end.

**Dependencies:** Phase 4 complete + `GEMINI_API_KEY` confirmed working

- [ ] Implement `providers/base.py` — `BaseLLMProvider` ABC
- [ ] Implement `providers/gemini_provider.py` — `GeminiLLMProvider`
- [ ] Implement `llm_service.py` — wraps Gemini via `langchain-google-genai`
- [ ] Implement `research_agent.py` — full RAG chain (retrieval → prompt → generate → sources)
- [ ] Implement `research.py` router — query endpoint
- [ ] Write Pydantic schemas: `QueryRequest`, `QueryResponse`, `SourceReference`
- [ ] Implement anti-injection system prompt (see RAG_DESIGN.md §3.4)
- [ ] Implement `has_context: false` response path for insufficient evidence
- [ ] Test standard research questions against "Attention Is All You Need":
  - [ ] "What architecture is proposed?" → grounded answer ✅
  - [ ] "What datasets were used?" → WMT 2014 mentioned ✅
  - [ ] "What BLEU score was achieved?" → specific number ✅
  - [ ] "What future work is suggested?" → grounded answer ✅
  - [ ] "What is the stock price?" → `has_context: false` ✅
- [ ] Test: Source references populated with page numbers and text excerpts
- [ ] Test: 502 returned when Gemini API is unreachable (mock test)

**Acceptance Criteria — Phase 5:**
- Q&A answers match paper content (manually verified) ✅
- Source references populated, page numbers shown ✅
- Out-of-scope query produces `has_context: false` with honest message ✅
- No hallucinated content in verified answers ✅

---

## Phase 6 — Summary & Research Insights

**Objective:** Implement single-call structured summary and insights generation.

**Dependencies:** Phase 5 complete (LLM service available)

- [ ] Implement `summary_service.py` — broad retrieval + single structured Gemini call
- [ ] Implement `insights_service.py` — broad retrieval + single structured Gemini call
- [ ] Add summary endpoint to `research.py` router
- [ ] Add insights endpoint to `research.py` router
- [ ] Implement in-memory caching (summary + insights per document_id)
- [ ] Write Pydantic schemas: `SummaryResponse`, `InsightsResponse`
- [ ] Implement JSON output parsing with Pydantic validation
- [ ] Implement graceful fallback if JSON parsing fails (return error, don't crash)
- [ ] Test: Generate summary for "Attention Is All You Need" → verify 9 dimensions populated
- [ ] Test: Generate insights → valid JSON, 7 fields, methodology_tags array populated
- [ ] Test: Missing dimension → "Not identified in this paper." not null/empty
- [ ] Test: Second request returns cached result (verify by checking response time)
- [ ] Test: `cached: true` field present on cached responses

**Acceptance Criteria — Phase 6:**
- Summary: all 9 dimensions have content or honest "Not identified" ✅
- Insights: all 7 dimensions populated, methodology_tags is an array ✅
- No fabricated information (manually verified) ✅
- Cache returns results instantly on second call ✅
- Total Gemini calls for a full demo session ≤ 10 ✅

---

## Phase 7 — Frontend/Backend Integration

**Objective:** Connect the static frontend shell to the live backend APIs. Full end-to-end data flow in the browser.

**Dependencies:** Phases 2, 5, 6 complete

- [ ] Implement `lib/api.ts` — Axios instance + typed API functions matching API_SPEC.md
- [ ] Implement `types/document.ts` and `types/research.ts` — TypeScript interfaces
- [ ] Implement `useDocumentUpload.ts` — mutation + progress tracking
- [ ] Implement `useProcessingStatus.ts` — polling hook (2s interval while processing)
- [ ] Implement `useResearchQuery.ts` — mutation hook for Q&A
- [ ] Implement `useSummary.ts` — query hook (auto-fetch when document ready)
- [ ] Implement `useInsights.ts` — query hook (auto-fetch when document ready)
- [ ] Wire workspace state machine: EMPTY → PROCESSING → READY → ERROR
- [ ] Connect `UploadZone` → upload API + state transition
- [ ] Connect `ProcessingStatus` → real stage data from status polling
- [ ] Connect `SummaryPanel` → real 9-dimension summary data
- [ ] Connect `InsightsPanel` → real 7-dimension insights data
- [ ] Connect `ResearchAssistant` → real query API + message history
- [ ] Connect `SourceReferences` → real source data from query responses
- [ ] Test complete end-to-end flow with a real PDF in the browser
- [ ] Verify: Embedding stage shows "first run may take longer" note
- [ ] Verify: Summary/insights show skeletons while loading
- [ ] Verify: Error states display correctly for all error scenarios

**Acceptance Criteria — Phase 7:**
- Full user journey works end-to-end in the browser ✅
- Processing stages update in real-time ✅
- Real grounded answers displayed with real source references ✅
- Real 9-dimension summary displayed ✅
- Real 7-dimension insights displayed as "Paper Insights" ✅
- All error scenarios display appropriate UI states ✅

---

## Phase 8 — Testing & Reliability Hardening

**Objective:** Build the test suite and harden all error paths.

**Dependencies:** Phase 7 complete

- [ ] Create `backend/tests/conftest.py` — fixtures, mock `GeminiLLMProvider`
- [ ] Write `test_parser.py` — extraction correctness, scanned PDF, empty PDF
- [ ] Write `test_chunking.py` — sizes, overlap, metadata integrity
- [ ] Write `test_retrieval.py` — relevant chunks for known queries (mock embeddings)
- [ ] Write `test_summary.py` — 9 dimensions, "Not identified" fallback (mock LLM)
- [ ] Write `test_insights.py` — 7 fields, JSON validity (mock LLM)
- [ ] Write `test_api.py` — all endpoints: happy path + all error codes
- [ ] All error HTTP status codes verified
- [ ] All error code strings verified (DOCUMENT_NOT_FOUND, etc.)
- [ ] Test: Very short paper (1-2 pages) handles gracefully
- [ ] Test: Paper with tables/equations handles gracefully
- [ ] Fix any bugs found during testing

**Acceptance Criteria — Phase 8:**
- All test files pass `pytest` ✅
- Test coverage: >70% of service layer ✅
- All error scenarios produce correct HTTP codes ✅
- No unhandled exceptions under normal error conditions ✅
- Mock providers allow testing without consuming Gemini quota ✅

---

## Phase 9 — Langflow Academic Demonstration

**Objective:** Build a visual representation of the RAG pipeline in Langflow for academic/PPT purposes.

**Dependencies:** Phase 8 complete

- [x] Install Langflow in isolated virtual environment (`backend/.langflow_venv`)
- [x] Start Langflow server at `http://127.0.0.1:7860`
- [x] Build RAG pipeline manually in the Langflow UI
- [x] Export Langflow flow to `docs/langflow_academic_demo.json`
- [x] Document production vs. demonstration differences in `docs/LANGFLOW_VS_PRODUCTION.md`

**Acceptance Criteria — Phase 9:**
- Langflow installed and verified ✅
- Langflow UI used to manually build the workflow ✅
- Exported JSON saved to `docs/langflow_academic_demo.json` ✅
- Honest documentation of production vs. Langflow demo ✅
- Langflow flow was NOT executed (no Gemini API calls made) — intentional ✅

---

## Phase 10 — Documentation & Submission Readiness

**Objective:** Prepare for academic submission and demonstration.

**Dependencies:** Phase 9 complete

- [x] Complete `README.md` with: project description, setup instructions, API overview, testing
- [x] Verify `.gitignore` — no API keys committed; all runtime data excluded
- [x] Verify `backend/.env.example` — all keys documented, no real values
- [x] Security audit — `backend/.env` confirmed ignored, no secrets in tracked files
- [x] Langflow task: flow exported to `docs/langflow_academic_demo.json`
- [ ] Final end-to-end demo run with "Attention Is All You Need" (reserved for demo session)
- [ ] Screenshots added (Phase 11)
- [ ] Prepare viva talking points

**Acceptance Criteria — Phase 10:**
- No secrets committed to git ✅
- README explains system clearly for a professor audience ✅
- Langflow workflow created and exported ✅
- `.gitignore` covers all runtime/secret/large files ✅
- Backend tests: 148 passing ✅

---

## Risk Register (Updated v1.1)

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Python 3.11 package conflicts | Low | High | Explicitly use `py -3.11 -m venv`; test all imports in Phase 1 before proceeding |
| PyTorch CPU wheel install issues on Windows | Medium | High | Use `--index-url https://download.pytorch.org/whl/cpu` explicitly; test in Phase 1 |
| HuggingFace model download blocked (network) | Low | High | Download and cache model in Phase 1; cache persists in `~/.cache/huggingface/` |
| Gemini API rate limit during demo | Low | Medium | Summary/insights cached; typical demo is 7 calls total, well within Free Tier |
| Gemini model discontinued/renamed | Low | Medium | Model is env-var configurable; change `GEMINI_MODEL=` without code changes |
| ChromaDB 1.5.x API breaking change vs. langchain-chroma | Low | Medium | Use `langchain-chroma 0.2.x` adapter; test in Phase 4 |
| Scanned PDF uploaded during demo | Medium | Medium | Clear error message; prepare text-layer PDFs for demo |
| Next.js 15 compatibility issue | Low | Low | Well-established version; Node 24 is compatible |
| In-memory state lost on server restart | Medium | Low | Frontend handles gracefully; re-upload is simple |

---

## Demonstration Plan

**Recommended demo paper:** "Attention Is All You Need" (Vaswani et al., 2017)
- Freely available as PDF
- Well-known to CS professors
- Clear answers to all standard research questions
- 15 pages — processes in ~60-90 seconds

**Demo sequence:**
1. Open ResearchPilot AI → show empty workspace
2. Upload "Attention Is All You Need.pdf"
3. Walk through processing stages (explain each stage)
4. Switch to **Summary** tab → walk through 9 dimensions
5. Switch to **Paper Insights** tab → show structured insights
6. Switch to **Research Assistant** tab → ask 3 questions:
   - "What is the Transformer architecture?"
   - "What results did the model achieve on translation tasks?"
   - "What are the limitations of this approach?"
7. Show source references for one answer
8. Ask out-of-scope question: "What is the stock market performance of this research group?" → show honest "not found" response
9. Explain the trust contract: paper-grounded, never fabricated

**Expected Gemini calls during demo:** 1 (summary) + 1 (insights) + 3 (Q&A) + 1 (out-of-scope) = **6 calls**

---

## LangChain Usage Documentation (for Academic Report)

LangChain is used at these specific points in the pipeline:

1. `Document` abstraction — standard document format throughout pipeline
2. `RecursiveCharacterTextSplitter` — intelligent paragraph-aware chunking
3. `HuggingFaceEmbeddings` — local CPU embedding model integration
4. `Chroma` (langchain-chroma) — ChromaDB vector store interface
5. `ChatGoogleGenerativeAI` — Gemini LLM integration
6. `ChatPromptTemplate` — structured research Q&A prompt construction
7. LCEL `|` composition — connecting prompt → llm → output_parser
8. `StrOutputParser` — standardized output handling

This demonstrates genuine LangChain usage for RAG orchestration, not a superficial dependency.

---

*This plan supersedes DEVELOPMENT_PLAN.md v1.0. Python 3.11 specified. Gemini Free Tier noted. Local embeddings first-run note added. Langflow task added to Phase 10.*
