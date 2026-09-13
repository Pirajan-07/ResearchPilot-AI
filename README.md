# ResearchPilot AI

**Advanced Document Intelligence & Grounded Research Q&A Platform**

---

## 1. Overview
ResearchPilot AI is an AI-powered document intelligence platform designed to assist researchers in analyzing complex academic literature. By leveraging a local Retrieval-Augmented Generation (RAG) architecture, it allows users to upload a research PDF, extract and chunk document content, and perform grounded Q&A with explicit source and page citations. The platform strictly enforces grounded generation, ensuring that all answers, summaries, and insights are derived exclusively from the provided document.

## 2. Problem Statement
Researchers frequently spend hours reading dense academic papers to extract core methodologies, findings, and limitations. General-purpose LLMs can process text but often hallucinate or struggle with long-context source attribution. ResearchPilot AI solves this by explicitly linking answers to the underlying source chunks, drastically reducing hallucination risk while accelerating literature review.

## 3. Proposed Solution
The platform provides a streamlined pipeline for single-document PDF analysis. It extracts text, embeds it locally using lightweight Sentence Transformers, stores it in ChromaDB, and retrieves semantic matches to construct grounded prompts for Google Gemini (gemini-3.5-flash). This ensures high-accuracy answers paired with exact citations.

## 4. Core Features
- **PDF Upload & Text Extraction:** Reliable parsing of research papers using PyMuPDF.
- **Document Chunking:** Semantic-aware chunking optimized for RAG.
- **Local Embeddings:** Offline, fast embedding generation using `all-MiniLM-L6-v2`.
- **Vector Indexing:** Persistent local storage using ChromaDB.
- **Semantic Retrieval:** High-precision similarity search for user queries.
- **Grounded Q&A:** Accurate answers citing exact document chunks and page numbers.
- **Structured Summary:** 9-dimension automated paper summary (Overview, Problem, Objectives, Methodology, Dataset, Findings, Limitations, Conclusion, Future Research).
- **Structured Insights:** 7-dimension deep analysis (Problem, Methodology, Dataset, Contribution, Findings, Limitations, Future Direction).
- **Document Library & Processing Status:** Real-time feedback on document state.
- **Analysis Caching:** Prevents redundant API calls to preserve quotas.
- **Graceful Error Handling:** Validation for empty queries and missing/invalid documents.

## 5. How It Works
1. **Upload:** User uploads a PDF document via the Next.js web interface.
2. **Process:** The FastAPI backend extracts text, splits it, generates embeddings, and indexes it into ChromaDB.
3. **Analyze:** The user requests a summary, insights, or asks a direct question.
4. **Retrieve & Generate:** The system retrieves the most relevant semantic chunks and constructs a strict prompt for Gemini.
5. **Review:** The user receives a grounded response with interactive source citations pointing to the exact page and excerpt.

## 6. RAG Architecture
The implemented RAG pipeline operates in two distinct phases:

**Ingestion / Indexing:**
PDF Document → PyMuPDF Extraction → RecursiveCharacterTextSplitter (chunk size: 800, overlap: 150) → `all-MiniLM-L6-v2` Local Embeddings → ChromaDB Persistent Vector Store

**Query / Generation:**
User Question → Embedding Generation → Semantic Similarity Retrieval → Grounded Prompt Construction → `gemini-3.5-flash` LLM Invocation → Q&A / Summary / Insights (with explicit source/page/chunk citations)

## 7. Technology Stack
**Frontend:**
- Next.js 15
- React
- TypeScript
- Tailwind CSS
- Lucide Icons
- TanStack Query

**Backend:**
- Python 3.11
- FastAPI
- Pydantic
- Uvicorn
- PyMuPDF

**AI / Retrieval:**
- LangChain
- Google Gemini (`gemini-3.5-flash`)
- Sentence Transformers (`all-MiniLM-L6-v2`)
- ChromaDB

**Workflow Visualization:**
- Langflow *(Academic visualization of the RAG pipeline)*

## 8. System Architecture
- **Client Layer:** Next.js 15 SPA providing an interactive document workspace.
- **API Layer:** FastAPI providing robust, type-checked REST endpoints.
- **RAG Engine:** LangChain orchestration for retrieval and prompt formatting.
- **Data Layer:** Local ChromaDB for vectors and filesystem storage for PDFs.

