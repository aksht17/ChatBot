from google import genai
from google.genai import types

from vectorstore import query
from config import (
    EMBED_DIMENSION,
    EMBED_MODEL,
    GEMINI_LLM_API_KEY,
    LLM_MODEL,
    RAG_TOP_K,
    SYSTEM_PROMPT,
)

embedding_client = genai.Client(api_key=GEMINI_LLM_API_KEY, http_options={"api_version": "v1"})


def embed_query(text):
    if not GEMINI_LLM_API_KEY:
        raise ValueError("GEMINI_LLM_API_KEY is not set.")

    response = embedding_client.models.embed_content(
        model=EMBED_MODEL,
        contents=[text],
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=EMBED_DIMENSION,
        ),
    )
    return response.embeddings[0].values


def ask(question):
    query_embedding = embed_query(question)
    search_results = query(query_embedding, k=max(1, int(RAG_TOP_K)))
    matches = (
        search_results.get("matches", [])
        if isinstance(search_results, dict)
        else search_results.matches
    )
    context_snippets = []
    for match in matches:
        metadata = match.get("metadata", {}) if isinstance(match, dict) else match.metadata
        text = metadata.get("text", "")
        if text:
            context_snippets.append(text)

    if not context_snippets:
        return "I could not find relevant ingested context for that question."

    context = "\n\n".join(context_snippets)
    system_prompt = (SYSTEM_PROMPT or "").strip()
    user_prompt = f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"

    if not GEMINI_LLM_API_KEY:
        raise ValueError("GEMINI_LLM_API_KEY is not set.")

    response = embedding_client.models.generate_content(
        model=LLM_MODEL,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt or None,
            temperature=0.2,
        ),
    )
    return (response.text or "").strip()
