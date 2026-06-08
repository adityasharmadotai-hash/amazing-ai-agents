"""
Competitor Intelligence Agent - Main Streamlit Application
Monitors competitors across web, pricing, social media, hiring, and product launches
"""

import os
import json
from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.express as px
import pytz

# Try to import local modules, with graceful fallback
try:
    from database import Database
    from ai_analysis import CompetitorAnalyzer, ReportGenerator
    from scraper import WebScraper, PricingScraper, HiringTracker
    from alerts import AlertManager
except ImportError as e:
    st.error(f"⚠️ Missing module: {str(e)}")
    st.info("Make sure all .py files are in the same directory as app.py")
    st.stop()

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="Competitor Intelligence Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Brand palette
PRIMARY = "#667eea"
GRADIENTS = [
    "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
    "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
]

# Custom CSS for professional styling
st.markdown("""
<style>
    * { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }

    /* Gradient KPI tiles */
    .kpi {
        padding: 18px 20px;
        border-radius: 14px;
        color: white;
        box-shadow: 0 6px 18px rgba(102, 126, 234, 0.25);
        min-height: 110px;
    }
    .kpi .kpi-top { font-size: 22px; opacity: 0.95; }
    .kpi .kpi-val { font-size: 34px; font-weight: 700; line-height: 1.1; margin-top: 4px; }
    .kpi .kpi-lbl { font-size: 13px; opacity: 0.92; margin-top: 4px; }

    .alert-box {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 14px 16px; border-radius: 10px; color: white; margin: 8px 0;
    }
    .success-box {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 14px 16px; border-radius: 10px; color: white; margin: 8px 0;
    }

    /* App header */
    .app-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 18px 24px; border-radius: 14px; color: white; margin-bottom: 18px;
        box-shadow: 0 6px 18px rgba(102, 126, 234, 0.25);
    }
    .app-header h1 { margin: 0; font-size: 26px; font-weight: 700; }
    .app-header p { margin: 4px 0 0 0; font-size: 13px; opacity: 0.9; }

    /* Settings section cards */
    .settings-card {
        background-color: #f8f9fb; border: 1px solid #eceef3;
        border-left: 4px solid #667eea; border-radius: 10px;
        padding: 8px 18px 4px 18px; margin-bottom: 6px;
    }

    .stMetric {
        background-color: #f8f9fa; padding: 14px; border-radius: 10px;
        border-left: 4px solid #667eea;
    }
    section[data-testid="stSidebar"] { background-color: #fbfbfd; }
</style>
""", unsafe_allow_html=True)

# ==================== INITIALIZATION ====================
@st.cache_resource
def init_components():
    """Initialize all components (cached for the session)."""
    try:
        db = Database("competitors.db")
        analyzer = CompetitorAnalyzer()
        scraper = WebScraper()
        pricing_scraper = PricingScraper()
        hiring_tracker = HiringTracker()
        alert_manager = AlertManager(db)
        return db, analyzer, scraper, pricing_scraper, hiring_tracker, alert_manager
    except Exception as e:
        st.error(f"Failed to initialize components: {str(e)}")
        return None, None, None, None, None, None


db, analyzer, scraper, pricing_scraper, hiring_tracker, alert_manager = init_components()

if db is None:
    st.error("Application failed to initialize. Please check your configuration.")
    st.stop()

report_generator = ReportGenerator(db, analyzer)


# ==================== CONFIG / STATE ====================
def resolve_openai_key():
    """Resolve the OpenAI key: runtime Settings override > st.secrets > env var."""
    if st.session_state.get("openai_api_key"):
        return st.session_state["openai_api_key"]
    try:
        if "OPENAI_API_KEY" in st.secrets:
            return st.secrets["OPENAI_API_KEY"]
    except Exception:
        pass
    return os.getenv("OPENAI_API_KEY", "")


def resolve_openai_model():
    """Resolve the model: runtime Settings override > env var > default."""
    return st.session_state.get("openai_model") or os.getenv("OPENAI_MODEL", "gpt-4o")


