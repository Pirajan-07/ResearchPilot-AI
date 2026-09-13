# ResearchPilot-AI: Production vs Academic Demonstration

This document outlines the differences between our actual production implementation of the Retrieval-Augmented Generation (RAG) pipeline and the visual representation built in Langflow for academic/presentation purposes.

## 1. Production Implementation (Actual System)

The core application runs on a robust, custom-built stack optimized for performance, scalability, and API quota management.

- **Frontend**: Next.js (React) providing a customized chat interface and document upload capabilities.
- **Backend**: FastAPI (Python) serving REST APIs.
- **Document Processing**: `PyMuPDF` for PDF text extraction.
- **Text Splitting**: `RecursiveCharacterTextSplitter` (chunk size: 800, overlap: 150) implemented via Langchain in Python.
- **Embeddings**: Local `all-MiniLM-L6-v2` models using HuggingFace sentence-transformers.
- **Vector Database**: `ChromaDB` running locally for similarity search.
- **LLM Engine**: `Gemini 3.5 Flash` accessed via `langchain-google-genai`, with structured output, strict prompt grounding, and API quota management.

**Key Advantages:** 
- Full control over error handling and API quotas (e.g., avoiding unnecessary Gemini API calls).
- Seamless integration between the Next.js frontend and FastAPI backend.
- Custom logic for parsing complex academic papers and maintaining conversational state.

## 2. Langflow Academic Demonstration

To visually present the architecture in a clean, PPT-ready format for academic or stakeholder demonstrations, we have modeled the exact same pipeline using Langflow. 

- **Purpose**: Purely for visual demonstration and architectural understanding. **It does not replace the production FastAPI application.**
- **Components Mapped**:
  - `PyMuPDF Loader` -> Reads the PDF.
  - `Recursive Character Text Splitter` -> Chunks the text (800 chunk size / 150 overlap).
  - `HuggingFace Embeddings` -> Uses `all-MiniLM-L6-v2`.
  - `Chroma` -> Simulates the vector storage.
  - `Prompt Template` & `Chat Input/Output` -> Represents the prompt grounding step.
  - `Google Generative AI` -> Represents the Gemini 3.5 Flash integration.

**Why Not Use Langflow in Production?**
While Langflow provides an excellent visual representation, our production app requires fine-grained control over local embedding execution, API rate limits (essential due to Gemini free-tier constraints), and custom frontend interactions that are best handled by our bespoke FastAPI/Next.js stack.

## Resources
- **Exported Flow JSON**: [`langflow_academic_demo.json`](./langflow_academic_demo.json)
- **Visual Diagram**: Screenshots of the Langflow canvas were captured during the workflow construction and are available in the project artifacts for use in PowerPoint presentations.
- **Important note:** The Langflow workflow was constructed manually in the Langflow UI for visual demonstration purposes. It was intentionally **not executed** — no Gemini API calls were made during the demonstration, to preserve free-tier quota.
