# ResearchPilot AI — Technology Stack

**Version:** 1.1 (Revised — Free-Tier Gemini + Local Embeddings)
**Status:** Architecture Phase — Approved for Phase 1
**Last Revised:** 2026-09-11

---

## Environment Facts (Observed & Validated)

| Tool | Version | Notes |
|---|---|---|
| OS | Windows 11 | Primary development environment |
| Python | **3.11.9** | ✅ Selected runtime — see §2 below |
| Python (also installed) | 3.14.7 | NOT used — compatibility risk |
| Node.js | 24.19.0 | Current LTS-adjacent stable |
| npm | 11.17.0 | Current |
| npx create-next-app | **16.3.5** | Current stable Next.js |

---

## 1. Frontend Stack

### 1.1 Selected Stack

| Technology | Version Target | Role |
|---|---|---|
| Next.js | **15.x** (App Router) | Frontend framework |
| TypeScript | 5.x | Type safety |
| Tailwind CSS | 3.x (stable) | Utility-first styling |
| shadcn/ui | latest | Accessible component primitives |
| Lucide React | latest | Icon system |
| TanStack Query | v5 | Server state, polling, cache |
| Axios | 1.x | HTTP client |
| React Hot Toast | latest | Notification toasts |

### 1.2 Decision: Next.js Version

**Decision:** Use **Next.js 15.x** (not 14 as previously stated).

**Reason:** `npx create-next-app@latest` resolves to **16.3.5** as of inspection date. However, Next.js 16 is still in active release cycle. Next.js **15.x** is the proven stable LTS-equivalent used in production-grade projects today. Next.js 14 is outdated. We pin to 15.x for the best stability/feature balance.

- Alternative considered: Next.js 16.x
- Why downgraded to 15: Next.js 16 is very new (Sept 2025). For a submission deadline of Sept 15, 2026, using the 1-year-matured stable version is the correct professional choice.
- Alternative considered: Vite + React SPA
- Why rejected: Less project structure discipline; no built-in routing conventions; App Router's RSC model gives cleaner data-fetching patterns.

**Node.js 24 compatibility:** ✅ Node 24 is compatible with Next.js 15.

### 1.3 Decision: Tailwind CSS Version

**Decision:** Tailwind CSS **4.x** (actually installed).

**Note:** The original plan targeted Tailwind CSS 3.x due to shadcn/ui compatibility concerns. In practice, the project was bootstrapped with Tailwind CSS 4.x (via `@tailwindcss/postcss` and the v4 PostCSS plugin). The v4 engine is what is installed and running in production. The `package.json` confirms `"tailwindcss": "^4"`.

---

## 2. Backend: Python Version Decision

**Decision: Python 3.11.9**

**Reason:** Python 3.11 is the proven stable LTS-class version for the entire ML/AI Python ecosystem. All critical dependencies have been validated against it:

| Package | Latest for 3.11 | Python Constraint |
|---|---|---|
| langchain-google-genai | 4.4.0 | >=3.10.0, <4.0.0 ✅ |
| chromadb | 1.5.9 | >=3.8 ✅ |
| sentence-transformers | 6.0.1 | >=3.9 ✅ |
| pymupdf | 1.28.2 | >=3.8 ✅ |
| fastapi | 0.115.x | >=3.8 ✅ |

**Why NOT Python 3.14:** Python 3.14.7 is the current default, but it is too new for the AI/ML ecosystem. Many packages (notably those with C extensions like `chromadb`, `sentence-transformers`, `torch`) may not have stable 3.14 wheels. Running on 3.14 risks broken installs mid-development — unacceptable for a Sept 15 deadline.

**How to use 3.11:** Use `py -3.11 -m venv .venv` to create the virtual environment. This explicitly targets the 3.11 install.

---

## 3. Backend Stack

### 3.1 Selected Stack

| Technology | Version Target | Role |
|---|---|---|
| Python | **3.11.9** | Runtime |
| FastAPI | 0.115.x | API framework (async-native, OpenAPI auto-gen) |
| Uvicorn | 0.32.x | ASGI server |
| Pydantic v2 | 2.x | Schema validation + settings management |
| pydantic-settings | 2.x | .env loading via BaseSettings |
| python-multipart | 0.0.x | File upload parsing |
| aiofiles | 24.x | Async file I/O |
| PyMuPDF (fitz) | **1.28.2** | PDF text extraction |
| LangChain | 0.3.x | RAG orchestration framework |
| langchain-google-genai | **4.4.0** | Gemini LLM integration via LangChain |
| google-genai | >=2.20.0 | Underlying Google AI SDK (transitive) |
| langchain-huggingface | 0.1.x | HuggingFace embedding integration |
| sentence-transformers | **6.0.1** | Local CPU embedding model runtime |
| langchain-chroma | 0.2.x | ChromaDB integration for LangChain |
| chromadb | **1.5.9** | Local persistent vector database |
| python-dotenv | 1.x | .env loading |
| loguru | 0.7.x | Structured logging |

