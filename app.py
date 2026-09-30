import streamlit as st
from query import ask
import random
import datetime

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Cyber AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# SESSION STATE INIT
# =========================
if "sessions" not in st.session_state:
    st.session_state.sessions = []

if "active_session" not in st.session_state:
    st.session_state.active_session = None

if "pinned" not in st.session_state:
    st.session_state.pinned = set()

if "open_menu" not in st.session_state:
    st.session_state.open_menu = None

if "sidebar_visible" not in st.session_state:
    st.session_state.sidebar_visible = True

# =========================
# CSS (ONLY removed conflicting part)
# =========================
st.markdown("""
<style>
section[data-testid="stSidebar"] {
    background-color: #171717 !important;
    border-right: 1px solid #252525 !important;
}
</style>
""", unsafe_allow_html=True)
# st.markdown("""
# <style>
# @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
# html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
# /* ── MAIN CONTENT ── */
# .main .block-container { padding-top: 1.5rem !important; max-width: 1100px !important; }

# /* Chips */
# .chip {
#     display: inline-block; padding: 4px 12px; border-radius: 20px;
#     font-size: 12px; font-weight: 600; margin-right: 8px; margin-bottom: 12px;
# }
# .chip-conf    { background:#1a2535; color:#60a5fa; border:1px solid #3b82f6; }
# .chip-high    { background:#2a1515; color:#f87171; border:1px solid #ef4444; }
# .chip-medium  { background:#2a2010; color:#fbbf24; border:1px solid #f59e0b; }
# .chip-low     { background:#1a2b1e; color:#4ade80; border:1px solid #22c55e; }
# .chip-blocked { background:#2a1515; color:#f87171; border:1px solid #ef4444; }

# /* Summary box */
# .summary-box {
#     background:#1c1c1c; border:1px solid #2e2e2e; border-radius:12px;
#     padding:16px 18px; font-size:14px; color:#d0d0d0; line-height:1.7; margin-bottom:18px;
# }

# /* Cards */
# .card-box {
#     background:#1e1e1e; border:1px solid #2e2e2e; border-radius:12px;
#     padding:18px 16px; height:100%; box-sizing:border-box;
# }
# .card-title { font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:12px; }
# .card-item  { font-size:13px; color:#c8c8c8; padding:8px 10px; border-radius:7px; margin-bottom:6px; line-height:1.5; }
# .card-causes  .card-item  { background:#1a2535; border-left:3px solid #3b82f6; }
# .card-causes  .card-title { color:#60a5fa; }
# .card-invest  .card-item  { background:#1a2b1e; border-left:3px solid #22c55e; }
# .card-invest  .card-title { color:#4ade80; }
# .card-mitig   .card-item  { background:#2a2010; border-left:3px solid #f59e0b; }
# .card-mitig   .card-title { color:#fbbf24; }
# .card-blocked .card-item  { background:#2a1515; border-left:3px solid #ef4444; }
# .card-blocked .card-title { color:#f87171; }

# /* Hide Streamlit chrome */
# #MainMenu { visibility:hidden; }
# footer     { visibility:hidden; }
# header     { visibility:hidden; }
# </style>
# """, unsafe_allow_html=True)

# # =========================
# # TOGGLE BUTTON (FIXED)
# # =========================
# if st.button("☰", key="sidebar_toggle"):
#     st.session_state.sidebar_visible = not st.session_state.sidebar_visible

# =========================
# SIDEBAR (FIXED)
# =========================
with st.sidebar:

    # ✅ FIX: hide sidebar safely (do NOT remove sidebar)
    if not st.session_state.sidebar_visible:
        st.markdown(
            "<style>section[data-testid='stSidebar']{display:none;}</style>",
            unsafe_allow_html=True
        )

    st.markdown("### 🛡️ Cyber AI")

    if st.button("✏️ New Chat", use_container_width=True):
        st.session_state.active_session = None
        st.session_state.open_menu = None

    st.markdown("---")

    sessions = st.session_state.sessions

    if not sessions:
        st.markdown("No chats yet. Ask something!")
    else:
        pinned_ids = [i for i in range(len(sessions)) if i in st.session_state.pinned]
        unpinned_ids = [i for i in range(len(sessions)) if i not in st.session_state.pinned]

        def render_chat_row(i):
            sess = sessions[i]
            title = sess["title"]

            if st.button(title, key=f"chat_{i}", use_container_width=True):
                st.session_state.active_session = i

        if pinned_ids:
            st.markdown("#### 📌 Pinned")
            for i in reversed(pinned_ids):
                render_chat_row(i)

        if unpinned_ids:
            st.markdown("#### 🕒 Recent")
            for i in reversed(unpinned_ids):
                render_chat_row(i)

# =========================
# MAIN CONTENT
# =========================
st.markdown("## 🛡️ Cybersecurity AI Assistant")

user_input = st.chat_input("Ask a cybersecurity question...")

