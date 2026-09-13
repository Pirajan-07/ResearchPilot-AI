# ResearchPilot AI — API Specification

**Version:** 1.1 (Revised)
**Status:** Architecture Phase — Approved for Phase 1
**Last Revised:** 2026-09-11
**Base URL (development):** `http://localhost:8000/api`

---

## 1. API Design Principles

- RESTful resource-oriented design
- JSON request/response bodies (except file uploads: multipart/form-data)
- HTTP status codes used semantically
- All errors return a consistent error envelope
- All timestamps: ISO 8601 UTC
- Document identity: UUID v4

---

## 2. Error Envelope

All error responses follow this structure:

```json
{
  "error": {
    "code": "DOCUMENT_NOT_FOUND",
    "message": "The requested document was not found.",
    "detail": null
  }
}
```

### Standard Error Codes

| Code | HTTP Status | When |
|---|---|---|
| VALIDATION_ERROR | 422 | Invalid request body/parameters |
| FILE_TOO_LARGE | 413 | Upload exceeds configured limit (default 50 MB) |
| INVALID_FILE_TYPE | 415 | Non-PDF uploaded |
| SCANNED_PDF | 422 | PDF has no text layer (image-only) |
| DOCUMENT_NOT_FOUND | 404 | document_id doesn't exist in registry |
| DOCUMENT_NOT_READY | 409 | Query/summary/insights before indexing complete |
| PROCESSING_FAILED | 500 | Pipeline failure (extraction/embedding/indexing) |
| LLM_ERROR | 502 | Gemini API error or timeout |
| INTERNAL_ERROR | 500 | Unexpected backend error |

---

## 3. Endpoints

---

### 3.1 Health Check

**GET** `/health`

Returns service health. Used by frontend to verify backend is available.

**Response 200:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "2026-09-11T17:40:00Z",
  "providers": {
    "llm": "gemini",
    "embeddings": "local-huggingface",
    "vector_store": "chromadb"
  }
}
```

---

### 3.2 Upload Document

**POST** `/api/documents/upload`

Upload a research paper PDF for processing.

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|---|---|---|---|
| file | File | Yes | PDF, max 50 MB (configurable) |

**Response 202 Accepted:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "attention_is_all_you_need.pdf",
  "status": "pending",
  "created_at": "2026-09-11T17:40:00Z",
  "message": "Document accepted. Processing started."
}
```

Processing begins asynchronously. Poll `/status` for updates.

**Possible Errors:** 413, 415, 422, 500

---

### 3.3 Get Document Status

**GET** `/api/documents/{document_id}/status`

Poll for processing status of an uploaded document.

**Response 200:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "attention_is_all_you_need.pdf",
  "status": "ready",
  "progress": {
    "current_stage": "indexing",
    "stages": [
      { "name": "validation",  "label": "Validating file",           "status": "complete" },
      { "name": "extraction",  "label": "Extracting text",           "status": "complete" },
      { "name": "chunking",    "label": "Processing content",        "status": "complete" },
      { "name": "embedding",   "label": "Generating embeddings",     "status": "complete" },
      { "name": "indexing",    "label": "Building knowledge index",  "status": "complete" }
    ]
  },
  "page_count": 15,
  "chunk_count": 87,
  "created_at": "2026-09-11T17:40:00Z",
  "completed_at": "2026-09-11T17:41:15Z",
  "error": null
}
```

**Status values:** `pending` | `processing` | `ready` | `failed`

**Stage status values:** `pending` | `active` | `complete` | `failed`

**Polling guidance:** Frontend polls every 2 seconds while `status == "processing"`. Stop when `ready` or `failed`.

**Note on embedding stage:** On first-ever run, the `embedding` stage may take 30+ seconds because the HuggingFace model must be downloaded (~90 MB). Subsequent runs use the cached model and take 5-15 seconds. The frontend should show this stage with a message like "Generating embeddings (first run may take longer)..." without an artificial timeout.

**Possible Errors:** 404

---

### 3.4 Query Document (Research Assistant)

**POST** `/api/documents/{document_id}/query`

Submit a research question. Returns a grounded answer with source references.

**Request Body:**
```json
{
  "query": "What methodology does this paper use?",
  "top_k": 5
}
```

| Field | Type | Required | Default | Constraints |
|---|---|---|---|---|
| query | string | Yes | — | 1–500 characters |
| top_k | integer | No | 5 (from env) | 1–10 |

**Response 200 (answer found):**
```json
{
  "query": "What methodology does this paper use?",
  "answer": "The paper proposes the Transformer architecture, which relies entirely on self-attention mechanisms and dispenses with recurrence and convolutions. The model consists of stacked encoder and decoder layers, each using multi-head attention and position-wise feed-forward networks (Source 1). Positional encodings are added to the input embeddings to retain sequence order information (Source 2).",
  "has_context": true,
  "sources": [
    {
      "chunk_id": "doc_550e8400_chunk_0042",
      "page_number": 3,
      "page_label": "Page 3 (approx.)",
      "text_excerpt": "We describe the Transformer model architecture, consisting of an encoder and decoder, each composed of a stack of N = 6 identical layers...",
      "relevance_score": 0.891
    },
    {
      "chunk_id": "doc_550e8400_chunk_0019",
      "page_number": 2,
      "page_label": "Page 2 (approx.)",
      "text_excerpt": "Since our model contains no recurrence and no convolution, in order for the model to make use of the order of the sequence...",
      "relevance_score": 0.847
    }
  ]
}
```

**Response 200 (no relevant context):**
```json
{
  "query": "What is the company's stock price?",
  "answer": "I couldn't find sufficient evidence for that in the uploaded paper.",
  "has_context": false,
  "sources": []
}
```

**Note:** `has_context: false` is a **200 OK**, not an error. The system correctly answered: "this is not in the paper." The frontend renders this response distinctly (no source section, advisory icon).

**Possible Errors:** 404 (not found), 409 (not ready), 422 (invalid query), 502 (Gemini error)

---

### 3.5 Get Document Summary

**GET** `/api/documents/{document_id}/summary`

Returns structured 9-dimension summary. Generated on first request; cached in memory thereafter.

**Response 200:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "attention_is_all_you_need.pdf",
  "generated_at": "2026-09-11T17:41:30Z",
  "cached": false,
  "summary": {
    "overview": "\"Attention Is All You Need\" (Vaswani et al., 2017) introduces the Transformer, a neural network architecture for sequence transduction based entirely on attention mechanisms, without recurrence or convolutions.",
    "research_problem": "Existing sequence transduction models rely on recurrent neural networks, creating bottlenecks for parallelization and difficulties learning long-range dependencies.",
    "objectives": "To develop a model architecture based solely on attention mechanisms that eliminates sequential computation and enables superior parallelization.",
    "methodology": "The Transformer uses stacked multi-head self-attention layers and position-wise feed-forward networks in both encoder and decoder, with positional encodings replacing recurrent computation.",
    "dataset": "WMT 2014 English-to-German (4.5M sentence pairs) and English-to-French (36M sentence pairs) translation datasets.",
    "key_findings": "The Transformer achieves 28.4 BLEU on WMT 2014 EN-DE, outperforming all prior models, while training in 12 hours on 8 P100 GPUs.",
    "limitations": "Not identified in this paper.",
    "conclusion": "The Transformer demonstrates that attention-only architectures achieve state-of-the-art results with superior training efficiency compared to RNN-based models.",
    "future_direction": "Extension to images, audio, and video modalities; investigation of local and restricted attention for handling larger inputs."
  }
}
```