## 9. Application Workflow
Upload Document → Polling Status (Processing) → Document Ready → Workspace Dashboard → Request Summary/Insights or Ask Questions → View Grounded Results with Citations.

## 10. Langflow Academic Visualization
**ResearchPilot AI — RAG Architecture (Langflow Visualization)**
A Langflow workflow (`docs/langflow_academic_demo.json`) is provided as an academic visualization of the production RAG architecture. Note that the actual production application is implemented natively using FastAPI and LangChain for optimal performance and integration.

## 11. Project Structure
```
ResearchPilot-AI/
├── backend/            # FastAPI backend application
│   ├── app/            # Application logic, routes, and services
│   ├── tests/          # Pytest suite
│   ├── storage/        # Local document and vector storage (git-ignored)
│   ├── .env.example    # Environment configuration template
│   └── requirements.txt
├── frontend/           # Next.js frontend application
│   ├── src/            # React components, pages, and hooks
│   └── package.json
├── docs/               # Architecture, specs, and screenshots
│   ├── presentation/   # Project presentation files
│   └── screenshots/    # UI and flow demonstration images
├── .gitignore          # Root gitignore rules
└── README.md           # This documentation
```

## 12. Installation
Ensure you have **Python 3.11** and **Node.js (v18+)** installed.

**Backend Setup:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**Frontend Setup:**
```bash
cd frontend
npm install
```

## 13. Environment Configuration
**Backend:**
Copy the template and provide your API key.
```bash
cd backend
cp .env.example .env
```
*Note: Edit `.env` to include your `GEMINI_API_KEY`. Never commit this file.*

## 14. Running the Application
**Start the Backend:**
```bash
cd backend
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

**Start the Frontend:**
```bash
cd frontend
npm run dev
```
The application will be accessible at `http://localhost:3000`.

## 15. API Overview
- `POST /api/documents/`: Upload and ingest a PDF document.
- `GET /api/documents/{document_id}`: Retrieve document processing status.
- `POST /api/documents/{document_id}/query`: Submit a query and retrieve a grounded answer with citations.
- `GET /api/documents/{document_id}/summary`: Generate a 9-dimension structured summary.
- `GET /api/documents/{document_id}/insights`: Generate 7-dimension deep paper insights.

## 16. Testing & Validation
The project includes a robust test suite to guarantee reliability.
- **Backend Tests:** 148 / 148 tests passed successfully using Pytest.
- **Validation Checks Verified:**
  - Frontend production build & linting
  - PDF extraction and vector indexing
  - Grounded Q&A with exact page/chunk citations
  - Invalid upload handling & missing document 404 responses
  - Empty query validation
  - Analysis caching for performance

## 17. Security & Privacy
- **API Key Security:** Managed strictly via backend environment variables (`.env`). Keys are never exposed to the frontend or committed to source control.
- **Local Data Storage:** PDFs and ChromaDB vectors are stored locally on the server. No private documents are leaked to third-party databases.
- **Grounded Generation:** The system limits hallucination risk by enforcing generation based *only* on retrieved context.
- **Repository Safety:** All runtime artifacts, caches, and uploaded documents are explicitly ignored in `.gitignore`.

## 18. Current Scope (MVP)
The current MVP strictly focuses on **single-document PDF analysis** (upload, process, and query one document at a time) with integrated structured summaries and insights.

## 19. Future Scope (Planned / Not Implemented)
- Multi-document synthesis and comparative analysis
- Collaborative research workspaces for team sharing
- Extended format support (Word, LaTeX, EPUB)
- External academic and web source ingestion
- Citation network analysis and knowledge graphs
- Trend analysis across research topics

## 20. Screenshots / Demo
*(Please refer to `docs/screenshots/` for visual documentation of the Dashboard, Document Workspace, Grounded Q&A, and Summary interface).*

## 21. Limitations
- Large PDFs (>50MB) may exceed processing timeouts or local memory constraints.
- Local embeddings (`all-MiniLM-L6-v2`) are highly efficient but may miss nuanced cross-lingual semantic matches compared to larger cloud models.
- Q&A is strictly limited to information present in the text; it cannot verify external claims.

## 22. GitHub / Project Information
**Repository:** [https://github.com/Pirajan-07/ResearchPilot-AI](https://github.com/Pirajan-07/ResearchPilot-AI)
**Author:** Pirajan-07
