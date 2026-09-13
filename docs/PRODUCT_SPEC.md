# ResearchPilot AI — Product Specification

**Version:** 1.1 (Revised — Free-Tier Gemini + Local Embeddings)  
**Status:** Architecture Phase — Approved for Phase 1  
**Last Revised:** 2026-09-11  
**Course:** Emerging Trends in AI / IOC

---

## 1. Product Overview

ResearchPilot AI is a focused, document-grounded AI research workspace for academic users. It enables a researcher to upload a research paper (PDF), automatically process and index its content, and then engage in structured analysis through three complementary lenses:

1. **Research Assistant** — Grounded question-answering backed by RAG (powered by Gemini Free Tier)
2. **Structured Summary** — Auto-generated structured abstract across 9 standard dimensions
3. **Paper Insights** — Structured extracted metadata about THIS paper (problem, method, findings, gaps)

The core design philosophy is *document-grounded intelligence*: every answer, summary, and insight is derived directly from the uploaded paper, never from hallucinated general knowledge. The system communicates this trust contract clearly to the user at every step.

---

## 2. Target User

**Primary:** Computer Science / AI graduate or undergraduate student reviewing a research paper for coursework, seminar preparation, or research reading.

**Secondary (post-MVP):** Academic researchers wanting rapid literature triage across multiple papers.

---

## 3. Core Problem Statement

Researchers spend significant time reading and re-reading papers to extract key information. Current general-purpose chatbots either hallucinate content or provide responses not grounded in the specific paper being studied. ResearchPilot AI provides a trustworthy, paper-specific research workspace that accelerates comprehension without sacrificing accuracy.

---

## 4. MVP Feature Scope

### 4.1 Included in MVP

| Feature | Description | Priority |
|---|---|---|
| PDF Upload | Single PDF upload, up to 50 MB | P0 |
| Document Validation | File type, size, corruption check | P0 |
| Text Extraction | Full-text extraction with page metadata | P0 |
| Document Chunking | Semantic chunking with configurable parameters | P0 |
| Embedding Generation | Per-chunk vector embeddings | P0 |
| Vector Storage | Local persistent vector store (ChromaDB) | P0 |
| Semantic Retrieval | Top-k similarity retrieval per query | P0 |
| Grounded Q&A | RAG-powered answers with source attribution | P0 |
| Structured Summary | 9-dimension paper summary | P0 |
| Research Insights | 7-dimension structured insight extraction | P0 |
| Source References | Chunk/page attribution displayed in UI | P0 |
| Processing Status | Real-time pipeline stage feedback | P0 |
| Error Handling | Graceful failure with recovery guidance | P0 |

### 4.2 Explicitly Out of Scope for MVP

| Feature | Reason for Deferral |
|---|---|
| Multi-paper upload/comparison | Increases complexity disproportionately |
| Citation network analysis | Requires external data sources |
| Research trend prediction | Insufficient data at MVP scale |
| Knowledge graph generation | Visualization scope too wide |
| External academic search | External API dependencies add fragility |
| Voice/image input | Separate modality, separate scope |
| Authentication / user accounts | No multi-user requirement at MVP |
| Payments / enterprise features | Not relevant for academic MVP |
| Multi-agent orchestration | Single agent sufficient for MVP scope |

---

## 5. User Journey (Happy Path)

```
1. User opens ResearchPilot AI
2. Empty Workspace is shown — clear explanation, prominent upload CTA
3. User drags/selects a PDF research paper
4. Upload begins → frontend shows upload progress
5. Backend validates file → extraction → chunking → embedding → vector store
6. Frontend shows staged progress indicators for each pipeline step
7. On success: Research Workspace activates with paper metadata shown
8. User reads auto-generated Structured Summary (9 dimensions)
9. User reads Research Insights panel (7 dimensions)
10. User types questions into Research Assistant
11. Answers appear with grounded source references
12. User can clear and upload a new paper
```

---

## 6. User Journey (Error Paths)

| Error | What the UI Shows |
|---|---|
| Non-PDF uploaded | "Only PDF files are supported. Please upload a valid PDF." |
| PDF > 50 MB | "File too large. Maximum supported size is 50 MB." |
| Corrupt/unreadable PDF | "We couldn't extract text from this PDF. Please check that the file is not corrupted or password-protected." |
| Processing failure (server) | "Something went wrong during processing. Please try again." with retry button |
| Query with no relevant context | "This question could not be answered from the uploaded paper. Please check the paper content." |
| Network failure | "Connection lost. Please check your network and try again." |

---

## 7. Information Architecture

```
Application Shell
├── Brand: ResearchPilot AI
├── [Active] Workspace           — primary research experience
├── [Active] Research Assistant  — grounded Q&A panel
├── [Active] Summary             — structured summary panel
├── [Active] Paper Insights      — paper-specific insights panel
└── [Disabled/Future] Settings   — configuration (future)
```

