from google import genai

from config import GEMINI_API_KEY, EMBED_MODEL

client = genai.Client(api_key=GEMINI_API_KEY,http_options={"api_version": "v1"})


def embed_texts(texts):
    if not texts:
        return []
    response = client.models.embed_content(model=EMBED_MODEL, contents=texts)
    return [embedding.values for embedding in response.embeddings]


def embed_text(text):
    return embed_texts([text])[0]