# Default app settings (live in session_state so the Settings page can edit them
# and every page reads the same values).
_DEFAULTS = {
    "alert_email": os.getenv("ALERT_EMAIL", ""),
    "alert_frequency": "Daily",
    "alert_types": ["Price Changes", "Hiring Activity", "Product Launches"],
    "alert_severity_default": "All",
    "monitor_pricing": True,
    "monitor_social": True,
    "monitor_hiring": True,
    "monitor_products": True,
}
for _k, _v in _DEFAULTS.items():
    st.session_state.setdefault(_k, _v)

# Apply the resolved OpenAI config to the (cached) analyzer on every run.
if analyzer is not None:
    _key, _model = resolve_openai_key(), resolve_openai_model()
    if _key != (analyzer.api_key or "") or _model != analyzer.model:
        analyzer.configure(api_key=_key or None, model=_model)


def get_competitors():
    """Fetch competitors, returning an empty list on error."""
    try:
        return db.get_competitors() or []
    except Exception:
        return []


def kpi_card(container, emoji, value, label, gradient):
    """Render a gradient KPI tile inside the given container."""
    container.markdown(
        f'<div class="kpi" style="background:{gradient}">'
        f'<div class="kpi-top">{emoji}</div>'
        f'<div class="kpi-val">{value}</div>'
        f'<div class="kpi-lbl">{label}</div></div>',
        unsafe_allow_html=True,
    )


# ==================== SIDEBAR (NAVIGATION) ====================
PAGES = [
    "📊 Dashboard",
    "🌐 Website Monitoring",
    "💰 Pricing Intelligence",
    "👥 Hiring Activity",
    "🚀 Product Launches",
    "📧 Alerts & Reports",
    "⚙️ Settings",
]

with st.sidebar:
    st.markdown("## 🔍 Competitor IQ")
    st.caption("Competitive intelligence, automated.")

    page = st.radio("Navigate", PAGES, key="nav")

    st.divider()

    with st.expander("➕ Add Competitor", expanded=False):
        with st.form("add_competitor"):
            comp_name = st.text_input("Competitor Name", placeholder="e.g., Segment, Mixpanel")
            comp_website = st.text_input("Website URL", placeholder="https://example.com")
            comp_linkedin = st.text_input("LinkedIn URL", placeholder="linkedin.com/company/...")
            comp_twitter = st.text_input("Twitter Handle", placeholder="@company")

            if st.form_submit_button("Add Competitor"):
                if comp_name and comp_website:
                    try:
                        db.add_competitor(comp_name, comp_website, comp_linkedin, comp_twitter)
                        st.success(f"✅ Added {comp_name}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to add competitor: {str(e)}")
                else:
                    st.error("Name and website are required")

    st.divider()

    # Connection status
    if analyzer and analyzer.client:
        st.success(f"🔑 OpenAI connected\n\n`{analyzer.model}`")
    else:
        st.warning("🔑 OpenAI not configured")
    st.caption("Manage keys & settings on the **⚙️ Settings** page.")


# ==================== HEADER ====================
def render_header(subtitle):
    competitors = get_competitors()
    try:
        last_scan = db.get_last_scan_time()
        if last_scan:
            hours_ago = (datetime.now(pytz.UTC) - last_scan).total_seconds() / 3600
            last_scan_str = f"{int(hours_ago)}h ago" if hours_ago < 24 else "1d+ ago"
        else:
            last_scan_str = "Never"
    except Exception:
        last_scan_str = "—"

    head_col, m1, m2 = st.columns([3, 1, 1])
    with head_col:
        st.markdown(
            f'<div class="app-header"><h1>🔍 Competitor Intelligence</h1>'
            f'<p>{subtitle}</p></div>',
            unsafe_allow_html=True,
        )
    with m1:
        st.metric("Competitors", len(competitors))
    with m2:
        st.metric("Last Scan", last_scan_str)