### 3.2 AI Provider Architecture

#### LLM Provider: Google Gemini (Free Tier)

**Decision:** Replace all OpenAI LLM references with Google Gemini via `langchain-google-genai`.

**Reason:** No OpenAI API key available. A Gemini Free Tier project already exists. `langchain-google-genai 4.4.0` supports Python >=3.10 and is actively maintained.

**Selected model: `gemini-3.5-flash`**

- Rationale: Current-generation Flash model offering low latency, structured output support, function calling, and strong instruction following. Available on Gemini API Free Tier. Suitable for research Q&A + structured summary generation. Not hard-coded — configured via `GEMINI_MODEL` env var.
- Alternative considered: `gemini-2.5-flash` — still valid but not the current-generation replacement
- Alternative considered: `gemini-3.5-pro` — rejected (higher cost; not free tier for most usage levels)
- Fall-back if model changes: change `GEMINI_MODEL=` in `.env` — no code changes required

**LangChain integration:**
```python
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(
    model=settings.GEMINI_MODEL,   # from env: "gemini-3.5-flash"
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.1,
    max_tokens=1200,
)
```

#### Embedding Provider: Local HuggingFace (Zero Cost)

**Decision:** Use local sentence-transformers model via `langchain-huggingface`. No paid API calls for embeddings.

**Selected model: `sentence-transformers/all-MiniLM-L6-v2`**

- Embedding dimension: 384
- Max sequence length: 256 tokens (~1000 characters)
- Size: ~90 MB (downloaded once; cached locally)
- CPU performance: ~500-1000 sentences/second on modern CPU
- MTEB score: Strong retrieval performance for English text
- ChromaDB compatibility: ✅ 384-dim vectors fully supported

**Rationale for this model over alternatives:**
- `all-mpnet-base-v2`: Better quality but 768-dim, 4x slower on CPU — too slow for first-run demo setup
- `all-MiniLM-L12-v2`: 33% slower than L6 with marginal quality gain — not justified for MVP
- `BAAI/bge-small-en-v1.5`: Comparable quality, slightly smaller; either is acceptable. `all-MiniLM-L6-v2` has broader documentation and troubleshooting resources, making it the safer choice for a deadline project.

Model must be configurable via `EMBEDDING_MODEL` env var. Swapping models requires re-indexing (dimensions may differ). This is documented in the Development Plan.

**LangChain integration:**
```python
from langchain_huggingface import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name=settings.EMBEDDING_MODEL,   # "sentence-transformers/all-MiniLM-L6-v2"
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}
)
```

#### Vector Store: ChromaDB 1.5.9

**Decision:** ChromaDB in embedded (local) mode.

**Reason:** No server process required, installs via pip on Windows, persists to disk, metadata filtering, cosine similarity — all required features present. Fully compatible with `langchain-chroma`.

**ChromaDB 1.5.x note:** ChromaDB 1.x introduced a new embedding function API. When using LangChain's `Chroma` wrapper (`langchain-chroma`), use the `langchain-chroma` adapter which handles this correctly. Do NOT call ChromaDB's native embedding functions directly — use LangChain's abstraction.

### 3.3 Provider Abstraction Layer

To support future provider swaps without rewriting service code, all AI services are accessed through thin provider wrappers:

```python
# app/providers/llm_provider.py
class BaseLLMProvider(ABC):
    @abstractmethod
    def get_llm(self) -> BaseChatModel: ...

class GeminiLLMProvider(BaseLLMProvider):
    def get_llm(self) -> ChatGoogleGenerativeAI: ...

# app/providers/embedding_provider.py
class BaseEmbeddingProvider(ABC):
    @abstractmethod
    def get_embeddings(self) -> Embeddings: ...

class LocalHuggingFaceEmbeddingProvider(BaseEmbeddingProvider):
    def get_embeddings(self) -> HuggingFaceEmbeddings: ...
```

