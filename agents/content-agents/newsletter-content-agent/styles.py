"""
modules/styles.py
-----------------
Custom CSS for a clean, modern dark UI + a clipboard copy button.
"""

import json
import streamlit as st
import streamlit.components.v1 as components

CSS = """
<style>
    /* ---- Layout & typography ---- */
    .block-container { padding-top: 2.2rem; max-width: 980px; }
    html, body, [class*="css"] { font-family: 'Inter', 'Segoe UI', sans-serif; }

    h1, h2, h3 { letter-spacing: -0.01em; }

    /* ---- Hero header ---- */
    .app-hero {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%);
        padding: 1.6rem 1.8rem;
        border-radius: 16px;
        margin-bottom: 1.4rem;
        box-shadow: 0 10px 30px rgba(99,102,241,0.25);
    }
    .app-hero h1 { color: #fff; margin: 0; font-size: 1.7rem; font-weight: 750; }
    .app-hero p  { color: rgba(255,255,255,0.85); margin: 0.3rem 0 0; font-size: 0.95rem; }

    /* ---- Metric / stat cards ---- */
    .stat-card {
        background: #1a1d28;
        border: 1px solid #262a38;
        border-radius: 14px;
        padding: 1.1rem 1.2rem;
        text-align: center;
    }
    .stat-card .num   { font-size: 1.9rem; font-weight: 750; color: #818cf8; }
    .stat-card .label { font-size: 0.8rem; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.05em; }

    /* ---- Section card ---- */
    .section-card {
        background: #1a1d28;
        border: 1px solid #262a38;
        border-radius: 14px;
        padding: 1.3rem 1.5rem;
        margin-bottom: 1rem;
    }

    /* ---- Buttons ---- */
    .stButton > button {
        border-radius: 10px;
        border: none;
        font-weight: 600;
        padding: 0.55rem 1.1rem;
    }
    div[data-testid="stForm"] .stButton > button,
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: #fff;
    }

    /* ---- Article chip ---- */
    .article-chip {
        background: #14161f;
        border: 1px solid #262a38;
        border-left: 3px solid #6366f1;
        border-radius: 10px;
        padding: 0.7rem 0.9rem;
        margin-bottom: 0.55rem;
    }
    .article-chip .t { font-weight: 600; color: #e5e7eb; font-size: 0.92rem; }
    .article-chip .m { color: #9ca3af; font-size: 0.78rem; margin-top: 0.2rem; }

    /* ---- Preview surface ---- */
    .preview-surface {
        background: #15171f;
        border: 1px solid #262a38;
        border-radius: 14px;
        padding: 1.6rem 2rem;
    }

    /* ---- Sidebar tweaks ---- */
    section[data-testid="stSidebar"] { background: #14161f; }
    .sidebar-brand { font-size: 1.15rem; font-weight: 750; color: #e5e7eb; padding: 0.2rem 0 0.6rem; }
    .sidebar-brand span { color: #818cf8; }

    /* hide default streamlit chrome */
    #MainMenu, footer { visibility: hidden; }
</style>
"""


def inject():
    """Inject global CSS. Call once near the top of the app."""
    st.markdown(CSS, unsafe_allow_html=True)


def hero(title: str, subtitle: str = ""):
    st.markdown(
        f'<div class="app-hero"><h1>{title}</h1>'
        f'<p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )


def stat_card(num, label):
    return (
        f'<div class="stat-card"><div class="num">{num}</div>'
        f'<div class="label">{label}</div></div>'
    )


def copy_button(text: str, label: str = "📋 Copy to clipboard"):
    """Render a JS-powered copy-to-clipboard button via components.html."""
    payload = json.dumps(text)
    components.html(
        f"""
        <button id="copybtn" style="
            background: linear-gradient(135deg,#6366f1,#8b5cf6);
            color:#fff;border:none;border-radius:10px;
            padding:0.6rem 1.1rem;font-weight:600;cursor:pointer;
            font-family:'Inter',sans-serif;font-size:0.9rem;width:100%;">
            {label}
        </button>
        <script>
            const btn = document.getElementById("copybtn");
            btn.addEventListener("click", async () => {{
                try {{
                    await navigator.clipboard.writeText({payload});
                    btn.innerText = "✅ Copied!";
                    setTimeout(() => btn.innerText = "{label}", 1800);
                }} catch (e) {{
                    btn.innerText = "⚠️ Press Ctrl/Cmd+C";
                }}
            }});
        </script>
        """,
        height=56,
    )
