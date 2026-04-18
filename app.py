import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from utils.data_loader import load_dataset, get_schema_summary
from utils.llm_client import query_llm, build_prompt
from utils.query_engine import run_sql, run_python_analysis
from components.chart_renderer import render_chart
from components.result_display import display_results

st.set_page_config(
    page_title="DatumAI",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS injected via st.markdown (safe for <style> tags) ───
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@300;400;500&display=swap');

:root {
    --bg:      #05070d;
    --bg2:     #0b0e18;
    --bg3:     #111420;
    --bg4:     #181c2a;
    --border:  #1f2538;
    --border2: #2d3450;
    --accent:  #00ff99;
    --blue:    #00d4ff;
    --purple:  #b388ff;
    --text:    #f0f2fa;
    --text2:   #a8b0cc;
    --muted:   #5a6485;
    --dim:     #2e3654;
    --danger:  #ff6b6b;
    --warn:    #ffcc44;
    --r:       10px;
    --ui:      'Syne', sans-serif;
    --mono:    'JetBrains Mono', monospace;
}

html, body, .stApp {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: var(--ui) !important;
}

/* Hide streamlit chrome */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
.stDeployButton { display: none !important; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: var(--bg2) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebarContent"] {
    padding: 0 !important;
}

/* Main content area */
.main .block-container {
    padding: 2rem 2.5rem 6rem !important;
    max-width: 1100px !important;
}

/* Typography */
h1, h2, h3 {
    font-family: var(--ui) !important;
    font-weight: 800 !important;
    letter-spacing: -0.03em !important;
    color: var(--text) !important;
}

/* Buttons */
.stButton > button {
    background: transparent !important;
    border: 1px solid var(--border2) !important;
    color: var(--text2) !important;
    font-family: var(--ui) !important;
    font-size: 0.78rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.05em !important;
    border-radius: 8px !important;
    padding: 0.5rem 1rem !important;
    transition: all 0.15s ease !important;
    width: 100% !important;
}
.stButton > button:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
    background: rgba(0,255,153,0.06) !important;
    box-shadow: 0 0 20px rgba(0,255,153,0.15) !important;
    transform: translateY(-1px) !important;
}

/* Download button */
[data-testid="stDownloadButton"] > button {
    background: rgba(0,212,255,0.07) !important;
    border: 1px solid rgba(0,212,255,0.35) !important;
    color: var(--blue) !important;
    font-family: var(--mono) !important;
    font-size: 0.73rem !important;
    border-radius: 7px !important;
    width: auto !important;
    padding: 0.4rem 1.1rem !important;
    transition: all 0.15s !important;
}
[data-testid="stDownloadButton"] > button:hover {
    background: rgba(0,212,255,0.14) !important;
    box-shadow: 0 0 16px rgba(0,212,255,0.2) !important;
}

/* Chat input */
[data-testid="stChatInput"] > div {
    background: var(--bg3) !important;
    border: 1px solid var(--border2) !important;
    border-radius: 14px !important;
    transition: all 0.2s !important;
}
[data-testid="stChatInput"] > div:focus-within {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 1px rgba(0,255,153,0.2), 0 0 24px rgba(0,255,153,0.1) !important;
}
[data-testid="stChatInput"] textarea {
    background: transparent !important;
    color: var(--text) !important;
    font-family: var(--ui) !important;
    font-size: 0.95rem !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: var(--muted) !important;
}

/* Expanders */
[data-testid="stExpander"] {
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r) !important;
    overflow: hidden !important;
    margin-bottom: 0.4rem !important;
}
[data-testid="stExpander"] summary {
    font-family: var(--mono) !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.07em !important;
    color: var(--muted) !important;
    padding: 0.65rem 1rem !important;
    background: var(--bg3) !important;
    border-radius: var(--r) !important;
}
[data-testid="stExpander"] summary:hover { color: var(--blue) !important; }
[data-testid="stExpander"] summary p { color: inherit !important; }

/* Code blocks */
[data-testid="stCode"], code, pre {
    background: #07090f !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-family: var(--mono) !important;
    font-size: 0.77rem !important;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--r) !important;
    overflow: hidden !important;
}

/* Selectbox */
[data-testid="stSelectbox"] > div > div {
    background: var(--bg3) !important;
    border: 1px solid var(--border2) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-family: var(--ui) !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background: var(--bg3) !important;
    border: 1px dashed var(--border2) !important;
    border-radius: 10px !important;
}
[data-testid="stFileUploader"] label { color: var(--text2) !important; }

/* Alerts */
[data-testid="stAlert"] {
    border-radius: var(--r) !important;
    font-family: var(--ui) !important;
}