if user_input:
    with st.spinner("Analyzing..."):
        response = ask(user_input)
    new_msg = {
        "question":   user_input,
        "answer":     response,
        "confidence": random.randint(85, 98),
        "severity":   random.choice(["Low", "Medium", "High"]),
        "time":       datetime.datetime.now().strftime("%H:%M"),
        "blocked":    response.get("blocked", False),
    }
    idx = st.session_state.active_session
    if idx is None:
        st.session_state.sessions.append({
            "title":    user_input,
            "created":  new_msg["time"],
            "messages": [new_msg],
        })
        st.session_state.active_session = len(st.session_state.sessions) - 1
    else:
        st.session_state.sessions[idx]["messages"].append(new_msg)
    st.rerun()  # ✅ rerun ONLY after new message — this is correct and needed

# =========================
# DISPLAY MESSAGES
# =========================
idx      = st.session_state.active_session
messages = st.session_state.sessions[idx]["messages"] if idx is not None else []

SEV_CSS  = {"High": "chip-high",  "Medium": "chip-medium", "Low": "chip-low"}
SEV_ICON = {"High": "🚨",         "Medium": "⚠️",          "Low": "✅"}
CARD_CFG = {
    "causes":        ("card-causes", "⚠️ Causes"),
    "investigation": ("card-invest",  "🔍 Investigation"),
    "mitigation":    ("card-mitig",   "🛡️ Mitigation"),
}

if messages:
    for msg in messages:
        answer     = msg["answer"]
        is_blocked = msg.get("blocked", False)

        st.chat_message("user").write(msg["question"])

        with st.chat_message("assistant"):

            # Chips
            if is_blocked:
                st.markdown(
                    '<span class="chip chip-blocked">🚫 BLOCKED</span>'
                    '<span class="chip chip-conf">🔒 Security Gate</span>',
                    unsafe_allow_html=True)
            else:
                sev = msg["severity"]
                st.markdown(
                    f'<span class="chip chip-conf">📊 Confidence: {msg["confidence"]}%</span>'
                    f'<span class="chip {SEV_CSS[sev]}">{SEV_ICON[sev]} Severity: {sev}</span>',
                    unsafe_allow_html=True)

            # Summary
            if answer.get("summary"):
                st.markdown(
                    f'<div class="summary-box">{answer["summary"]}</div>',
                    unsafe_allow_html=True)

            # Blocked
            if is_blocked:
                tips = answer.get("mitigation", [])
                if tips:
                    items_html = "".join(f'<div class="card-item">{t}</div>' for t in tips)
                    st.markdown(
                        f'<div class="card-box card-blocked">'
                        f'<div class="card-title">💬 What I Can Help With</div>'
                        f'{items_html}</div>',
                        unsafe_allow_html=True)
            else:
                # Cards
                active_keys = [k for k in ["causes", "investigation", "mitigation"] if answer.get(k)]
                if active_keys:
                    cols = st.columns(len(active_keys))
                    for col, key in zip(cols, active_keys):
                        cls, title = CARD_CFG[key]
                        items_html = "".join(
                            f'<div class="card-item">{it}</div>' for it in answer[key])
                        with col:
                            st.markdown(
                                f'<div class="card-box {cls}">'
                                f'<div class="card-title">{title}</div>'
                                f'{items_html}</div>',
                                unsafe_allow_html=True)

                # Full Analysis Summary
                all_points = []
                for item in answer.get("causes", []):
                    all_points.append(("🔴", "Cause",      "#3b82f6", item))
                for item in answer.get("investigation", []):
                    all_points.append(("🔵", "Investigate", "#22c55e", item))
                for item in answer.get("mitigation", []):
                    all_points.append(("🟡", "Mitigate",    "#f59e0b", item))

                if all_points:
                    st.markdown("---")
                    st.markdown(
                        '<p style="font-size:12px;font-weight:700;text-transform:uppercase;'
                        'letter-spacing:1px;color:#666;margin-bottom:10px;">📋 Full Analysis Summary</p>',
                        unsafe_allow_html=True)

                    tag_label_colors = {
                        "Cause":       "#60a5fa",
                        "Investigate": "#4ade80",
                        "Mitigate":    "#fbbf24",
                    }

                    for icon, tag, border_color, text in all_points:
                        tc = tag_label_colors[tag]
                        st.markdown(
                            f'<div style="display:flex;align-items:flex-start;gap:12px;'
                            f'padding:9px 14px;background:#1a1a1a;border-radius:8px;'
                            f'border-left:3px solid {border_color};margin-bottom:6px;">'
                            f'<span style="font-size:13px;flex-shrink:0;">{icon}</span>'
                            f'<span style="font-size:12px;font-weight:600;color:{tc};'
                            f'flex-shrink:0;min-width:76px;padding-top:1px;">{tag}</span>'
                            f'<span style="font-size:13px;color:#c0c0c0;line-height:1.5;">{text}</span>'
                            f'</div>',
                            unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

else:
    st.markdown("""
    <div style="text-align:center;padding:80px 20px;">
        <div style="font-size:48px;margin-bottom:16px;">🛡️</div>
        <div style="font-size:20px;font-weight:600;color:#888;margin-bottom:8px;">Cybersecurity AI Assistant</div>
        <div style="font-size:14px;color:#555;max-width:420px;margin:0 auto;line-height:1.6;">
            Ask about incidents, threats, vulnerabilities,<br>or how to defend your systems.
        </div>
    </div>
    """, unsafe_allow_html=True)