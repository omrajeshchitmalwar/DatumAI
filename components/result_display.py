"""
components/result_display.py
Renders the structured result dict with a high-contrast dark terminal UI.
"""
import streamlit as st
import pandas as pd
from typing import Any


def display_results(result: dict[str, Any]) -> None:
    """
    Render a full analysis response:
      - Error / warning banners
      - Insight card (leads the response)
      - SQL expander
      - Python expander
      - Plotly chart
      - Result dataframe + CSV download
      - Follow-up suggestion buttons
    """
    # ✅ ADD THIS BLOCK HERE
    if "_render_id" not in st.session_state:
        st.session_state["_render_id"] = 0

    st.session_state["_render_id"] += 1
    rid = st.session_state["_render_id"]

    # ── Error ────────────────────────────────────────────────────
    if result.get("type") == "error":
        st.markdown(f"""
        <div style="background:rgba(255,107,107,0.08);border:1px solid rgba(255,107,107,0.3);border-radius:10px;padding:0.9rem 1.1rem;margin:0.3rem 0;">
            <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:0.82rem;color:#ff6b6b;margin-bottom:4px;">Error</div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:0.73rem;color:#cc5555;line-height:1.55;">{result.get('message','An unknown error occurred.')}</div>
        </div>""", unsafe_allow_html=True)
        return

    error      = result.get("error")
    error_note = result.get("error_note")

    if error:
        st.markdown(f"""
        <div style="background:rgba(255,107,107,0.08);border:1px solid rgba(255,107,107,0.28);border-radius:10px;padding:0.8rem 1rem;margin:0.3rem 0;">
            <div style="font-family:'JetBrains Mono',monospace;font-size:0.71rem;color:#ff6b6b;line-height:1.5;">{error}</div>
        </div>""", unsafe_allow_html=True)

    if error_note:
        st.markdown(f"""
        <div style="background:rgba(255,204,68,0.07);border:1px solid rgba(255,204,68,0.25);border-radius:10px;padding:0.75rem 1rem;margin:0.3rem 0;">
            <div style="font-family:'JetBrains Mono',monospace;font-size:0.71rem;color:#ffcc44;line-height:1.5;">ℹ {error_note}</div>
        </div>""", unsafe_allow_html=True)

    # ── Insight card ─────────────────────────────────────────────
    insight = result.get("insight")
    if insight:
        st.markdown(f"""
        <div style="
            position:relative;overflow:hidden;
            background:linear-gradient(135deg,rgba(0,255,153,0.06) 0%,rgba(0,212,255,0.03) 100%);
            border:1px solid rgba(0,255,153,0.2);
            border-radius:12px;
            padding:1rem 1.2rem 1rem 1.35rem;
            margin:0.3rem 0 0.8rem;
        ">
            <div style="position:absolute;top:0;left:0;width:3px;height:100%;background:linear-gradient(180deg,#00ff99,#00d4ff);border-radius:3px 0 0 3px;"></div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:0.57rem;color:#00ff99;letter-spacing:0.13em;text-transform:uppercase;margin-bottom:0.55rem;">Insight</div>
            <div style="font-family:'Syne',sans-serif;font-size:0.92rem;color:#f0f2fa;line-height:1.68;font-weight:400;">{insight}</div>
        </div>""", unsafe_allow_html=True)

    # ── SQL expander ─────────────────────────────────────────────
    sql = result.get("sql")
    if sql:
        with st.expander("◈  SQL query", expanded=False):
            st.code(sql, language="sql")

    # ── Python expander ──────────────────────────────────────────
    python_code = result.get("python")
    if python_code:
        with st.expander("◈  Python code", expanded=False):
            st.code(python_code, language="python")

    # ── Plotly chart ─────────────────────────────────────────────
    chart = result.get("chart")
    if chart is not None:
        chart.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(11,14,24,0.7)",
            font=dict(family="'Syne', sans-serif", color="#a8b0cc", size=12),
            title_font=dict(family="'Syne', sans-serif", color="#f0f2fa", size=14, weight=700),
            xaxis=dict(
                gridcolor="#1f2538",
                linecolor="#1f2538",
                tickfont=dict(family="'JetBrains Mono',monospace", size=10, color="#5a6485"),
                title_font=dict(color="#a8b0cc"),
            ),
            yaxis=dict(
                gridcolor="#1f2538",
                linecolor="#1f2538",
                tickfont=dict(family="'JetBrains Mono',monospace", size=10, color="#5a6485"),
                title_font=dict(color="#a8b0cc"),
            ),
            legend=dict(
                bgcolor="rgba(11,14,24,0.85)",
                bordercolor="#1f2538",
                borderwidth=1,
                font=dict(family="'Syne',sans-serif", size=11, color="#a8b0cc"),
            ),
            colorway=["#00ff99","#00d4ff","#b388ff","#ffcc44","#ff6b6b","#34d399","#60a5fa"],
            margin=dict(t=44, b=32, l=8, r=8),
        )
        st.markdown('<div style="background:#0b0e18;border:1px solid #1f2538;border-radius:12px;overflow:hidden;margin:0.5rem 0 0.7rem;">', unsafe_allow_html=True)
        st.plotly_chart(chart, use_container_width=True, config={
            "displaylogo": False,
            "modeBarButtonsToRemove": ["select2d","lasso2d","toImage"],
        })
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Result table ─────────────────────────────────────────────
    result_df = result.get("result_df")
    if result_df is not None and not result_df.empty:
        row_count = len(result_df)
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:10px;margin:0.7rem 0 0.35rem;">
            <span style="font-family:'JetBrains Mono',monospace;font-size:0.6rem;color:#5a6485;text-transform:uppercase;letter-spacing:0.1em;">Results</span>
            <span style="font-family:'JetBrains Mono',monospace;font-size:0.6rem;color:#00ff99;background:rgba(0,255,153,0.08);border:1px solid rgba(0,255,153,0.18);border-radius:99px;padding:1px 7px;">{row_count:,} rows</span>
        </div>""", unsafe_allow_html=True)

        st.dataframe(result_df, use_container_width=True, height=min(320, 44 + row_count * 36))

        csv_bytes = result_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="↓ Download CSV",
            data=csv_bytes,
            file_name="query_result.csv",
            mime="text/csv",
            key=f"dl_{id(result_df)}",
        )

    # ── Follow-up chips ──────────────────────────────────────────
    follow_ups = result.get("follow_ups", [])
    if follow_ups:
        st.markdown("""
        <div style="font-family:'JetBrains Mono',monospace;font-size:0.57rem;color:#2d3450;letter-spacing:0.1em;text-transform:uppercase;margin:1rem 0 0.45rem;">
            Continue exploring
        </div>""", unsafe_allow_html=True)

        cols = st.columns(min(len(follow_ups), 2))
        for i, question in enumerate(follow_ups[:4]):
            with cols[i % 2]:
                if st.button(question, key=f"fu_{rid}_{i}"):
                    st.session_state["_pending_question"] = question
                    st.rerun()

    # Turn separator
    st.markdown('<div style="height:0.5rem;border-bottom:1px solid #111420;margin-bottom:0.5rem;"></div>', unsafe_allow_html=True)
