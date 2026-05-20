from fastapi import FastAPI, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import config as cfg
from content_extractors import AUDIO_VIDEO_EXTENSIONS, IMAGE_EXTENSIONS, extract_from_bytes
from embedder import embed_texts
from rag_chain import ask
from scraper import scrape_url
from vectorstore import upsert
import requests

app = FastAPI()

class Query(BaseModel):
    question: str


class UrlIn(BaseModel):
    url: str

@app.post("/chat")
def chat(q: Query):
    try:
        return {"answer": ask(q.question)}
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(exc)},
        )

def chunk_text(text, max_tokens, overlap_tokens):
    if not text:
        return []

    words = text.split()
    if not words:
        return []

    chunks = []
    current = []
    current_tokens = 0

    for word in words:
        word_tokens = max(1, len(word) // 4)
        if current and current_tokens + word_tokens > max_tokens:
            chunk = " ".join(current).strip()
            if chunk:
                chunks.append(chunk)

            if overlap_tokens > 0:
                overlap = []
                overlap_count = 0
                for w in reversed(current):
                    t = max(1, len(w) // 4)
                    if overlap_count + t > overlap_tokens:
                        break
                    overlap.append(w)
                    overlap_count += t
                current = list(reversed(overlap))
                current_tokens = overlap_count
            else:
                current = []
                current_tokens = 0

        current.append(word)
        current_tokens += word_tokens

    if current:
        chunk = " ".join(current).strip()
        if chunk:
            chunks.append(chunk)

    return chunks


def _batch_items(items, size):
    for start in range(0, len(items), size):
        yield items[start:start + size]


def _ingest_documents(documents):
    if not documents:
        return 0
    chunks = []
    max_tokens = max(1, int(cfg.CHUNK_TOKENS))
    overlap_tokens = max(0, int(cfg.CHUNK_OVERLAP_TOKENS))
    for document in documents:
        for chunk in chunk_text(document["content"], max_tokens, overlap_tokens):
            if chunk.strip():
                chunks.append({"source": document["source"], "content": chunk})
    if not chunks:
        return 0
    batch_size = max(1, int(cfg.EMBED_BATCH_SIZE))
    embedded_count = 0
    for batch in _batch_items(chunks, batch_size):
        texts = [item["content"] for item in batch]
        embeddings = embed_texts(texts)
        upsert(list(zip(batch, embeddings)))
        embedded_count += len(batch)
    return embedded_count


def _looks_like_file(url):
    base = url.split("?")[0].lower()
    return base.endswith(
        (
            ".pdf",
            ".docx",
            ".pptx",
            ".xlsx",
            ".xls",
            ".csv",
            ".zip",
            ".txt",
            ".md",
            ".json",
            ".html",
            ".htm",
        )
        + IMAGE_EXTENSIONS
        + AUDIO_VIDEO_EXTENSIONS
    )


@app.post("/upload")
async def upload(file: UploadFile):
    content = await file.read()
    documents = extract_from_bytes(
        file.filename,
        content,
        follow_links_depth=cfg.LINK_FOLLOW_DEPTH,
        follow_urls_in_text=cfg.FOLLOW_URLS_IN_TEXT,
        max_urls=cfg.MAX_URLS_PER_DOC,
        enable_ocr=cfg.ENABLE_OCR,
        enable_audio_video=cfg.ENABLE_AUDIO_VIDEO,
        whisper_model=cfg.WHISPER_MODEL,
        whisper_device=cfg.WHISPER_DEVICE,
        whisper_compute_type=cfg.WHISPER_COMPUTE_TYPE,
        archive_depth=cfg.ARCHIVE_DEPTH,
    )

    if not documents:
        return {"status": "no_content", "message": "No text extracted."}
    chunk_count = _ingest_documents(documents)
    return {"status": "uploaded", "chunks": chunk_count}


@app.post("/upload-url")
def upload_url(payload: UrlIn):
    url = payload.url.strip()
    if not url:
        return {"status": "error", "message": "URL is required."}

    if _looks_like_file(url):
        try:
            resp = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
        except Exception as exc:
            return {"status": "error", "message": f"Failed to fetch URL: {exc}"}

        name = url.split("?")[0].split("/")[-1] or "downloaded-file"
        documents = extract_from_bytes(
            name,
            resp.content,
            follow_links_depth=cfg.LINK_FOLLOW_DEPTH,
            follow_urls_in_text=cfg.FOLLOW_URLS_IN_TEXT,
            max_urls=cfg.MAX_URLS_PER_DOC,
            enable_ocr=cfg.ENABLE_OCR,
            enable_audio_video=cfg.ENABLE_AUDIO_VIDEO,
            whisper_model=cfg.WHISPER_MODEL,
            whisper_device=cfg.WHISPER_DEVICE,
            whisper_compute_type=cfg.WHISPER_COMPUTE_TYPE,
            archive_depth=cfg.ARCHIVE_DEPTH,
        )
    else:
        documents = scrape_url(url, depth=cfg.LINK_FOLLOW_DEPTH)

    if not documents:
        return {"status": "no_content", "message": "No text extracted."}

    chunk_count = _ingest_documents(documents)
    return {"status": "uploaded", "chunks": chunk_count}