Future providers (OpenAI, Anthropic, Ollama) would implement these interfaces without touching the service layer.

---

## 4. LangChain Usage Map

LangChain is used for **real, non-trivial purposes** at each stage:

| LangChain Component | Where Used | Purpose |
|---|---|---|
| `RecursiveCharacterTextSplitter` | `chunking_service.py` | Intelligent paragraph-aware chunking |
| `Document` | `parser_service.py` | Standard document abstraction with metadata |
| `HuggingFaceEmbeddings` | `embedding_service.py` | Local embedding generation |
| `Chroma` (langchain-chroma) | `vector_store_service.py` | Vector storage + retrieval interface |
| `ChatGoogleGenerativeAI` | `llm_service.py` | Gemini LLM calls |
| `PromptTemplate` / `ChatPromptTemplate` | `research_agent.py` | Structured prompt construction |
| `RetrievalQA` / custom LCEL chain | `research_agent.py` | RAG chain orchestration |
| `StrOutputParser` / JSON output | `summary_service.py`, `insights_service.py` | Structured output parsing |

LangChain is NOT used merely to claim usage. Each usage is justified by real functionality it provides.

---

## 5. Configuration / Infrastructure

| Item | Technology |
|---|---|
| Backend env | `backend/.env` + `pydantic-settings` |
| Frontend env | `frontend/.env.local` |
| Cross-origin | FastAPI CORS middleware (localhost:3000 only in dev) |
| File storage | Local filesystem (`backend/storage/uploads/`) |
| Vector storage | Local ChromaDB (`backend/storage/chroma_db/`) |
| Model cache | HuggingFace default cache (`~/.cache/huggingface/`) |

No cloud infrastructure, no database, no container orchestration required.

---

## 6. Development Tooling

| Tool | Role |
|---|---|
| Python 3.11.9 venv | Isolated backend environment |
| Ruff | Python linter + formatter |
| mypy | Python type checking |
| pytest + pytest-asyncio | Backend testing |
| ESLint + Prettier | Frontend linting/formatting |
| Git | Version control |
| PowerShell | Windows terminal |

---

## 7. Pinned Dependency Targets (requirements.txt)

```
fastapi>=0.115.0,<0.116.0
uvicorn[standard]>=0.32.0,<0.33.0
python-multipart>=0.0.9
aiofiles>=24.0.0
pymupdf>=1.28.0,<1.29.0
langchain>=0.3.0,<0.4.0
langchain-core>=1.6.0
langchain-google-genai>=4.4.0,<5.0.0
langchain-huggingface>=0.1.0,<0.2.0
langchain-chroma>=0.2.0,<0.3.0
chromadb>=1.5.0,<2.0.0
sentence-transformers>=6.0.0,<7.0.0
torch>=2.0.0    # CPU only; transitive from sentence-transformers
pydantic>=2.0.0,<3.0.0
pydantic-settings>=2.0.0,<3.0.0
python-dotenv>=1.0.0
loguru>=0.7.0
```

**Note on torch:** `sentence-transformers` requires PyTorch. The CPU-only wheel is sufficient and avoids CUDA dependencies. Installation instruction: `pip install torch --index-url https://download.pytorch.org/whl/cpu` before installing sentence-transformers, OR rely on pip resolving the CPU wheel automatically. This is documented in Phase 1 setup steps.

---

## 8. Frontend Dependency Targets (package.json)

```json
{
  "dependencies": {
    "next": "^15.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "@tanstack/react-query": "^5.0.0",
    "axios": "^1.7.0",
    "lucide-react": "latest",
    "react-hot-toast": "^2.4.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.4.0"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "@types/react": "^19.0.0",
    "@types/node": "^22.0.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0",
    "eslint": "^9.0.0",
    "eslint-config-next": "^15.0.0"
  }
}
```

---

## 9. Removed Dependencies (vs. Previous v1.0)

The following were in the v1.0 tech stack and are **completely removed**:

| Removed Dependency | Why Removed |
|---|---|
| `openai` Python SDK | No OpenAI API key; replaced by Gemini |
| `langchain-openai` | Replaced by `langchain-google-genai` |
| `OPENAI_API_KEY` env var | Does not exist in this project |
| `gpt-4o` model reference | Does not exist in this project |
| `text-embedding-3-small` | Replaced by local `all-MiniLM-L6-v2` |
| Next.js 14 | Replaced by Next.js 15.x |

---

*This document supersedes TECH_STACK.md v1.0. All references in other documents should be consistent with this version.*
