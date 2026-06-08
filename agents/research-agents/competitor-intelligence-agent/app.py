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

# Custom CSS for professional styling
st.markdown("""
<style>
    * {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3);
    }

    .alert-box {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 15px;
        border-radius: 8px;
        color: white;
        margin: 10px 0;
    }

    .success-box {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 15px;
        border-radius: 8px;
        color: white;
        margin: 10px 0;
    }

    .header-title {
        color: #1f77b4;
        font-weight: 700;
        font-size: 32px;
        margin-bottom: 10px;
    }

    .stMetric {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #667eea;
    }
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


# ==================== API KEY RESOLUTION ====================
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


# Apply the resolved config to the (cached) analyzer on every run so a key
# entered on the Settings tab — or set via st.secrets — takes effect immediately.
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


# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("### ⚙️ Configuration")

    # Competitor input
    with st.form("add_competitor"):
        st.subheader("Add Competitor")
        comp_name = st.text_input("Competitor Name", placeholder="e.g., Segment, Mixpanel")
        comp_website = st.text_input("Website URL", placeholder="https://example.com")
        comp_linkedin = st.text_input("LinkedIn Company URL", placeholder="linkedin.com/company/...")
        comp_twitter = st.text_input("Twitter Handle", placeholder="@company")

        if st.form_submit_button("➕ Add Competitor"):
            if comp_name and comp_website:
                try:
                    db.add_competitor(comp_name, comp_website, comp_linkedin, comp_twitter)
                    st.success(f"✅ Added {comp_name}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to add competitor: {str(e)}")
            else:
                st.error("Please fill in required fields")

    st.divider()

    # Alert settings
    st.subheader("🔔 Alert Settings")
    alert_email = st.text_input(
        "Alert Email",
        value=st.session_state.get("alert_email", os.getenv("ALERT_EMAIL", "")),
        key="sidebar_alert_email",
    )
    alert_frequency = st.selectbox(
        "Check Frequency",
        ["Hourly", "6-Hourly", "Daily", "Weekly"],
        key="sidebar_alert_frequency",
    )

    # Feature toggles
    st.subheader("📊 Monitoring Features")
    col1, col2 = st.columns(2)
    with col1:
        monitor_pricing = st.checkbox("💰 Pricing", value=True, key="toggle_pricing")
        monitor_social = st.checkbox("📱 Social Media", value=True, key="toggle_social")
    with col2:
        monitor_hiring = st.checkbox("👥 Hiring Activity", value=True, key="toggle_hiring")
        monitor_products = st.checkbox("🚀 Product Launches", value=True, key="toggle_products")

    st.divider()

    # API connection status
    st.subheader("🔑 OpenAI Connection")
    if analyzer and analyzer.client:
        st.success(f"✅ Connected ({analyzer.model})")
    else:
        st.warning("⚠️ No API key configured")
    st.caption("Configure your key on the **⚙️ Settings** tab.")

# ==================== MAIN DASHBOARD ====================
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.markdown('<h1 class="header-title">🔍 Competitor Intelligence</h1>', unsafe_allow_html=True)

with col2:
    try:
        competitors = get_competitors()
        st.metric("Competitors Tracked", len(competitors))
    except Exception:
        st.metric("Competitors Tracked", "Error")

with col3:
    try:
        last_scan = db.get_last_scan_time()
        if last_scan:
            time_ago = datetime.now(pytz.UTC) - last_scan
            hours_ago = time_ago.total_seconds() / 3600
            st.metric("Last Scan", f"{int(hours_ago)}h ago" if hours_ago < 24 else "1d+ ago")
        else:
            st.metric("Last Scan", "Never")
    except Exception:
        st.metric("Last Scan", "Error")

# ==================== TABS ====================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Dashboard",
    "🌐 Website Monitoring",
    "💰 Pricing Intelligence",
    "👥 Hiring Activity",
    "🚀 Product Launches",
    "📧 Alerts & Reports",
    "⚙️ Settings"
])

# ==================== TAB 1: DASHBOARD ====================
with tab1:
    st.markdown("## Executive Summary")

    try:
        competitors = get_competitors()

        if not competitors:
            st.info("👈 Add competitors from the sidebar to get started")
        else:
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                try:
                    active_changes = len(db.get_recent_changes(days=7))
                    st.metric("🔴 Changes (7d)", active_changes)
                except Exception:
                    st.metric("🔴 Changes (7d)", "N/A")

            with col2:
                try:
                    price_changes = len(db.get_price_changes())
                    st.metric("💲 Price Changes", price_changes)
                except Exception:
                    st.metric("💲 Price Changes", "N/A")

            with col3:
                try:
                    job_openings = len(db.get_all_job_openings())
                    st.metric("📋 Job Openings", job_openings)
                except Exception:
                    st.metric("📋 Job Openings", "N/A")

            with col4:
                try:
                    product_launches = len(db.get_product_launches())
                    st.metric("🚀 New Products", product_launches)
                except Exception:
                    st.metric("🚀 New Products", "N/A")

            st.divider()

            # Recent activity
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
                        comp_id = comp['id']
                        changes = len(db.get_competitor_changes(comp_id, days=30))
                        health_data.append({
                            'Competitor': comp['name'],
                            'Activity (30d)': changes
                        })

                    if health_data:
                        health_df = pd.DataFrame(health_data)
                        fig = px.bar(
                            health_df,
                            x='Competitor',
                            y='Activity (30d)',
                            color='Activity (30d)',
                            color_continuous_scale='Viridis'
                        )
                        fig.update_layout(showlegend=False, height=300)
                        st.plotly_chart(fig, use_container_width=True)
                except Exception:
                    st.info("Unable to load health metrics")

            st.divider()

            # Alerts
            st.markdown("### 🔔 Active Alerts")
            try:
                alerts = db.get_all_alerts()
                if alerts:
                    for alert in alerts[:5]:
                        if alert['severity'] == 'high':
                            st.markdown(f'<div class="alert-box">⚠️ **{alert["competitor_name"]}**: {alert["description"]}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="success-box">ℹ️ **{alert["competitor_name"]}**: {alert["description"]}</div>', unsafe_allow_html=True)
                else:
                    st.success("✅ No alerts at this time")
            except Exception:
                st.info("Unable to load alerts")

    except Exception as e:
        st.error(f"Dashboard error: {str(e)}")

# ==================== TAB 2: WEBSITE MONITORING ====================
with tab2:
    st.markdown("## Website Monitoring")
    st.write("Track website changes, new features, and content updates")

    try:
        competitors = get_competitors()

        col1, col2 = st.columns([3, 1])

        with col1:
            if competitors:
                selected_competitor = st.selectbox(
                    "Select Competitor",
                    [c['name'] for c in competitors],
                    key="website_select"
                )
            else:
                st.warning("No competitors added yet")
                selected_competitor = None

        with col2:
            if st.button("🔄 Scan Now", key="website_scan"):
                if selected_competitor:
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

        # Website monitoring results
        if selected_competitor and competitors:
            comp = next((c for c in competitors if c['name'] == selected_competitor), None)
            if comp:
                try:
                    changes = db.get_competitor_changes(comp['id'], days=30)
                    website_changes = [c for c in changes if c['change_type'] == 'website_update']

                    if website_changes:
                        for idx, change in enumerate(website_changes[:10]):
                            with st.expander(f"📄 {change['detected_at'][:10]} - Website Update"):
                                st.write(change['description'])

                                if analyzer:
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

# ==================== TAB 3: PRICING INTELLIGENCE ====================
with tab3:
    st.markdown("## Pricing Intelligence")
    st.write("Monitor pricing changes, plans, and offers")

    try:
        competitors = get_competitors()

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            if competitors:
                pricing_competitor = st.selectbox(
                    "Select Competitor",
                    [c['name'] for c in competitors],
                    key="pricing_select"
                )
            else:
                st.warning("No competitors added")
                pricing_competitor = None

        with col2:
            if st.button("💰 Check Pricing", key="pricing_check"):
                if pricing_competitor and competitors:
                    with st.spinner("Checking pricing..."):
                        try:
                            comp = next((c for c in competitors if c['name'] == pricing_competitor), None)
                            if comp and pricing_scraper:
                                pricing_data = pricing_scraper.get_pricing(comp['website_url'])
                                db.add_price_change(comp['id'], json.dumps(pricing_data))
                                st.success("✅ Pricing updated")
                        except Exception as e:
                            st.error(f"Failed: {str(e)}")

        with col3:
            if st.button("📊 Generate Report", key="pricing_generate_report"):
                if pricing_competitor and competitors:
                    try:
                        comp = next((c for c in competitors if c['name'] == pricing_competitor), None)
                        if comp:
                            st.session_state["pricing_report"] = report_generator.generate_executive_summary(comp['id'])
                            st.success("✅ Report ready — download below.")
                    except Exception as e:
                        st.error(f"Report failed: {str(e)}")

        # Offer the generated report for download (persists across reruns)
        if st.session_state.get("pricing_report"):
            st.download_button(
                "⬇️ Download Pricing Report (JSON)",
                data=json.dumps(st.session_state["pricing_report"], indent=2, default=str),
                file_name="pricing_report.json",
                mime="application/json",
                key="pricing_report_download",
            )

        st.divider()

        # Pricing history
        if pricing_competitor and competitors:
            comp = next((c for c in competitors if c['name'] == pricing_competitor), None)
            if comp:
                try:
                    price_history = db.get_competitor_price_history(comp['id'])

                    if price_history:
                        st.markdown("### Pricing History")

                        # Display latest pricing
                        latest = price_history[0]
                        st.json(json.loads(latest['pricing_data']))

                        # Pricing timeline
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("### 📈 Pricing Changes Timeline")
                            timeline_data = []
                            for entry in price_history:
                                timeline_data.append({
                                    'Date': entry['detected_at'][:10],
                                    'Status': '💾 Recorded'
                                })

                            if timeline_data:
                                timeline_df = pd.DataFrame(timeline_data)
                                st.dataframe(timeline_df, use_container_width=True, hide_index=True)
                    else:
                        st.info("No pricing data recorded yet. Click 'Check Pricing' to start tracking.")
                except Exception as e:
                    st.error(f"Error loading pricing: {str(e)}")

    except Exception as e:
        st.error(f"Pricing intelligence error: {str(e)}")

# ==================== TAB 4: HIRING ACTIVITY ====================
with tab4:
    st.markdown("## Hiring Activity Tracking")
    st.write("Monitor job postings and hiring trends")

    try:
        competitors = get_competitors()

        col1, col2 = st.columns([3, 1])

        with col1:
            if competitors:
                hiring_competitor = st.selectbox(
                    "Select Competitor",
                    [c['name'] for c in competitors],
                    key="hiring_select"
                )
            else:
                st.warning("No competitors added")
                hiring_competitor = None

        with col2:
            if st.button("👥 Scan Jobs", key="hiring_scan"):
                if hiring_competitor and competitors:
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

        # Job listings
        if hiring_competitor and competitors:
            comp = next((c for c in competitors if c['name'] == hiring_competitor), None)
            if comp:
                try:
                    jobs = db.get_competitor_job_openings(comp['id'])

                    if jobs:
                        st.markdown("### Active Job Openings")

                        # Department breakdown
                        dept_data = {}
                        for job in jobs:
                            dept = job['department'] or 'Other'
                            dept_data[dept] = dept_data.get(dept, 0) + 1

                        col1, col2 = st.columns(2)

                        with col1:
                            fig = px.pie(
                                values=list(dept_data.values()),
                                names=list(dept_data.keys()),
                                title="Openings by Department"
                            )
                            st.plotly_chart(fig, use_container_width=True)

                        with col2:
                            st.markdown("### Job Titles")
                            job_titles = pd.DataFrame([
                                {'Title': j['title'], 'Department': j['department'] or 'N/A'}
                                for j in jobs[:10]
                            ])
                            st.dataframe(job_titles, use_container_width=True, hide_index=True)
                    else:
                        st.info("No job openings tracked yet")
                except Exception as e:
                    st.error(f"Error loading jobs: {str(e)}")

    except Exception as e:
        st.error(f"Hiring activity error: {str(e)}")

# ==================== TAB 5: PRODUCT LAUNCHES ====================
with tab5:
    st.markdown("## Product Launch Tracker")
    st.write("Detect new features, products, and announcements")

    try:
        competitors = get_competitors()

        col1, col2 = st.columns([3, 1])

        with col1:
            if competitors:
                product_competitor = st.selectbox(
                    "Select Competitor",
                    [c['name'] for c in competitors],
                    key="product_select"
                )
            else:
                st.warning("No competitors added")
                product_competitor = None

        with col2:
            if st.button("🚀 Check Launches", key="product_check"):
                if product_competitor and competitors:
                    with st.spinner("Checking for product launches..."):
                        try:
                            comp = next((c for c in competitors if c['name'] == product_competitor), None)
                            if comp and analyzer:
                                launches = analyzer.detect_product_launches(comp['name'])
                                for launch in launches:
                                    db.add_product_launch(
                                        comp['id'],
                                        launch.get('name'),
                                        launch.get('description'),
                                        launch.get('url')
                                    )
                                st.success(f"✅ Found {len(launches)} product launches")
                        except Exception as e:
                            st.error(f"Failed: {str(e)}")

        st.divider()

        # Product launches
        if product_competitor and competitors:
            comp = next((c for c in competitors if c['name'] == product_competitor), None)
            if comp:
                try:
                    launches = db.get_competitor_product_launches(comp['id'])

                    if launches:
                        st.markdown("### Recent Product Launches")

                        for idx, launch in enumerate(launches):
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

# ==================== TAB 6: ALERTS & REPORTS ====================
with tab6:
    st.markdown("## Alerts & Reports")

    competitors = get_competitors()

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📧 Send Alert Email", key="alerts_send_email"):
            with st.spinner("Sending alerts..."):
                try:
                    recipient = st.session_state.get("alert_email") or alert_email or "admin@example.com"
                    alert_manager.send_daily_digest(recipient)
                    st.success("✅ Alerts sent successfully")
                except Exception as e:
                    st.error(f"Failed to send: {str(e)}")

    with col2:
        if st.button("📊 Generate Report", key="alerts_generate_report"):
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

    # Offer the generated market report for download
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

    # Alert settings
    st.markdown("### 🔔 Alert Configuration")

    col1, col2 = st.columns(2)

    with col1:
        alert_types = st.multiselect(
            "Alert Types",
            ["Price Changes", "Hiring Activity", "Product Launches", "Website Changes"],
            default=["Price Changes", "Hiring Activity", "Product Launches"],
            key="alerts_types",
        )

    with col2:
        severity_filter = st.selectbox(
            "Severity Level",
            ["All", "High", "Medium", "Low"],
            key="alerts_severity",
        )

    st.divider()

    # Alert history
    st.markdown("### Alert History")
    try:
        alerts = db.get_all_alerts()

        if alerts:
            alerts_df = pd.DataFrame(alerts)
            alerts_df['triggered_at'] = pd.to_datetime(alerts_df['triggered_at']).dt.strftime('%Y-%m-%d %H:%M')

            if severity_filter != "All":
                alerts_df = alerts_df[alerts_df['severity'].str.lower() == severity_filter.lower()]

            st.dataframe(
                alerts_df[['competitor_name', 'description', 'severity', 'triggered_at']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No alerts yet")
    except Exception as e:
        st.error(f"Error loading alerts: {str(e)}")

# ==================== TAB 7: SETTINGS ====================
with tab7:
    st.markdown("## ⚙️ Configuration")
    st.write("Configure API access and application settings. Settings apply for the current session.")

    # ---- OpenAI configuration ----
    st.markdown("### 🔑 OpenAI API")

    current_key = resolve_openai_key()
    if analyzer and analyzer.client:
        st.success(f"✅ OpenAI is connected using model **{analyzer.model}**")
    elif current_key:
        st.warning("A key is set but the client could not be initialized. Verify the key is valid.")
    else:
        st.info("No OpenAI API key configured yet. Add one below to enable AI analysis.")

    with st.form("openai_settings"):
        key_input = st.text_input(
            "OpenAI API Key",
            type="password",
            value=st.session_state.get("openai_api_key", ""),
            placeholder="sk-...",
            help="Your key is kept in this session only and is never written to disk.",
        )

        model_options = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]
        current_model = resolve_openai_model()
        if current_model not in model_options:
            model_options.insert(0, current_model)
        model_input = st.selectbox(
            "Model",
            model_options,
            index=model_options.index(current_model),
            help="The OpenAI model used for all AI analysis.",
        )

        col_a, col_b = st.columns(2)
        with col_a:
            save_clicked = st.form_submit_button("💾 Save & Connect")
        with col_b:
            test_clicked = st.form_submit_button("🧪 Test Connection")

        if save_clicked:
            st.session_state["openai_api_key"] = key_input.strip()
            st.session_state["openai_model"] = model_input
            ok = analyzer.configure(api_key=key_input.strip() or None, model=model_input)
            if ok:
                st.success("✅ Settings saved and OpenAI connected.")
            else:
                st.error("Saved, but no valid key was provided — AI features will use fallback analysis.")

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

    # ---- Alert configuration ----
    st.markdown("### 📧 Alerts")
    alert_email_setting = st.text_input(
        "Default Alert Email",
        value=st.session_state.get("alert_email", os.getenv("ALERT_EMAIL", "")),
        placeholder="alerts@yourcompany.com",
        key="settings_alert_email",
    )
    if st.button("💾 Save Alert Email", key="settings_save_alert_email"):
        st.session_state["alert_email"] = alert_email_setting.strip()
        st.success("✅ Alert email saved.")

    st.divider()

    # ---- Diagnostics ----
    st.markdown("### 🩺 Diagnostics")
    diag_col1, diag_col2 = st.columns(2)
    with diag_col1:
        st.metric("OpenAI", "Connected" if (analyzer and analyzer.client) else "Not configured")
    with diag_col2:
        st.metric("Database", "OK" if db else "Error")

# ==================== FOOTER ====================
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; margin-top: 30px;'>
    <p>🚀 Competitor Intelligence Agent v1.0 | Powered by OpenAI & Streamlit</p>
    <p style='font-size: 12px;'>Built with ❤️ for founders and marketers</p>
</div>
""", unsafe_allow_html=True)
