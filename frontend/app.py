import os

import requests
import streamlit as st

st.set_page_config(
        page_title="IITK Placement RAG Chatbot",
        page_icon="C",
        layout="wide",
)

API_BASE_URL = st.secrets.get(
    "API_BASE_URL",
    os.getenv("API_BASE_URL", "http://localhost:8000"),
)

st.markdown(
        """
<style>
@import url("https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=JetBrains+Mono:wght@400;500&display=swap");

:root {
    --ink: #0f172a;
    --muted: #475569;
    --card: #ffffff;
    --border: #e2e8f0;
    --shadow: 0 18px 45px rgba(15, 23, 42, 0.12);
}

html, body, [class*="css"] {
    font-family: "Space Grotesk", sans-serif;
    color: var(--ink);
}

.stApp {
    background: radial-gradient(circle at 10% 20%, #fff7ed 0%, transparent 40%),
        radial-gradient(circle at 90% 10%, #e0f2fe 0%, transparent 35%),
        linear-gradient(135deg, #f8fafc 0%, #ecfeff 45%, #fef9c3 100%);
}

.hero {
    background: linear-gradient(120deg, rgba(255, 255, 255, 0.95), rgba(236, 254, 255, 0.9));
    border: 1px solid var(--border);
    border-radius: 28px;
    padding: 28px 32px;
    box-shadow: var(--shadow);
    position: relative;
    overflow: hidden;
    animation: rise 0.7s ease both;
}

.hero::after {
    content: "";
    position: absolute;
    width: 220px;
    height: 220px;
    background: radial-gradient(circle, rgba(251, 146, 60, 0.35), transparent 70%);
    top: -40px;
    right: -40px;
    animation: float 8s ease-in-out infinite;
}

.badge-row {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-bottom: 12px;
}

.badge {
    font-family: "JetBrains Mono", monospace;
    font-size: 12px;
    letter-spacing: 0.02em;
    text-transform: uppercase;
    padding: 6px 10px;
    border-radius: 999px;
    border: 1px solid var(--border);
    background: #ffffff;
}

.main-title {
    font-size: 40px;
    font-weight: 700;
    letter-spacing: -0.02em;
}

.subtitle {
    color: var(--muted);
    font-size: 16px;
    margin-top: 6px;
}

.section-title {
    font-size: 20px;
    font-weight: 600;
    margin: 24px 0 12px 0;
}

.card {
    background: rgba(255, 255, 255, 0.92);
    border-radius: 22px;
    padding: 20px 22px;
    border: 1px solid var(--border);
    box-shadow: 0 14px 35px rgba(15, 23, 42, 0.08);
    animation: rise 0.6s ease both;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.card:hover {
    transform: translateY(-4px);
    box-shadow: 0 18px 35px rgba(15, 23, 42, 0.14);
}

.card-title {
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 6px;
}

.card-note {
    color: var(--muted);
    font-size: 14px;
    margin-bottom: 12px;
}

.card-orange {
    border-left: 6px solid #f97316;
}

.card-blue {
    border-left: 6px solid #0ea5e9;
}

.card-green {
    border-left: 6px solid #22c55e;
}

.answer-box {
    margin-top: 14px;
    padding: 16px;
    border-radius: 16px;
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
}

div[data-testid="stTextInput"] input,
div[data-testid="stFileUploader"] section {
    border-radius: 12px !important;
    border: 1px solid var(--border) !important;
    background: #ffffff !important;
}

div.stButton > button {
    border-radius: 12px;
    border: 0;
    padding: 10px 18px;
    background: linear-gradient(120deg, #f97316, #fb7185);
    color: #ffffff;
    font-weight: 600;
    box-shadow: 0 10px 24px rgba(249, 115, 22, 0.35);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

div.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 14px 28px rgba(249, 115, 22, 0.45);
}

@keyframes float {
    0% { transform: translate(0, 0); }
    50% { transform: translate(-8px, 10px); }
    100% { transform: translate(0, 0); }
}

@keyframes rise {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>
""",
        unsafe_allow_html=True,
)

st.markdown(
        """
<div class="hero">
    <div class="badge-row">
        <span class="badge">FastAPI</span>
        <span class="badge">Streamlit</span>
        <span class="badge">RAG Pipeline</span>
        <span class="badge">Gemini Embeddings</span>
        <span class="badge">Groq LLM</span>
    </div>
    <div class="main-title">IITK Placement RAG Chatbot</div>
    <div class="subtitle">Upload files, ingest URLs, and ask questions about placement data.</div>
</div>
""",
        unsafe_allow_html=True,
)


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

st.markdown('<div class="section-title">Data intake</div>', unsafe_allow_html=True)
upload_col, url_col = st.columns(2, gap="large")

with upload_col:
    st.markdown('<div class="card card-orange">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Upload documents</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="card-note">PDF, DOCX, PPTX, spreadsheets, and text files are supported.</div>',
        unsafe_allow_html=True,
    )
    files = st.file_uploader("Choose files", accept_multiple_files=True)
    if files and st.button("Upload files", key="upload_btn"):
        for f in files:
            post_json_request("/upload", files={"file": (f.name, f.getvalue())})
        st.success("Uploaded!")
    st.markdown("</div>", unsafe_allow_html=True)

with url_col:
    st.markdown('<div class="card card-blue">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Ingest a URL</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="card-note">Paste a public page or direct file link to ingest content.</div>',
        unsafe_allow_html=True,
    )
    url = st.text_input("Enter a URL", placeholder="https://example.com/data")
    if url and st.button("Ingest URL", key="ingest_btn"):
        result = post_json_request("/upload-url", json={"url": url})
        if result:
            st.write(result)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="section-title">Ask the chatbot</div>', unsafe_allow_html=True)
st.markdown('<div class="card card-green">', unsafe_allow_html=True)
st.markdown(
    '<div class="card-note">Ask about placement stats, companies, or summaries.</div>',
    unsafe_allow_html=True,
)
q = st.text_input("Ask a question", placeholder="Example: Which companies hired the most students?")
if q:
    result = post_json_request("/chat", json={"question": q})
    if result:
        st.markdown('<div class="answer-box">', unsafe_allow_html=True)
        st.write(result.get("answer", result))
        st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)
