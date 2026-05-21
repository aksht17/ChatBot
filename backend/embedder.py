import time

from google import genai
from google.genai import errors

from config import EMBED_MODEL, GEMINI_EMBED_API_KEY

client = genai.Client(api_key=GEMINI_EMBED_API_KEY, http_options={"api_version": "v1"})


def embed_texts(texts):
    if not texts:
        return []

    if not GEMINI_EMBED_API_KEY:
        raise ValueError("GEMINI_EMBED_API_KEY is not set.")

    attempts = 0
    delay_seconds = 2
    last_error = None
    while attempts < 4:
        try:
            response = client.models.embed_content(model=EMBED_MODEL, contents=texts)
            return [embedding.values for embedding in response.embeddings]
        except Exception as exc:
            last_error = exc
            status_code = getattr(exc, "status_code", None)
            if status_code != 429 and "RESOURCE_EXHAUSTED" not in str(exc):
                raise
            attempts += 1
            if attempts < 4:
                time.sleep(delay_seconds)
                delay_seconds *= 2

    raise last_error


def embed_text(text):
    return embed_texts([text])[0]