**"Not identified" value:** If a dimension cannot be answered from retrieved context, its value is exactly: `"Not identified in this paper."` — never null, never fabricated.

**`cached` field:** When `true`, this is a previously generated result returned instantly. When `false`, Gemini was called.

**Performance note:** First call takes 10-20 seconds (Gemini API round-trip). Subsequent calls return immediately from cache.

**Possible Errors:** 404, 409, 502

---

### 3.6 Get Research Insights

**GET** `/api/documents/{document_id}/insights`

Returns structured 7-dimension research insights. Generated on first request; cached thereafter.

**Response 200:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "attention_is_all_you_need.pdf",
  "generated_at": "2026-09-11T17:41:50Z",
  "cached": false,
  "insights": {
    "research_problem": "The sequential nature of RNN-based models prevents parallelization during training and creates difficulty modeling long-range dependencies.",
    "methodology": "Self-attention with multi-head attention, position-wise feed-forward networks, positional encodings, encoder-decoder architecture.",
    "methodology_tags": ["Transformer", "Self-Attention", "Multi-Head Attention", "Encoder-Decoder", "Positional Encoding"],
    "dataset": "WMT 2014 English-German and English-French translation benchmarks.",
    "main_contribution": "The Transformer: the first sequence transduction model relying entirely on self-attention without recurrence or convolutions.",
    "key_findings": [
      "28.4 BLEU on WMT 2014 EN-DE, surpassing all previous models",
      "41.0 BLEU on WMT 2014 EN-FR, a new single-model record",
      "Trained 3x faster than best recurrent models on 8 P100 GPUs"
    ],
    "limitations": [
      "Not identified in this paper."
    ],
    "future_direction": "Extension of attention mechanisms to other modalities; investigation of local and restricted attention for larger sequences."
  }
}
```

**Important UI note:** These insights describe **this specific paper only**. The frontend must display them as "Paper Insights" — NOT "Research Trends" or "Global Analysis."

**Possible Errors:** 404, 409, 502

---

### 3.7 Delete Document

**DELETE** `/api/documents/{document_id}`

Removes all document data: uploaded file, ChromaDB collection, in-memory state, cached summary/insights.

**Response 200:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Document and all associated data deleted successfully."
}
```

**Possible Errors:** 404

---

## 4. Frontend Environment

```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

This is the **only** environment variable the frontend needs. It is public (prefixed with `NEXT_PUBLIC_`). No secrets are exposed to the frontend.

---

## 5. Backend Environment (.env)

```bash
# === AI Providers ===
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# === Storage ===
UPLOAD_DIR=./storage/uploads
CHROMA_PERSIST_DIRECTORY=./storage/chroma_db

# === Processing Parameters ===
MAX_UPLOAD_SIZE_MB=50
CHUNK_SIZE=800
CHUNK_OVERLAP=150
RETRIEVAL_TOP_K=5

# === Server ===
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO

# === CORS ===
CORS_ORIGINS=http://localhost:3000
```

**Security:** This file is GITIGNORED. `.env.example` with empty values is committed.

---

## 6. OpenAPI Documentation

FastAPI auto-generates interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- JSON: `http://localhost:8000/openapi.json`

No manual maintenance required.

---

## 7. CORS Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # ["http://localhost:3000"]
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
    allow_credentials=False,
)
```

---

*This document supersedes API_SPEC.md v1.0. OpenAI references removed. Gemini error codes updated. page_label field added to source references.*
