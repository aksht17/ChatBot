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
@import url("https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700&family=Space+Mono:wght@400;700&display=swap");

:root {
    --ink: #0b1220;
    --muted: #5b6473;
    --panel: #ffffff;
    --border: #e7e9ef;
    --accent: #0f172a;
    --brand: #f7a928;
    --brand-2: #ffd27a;
    --chat-bg: #f2f4fb;
}

html, body, [class*="css"] {
    font-family: "Manrope", sans-serif;
    color: var(--ink);
}

.stApp {
    background: radial-gradient(circle at 15% 15%, #eef2ff 0%, transparent 35%),
        radial-gradient(circle at 85% 10%, #ffe8c7 0%, transparent 40%),
        #f5f6fb;
}

.app-shell {
    max-width: 680px;
    margin: 0 auto;
    padding: 24px 12px 64px;
}

.chat-panel {
    background: var(--panel);
    border-radius: 28px;
    border: 1px solid var(--border);
    box-shadow: 0 20px 40px rgba(15, 23, 42, 0.1);
    overflow: hidden;
}

.chat-header {
    background: linear-gradient(135deg, var(--brand), var(--brand-2));
    padding: 18px 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
}

.header-left {
    display: flex;
    align-items: center;
    gap: 12px;
}

.avatar {
    width: 46px;
    height: 46px;
    border-radius: 50%;
    background: #ffffff;
    display: grid;
    place-items: center;
    font-weight: 700;
    color: #111827;
    border: 2px solid rgba(255, 255, 255, 0.7);
}

.header-title {
    font-size: 18px;
    font-weight: 700;
}

.header-status {
    font-size: 12px;
    color: #1f2937;
    display: flex;
    align-items: center;
    gap: 6px;
}

.status-dot {
    width: 8px;
    height: 8px;
    background: #22c55e;
    border-radius: 50%;
}

.header-action {
    width: 36px;
    height: 36px;
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.7);
    display: grid;
    place-items: center;
    font-size: 16px;
}

.chat-body {
    padding: 20px;
    min-height: 340px;
    background: #ffffff;
}

.reply-bar {
    background: #eef2ff;
    border: 1px solid #c7d2fe;
    padding: 8px 12px;
    border-radius: 12px;
    font-size: 13px;
    color: #3730a3;
    margin-bottom: 12px;
}

.reply-action button {
    background: transparent !important;
    border: none !important;
    color: #2563eb !important;
    font-size: 12px !important;
    padding: 2px 0 !important;
}

div[data-testid="stChatMessage"] {
    background: var(--chat-bg);
    border: 1px solid #e6e8f2;
    border-radius: 16px;
    padding: 10px 14px;
    margin-bottom: 10px;
}

div[data-testid="stChatMessage"] p {
    margin: 0;
}

.empty-state {
    text-align: center;
    padding: 40px 16px;
    border-radius: 18px;
    border: 1px dashed var(--border);
    background: #f9fafb;
    color: var(--muted);
}

.input-actions {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 16px 6px;
    border-top: 1px solid var(--border);
    border-bottom: 0;
    background: #ffffff;
    border-radius: 16px 16px 0 0;
}

.tool-hint {
    color: var(--muted);
    font-size: 12px;
}

button[data-testid="stPopoverButton"] {
    width: 34px !important;
    height: 34px !important;
    border-radius: 10px !important;
    border: 1px solid var(--border) !important;
    background: #ffffff !important;
    font-size: 18px !important;
    color: var(--accent) !important;
    box-shadow: 0 6px 16px rgba(15, 23, 42, 0.08) !important;
}

div[data-testid="stPopoverContent"] {
    padding: 12px !important;
    border-radius: 12px !important;
}

.footer-actions {
    display: flex;
    justify-content: center;
    gap: 40px;
    padding: 14px 0 10px;
    color: var(--muted);
    font-size: 13px;
}

div[data-testid="stChatInput"] textarea {
    border-radius: 0 0 16px 16px !important;
    border: 1px solid var(--border) !important;
    border-top: 0 !important;
    background: #ffffff !important;
}

div[data-testid="stChatInput"] {
    background: #ffffff;
    border-top: 0;
    padding-top: 0;
    margin-top: -6px;
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
    """
<div class="chat-panel">
  <div class="chat-header">
    <div class="header-left">
      <div class="avatar">AI</div>
      <div>
        <div class="header-title">Placement AI Agent</div>
        <div class="header-status"><span class="status-dot"></span>24/7 Online</div>
      </div>
    </div>
    <div class="header-action">&#x21bb;</div>
  </div>
  <div class="chat-body">
""",
    unsafe_allow_html=True,
)

if st.session_state.reply_context:
    reply_text = html.escape(st.session_state.reply_context)
    st.markdown(
        f'<div class="reply-bar">Replying to: {reply_text}</div>',
        unsafe_allow_html=True,
    )

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

st.markdown(
    """
  </div>
  <div class="input-actions">
""",
    unsafe_allow_html=True,
)

action_col, hint_col = st.columns([0.12, 0.88], vertical_alignment="center")
with action_col:
    with st.popover("+"):
        files = st.file_uploader(
            "Upload files",
            accept_multiple_files=True,
            key="file_uploader",
        )
        url = st.text_input("Add URL", placeholder="https://example.com")
        if url and st.button("Ingest URL", key="ingest_url"):
            result = post_json_request("/upload-url", json={"url": url})
            if result:
                st.session_state.last_upload_note = "URL ingested successfully."

with hint_col:
    st.markdown(
        '<div class="tool-hint">Attach files or a link to add more context.</div>',
        unsafe_allow_html=True,
    )
    if st.session_state.last_upload_note:
        st.caption(st.session_state.last_upload_note)

st.markdown("</div>", unsafe_allow_html=True)

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

if st.session_state.reply_context and st.button("Clear reply", key="clear_reply"):
    st.session_state.reply_context = None
    st.rerun()

st.markdown(
    """
</div>
<div class="footer-actions">
  <span>Voice Chat</span>
  <span>History</span>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown("</div>", unsafe_allow_html=True)
