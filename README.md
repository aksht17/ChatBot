# ChatBot
RAG chatbot for placement data with a FastAPI backend and a static web frontend.

## Project layout
- backend/ - FastAPI app, ingestion, RAG pipeline
- web/ - static frontend for Vercel

## Local setup
### Prerequisites
- Python 3.10+
- A Pinecone index that matches `PINECONE_INDEX`

### Install dependencies
From the repo root (the folder that contains `backend/` and `web/`):

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

### Configure environment
Create `.env` at the repo root (do not commit it):

```dotenv
GEMINI_EMBED_API_KEY=your_gemini_embedding_key
GEMINI_LLM_API_KEY=your_gemini_llm_key
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
Serve the static site and point it at your backend:

1) Update `web/config.js` with your backend URL.
2) Serve the `web/` folder (any static server works).

Example:
```bash
cd web
python -m http.server 5173
```

## Deploy
### Render (backend)
1) New Web Service -> connect your GitHub repo
2) Root Directory: `backend`
3) Build Command: `pip install -r requirements.txt`
4) Start Command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
5) Add environment variables: `GEMINI_EMBED_API_KEY`, `GEMINI_LLM_API_KEY`, `PINECONE_API_KEY`, `PINECONE_ENV`, `PINECONE_INDEX`

### Vercel (frontend)
This repo includes a static frontend in `web/` for Vercel deployment.

1) In Vercel, import the GitHub repo
2) Framework Preset: **Other**
3) Root Directory: `web`
4) Build Command: (leave empty)
5) Output Directory: `.`

Update the backend URL in [web/config.js](web/config.js) before deploying:

```js
window.APP_CONFIG = {
	API_BASE_URL: "https://your-render-service.onrender.com"
};
```


## Notes
- Rotate any keys that were previously committed.
- Ensure the Pinecone index exists and matches `PINECONE_INDEX`.