# ==================== PAGE: DASHBOARD ====================
if page == PAGES[0]:
    render_header("Executive summary across all tracked competitors")

    try:
        competitors = get_competitors()

        if not competitors:
            st.info("👈 Add competitors from the sidebar to get started")
        else:
            c1, c2, c3, c4 = st.columns(4)
            try:
                active_changes = len(db.get_recent_changes(days=7))
            except Exception:
                active_changes = "N/A"
            try:
                price_changes = len(db.get_price_changes())
            except Exception:
                price_changes = "N/A"
            try:
                job_openings = len(db.get_all_job_openings())
            except Exception:
                job_openings = "N/A"
            try:
                product_launches = len(db.get_product_launches())
            except Exception:
                product_launches = "N/A"

            kpi_card(c1, "🔴", active_changes, "Changes (7d)", GRADIENTS[0])
            kpi_card(c2, "💲", price_changes, "Price Changes", GRADIENTS[1])
            kpi_card(c3, "📋", job_openings, "Job Openings", GRADIENTS[2])
            kpi_card(c4, "🚀", product_launches, "New Products", GRADIENTS[3])

            st.write("")
            st.divider()

            st.markdown("### 📈 Recent Activity")
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### Latest Changes")
                try:
                    recent_changes = db.get_recent_changes(days=7)
                    if recent_changes:
                        changes_df = pd.DataFrame(recent_changes)
                        changes_df['detected_at'] = pd.to_datetime(changes_df['detected_at']).dt.strftime('%Y-%m-%d %H:%M')
                        st.dataframe(
                            changes_df[['competitor_name', 'change_type', 'description', 'detected_at']],
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.info("No recent changes detected")
                except Exception:
                    st.info("Unable to load recent changes")

            with col2:
                st.markdown("#### Competitor Health")
                try:
                    health_data = []
                    for comp in competitors:
                        changes = len(db.get_competitor_changes(comp['id'], days=30))
                        health_data.append({'Competitor': comp['name'], 'Activity (30d)': changes})

                    if health_data:
                        health_df = pd.DataFrame(health_data)
                        fig = px.bar(
                            health_df, x='Competitor', y='Activity (30d)',
                            color='Activity (30d)', color_continuous_scale='Tealgrn'
                        )
                        fig.update_layout(showlegend=False, height=320, margin=dict(t=10, b=10))
                        st.plotly_chart(fig, use_container_width=True)
                except Exception:
                    st.info("Unable to load health metrics")

            st.divider()

            st.markdown("### 🔔 Active Alerts")
            try:
                alerts = db.get_all_alerts()
                if alerts:
                    for alert in alerts[:5]:
                        css = "alert-box" if alert['severity'] == 'high' else "success-box"
                        icon = "⚠️" if alert['severity'] == 'high' else "ℹ️"
                        st.markdown(
                            f'<div class="{css}">{icon} <b>{alert["competitor_name"]}</b>: {alert["description"]}</div>',
                            unsafe_allow_html=True,
                        )
                else:
                    st.success("✅ No alerts at this time")
            except Exception:
                st.info("Unable to load alerts")

    except Exception as e:
        st.error(f"Dashboard error: {str(e)}")

# ==================== PAGE: WEBSITE MONITORING ====================
elif page == PAGES[1]:
    render_header("Track website changes, new features, and content updates")

    try:
        competitors = get_competitors()
        col1, col2 = st.columns([3, 1])

        with col1:
            if competitors:
                selected_competitor = st.selectbox(
                    "Select Competitor", [c['name'] for c in competitors], key="website_select"
                )
            else:
                st.warning("No competitors added yet")
                selected_competitor = None

        with col2:
            st.write("")
            st.write("")
            scan_clicked = st.button("🔄 Scan Now", key="website_scan", use_container_width=True)

        if scan_clicked and selected_competitor:
            with st.spinner("Scanning website..."):
                try:
                    comp = next((c for c in competitors if c['name'] == selected_competitor), None)
                    if comp and scraper:
                        website_data = scraper.scrape_website(comp['website_url'])
                        if website_data and analyzer:
                            analysis = analyzer.analyze_website_changes(website_data, comp['name'])
                            db.add_change(comp['id'], 'website_update', analysis)
                            st.success("✅ Website scan complete")
                        else:
                            st.error("Failed to scan website")
                except Exception as e:
                    st.error(f"Scan failed: {str(e)}")

        st.divider()

        if selected_competitor and competitors:
            comp = next((c for c in competitors if c['name'] == selected_competitor), None)
            if comp:
                try:
                    changes = db.get_competitor_changes(comp['id'], days=30)
                    website_changes = [c for c in changes if c['change_type'] == 'website_update']

                    if website_changes:
                        for change in website_changes[:10]:
                            with st.expander(f"📄 {change['detected_at'][:10]} — Website Update"):
                                st.write(change['description'])
                                if analyzer and analyzer.client:
                                    with st.spinner("Analyzing..."):
                                        try:
                                            ai_insight = analyzer.generate_insight(change['description'])
                                            st.markdown("**🤖 AI Analysis:**")
                                            st.write(ai_insight)
                                        except Exception:
                                            st.info("AI analysis unavailable")
                    else:
                        st.info("No website changes detected yet")
                except Exception as e:
                    st.error(f"Error loading changes: {str(e)}")

    except Exception as e:
        st.error(f"Website monitoring error: {str(e)}")

# ==================== PAGE: PRICING INTELLIGENCE ====================
elif page == PAGES[2]:
    render_header("Monitor pricing changes, plans, and offers")

    try:
        competitors = get_competitors()
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            if competitors:
                pricing_competitor = st.selectbox(
                    "Select Competitor", [c['name'] for c in competitors], key="pricing_select"
                )
            else:
                st.warning("No competitors added")
                pricing_competitor = None

        with col2:
            st.write("")
            st.write("")
            check_clicked = st.button("💰 Check Pricing", key="pricing_check", use_container_width=True)

        with col3:
            st.write("")
            st.write("")
            report_clicked = st.button("📊 Generate Report", key="pricing_generate_report", use_container_width=True)

        if check_clicked and pricing_competitor:
            with st.spinner("Checking pricing..."):
                try:
                    comp = next((c for c in competitors if c['name'] == pricing_competitor), None)
                    if comp and pricing_scraper:
                        pricing_data = pricing_scraper.get_pricing(comp['website_url'])
                        db.add_price_change(comp['id'], json.dumps(pricing_data))
                        st.success("✅ Pricing updated")
                except Exception as e:
                    st.error(f"Failed: {str(e)}")

        if report_clicked and pricing_competitor:
            try:
                comp = next((c for c in competitors if c['name'] == pricing_competitor), None)
                if comp:
                    st.session_state["pricing_report"] = report_generator.generate_executive_summary(comp['id'])
                    st.success("✅ Report ready — download below.")
            except Exception as e:
                st.error(f"Report failed: {str(e)}")

        if st.session_state.get("pricing_report"):
            st.download_button(
                "⬇️ Download Pricing Report (JSON)",
                data=json.dumps(st.session_state["pricing_report"], indent=2, default=str),
                file_name="pricing_report.json",
                mime="application/json",
                key="pricing_report_download",
            )

        st.divider()

        if pricing_competitor and competitors:
            comp = next((c for c in competitors if c['name'] == pricing_competitor), None)
            if comp:
                try:
                    price_history = db.get_competitor_price_history(comp['id'])
                    if price_history:
                        st.markdown("### Latest Pricing Snapshot")
                        latest = price_history[0]
                        st.json(json.loads(latest['pricing_data']))

                        st.markdown("### 📈 Pricing History")
                        timeline_df = pd.DataFrame([
                            {'Date': e['detected_at'][:10], 'Status': '💾 Recorded'} for e in price_history
                        ])
                        st.dataframe(timeline_df, use_container_width=True, hide_index=True)
                    else:
                        st.info("No pricing data recorded yet. Click 'Check Pricing' to start tracking.")
                except Exception as e:
                    st.error(f"Error loading pricing: {str(e)}")

    except Exception as e:
        st.error(f"Pricing intelligence error: {str(e)}")

# ==================== PAGE: HIRING ACTIVITY ====================
elif page == PAGES[3]:
    render_header("Monitor job postings and hiring trends")

    try:
        competitors = get_competitors()
        col1, col2 = st.columns([3, 1])

        with col1:
            if competitors:
                hiring_competitor = st.selectbox(
                    "Select Competitor", [c['name'] for c in competitors], key="hiring_select"
                )
            else:
                st.warning("No competitors added")
                hiring_competitor = None

        with col2:
            st.write("")
            st.write("")
            jobs_clicked = st.button("👥 Scan Jobs", key="hiring_scan", use_container_width=True)

        if jobs_clicked and hiring_competitor:
            with st.spinner("Scanning job postings..."):
                try:
                    comp = next((c for c in competitors if c['name'] == hiring_competitor), None)
                    if comp and hiring_tracker:
                        jobs = hiring_tracker.get_job_postings(comp['name'])
                        for job in jobs:
                            db.add_job_opening(comp['id'], job['title'], job['department'], job.get('description', ''))
                        st.success(f"✅ Found {len(jobs)} job openings")
                except Exception as e:
                    st.error(f"Failed: {str(e)}")

        st.divider()

        if hiring_competitor and competitors:
            comp = next((c for c in competitors if c['name'] == hiring_competitor), None)
            if comp:
                try:
                    jobs = db.get_competitor_job_openings(comp['id'])
                    if jobs:
                        st.markdown("### Active Job Openings")
                        dept_data = {}
                        for job in jobs:
                            dept = job['department'] or 'Other'
                            dept_data[dept] = dept_data.get(dept, 0) + 1

                        col1, col2 = st.columns(2)
                        with col1:
                            fig = px.pie(
                                values=list(dept_data.values()),
                                names=list(dept_data.keys()),
                                title="Openings by Department",
                                color_discrete_sequence=px.colors.sequential.Tealgrn,
                            )
                            fig.update_layout(height=340, margin=dict(t=40, b=10))
                            st.plotly_chart(fig, use_container_width=True)
                        with col2:
                            st.markdown("### Job Titles")
                            job_titles = pd.DataFrame([
                                {'Title': j['title'], 'Department': j['department'] or 'N/A'} for j in jobs[:10]
                            ])
                            st.dataframe(job_titles, use_container_width=True, hide_index=True)
                    else:
                        st.info("No job openings tracked yet")
                except Exception as e:
                    st.error(f"Error loading jobs: {str(e)}")

    except Exception as e:
        st.error(f"Hiring activity error: {str(e)}")

# ==================== PAGE: PRODUCT LAUNCHES ====================
elif page == PAGES[4]:
    render_header("Detect new features, products, and announcements")

    try:
        competitors = get_competitors()
        col1, col2 = st.columns([3, 1])

        with col1:
            if competitors:
                product_competitor = st.selectbox(
                    "Select Competitor", [c['name'] for c in competitors], key="product_select"
                )
            else:
                st.warning("No competitors added")
                product_competitor = None

        with col2:
            st.write("")
            st.write("")
            launch_clicked = st.button("🚀 Check Launches", key="product_check", use_container_width=True)

        if launch_clicked and product_competitor:
            with st.spinner("Checking for product launches..."):
                try:
                    comp = next((c for c in competitors if c['name'] == product_competitor), None)
                    if comp and analyzer:
                        launches = analyzer.detect_product_launches(comp['name'])
                        for launch in launches:
                            db.add_product_launch(
                                comp['id'], launch.get('name'), launch.get('description'), launch.get('url')
                            )
                        st.success(f"✅ Found {len(launches)} product launches")
                except Exception as e:
                    st.error(f"Failed: {str(e)}")

        st.divider()

        if product_competitor and competitors:
            comp = next((c for c in competitors if c['name'] == product_competitor), None)
            if comp:
                try:
                    launches = db.get_competitor_product_launches(comp['id'])
                    if launches:
                        st.markdown("### Recent Product Launches")
                        for launch in launches:
                            with st.expander(f"🎉 {launch['product_name']} ({launch['announced_at'][:10]})"):
                                st.write(launch['description'] or "No description available")
                                if launch['url']:
                                    st.link_button("View Product", launch['url'])
                    else:
                        st.info("No product launches tracked yet")
                except Exception as e:
                    st.error(f"Error loading launches: {str(e)}")

    except Exception as e:
        st.error(f"Product launches error: {str(e)}")

# ==================== PAGE: ALERTS & REPORTS ====================
elif page == PAGES[5]:
    render_header("Send alerts and generate competitive reports")

    competitors = get_competitors()
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📧 Send Alert Email", key="alerts_send_email", use_container_width=True):
            with st.spinner("Sending alerts..."):
                try:
                    recipient = st.session_state.get("alert_email") or "admin@example.com"
                    alert_manager.send_daily_digest(recipient)
                    st.success("✅ Alerts sent successfully")
                except Exception as e:
                    st.error(f"Failed to send: {str(e)}")

    with col2:
        if st.button("📊 Generate Report", key="alerts_generate_report", use_container_width=True):
            try:
                comp_ids = [c['id'] for c in competitors]
                if comp_ids:
                    st.session_state["market_report"] = report_generator.generate_market_analysis(comp_ids)
                    st.success("✅ Report ready — download below.")
                else:
                    st.info("Add competitors first to generate a report.")
            except Exception as e:
                st.error(f"Report failed: {str(e)}")

    with col3:
        report_format = st.selectbox("Format", ["JSON", "Excel", "PDF"], key="alerts_report_format")

    if st.session_state.get("market_report"):
        st.download_button(
            "⬇️ Download Market Report (JSON)",
            data=json.dumps(st.session_state["market_report"], indent=2, default=str),
            file_name="market_report.json",
            mime="application/json",
            key="market_report_download",
        )
        if report_format != "JSON":
            st.caption(f"ℹ️ {report_format} export is not available yet — the report is provided as JSON.")

    st.divider()

    st.markdown("### Alert History")
    severity_options = ["All", "High", "Medium", "Low"]
    default_sev = st.session_state.get("alert_severity_default", "All")
    history_filter = st.selectbox(
        "Filter by severity",
        severity_options,
        index=severity_options.index(default_sev) if default_sev in severity_options else 0,
        key="alerts_history_severity",
    )

    try:
        alerts = db.get_all_alerts()
        if alerts:
            alerts_df = pd.DataFrame(alerts)
            alerts_df['triggered_at'] = pd.to_datetime(alerts_df['triggered_at']).dt.strftime('%Y-%m-%d %H:%M')
            if history_filter != "All":
                alerts_df = alerts_df[alerts_df['severity'].str.lower() == history_filter.lower()]
            st.dataframe(
                alerts_df[['competitor_name', 'description', 'severity', 'triggered_at']],
                use_container_width=True, hide_index=True
            )
        else:
            st.info("No alerts yet")
    except Exception as e:
        st.error(f"Error loading alerts: {str(e)}")

# ==================== PAGE: SETTINGS ====================
elif page == PAGES[6]:
    render_header("All configuration and default settings in one place")

    # ---- OpenAI API ----
    st.markdown('<div class="settings-card"><h3>🔑 OpenAI API</h3></div>', unsafe_allow_html=True)
    current_key = resolve_openai_key()
    if analyzer and analyzer.client:
        st.success(f"✅ Connected using model **{analyzer.model}**")
    elif current_key:
        st.warning("A key is set but the client could not be initialized. Verify the key is valid.")
    else:
        st.info("No OpenAI API key configured yet. Add one below to enable AI analysis.")

    with st.form("openai_settings"):
        key_input = st.text_input(
            "OpenAI API Key", type="password",
            value=st.session_state.get("openai_api_key", ""),
            placeholder="sk-...",
            help="Kept in this session only; never written to disk.",
        )
        model_options = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]
        current_model = resolve_openai_model()
        if current_model not in model_options:
            model_options.insert(0, current_model)
        model_input = st.selectbox("Model", model_options, index=model_options.index(current_model))

        c_a, c_b = st.columns(2)
        with c_a:
            save_clicked = st.form_submit_button("💾 Save & Connect", use_container_width=True)
        with c_b:
            test_clicked = st.form_submit_button("🧪 Test Connection", use_container_width=True)

        if save_clicked:
            st.session_state["openai_api_key"] = key_input.strip()
            st.session_state["openai_model"] = model_input
            ok = analyzer.configure(api_key=key_input.strip() or None, model=model_input)
            if ok:
                st.success("✅ Settings saved and OpenAI connected.")
            else:
                st.error("Saved, but no valid key provided — AI features will use fallback analysis.")

        if test_clicked:
            test_key = key_input.strip() or current_key
            if not test_key:
                st.error("Enter an API key first.")
            else:
                with st.spinner("Testing connection..."):
                    try:
                        analyzer.configure(api_key=test_key, model=model_input)
                        result = analyzer.generate_insight("Test connectivity ping.")
                        st.success("✅ Connection works.")
                        st.caption(f"Sample response: {result[:160]}")
                    except Exception as e:
                        st.error(f"Connection failed: {str(e)}")

    st.caption(
        "💡 On Streamlit Cloud you can instead set `OPENAI_API_KEY` under "
        "**App → Settings → Secrets** so the key persists across restarts."
    )

    st.divider()

    # ---- Alerts ----
    st.markdown('<div class="settings-card"><h3>📧 Alerts</h3></div>', unsafe_allow_html=True)
    a1, a2 = st.columns(2)
    with a1:
        st.text_input("Default Alert Email", key="alert_email", placeholder="alerts@yourcompany.com")
        st.selectbox("Check Frequency", ["Hourly", "6-Hourly", "Daily", "Weekly"], key="alert_frequency")
    with a2:
        st.multiselect(
            "Default Alert Types",
            ["Price Changes", "Hiring Activity", "Product Launches", "Website Changes"],
            key="alert_types",
        )
        st.selectbox("Default Severity Filter", ["All", "High", "Medium", "Low"], key="alert_severity_default")
    st.caption("Changes are saved automatically for this session.")

    st.divider()

    # ---- Monitoring features ----
    st.markdown('<div class="settings-card"><h3>📊 Monitoring Features</h3></div>', unsafe_allow_html=True)
    m1, m2 = st.columns(2)
    with m1:
        st.checkbox("💰 Pricing", key="monitor_pricing")
        st.checkbox("📱 Social Media", key="monitor_social")
    with m2:
        st.checkbox("👥 Hiring Activity", key="monitor_hiring")
        st.checkbox("🚀 Product Launches", key="monitor_products")

    st.divider()

    # ---- Diagnostics ----
    st.markdown('<div class="settings-card"><h3>🩺 Diagnostics</h3></div>', unsafe_allow_html=True)
    d1, d2, d3 = st.columns(3)
    with d1:
        st.metric("OpenAI", "Connected" if (analyzer and analyzer.client) else "Not configured")
    with d2:
        st.metric("Database", "OK" if db else "Error")
    with d3:
        st.metric("Competitors", len(get_competitors()))

# ==================== FOOTER ====================
st.divider()
st.markdown("""
<div style='text-align: center; color: #888; margin-top: 20px;'>
    <p>🚀 Competitor Intelligence Agent v1.0 | Powered by OpenAI & Streamlit</p>
    <p style='font-size: 12px;'>Built with ❤️ for founders and marketers</p>
</div>
""", unsafe_allow_html=True)
