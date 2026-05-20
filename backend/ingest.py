import os
from pathlib import Path
from urllib.parse import urlparse

import requests

import config as cfg
from content_extractors import extract_from_bytes
from drive_loader import load_drive_public
from embedder import embed_texts
from ingest_cache import IngestCache
from scraper import scrape_url
from vectorstore import upsert


BACKEND_DIR = Path(__file__).resolve().parent


def _estimate_token_count(text):
    # Approximate tokens (Gemini/LLM style) as ~4 chars per token.
    return max(1, len(text) // 4)


def chunk_text(text, max_tokens=800, overlap_tokens=80):
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

        if not current and word_tokens > max_tokens:
            chunks.append(word)

    if current:
        chunk = " ".join(current).strip()
        if chunk:
            chunks.append(chunk)

    return chunks


def _is_placeholder(value):
    return not value or "PASTE_" in value or "example.com" in value


def _source_setting(source, key, default):
    return source.get(key, default)


def _source_enabled(source):
    enabled = source.get("enabled", True)
    if isinstance(enabled, str):
        return enabled.strip().lower() not in {"false", "no", "0", "off"}
    return bool(enabled)


def _batches(items, size):
    for start in range(0, len(items), size):
        yield start, items[start:start + size]


def _extract_kwargs(source):
    return {
        "follow_links_depth": _source_setting(source, "depth", cfg.LINK_FOLLOW_DEPTH),
        "follow_urls_in_text": _source_setting(source, "follow_urls_in_text", cfg.FOLLOW_URLS_IN_TEXT),
        "max_urls": _source_setting(source, "max_urls", cfg.MAX_URLS_PER_DOC),
        "enable_ocr": _source_setting(source, "enable_ocr", cfg.ENABLE_OCR),
        "enable_audio_video": _source_setting(source, "enable_audio_video", cfg.ENABLE_AUDIO_VIDEO),
        "whisper_model": _source_setting(source, "whisper_model", cfg.WHISPER_MODEL),
        "whisper_device": _source_setting(source, "whisper_device", cfg.WHISPER_DEVICE),
        "whisper_compute_type": _source_setting(source, "whisper_compute_type", cfg.WHISPER_COMPUTE_TYPE),
        "archive_depth": _source_setting(source, "archive_depth", cfg.ARCHIVE_DEPTH),
    }


def _resolve_local_path(path_value):
    path = Path(path_value)
    if not path.is_absolute():
        path = BACKEND_DIR / path
    return path


def _documents_from_local_file(path, source, extract_kwargs):
    with open(path, "rb") as handle:
        content = handle.read()

    documents = extract_from_bytes(path.name, content, **extract_kwargs)
    for document in documents:
        # Keep URLs for linked files such as resume PDFs. Plain rows extracted
        # from the local CSV/Excel file get the local file as their source.
        if document.get("source", "").startswith("file:"):
            document["source"] = f"{source}:{path}"
    return documents


def _load_local_path(source):
    path_value = source.get("path", "")
    if _is_placeholder(path_value):
        return []

    path = _resolve_local_path(path_value)
    if not path.exists():
        print(f"Local path not found: {path}")
        return []

    extract_kwargs = _extract_kwargs(source)
    documents = []
    if path.is_file():
        return _documents_from_local_file(path, "local", extract_kwargs)

    for root, _, files in os.walk(path):
        for name in files:
            file_path = Path(root) / name
            documents += _documents_from_local_file(file_path, "local", extract_kwargs)
    return documents


def _load_website(source):
    url = source.get("url", "")
    if _is_placeholder(url):
        return []
    depth = _source_setting(source, "depth", cfg.LINK_FOLLOW_DEPTH)
    return scrape_url(url, depth=depth)


def _load_google_drive(source):
    url = source.get("url", "")
    if _is_placeholder(url):
        return []
    return load_drive_public(url, **_extract_kwargs(source))


def _load_web_file(source):
    url = source.get("url", "")
    if _is_placeholder(url):
        return []

    response = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    parsed = urlparse(url)
    name = os.path.basename(parsed.path) or "downloaded_file"
    return extract_from_bytes(name, response.content, **_extract_kwargs(source))


def _load_source_documents(source):
    source_type = source.get("type")
    if not _source_enabled(source):
        print(f"Skipping disabled source: {source_type}")
        return []

    loaders = {
        "local_path": _load_local_path,
        "local_excel": _load_local_path,
        "website": _load_website,
        "google_drive": _load_google_drive,
        "web_file": _load_web_file,
    }
    loader = loaders.get(source_type)
    if not loader:
        print(f"Skipping unknown source type: {source_type}")
        return []

    print(f"Loading {source_type}: {source.get('path') or source.get('url')}")
    documents = loader(source)
    print(f"{source_type} documents: {len(documents)}")
    return documents


def _configured_sources():
    sources = getattr(cfg, "DATA_SOURCES", [])
    if sources:
        return sources

    return [
        {"type": "website", "url": getattr(cfg, "IITK_PLACEMENT_URL", "")},
        {"type": "local_path", "path": getattr(cfg, "STUDENT_EXCEL_PATH", "")},
        {"type": "google_drive", "url": getattr(cfg, "GOOGLE_DRIVE_FOLDER_URL", "")},
    ]


def main():
    documents = []
    print(f"Config file: {cfg.__file__}")

    for source in _configured_sources():
        documents += _load_source_documents(source)

    if not documents:
        print("No documents found for ingestion.")
        return

    chunks = []
    max_tokens = max(1, int(cfg.CHUNK_TOKENS))
    overlap_tokens = max(0, int(cfg.CHUNK_OVERLAP_TOKENS))
    for document in documents:
        for content_chunk in chunk_text(
            document["content"],
            max_tokens=max_tokens,
            overlap_tokens=overlap_tokens,
        ):
            if content_chunk.strip():
                chunks.append({"source": document["source"], "content": content_chunk})

    cache = IngestCache(cfg.CACHE_DIR) if cfg.ENABLE_CACHE else None
    if cache:
        chunks_with_hashes = []
        for chunk in chunks:
            chunk_hash = cache.hash_text(chunk["content"])
            if cache.has_chunk(chunk_hash):
                continue
            chunks_with_hashes.append((chunk, chunk_hash))
        if not chunks_with_hashes:
            print("All chunks already cached. Nothing to embed.")
            return
    else:
        chunks_with_hashes = [(chunk, None) for chunk in chunks]

    print(f"Embedding {len(chunks_with_hashes)} chunks...")
    batch_size = max(1, cfg.EMBED_BATCH_SIZE)
    for start, batch in _batches(chunks_with_hashes, batch_size):
        batch_chunks = [item[0] for item in batch]
        texts = [item["content"] for item in batch_chunks]
        embeddings = embed_texts(texts)
        upsert(list(zip(batch_chunks, embeddings)))
        if cache:
            cache.add_chunk_hashes([item[1] for item in batch if item[1]])
        print(
            f"Embedded and uploaded {start + len(batch)} / {len(chunks_with_hashes)} chunks"
        )
    print("Done")


if __name__ == "__main__":
    main()
