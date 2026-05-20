import os

import requests
import streamlit as st

API_BASE_URL = st.secrets.get(
    "API_BASE_URL",
    os.getenv("API_BASE_URL", "http://localhost:8000"),
)
st.title("IITK Placement RAG Chatbot")


def post_json_request(path, **kwargs):
    try:
        response = requests.post(f"{API_BASE_URL}{path}", timeout=120, **kwargs)
    except requests.RequestException as exc:
        st.error(f"Backend is not reachable: {exc}")
        return None

    if not response.ok:
        st.error(f"Backend returned {response.status_code}")
        st.code(response.text[:2000])
        return None

    try:
        return response.json()
    except ValueError:
        st.error("Backend did not return JSON.")
        st.code(response.text[:2000])
        return None

files = st.file_uploader("Upload files", accept_multiple_files=True)
if files and st.button("Upload"):
    for f in files:
        post_json_request("/upload", files={"file": (f.name, f.getvalue())})
    st.success("Uploaded!")

url = st.text_input("Ingest a URL")
if url and st.button("Ingest URL"):
    result = post_json_request("/upload-url", json={"url": url})
    if result:
        st.write(result)

q = st.text_input("Ask a question:")
if q:
    result = post_json_request("/chat", json={"question": q})
    if result:
        st.write(result.get("answer", result))