All navigation items visible in MVP are functional. Future items are clearly marked.

---

## 8. Workspace States

### State A — Empty Workspace
- Product explanation (headline + 2-line description)
- Prominent drag-and-drop upload zone
- Supported formats and size limit shown
- Illustrative example workflow (3 steps visual)
- Empty state is not a blank page — it communicates value

### State B — Processing State
- Shows upload → extract → chunk → embed → index pipeline
- Each stage has a status indicator: pending / active / complete / failed
- Stage names are user-readable (not technical jargon)
- A cancel option is considered (not required for MVP)

### State C — Research Workspace
- Paper metadata card (title, detected page count, chunk count)
- Tab navigation: Summary | Insights | Assistant
- Summary tab: 9-dimension structured view
- Insights tab: 7-dimension structured view
- Assistant tab: conversational Q&A with source references

### State D — Error State
- Clear, non-technical error message
- Suggested recovery action
- Option to upload a new paper

---

## 9. Research Assistant Interaction Model

The Research Assistant is not a generic chatbot. It has a defined research-oriented identity communicated in its placeholder text, suggested prompts, and system behavior.

**Suggested example queries shown in empty assistant state:**
- "What is the main research problem addressed?"
- "What methodology does this paper use?"
- "What dataset was used in the experiments?"
- "What are the key findings?"
- "What are the limitations acknowledged?"
- "What future work do the authors suggest?"

**Answer format:**
- Direct answer paragraph
- Source references below the answer (document name + page/chunk reference)
- Clear visual separation between answer and sources

**Trust contract:**
- If no relevant context is found in the paper, the system responds: "I could not find sufficient information to answer this from the uploaded paper."
- The system never presents general knowledge as paper-sourced.

---

## 10. Structured Summary (9 Dimensions)

Each dimension is extracted from the paper using targeted RAG retrieval + structured LLM prompting.

| # | Dimension | Description |
|---|---|---|
| 1 | Paper Overview | Title, authors (if detectable), venue |
| 2 | Research Problem | The core problem the paper addresses |
| 3 | Objectives | What the authors set out to achieve |
| 4 | Methodology | Methods, algorithms, frameworks used |
| 5 | Dataset / Materials | Datasets used; experimental setup |
| 6 | Key Findings | Primary results and conclusions |
| 7 | Limitations | Acknowledged constraints and weaknesses |
| 8 | Conclusion | Authors' concluding statements |
| 9 | Future Research Direction | Suggested next steps by the authors |

If a dimension cannot be determined from the paper, it is marked "Not identified in the paper." — never fabricated.

---

## 11. Research Insights (7 Dimensions)

Displayed as structured data cards, not raw model output.

| # | Dimension | Display Format | Notes |
|---|---|---|---|
| 1 | Research Problem | Text card | Specific to THIS paper |
| 2 | Methodology | Text card + method tags | Specific to THIS paper |
| 3 | Dataset | Text card | Specific to THIS paper |
| 4 | Main Contribution | Text card | Specific to THIS paper |
| 5 | Key Findings | Bulleted list | Specific to THIS paper |
| 6 | Limitations | Bulleted list | Specific to THIS paper |
| 7 | Future Direction | Text card | Suggested by THIS paper's authors |

**UI wording requirement:** This panel is labeled "Paper Insights" — never "Research Trends" or "Global Analysis". The scope is limited to the uploaded paper. This is enforced at both the UI copy level and the LLM prompt level.

---

## 12. Non-Functional Requirements

| Requirement | Target |
|---|---|
| PDF upload size limit | 50 MB |
| Supported file types | PDF only (MVP) |
| Processing feedback latency | <500ms first status update |
| Q&A response latency | <8s (network-dependent) |
| Summary generation latency | <15s |
| Insights generation latency | <15s |
| Minimum supported browsers | Chrome 120+, Firefox 120+, Edge 120+ |
| Responsive layout | Desktop primary; tablet supported |
| Accessibility | WCAG 2.1 AA target |

---

## 13. Post-MVP Roadmap

### Phase 2 — Multi-Paper Workspace
- Upload multiple papers into a named workspace
- Compare papers across dimensions
- Cross-paper Q&A

### Phase 3 — Literature Intelligence
- External paper search (Semantic Scholar / arXiv API)
- Citation network analysis
- Research gap detection
- Trend analysis across paper sets

### Phase 4 — Collaboration & Export
- Summary/insights export (PDF, Markdown)
- Annotation layer on PDF viewer
- Team workspaces

---

*This document governs the MVP feature set and product experience. All implementation decisions must be consistent with the trust contract, information architecture, and feature boundaries defined here.*
