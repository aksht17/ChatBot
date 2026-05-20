# ChatBot
RAG chatbot for placement data with a FastAPI backend and Streamlit frontend.

## Project layout
- backend/ - FastAPI app, ingestion, RAG pipeline
- frontend/ - Streamlit UI
- requirements.txt - Streamlit Cloud dependencies

## Local setup
### Prerequisites
- Python 3.10+
- A Pinecone index that matches `PINECONE_INDEX`

### Install dependencies
From the repo root (the folder that contains `backend/` and `frontend/`):

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

### Configure environment
Create `.env` at the repo root (do not commit it):

```dotenv
GEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key
PINECONE_API_KEY=your_pinecone_key
PINECONE_ENV=us-east-1
PINECONE_INDEX=iitk-placements-3072
```

### Run backend
```bash
cd backend
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Run frontend
Streamlit does not read `.env` automatically. Set `API_BASE_URL` before running:

```powershell
$env:API_BASE_URL = "http://localhost:8000"
streamlit run frontend/app.py
```

## Deploy
### Render (backend)
1) New Web Service -> connect your GitHub repo
2) Root Directory: `backend`
3) Build Command: `pip install -r requirements.txt`
4) Start Command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
5) Add environment variables: `GEMINI_API_KEY`, `GROQ_API_KEY`, `PINECONE_API_KEY`, `PINECONE_ENV`, `PINECONE_INDEX`

### Streamlit Cloud (frontend)
1) New app -> select your GitHub repo
2) Main file: `frontend/app.py`
3) Secrets:

```toml
API_BASE_URL = "https://your-render-service.onrender.com"
```

## Notes
- Rotate any keys that were previously committed.
- Ensure the Pinecone index exists and matches `PINECONE_INDEX`.
