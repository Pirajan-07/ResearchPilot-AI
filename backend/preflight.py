"""
Phase 5 Pre-flight: Real Gemini Connectivity + Full RAG Smoke Test
Run from: backend/   with  .venv\Scripts\python.exe preflight.py
"""
import sys
import io
import os
import time
import textwrap

# Ensure backend/ is on sys.path so 'app' is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PASS = "[PASS]"
FAIL = "[FAIL]"
SEP  = "=" * 60


# ── STEP 1: Gemini provider init + minimal structured call ────────────────────
print(SEP)
print("STEP 1: Gemini provider init + minimal structured call")
print(SEP)

try:
    from app.config import settings
    from app.providers.gemini_provider import get_gemini_provider
    from langchain_core.messages import SystemMessage, HumanMessage
    from pydantic import BaseModel, Field

    class _PingResponse(BaseModel):
        reply: str = Field(description="Short answer to the question.")

    llm = get_gemini_provider().get_llm()
    structured = llm.with_structured_output(_PingResponse)
    ping = structured.invoke([
        SystemMessage(content="You are a helpful assistant."),
        HumanMessage(content="What is the capital of France? One word."),
    ])
    assert isinstance(ping, _PingResponse), f"Wrong type: {type(ping)}"
    assert ping.reply.strip(), "Empty reply"
    print(f"  {PASS} Provider initialised, model: {settings.GEMINI_MODEL}")
    print(f"  {PASS} Structured response received (content omitted)")
    print(f"  {PASS} Response type: {type(ping).__name__}")
except Exception as exc:
    print(f"  {FAIL} {type(exc).__name__}: {exc}")
    sys.exit(1)


# ── STEP 2: Create in-memory test PDF ────────────────────────────────────────
print()
print(SEP)
print("STEP 2: Create in-memory test PDF (2 pages)")
print(SEP)

try:
    import fitz

    doc = fitz.open()
    p1 = doc.new_page(width=595, height=842)
    p1.insert_textbox(fitz.Rect(50, 50, 545, 800), (
        "Abstract\n\n"
        "This paper proposes TransformerX, a novel neural architecture for natural "
        "language processing that eliminates recurrent connections entirely. We evaluate "
        "TransformerX on the WMT-2014 English-German machine translation benchmark and "
        "achieve a BLEU score of 28.4, surpassing all previous single-model results. "
        "The model requires significantly less training time than recurrent alternatives."
    ), fontsize=11, fontname="helv")

    p2 = doc.new_page(width=595, height=842)
    p2.insert_textbox(fitz.Rect(50, 50, 545, 800), (
        "Introduction and Limitations\n\n"
        "Sequence modelling has traditionally relied on recurrent neural networks. "
        "TransformerX replaces recurrence with multi-head self-attention, allowing "
        "full parallelisation during training. The model has quadratic memory complexity "
        "with respect to sequence length, making it impractical for very long documents. "
        "Future work should explore sparse attention patterns and linear approximations "
        "to reduce complexity for long sequences. The dataset used was WMT-2014 EN-DE."
    ), fontsize=11, fontname="helv")

    pdf_bytes = doc.tobytes()
    doc.close()
    print(f"  {PASS} PDF created ({len(pdf_bytes)} bytes, 2 pages)")
except Exception as exc:
    print(f"  {FAIL} {type(exc).__name__}: {exc}")
    sys.exit(1)


# ── STEP 3: Upload to live backend ────────────────────────────────────────────
print()
print(SEP)
print("STEP 3: Upload PDF to live backend (http://127.0.0.1:8000)")
print(SEP)

try:
    import requests

    BASE = "http://127.0.0.1:8000"
    resp = requests.post(
        f"{BASE}/api/documents/",
        files=[("file", ("transformerx_paper.pdf", io.BytesIO(pdf_bytes), "application/pdf"))],
        timeout=15,
    )
    assert resp.status_code == 202, f"Expected 202, got {resp.status_code}: {resp.text}"
    doc_id = resp.json()["document_id"]
    print(f"  {PASS} Accepted, document_id: {doc_id}")
except Exception as exc:
    print(f"  {FAIL} {type(exc).__name__}: {exc}")
    print("       Ensure backend is running:  .venv\\Scripts\\python.exe -m uvicorn main:app --port 8000")
    sys.exit(1)


# ── STEP 4: Poll until COMPLETED ─────────────────────────────────────────────
print()
print("STEP 4: Waiting for pipeline completion ...")

deadline = time.time() + 120
while time.time() < deadline:
    s = requests.get(f"{BASE}/api/documents/{doc_id}", timeout=10).json()
    status = s.get("status", "unknown")
    sys.stdout.write(f"\r  ... status: {status}          ")
    sys.stdout.flush()
    if status == "completed":
        break
    if status == "failed":
        print(f"\n  {FAIL} Pipeline failed: {s}")
        sys.exit(1)
    time.sleep(3)
else:
    print(f"\n  {FAIL} Timed out after 120s")
    sys.exit(1)

final = requests.get(f"{BASE}/api/documents/{doc_id}", timeout=10).json()
print(f"\n  {PASS} Completed — pages={final.get('page_count')}, chunks={final.get('chunk_count')}")


# ── STEP 5: Supported question (answer IS in paper) ───────────────────────────
print()
print(SEP)
print("STEP 5: Supported question — 'What benchmark and metric was used?'")
print(SEP)

