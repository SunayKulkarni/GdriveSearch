import html
import os
from datetime import datetime
from uuid import uuid4

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(
    page_title="Drive Agent",
    layout="wide",
    page_icon="🗂️",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [class*="st-"], .stApp {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: #f8f9fc;
}

.block-container {
    padding: 2rem 2rem 4rem 2rem !important;
    max-width: 900px !important;
}

/* ── Header ── */
.agent-header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 20px 24px;
    background: #ffffff;
    border: 1px solid #e8eaf0;
    border-radius: 16px;
    margin-bottom: 24px;
}
.agent-icon {
    width: 48px; height: 48px;
    background: #1a56db;
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 22px;
    flex-shrink: 0;
}
.agent-title { font-size: 1.2rem; font-weight: 600; color: #111827; }
.agent-sub { font-size: 0.85rem; color: #6b7280; margin-top: 2px; }
.agent-badge {
    margin-left: auto;
    background: #ecfdf5;
    color: #065f46;
    font-size: 0.75rem;
    font-weight: 500;
    padding: 4px 10px;
    border-radius: 999px;
    border: 1px solid #a7f3d0;
}

/* ── Chat bubbles ── */
.chat-row {
    display: flex;
    margin-bottom: 16px;
    align-items: flex-end;
    gap: 10px;
}
.chat-row.user { flex-direction: row-reverse; }

.avatar {
    width: 32px; height: 32px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 14px; font-weight: 600;
    flex-shrink: 0;
}
.avatar.user-av { background: #1a56db; color: #fff; }
.avatar.bot-av  { background: #f3f4f6; color: #374151; border: 1px solid #e5e7eb; }

.bubble {
    padding: 12px 16px;
    border-radius: 16px;
    max-width: 75%;
    font-size: 0.93rem;
    line-height: 1.6;
}
.bubble.user {
    background: #1a56db;
    color: #ffffff;
    border-bottom-right-radius: 4px;
}
.bubble.bot {
    background: #ffffff;
    color: #111827;
    border: 1px solid #e8eaf0;
    border-bottom-left-radius: 4px;
}

/* ── File grid ── */
.files-wrapper {
    margin: 8px 0 8px 42px;
}
.files-label {
    font-size: 0.78rem;
    font-weight: 500;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 10px;
}
.file-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 10px;
}
.file-card {
    background: #ffffff;
    border: 1px solid #e8eaf0;
    border-radius: 12px;
    padding: 14px;
    transition: box-shadow 0.15s, border-color 0.15s;
    cursor: default;
}
.file-card:hover {
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
    border-color: #c7d2fe;
}
.file-card-icon {
    font-size: 26px;
    margin-bottom: 8px;
    display: block;
}
.file-card-name {
    font-size: 0.88rem;
    font-weight: 600;
    color: #111827;
    margin-bottom: 4px;
    word-break: break-word;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}
.file-card-type {
    font-size: 0.75rem;
    color: #6b7280;
    background: #f3f4f6;
    display: inline-block;
    padding: 2px 8px;
    border-radius: 999px;
    margin-bottom: 6px;
}
.file-card-date {
    font-size: 0.73rem;
    color: #9ca3af;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #111827 !important;
}
section[data-testid="stSidebar"] * {
    color: #d1d5db !important;
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #f9fafb !important;
}
section[data-testid="stSidebar"] .stButton > button {
    background: #1f2937 !important;
    color: #e5e7eb !important;
    border: 1px solid #374151 !important;
    border-radius: 10px !important;
    font-size: 0.85rem !important;
    text-align: left !important;
    padding: 8px 12px !important;
    width: 100% !important;
    transition: background 0.15s !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: #374151 !important;
    border-color: #4b5563 !important;
}
section[data-testid="stSidebar"] hr {
    border-color: #374151 !important;
}

/* ── Chat input ── */
div[data-testid="stChatInput"] {
    border-top: 1px solid #e8eaf0;
    padding-top: 12px;
}
div[data-testid="stChatInput"] textarea {
    border-radius: 12px !important;
    border: 1px solid #d1d5db !important;
    font-size: 0.92rem !important;
    background: #ffffff !important;
    color: #111827 !important;
    caret-color: #1a56db !important;
}
div[data-testid="stChatInput"] textarea::placeholder {
    color: #9ca3af !important;
    opacity: 1 !important;
}
div[data-testid="stChatInput"] textarea:focus {
    border-color: #1a56db !important;
    box-shadow: 0 0 0 3px rgba(26, 86, 219, 0.12) !important;
    outline: none !important;
}
input, textarea, select {
    color: #111827 !important;
    background: #ffffff !important;
}

/* Open in Drive button */
.stLinkButton > a {
    background: #1a56db !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 0.78rem !important;
    padding: 5px 12px !important;
    text-decoration: none !important;
    display: inline-block;
    margin-top: 8px;
}
.stLinkButton > a:hover {
    background: #1e429f !important;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ── Session state ──
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid4())
if "prefill" not in st.session_state:
    st.session_state.prefill = ""

# ── Sidebar ──
with st.sidebar:
    st.markdown("### 🗂️ Drive Agent")
    st.markdown("Ask in plain English to find files across your Google Drive.")
    st.divider()

    st.markdown("**Quick searches**")
    queries = [
        ("📋", "Find all PDF files"),
        ("📊", "Show me all Google Sheets"),
        ("🖼️", "Find all images"),
        ("📄", "Find files named report"),
        ("🔍", "Search documents about marketing"),
        ("🕒", "Show recently modified files"),
        ("📁", "List all files"),
    ]
    for icon, q in queries:
        if st.button(f"{icon}  {q}", key=q):
            st.session_state.prefill = q

    st.divider()
    if st.button("🗑️  Clear chat"):
        st.session_state.messages = []
        st.rerun()

# ── Header ──
st.markdown("""
<div class="agent-header">
    <div class="agent-icon">🗂️</div>
    <div>
        <div class="agent-title">Google Drive Agent</div>
        <div class="agent-sub">Search and discover files conversationally</div>
    </div>
    <div class="agent-badge">● Live</div>
</div>
""", unsafe_allow_html=True)


# ── Helpers ──
def _format_date(iso: str) -> str:
    if not iso:
        return ""
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).strftime("%b %d, %Y")
    except Exception:
        return iso


def _file_icon(label: str) -> str:
    return {
        "Google Doc": "📄",
        "Google Sheet": "📊",
        "Google Slides": "📑",
        "PDF": "📋",
        "Image": "🖼️",
        "Folder": "📁",
    }.get(label, "📁")


def render_file_cards(files: list[dict]) -> None:
    if not files:
        return

    st.markdown(f"""
<div class="files-wrapper">
  <div class="files-label">{len(files)} file{'s' if len(files) != 1 else ''} found</div>
  <div class="file-grid">
""", unsafe_allow_html=True)

    for item in files:
        name = html.escape(str(item.get("name", "Untitled")))
        label = str(item.get("mimeTypeLabel", "File"))
        modified = _format_date(str(item.get("modifiedTime", "")))
        icon = _file_icon(label)

        st.markdown(f"""
    <div class="file-card">
      <span class="file-card-icon">{icon}</span>
      <div class="file-card-name">{name}</div>
      <span class="file-card-type">{html.escape(label)}</span>
      <div class="file-card-date">{html.escape(modified)}</div>
    </div>
""", unsafe_allow_html=True)

    st.markdown("</div></div>", unsafe_allow_html=True)

    # Open in Drive buttons (rendered outside raw HTML for Streamlit compatibility)
    cols = st.columns(min(len(files), 3))
    for idx, item in enumerate(files):
        link = str(item.get("webViewLink", ""))
        name = str(item.get("name", "File"))
        if link:
            with cols[idx % 3]:
                st.link_button(f"Open {name[:18]}{'…' if len(name) > 18 else ''} ↗", url=link)


# ── Render chat history ──
for msg in st.session_state.messages:
    role = msg.get("role", "assistant")
    content = html.escape(str(msg.get("content", ""))).replace("\n", "<br/>")
    av_class = "user-av" if role == "user" else "bot-av"
    av_label = "U" if role == "user" else "🤖"
    bubble_class = "user" if role == "user" else "bot"
    row_class = "user" if role == "user" else ""

    st.markdown(f"""
<div class="chat-row {row_class}">
  <div class="avatar {av_class}">{av_label}</div>
  <div class="bubble {bubble_class}">{content}</div>
</div>
""", unsafe_allow_html=True)

    if msg.get("files"):
        render_file_cards(msg["files"])

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)


# ── Input handling ──
prefill = st.session_state.prefill
user_input = st.chat_input("Ask me to find files… e.g. 'find all PDFs'")
prompt = prefill or user_input

if prefill:
    st.session_state.prefill = ""

if prompt:
    history_payload = [
        {"role": m.get("role", ""), "content": m.get("content", "")}
        for m in st.session_state.messages
    ]
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("Searching Drive…"):
        try:
            resp = requests.post(
                f"{BACKEND_URL}/chat",
                json={
                    "message": prompt,
                    "session_id": st.session_state.session_id,
                    "history": history_payload,
                },
                timeout=180,
            )
            if resp.status_code != 200:
                raise RuntimeError(f"Backend error {resp.status_code}: {resp.text}")

            payload = resp.json()
            st.session_state.session_id = payload.get("session_id", st.session_state.session_id)
            files_payload = payload.get("files", [])
            response_text = str(payload.get("response", ""))

            if files_payload:
                response_text = f"Found {len(files_payload)} file{'s' if len(files_payload) != 1 else ''}. Here's what I found:"

            assistant_msg = {
                "role": "assistant",
                "content": response_text,
                "files": files_payload,
            }
        except Exception as exc:
            assistant_msg = {
                "role": "assistant",
                "content": f"Something went wrong: {exc}",
                "files": [],
            }

    st.session_state.messages.append(assistant_msg)
    st.rerun()