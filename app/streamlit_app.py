import os
import json
import requests
import streamlit as st

#Config
DIFY_API_BASE = os.getenv("DIFY_API_BASE", "http://localhost:5001")
DIFY_API_KEY  = os.getenv("DIFY_API_KEY",  "")
WORKFLOW_ID   = os.getenv("WORKFLOW_ID",   "")

#UI
st.set_page_config(page_title="Wine RAG Demo", layout="wide")
st.title("🍷 Wine RAG Demo (via Dify)")

with st.sidebar:
    st.subheader("Settings")
    DIFY_API_BASE = st.text_input("Dify API Base", DIFY_API_BASE)
    WORKFLOW_ID   = st.text_input("Workflow ID", WORKFLOW_ID)
    DIFY_API_KEY  = st.text_input("API Key", DIFY_API_KEY, type="password")
    st.caption("Fill these or set via environment variables.")

query = st.text_input(
    "Ask a question about the wine data:",
    "List 5 wines from Sonoma that mention 'blackberry' in the notes. Return title and designation."
)

col_answer, col_side = st.columns([2, 1])

#Helpers
def run_workflow(q: str):
    """Call Dify workflow in blocking mode and return JSON."""
    url = f"{DIFY_API_BASE}/v1/workflows/{WORKFLOW_ID}/run"
    headers = {"Authorization": f"Bearer {DIFY_API_KEY}", "Content-Type": "application/json"}
    payload = {"inputs": {"query": q}, "response_mode": "blocking", "user": "prof_demo"}
    r = requests.post(url, json=payload, headers=headers, timeout=120)
    r.raise_for_status()
    return r.json()

def pick(obj, *keys, default=None):
    """Return the first present key in obj."""
    for k in keys:
        if isinstance(obj, dict) and k in obj:
            return obj[k]
    return default

def extract_outputs(data_json):
    """
    Robustly get the workflow outputs dict.
    Dify responses often look like: {"data": {"outputs": {...}, "intermediate_steps": [...]}}
    """
    if not isinstance(data_json, dict):
        return {}, []

    data_block = data_json.get("data") or {}
    outputs = data_block.get("outputs") or data_json.get("outputs") or {}
    steps   = data_block.get("intermediate_steps") or data_json.get("intermediate_steps") or []
    return outputs, steps

def extract_chunks(outputs: dict, steps: list):
    """
    Try to collect supporting chunks either from `outputs["evidence"]` 
    or by scan intermediate_steps result.
    """
    # 1) direct evidence array in outputs 
    if isinstance(outputs.get("evidence"), list):
        return outputs["evidence"]

    # 2) get result by the process
    chunks = []
    for s in steps or []:
        ntype = (s.get("node_type") or "").lower()
        if ntype in ("knowledge_retrieval", "knowledge"):
            result = s.get("outputs", {}).get("result", [])
            for it in result:
                chunks.append({
                    "text": it.get("text", ""),
                    "score": it.get("score"),
                    "meta": it.get("metadata", {})
                })
    return chunks

#Run
if st.button("Run"):
    if not (DIFY_API_BASE and WORKFLOW_ID and DIFY_API_KEY):
        st.error("Please provide API base / workflow id / API key.")
    else:
        try:
            with st.spinner("Querying..."):
                data = run_workflow(query)

            # get outputs & steps out
            outputs, steps = extract_outputs(data)
          
            answer  = pick(outputs, "output", "text", default="") 
            explain = pick(outputs, "output2", "reasoning_content", default="")

            # main answer
            with col_answer:
                st.subheader("Answer")
                st.write(answer or "_(No answer text)_")

                # reasoning / citations
                if explain:
                    st.markdown("---")
                    st.subheader("Reasoning / Citations")
                    st.write(explain)

            # get chunks
            chunks = extract_chunks(outputs, steps)
            with col_side:
                st.subheader("Supporting Chunks")
                if not chunks:
                    st.caption("No chunks captured from the workflow output.")
                for i, ch in enumerate(chunks[:8], 1):
                    st.markdown(f"**Chunk {i}**  (score: {ch.get('score')})")
                    text = ch.get("text", "") or ""
                    st.write(text[:500] + ("..." if len(text) > 500 else ""))
                    meta = ch.get("meta", {})
                    if meta:
                        st.caption(str(meta))
                    st.divider()

            # origin JSON
            with st.expander("Raw response (debug)"):
                st.code(json.dumps(data, ensure_ascii=False, indent=2))

        except requests.HTTPError as e:
            st.error(f"HTTPError: {e}\n\n{getattr(e.response, 'text', '')}")
        except Exception as e:
            st.error(f"Error: {e}")