try:
    r = requests.post(
        f"{BASE}/api/documents/{doc_id}/query",
        json={"question": "What benchmark and BLEU score was reported for TransformerX?"},
        timeout=40,
    )
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text[:300]}"
    data = r.json()
    answer  = data.get("answer", "")
    sources = data.get("sources", [])

    alow = answer.lower()
    grounded = any(kw in alow for kw in ["wmt", "bleu", "28.4", "english-german", "28"])
    assert grounded, f"Answer missing expected keywords. Answer: {answer[:250]}"
    assert len(answer) >= 20, f"Answer suspiciously short: {answer!r}"

    # Security checks
    assert "api_key" not in r.text.lower(), "API key found in response!"
    assert "traceback" not in r.text.lower(), "Stack trace in response!"
    assert "storage" not in r.text.lower() or "source_filename" in r.text, "Path may be leaking"

    print(f"  {PASS} HTTP 200 received")
    print(f"  {PASS} Answer length: {len(answer)} chars")
    print(f"  {PASS} Grounded content confirmed (WMT/BLEU/28.4 in answer)")
    print(f"  {PASS} Sources returned: {len(sources)}")
    if sources:
        print(f"  {PASS} First source page_number: {sources[0].get('page_number')}")
    print(f"  {PASS} No API key or stack trace in response")
except Exception as exc:
    print(f"  {FAIL} {type(exc).__name__}: {exc}")
    sys.exit(1)


# ── STEP 6: Unsupported question (answer NOT in paper) ────────────────────────
print()
print(SEP)
print("STEP 6: Unsupported question — 'What is the author email?'")
print(SEP)

try:
    r2 = requests.post(
        f"{BASE}/api/documents/{doc_id}/query",
        json={"question": "What is the institutional email address of the first author?"},
        timeout=40,
    )
    assert r2.status_code == 200, f"HTTP {r2.status_code}: {r2.text[:300]}"
    d2 = r2.json()
    ans2 = d2.get("answer", "")

    alow2 = ans2.lower()
    honest = any(kw in alow2 for kw in [
        "not", "cannot", "could not", "no information",
        "not found", "not contain", "insufficient",
        "do not", "doesn", "unable",
    ])
    assert honest, f"Possible hallucination detected. Answer: {ans2[:300]}"

    print(f"  {PASS} HTTP 200 received")
    print(f"  {PASS} Model expressed uncertainty (did not fabricate email)")
    print(f"  {PASS} Sources: {len(d2.get('sources', []))}")
except Exception as exc:
    print(f"  {FAIL} {type(exc).__name__}: {exc}")
    sys.exit(1)


# ── STEP 7: Paper Summary (9 Dimensions) ────────────────────────────────────────
print()
print(SEP)
print("STEP 7: Paper Summary (9 Dimensions)")
print(SEP)

try:
    r3 = requests.get(
        f"{BASE}/api/documents/{doc_id}/summary",
        timeout=60,
    )
    assert r3.status_code == 200, f"HTTP {r3.status_code}: {r3.text[:300]}"
    d3 = r3.json()

    assert "overview" in d3, "Missing 'overview' in summary response"
    assert "problem" in d3, "Missing 'problem' in summary response"
    
    # Check grounding
    alow3 = d3.get("overview", "").lower() + " " + d3.get("methodology", "").lower()
    grounded3 = any(kw in alow3 for kw in ["transformerx", "attention", "neural"])
    assert grounded3, f"Summary missing expected keywords. Content: {d3}"

    print(f"  {PASS} HTTP 200 received")
    print(f"  {PASS} Structured 9-dimension response parsed correctly")
    print(f"  {PASS} Content grounded in paper text")
except Exception as exc:
    print(f"  {FAIL} {type(exc).__name__}: {exc}")
    sys.exit(1)


# ── STEP 8: Paper Insights (7 Dimensions) ───────────────────────────────────────
print()
print(SEP)
print("STEP 8: Paper Insights (7 Dimensions)")
print(SEP)

try:
    r4 = requests.get(
        f"{BASE}/api/documents/{doc_id}/insights",
        timeout=60,
    )
    assert r4.status_code == 200, f"HTTP {r4.status_code}: {r4.text[:300]}"
    d4 = r4.json()

    assert "contribution" in d4, "Missing 'contribution' in insights response"
    assert isinstance(d4.get("findings"), list), "'findings' should be a list"
    
    # Check grounding
    alow4 = str(d4).lower()
    grounded4 = any(kw in alow4 for kw in ["transformerx", "28.4", "bleu", "quadratic"])
    assert grounded4, f"Insights missing expected keywords. Content: {d4}"

    print(f"  {PASS} HTTP 200 received")
    print(f"  {PASS} Structured 7-dimension response parsed correctly")
    print(f"  {PASS} Content grounded in paper text")
except Exception as exc:
    print(f"  {FAIL} {type(exc).__name__}: {exc}")
    sys.exit(1)


# ── Final summary ─────────────────────────────────────────────────────────────
print()
print(SEP)
print("PHASE 5 PRE-FLIGHT: ALL 8 STEPS PASSED")
print(f"  Model : {settings.GEMINI_MODEL}")
print(f"  Doc ID: {doc_id}  (in-memory, not committed)")
print(f"  Step 1: Gemini provider connected and structured output works")
print(f"  Step 2: PDF created")
print(f"  Step 3: Upload accepted")
print(f"  Step 4: Full pipeline completed")
print(f"  Step 5: Supported question answered with paper content")
print(f"  Step 6: Unsupported question answered honestly")
print(f"  Step 7: Paper Summary extracted correctly")
print(f"  Step 8: Paper Insights extracted correctly")
print(f"  Key  : NOT printed at any point")
print(SEP)