/* Spinner */
[data-testid="stSpinner"] > div > div {
    border-top-color: var(--accent) !important;
}

hr { border-color: var(--border) !important; margin: 1rem 0 !important; }

/* Scrollbars */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: var(--muted); }

/* Animations */
@keyframes cp-pulse {
    0%,100%{ opacity:1; transform:scale(1); }
    50%{ opacity:0.2; transform:scale(0.55); }
}
@keyframes cp-fadein {
    from{ opacity:0; transform:translateY(5px); }
    to{ opacity:1; transform:translateY(0); }
}
.cp-msg { animation: cp-fadein 0.2s ease forwards; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────
if "df"           not in st.session_state: st.session_state.df = None
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "schema"       not in st.session_state: st.session_state.schema = None


# ── Shared font import for iframe components ──────────────────────
FONT_LINK = "<link rel='stylesheet' href='https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@300;400;500&display=swap'>"

BASE_CSS = """
<style>
*{box-sizing:border-box;margin:0;padding:0;}
body{background:transparent;font-family:'Syne',sans-serif;color:#f0f2fa;}
</style>
"""


# ═══════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════
with st.sidebar:

    # ── Brand header ──
    st.markdown("""
    <div style="padding:1.2rem 1.3rem 1rem;border-bottom:1px solid #1f2538;margin-bottom:1.1rem;">
        <div style="display:flex;align-items:center;gap:10px;">
            <div style="width:34px;height:34px;background:linear-gradient(135deg,#00ff99,#00d4ff);border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:15px;color:#05070d;font-weight:900;flex-shrink:0;">⬡</div>
            <div>
                <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:0.95rem;color:#f0f2fa;letter-spacing:-0.02em;line-height:1.1;">DatumAI</div>
                <div style="font-family:'JetBrains Mono',monospace;font-size:0.57rem;color:#5a6485;letter-spacing:0.1em;margin-top:2px;">LOCAL · PRIVATE · FREE</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Model ──
    st.markdown('<div style="padding:0 1.3rem;font-family:\'JetBrains Mono\',monospace;font-size:0.57rem;color:#5a6485;letter-spacing:0.14em;text-transform:uppercase;margin-bottom:0.4rem;">Model</div>', unsafe_allow_html=True)
    model_choice = st.selectbox("model", ["llama3.2:3b","llama3.2:1b","llama3:latest"], index=0, label_visibility="collapsed")
    st.session_state.model = model_choice

    st.markdown("<div style='height:1.1rem'></div>", unsafe_allow_html=True)

    # ── Upload ──
    st.markdown('<div style="padding:0 1.3rem;font-family:\'JetBrains Mono\',monospace;font-size:0.57rem;color:#5a6485;letter-spacing:0.14em;text-transform:uppercase;margin-bottom:0.4rem;">Dataset</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "upload", type=["csv","xlsx","xls","json"],
        label_visibility="collapsed",
        help="Processed locally — nothing leaves your machine.",
    )

    if uploaded_file:
        with st.spinner("Parsing…"):
            df, error = load_dataset(uploaded_file)
        if error:
            st.markdown(f"""<div style="margin:0.5rem 0;padding:0.65rem 0.9rem;background:rgba(255,107,107,0.08);border:1px solid rgba(255,107,107,0.3);border-radius:8px;font-family:'JetBrains Mono',monospace;font-size:0.7rem;color:#ff6b6b;">✗ {error}</div>""", unsafe_allow_html=True)
        else:
            st.session_state.df = df
            st.session_state.schema = get_schema_summary(df)
            st.markdown(f"""<div style="margin:0.5rem 0;padding:0.75rem 1rem;background:rgba(0,255,153,0.07);border:1px solid rgba(0,255,153,0.25);border-radius:9px;">
                <div style="font-family:'Syne',sans-serif;font-size:0.82rem;font-weight:700;color:#00ff99;">✓ Dataset loaded</div>
                <div style="font-family:'JetBrains Mono',monospace;font-size:0.62rem;color:#5a6485;margin-top:3px;">{len(df):,} rows · {len(df.columns)} columns</div>
            </div>""", unsafe_allow_html=True)

    # ── Schema ──
    if st.session_state.df is not None:
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        st.markdown('<div style="padding:0 1.3rem;font-family:\'JetBrains Mono\',monospace;font-size:0.57rem;color:#5a6485;letter-spacing:0.14em;text-transform:uppercase;margin-bottom:0.3rem;">Schema</div>', unsafe_allow_html=True)

        dtype_color = {
            "int":"#00d4ff","float":"#00d4ff",
            "object":"#b388ff","str":"#b388ff",
            "bool":"#ffcc44","datetime":"#00ff99",
        }
        rows_html = ""
        for col, info in st.session_state.schema["columns"].items():
            dt = info["dtype"]
            c  = next((v for k, v in dtype_color.items() if k in dt), "#5a6485")
            rows_html += f"""<div style="display:flex;align-items:flex-start;gap:8px;padding:6px 1.3rem;border-bottom:1px solid #111420;">
                <span style="font-family:'JetBrains Mono',monospace;font-size:0.55rem;color:{c};background:rgba(255,255,255,0.05);border-radius:3px;padding:2px 5px;margin-top:1px;white-space:nowrap;flex-shrink:0;">{dt}</span>
                <div style="min-width:0;overflow:hidden;">
                    <div style="font-family:'Syne',sans-serif;font-size:0.75rem;font-weight:600;color:#a8b0cc;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{col}</div>
                    <div style="font-family:'JetBrains Mono',monospace;font-size:0.57rem;color:#2d3450;margin-top:1px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{info['sample']}</div>
                </div>
            </div>"""
        st.markdown(f'<div style="max-height:300px;overflow-y:auto;border-top:1px solid #1f2538;">{rows_html}</div>', unsafe_allow_html=True)

    # ── Clear ──
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    if st.button("⌫  Clear conversation", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

    st.markdown('<div style="padding:1.2rem 1.3rem 0.5rem;font-family:\'JetBrains Mono\',monospace;font-size:0.52rem;color:#1f2538;letter-spacing:0.06em;">Ollama · DuckDB · Plotly · Streamlit</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# MAIN — empty state (no dataset)
# ═══════════════════════════════════════════════════════════════════
if st.session_state.df is None:
    components.html(f"""
    {FONT_LINK}
    {BASE_CSS}
    <style>
    .hero{{display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:80vh;text-align:center;padding:2rem;}}
    .logo{{width:76px;height:76px;background:linear-gradient(135deg,rgba(0,255,153,0.18),rgba(0,212,255,0.1));border:1px solid rgba(0,255,153,0.25);border-radius:20px;display:flex;align-items:center;justify-content:center;font-size:34px;margin-bottom:2rem;}}
    h1{{font-weight:800;font-size:2.6rem;letter-spacing:-0.04em;color:#f0f2fa;margin:0 0 0.4rem;}}
    .sub{{font-family:'JetBrains Mono',monospace;font-size:0.73rem;color:#5a6485;letter-spacing:0.1em;margin:0 0 2.8rem;}}
    .pills{{display:flex;gap:0.55rem;flex-wrap:wrap;justify-content:center;margin-bottom:3rem;}}
    .pill{{font-family:'JetBrains Mono',monospace;font-size:0.65rem;border-radius:99px;padding:0.3rem 0.85rem;border:1px solid;}}
    .grid{{width:100%;max-width:660px;}}
    .grid-label{{font-family:'JetBrains Mono',monospace;font-size:0.57rem;color:#2d3450;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:0.8rem;}}
    .questions{{display:grid;grid-template-columns:1fr 1fr;gap:0.55rem;text-align:left;}}
    .q{{background:#0b0e18;border:1px solid #1f2538;border-radius:10px;padding:0.8rem 1rem;font-family:'Syne',sans-serif;font-size:0.78rem;color:#a8b0cc;line-height:1.45;}}
    .hint{{font-family:'JetBrains Mono',monospace;font-size:0.6rem;color:#1f2538;margin-top:2.4rem;letter-spacing:0.06em;}}
    </style>
    <div class="hero">
        <div class="logo">⬡</div>
        <h1>DatumAI</h1>
        <p class="sub">UPLOAD · ASK · UNDERSTAND</p>
        <div class="pills">
            <span class="pill" style="color:#00d4ff;border-color:rgba(0,212,255,0.3);background:rgba(0,212,255,0.07);">SQL generation</span>
            <span class="pill" style="color:#00ff99;border-color:rgba(0,255,153,0.3);background:rgba(0,255,153,0.07);">Interactive charts</span>
            <span class="pill" style="color:#b388ff;border-color:rgba(179,136,255,0.3);background:rgba(179,136,255,0.07);">AI insights</span>
            <span class="pill" style="color:#ffcc44;border-color:rgba(255,204,68,0.3);background:rgba(255,204,68,0.07);">100% local</span>
        </div>
        <div class="grid">
            <div class="grid-label">Try asking</div>
            <div class="questions">
                <div class="q">Why did sales drop in March?</div>
                <div class="q">Top 10 customers by revenue</div>
                <div class="q">Correlation between price and quantity?</div>
                <div class="q">Find outliers in order_value</div>
            </div>
        </div>
        <p class="hint">← Upload a dataset in the sidebar to begin</p>
    </div>
    """, height=680, scrolling=False)
    st.stop()


# ═══════════════════════════════════════════════════════════════════
# CHAT PAGE — dataset loaded
# ═══════════════════════════════════════════════════════════════════

# Page header
st.markdown(f"""
<div class="cp-msg" style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1.8rem;padding-bottom:1rem;border-bottom:1px solid #1f2538;">
    <div>
        <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:1.5rem;letter-spacing:-0.03em;color:#f0f2fa;">Ask your data</div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:0.62rem;color:#5a6485;margin-top:4px;letter-spacing:0.05em;">
            {st.session_state.schema['row_count']:,} rows &middot; {st.session_state.schema['column_count']} columns &middot; {st.session_state.model}
        </div>
    </div>
    <span style="font-family:'JetBrains Mono',monospace;font-size:0.58rem;color:#00ff99;background:rgba(0,255,153,0.08);border:1px solid rgba(0,255,153,0.2);border-radius:99px;padding:0.22rem 0.75rem;letter-spacing:0.08em;">● LIVE</span>
</div>
""", unsafe_allow_html=True)

# Pending follow-up injection
if st.session_state.get("_pending_question"):
    pending = st.session_state.pop("_pending_question")
    st.session_state.chat_history.append({"role": "user", "content": pending})

# ── Chat history ──────────────────────────────────────────────────
for message in st.session_state.chat_history:
    if message["role"] == "user":
        st.markdown(f"""
        <div class="cp-msg" style="display:flex;justify-content:flex-end;margin:0.4rem 0 0.7rem;">
            <div style="background:#111420;border:1px solid #2d3450;border-radius:16px 16px 4px 16px;padding:0.8rem 1.15rem;max-width:76%;font-family:'Syne',sans-serif;font-size:0.9rem;color:#f0f2fa;line-height:1.55;">{message['content']}</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div class="cp-msg">', unsafe_allow_html=True)
        display_results(message["content"])
        st.markdown('</div>', unsafe_allow_html=True)

# ── Chat input ────────────────────────────────────────────────────
user_question = st.chat_input("Ask anything about your data…")

if user_question:
    st.session_state.chat_history.append({"role": "user", "content": user_question})

    # Show user bubble immediately
    st.markdown(f"""
    <div class="cp-msg" style="display:flex;justify-content:flex-end;margin:0.4rem 0 0.7rem;">
        <div style="background:#111420;border:1px solid #2d3450;border-radius:16px 16px 4px 16px;padding:0.8rem 1.15rem;max-width:76%;font-family:'Syne',sans-serif;font-size:0.9rem;color:#f0f2fa;line-height:1.55;">{user_question}</div>
    </div>""", unsafe_allow_html=True)

    # Animated thinking indicator
    thinking_slot = st.empty()
    thinking_slot.markdown("""
    <div style="display:flex;align-items:center;gap:10px;background:#0b0e18;border:1px solid #1f2538;border-radius:12px;padding:0.85rem 1.15rem;width:fit-content;margin:0.2rem 0 0.8rem;">
        <div style="display:flex;gap:5px;align-items:center;">
            <div style="width:7px;height:7px;border-radius:99px;background:#00ff99;animation:cp-pulse 1.1s ease-in-out infinite;"></div>
            <div style="width:7px;height:7px;border-radius:99px;background:#00ff99;animation:cp-pulse 1.1s ease-in-out 0.22s infinite;"></div>
            <div style="width:7px;height:7px;border-radius:99px;background:#00ff99;animation:cp-pulse 1.1s ease-in-out 0.44s infinite;"></div>
        </div>
        <span style="font-family:'JetBrains Mono',monospace;font-size:0.72rem;color:#5a6485;">Analysing…</span>
    </div>
    """, unsafe_allow_html=True)

    # LLM call
    prompt = build_prompt(
        question=user_question,
        schema=st.session_state.schema,
        df_head=st.session_state.df.head(5).to_markdown(),
    )
    llm_response = query_llm(prompt=prompt, model=st.session_state.model)
    thinking_slot.empty()

    if "error" in llm_response:
        result = {"type": "error", "message": llm_response["error"]}
    else:
        result = run_sql(
            llm_response=llm_response,
            df=st.session_state.df,
            user_question=user_question,
        )
        if result.get("chart_hint"):
            result["chart"] = render_chart(
                df=result.get("result_df"),
                chart_hint=result["chart_hint"],
                question=user_question,
                x=result.get("chart_x"),
                y=result.get("chart_y"),
                color=result.get("chart_color"),
            )

    display_results(result)
    st.session_state.chat_history.append({"role": "assistant", "content": result})
