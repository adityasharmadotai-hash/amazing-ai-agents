"""Settings panel: API key, model params, theme, safety and behaviour toggles."""

from __future__ import annotations

from typing import Optional

import streamlit as st

from app.context import AnalystContext, build_llm
from core.config import AppSettings
from services.report_service import ReportService


def _has_api_key(settings: AppSettings) -> bool:
    """True if a Gemini key is available from secrets/.env or the session."""
    if settings.has_gemini_key():
        return True
    return bool(st.session_state.get("gemini_api_key_override", "").strip())


def render_settings(settings: AppSettings) -> None:
    """Render the settings expander and apply changes to the live context."""
    ctx: Optional[AnalystContext] = st.session_state.get("ctx")
    key_ready = _has_api_key(settings)

    # Open the panel automatically until a working API key is configured so new
    # users (and cloud deploys) can find where to paste it.
    with st.expander("⚙️ Settings — API Key & Preferences", expanded=not key_ready):
        if not key_ready:
            st.warning(
                "No Gemini API key detected. Paste your key below (or add "
                "`GEMINI_API_KEY` to the app's secrets) to enable AI features. "
                "Get one at https://aistudio.google.com/app/apikey",
                icon="🔑",
            )
        else:
            st.success("Gemini API key detected — AI features are enabled.", icon="✅")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**AI / Gemini**")
            api_key = st.text_input(
                "Gemini API Key",
                type="password",
                value="",
                placeholder="Paste your Gemini API key here",
                help="Stored only in this browser session; never written to disk.",
            )
            model_choices = [
                "gemini-2.0-flash",
                "gemini-2.5-flash",
                "gemini-2.5-pro",
                "gemini-flash-latest",
            ]
            if settings.gemini_model not in model_choices:
                model_choices.insert(0, settings.gemini_model)
            model = st.selectbox(
                "Model",
                model_choices,
                index=model_choices.index(settings.gemini_model),
                help="If a model is unavailable for your key, the app auto-falls back to a supported one.",
            )
            temperature = st.slider("Temperature", 0.0, 1.5, float(settings.gemini_temperature), 0.05)
            max_tokens = st.number_input(
                "Max Tokens", min_value=256, max_value=32768, value=int(settings.gemini_max_tokens), step=256
            )

        with col2:
            st.markdown("**Appearance & Behaviour**")
            chart_theme = st.selectbox(
                "Chart Theme",
                ["plotly_dark", "plotly", "plotly_white", "ggplot2", "seaborn", "simple_white"],
                index=0,
            )
            auto_explain = st.checkbox("Auto explain SQL", value=settings.auto_explain_sql)
            auto_charts = st.checkbox("Auto generate charts", value=settings.auto_generate_charts)
            write_mode = st.checkbox(
                "🔓 Enable write mode (dangerous)",
                value=st.session_state.get("write_mode_enabled", False),
                help="Allows INSERT/UPDATE/DELETE/DDL. Off by default for safety.",
            )

        if st.button("Apply settings", type="primary"):
            _apply(settings, ctx, api_key, model, temperature, max_tokens, chart_theme,
                   auto_explain, auto_charts, write_mode)
            st.success("Settings applied.")


def _apply(
    settings: AppSettings,
    ctx: Optional[AnalystContext],
    api_key: str,
    model: str,
    temperature: float,
    max_tokens: int,
    chart_theme: str,
    auto_explain: bool,
    auto_charts: bool,
    write_mode: bool,
) -> None:
    st.session_state.write_mode_enabled = write_mode
    if api_key.strip():
        st.session_state.gemini_api_key_override = api_key.strip()

    # Update settings object in place for new contexts.
    settings.gemini_model = model
    settings.gemini_temperature = temperature
    settings.gemini_max_tokens = int(max_tokens)
    settings.chart_theme = chart_theme
    settings.auto_explain_sql = auto_explain
    settings.auto_generate_charts = auto_charts

    if ctx is None:
        return

    # Apply to the live context.
    ctx.set_read_only(not write_mode)
    ctx.chart_service.set_theme(chart_theme)
    ctx.agent.auto_explain = auto_explain
    ctx.agent.auto_charts = auto_charts

    override_key = st.session_state.get("gemini_api_key_override")
    settings_for_llm = settings
    new_llm = build_llm(settings_for_llm, api_key=override_key)
    if new_llm is not None:
        new_llm.update_params(temperature=temperature, max_tokens=int(max_tokens), model=model)
    ctx.llm = new_llm
    ctx.agent.llm = new_llm
    ctx.report_service = ReportService(new_llm)
