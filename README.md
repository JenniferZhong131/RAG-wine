# Wine RAG (Dify)

This repository contains a Dify-based Retrieval-Augmented Generation (RAG) app for wine reviews.

## Quick Demo (Local)
1. Start Dify (Docker) on your machine.
2. Import the workflow (`workflow/rag_workflow.json`) into Dify (or open the existing app).
3. Upload the knowledge: CSV files with a single `text` column (`part_aa_desc.csv` ... `part_ad_desc.csv`).
4. Retrieval settings: Hybrid, weight 0.7/0.3, TopK=10, Score=0.1 (see `workflow/kb_settings.md`).
5. Run the small Streamlit app:
   ```bash
   pip install streamlit requests
   cp .env.example .env  # fill in DIFY_API_KEY & WORKFLOW_ID, or export vars manually
   streamlit run app/streamlit_app.py
