import hashlib

from pinecone import Pinecone, ServerlessSpec
from config import EMBED_DIMENSION, PINECONE_API_KEY, PINECONE_ENV, PINECONE_INDEX

pinecone_client = Pinecone(api_key=PINECONE_API_KEY)

def _extract_dimension(index_details):
    if isinstance(index_details, dict):
        return index_details.get("dimension")
    return getattr(index_details, "dimension", None)


def get_index():
    existing_names = [i.name for i in pinecone_client.list_indexes()]
    if PINECONE_INDEX not in existing_names:
        pinecone_client.create_index(
            name=PINECONE_INDEX,
            dimension=EMBED_DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region=PINECONE_ENV),
        )
    else:
        try:
            details = pinecone_client.describe_index(PINECONE_INDEX)
            index_dim = _extract_dimension(details)
        except Exception:
            index_dim = None
        if index_dim and index_dim != EMBED_DIMENSION:
            raise ValueError(
                "Pinecone index dimension does not match EMBED_DIMENSION. "
                f"Index: {index_dim}, EMBED_DIMENSION: {EMBED_DIMENSION}. "
                "Create a new index or change PINECONE_INDEX."
            )
    return pinecone_client.Index(PINECONE_INDEX)

def upsert(docs_with_embeddings):
    pinecone_index = get_index()
    upsert_vectors = []
    for doc, embedding in docs_with_embeddings:
        vector_hash = hashlib.sha256(
            f"{doc['source']}:{doc['content']}".encode("utf-8", errors="ignore")
        ).hexdigest()
        upsert_vectors.append(
            (vector_hash, embedding, {"text": doc["content"][:1000], "source": doc["source"]})
        )
    pinecone_index.upsert(vectors=upsert_vectors)

def query(embedding, k=5):
    pinecone_index = get_index()
    return pinecone_index.query(vector=embedding, top_k=k, include_metadata=True)
