import html
import os

import requests
import streamlit as st

st.set_page_config(
        page_title="IITK Placement Chatbot",
        page_icon="C",
        layout="centered",
)

API_BASE_URL = st.secrets.get(
        "API_BASE_URL",
        os.getenv("API_BASE_URL", "http://localhost:8000"),
)

st.markdown(
        """
<style>
@import url("https://fonts.googleapis.com/css2?family=Sora:wght@400;600&family=Space+Mono:wght@400;700&display=swap");

:root {
    --ink: #0b1220;
    --muted: #667085;
    --panel: #ffffff;
    --border: #e5e7eb;
    --accent: #111827;
    --chip: #eef2ff;
}

html, body, [class*="css"] {
    font-family: "Sora", sans-serif;
    color: var(--ink);
}

.stApp {
    background: #f6f7fb;
}

.app-shell {
    max-width: 900px;
    margin: 0 auto;
    padding: 20px 8px 80px;
}

.app-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 14px;
}

.app-title {
    font-size: 26px;
    font-weight: 600;
    letter-spacing: -0.02em;
}

.app-subtitle {
    font-size: 14px;
    color: var(--muted);
}

.status-chip {
    font-family: "Space Mono", monospace;
    font-size: 12px;
    padding: 6px 10px;
    background: var(--chip);
    color: #3730a3;
    border-radius: 999px;
    border: 1px solid #c7d2fe;
}

.toolbar {
    display: flex;
    align-items: center;
    gap: 14px;
    margin: 12px 0 18px;
}

.tool-hint {
    color: var(--muted);
    font-size: 13px;
}

.mini-uploader [data-testid="stFileUploader"] {
    width: 44px;
}

.mini-uploader [data-testid="stFileUploader"] label {
    display: none;
}

.mini-uploader [data-testid="stFileUploaderDropzone"] {
    border: none;
    padding: 0;
    background: transparent;
}

.mini-uploader [data-testid="stFileUploaderDropzone"] button {
    width: 38px;
    height: 38px;
    border-radius: 12px;
    border: 1px solid var(--border);
    background: #ffffff;
    box-shadow: 0 6px 16px rgba(15, 23, 42, 0.08);
    font-size: 0;
    cursor: pointer;
}

.mini-uploader [data-testid="stFileUploaderDropzone"] button::after {
    content: "+";
    font-size: 20px;
    color: var(--accent);
    line-height: 1;
}

.mini-uploader [data-testid="stFileUploaderDropzone"] small,
.mini-uploader [data-testid="stFileUploaderDropzone"] span {
    display: none !important;
}

.empty-state {
    text-align: center;
    padding: 40px 16px;
    border-radius: 18px;
    border: 1px dashed var(--border);
    background: rgba(255, 255, 255, 0.7);
    color: var(--muted);
}

.reply-bar {
    background: #eef2ff;
    border: 1px solid #c7d2fe;
    padding: 8px 12px;
    border-radius: 12px;
    font-size: 13px;
    color: #3730a3;
}

.reply-action button {
    background: transparent !important;
    border: none !important;
    color: #2563eb !important;
    font-size: 12px !important;
    padding: 2px 0 !important;
}

div[data-testid="stChatMessage"] {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 12px 16px;
    box-shadow: 0 10px 20px rgba(15, 23, 42, 0.06);
}

div[data-testid="stChatInput"] textarea {
    border-radius: 18px !important;
    border: 1px solid var(--border) !important;
}

div[data-testid="stChatInput"] {
    position: sticky;
    bottom: 0;
    background: #f6f7fb;
    padding-top: 8px;
}
</style>
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

if "messages" not in st.session_state:
    st.session_state.messages = []

if "reply_context" not in st.session_state:
    st.session_state.reply_context = None

if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = set()

if "last_upload_note" not in st.session_state:
    st.session_state.last_upload_note = ""

st.markdown('<div class="app-shell">', unsafe_allow_html=True)
st.markdown(
    f"""
<div class="app-header">
  <div>
    <div class="app-title">IITK Placement Chatbot</div>
    <div class="app-subtitle">Chat with your placement data. Add files or URLs for extra context.</div>
  </div>
  <div class="status-chip">Backend: {html.escape(API_BASE_URL)}</div>
</div>
""",
    unsafe_allow_html=True,
)

toolbar_col, hint_col = st.columns([0.12, 0.88], vertical_alignment="center")
with toolbar_col:
    st.markdown('<div class="mini-uploader">', unsafe_allow_html=True)
    files = st.file_uploader(
        "",
        accept_multiple_files=True,
        key="file_uploader",
        label_visibility="collapsed",
    )
    st.markdown("</div>", unsafe_allow_html=True)

with hint_col:
    st.markdown(
        '<div class="tool-hint">Use the + button to add files for ingestion.</div>',
        unsafe_allow_html=True,
    )
    if st.session_state.last_upload_note:
        st.caption(st.session_state.last_upload_note)

if files:
    new_files = [f for f in files if f.name not in st.session_state.uploaded_files]
    if new_files:
        with st.spinner("Ingesting files..."):
            uploaded_names = []
            for f in new_files:
                result = post_json_request("/upload", files={"file": (f.name, f.getvalue())})
                if result is not None:
                    uploaded_names.append(f.name)
            if uploaded_names:
                st.session_state.uploaded_files.update(uploaded_names)
                st.session_state.last_upload_note = f"Uploaded {len(uploaded_names)} file(s)."

with st.expander("Add URL", expanded=False):
    url = st.text_input("URL", placeholder="https://example.com", label_visibility="collapsed")
    if url and st.button("Ingest URL", key="ingest_url"):
        result = post_json_request("/upload-url", json={"url": url})
        if result:
            st.session_state.last_upload_note = "URL ingested successfully."

if not st.session_state.messages:
    st.markdown(
        '<div class="empty-state">Ask a question to start the conversation.</div>',
        unsafe_allow_html=True,
    )

for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.write(message["content"])
        st.markdown('<div class="reply-action">', unsafe_allow_html=True)
        if st.button("Reply", key=f"reply_{idx}"):
            st.session_state.reply_context = message["content"]
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

if st.session_state.reply_context:
    reply_col, clear_col = st.columns([0.85, 0.15])
    with reply_col:
        reply_text = html.escape(st.session_state.reply_context)
        st.markdown(
            f'<div class="reply-bar">Replying to: {reply_text}</div>',
            unsafe_allow_html=True,
        )
    with clear_col:
        if st.button("Clear", key="clear_reply"):
            st.session_state.reply_context = None
            st.rerun()

prompt = st.chat_input("Message")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    question = prompt
    if st.session_state.reply_context:
        question = (
            "Use the following context when replying.\n\n"
            f"Context: {st.session_state.reply_context}\n\n"
            f"User: {prompt}"
        )

    result = post_json_request("/chat", json={"question": question})
    if result is None:
        answer_text = "Sorry, I could not reach the backend."
    else:
        answer_text = result.get("answer", result)
        if not isinstance(answer_text, str):
            answer_text = str(answer_text)

    st.session_state.messages.append({"role": "assistant", "content": answer_text})
    st.session_state.reply_context = None
    st.rerun()

st.markdown("</div>", unsafe_allow_html=True)
