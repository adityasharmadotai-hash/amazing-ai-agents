"""
Competitor Intelligence Agent - Main Streamlit Application
Monitors competitors across web, pricing, social media, hiring, and product launches
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import Database
from ai_analysis import CompetitorAnalyzer
from scraper import WebScraper, PricingScraper, HiringTracker
from alerts import AlertManager
import pytz

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
    """Initialize all components"""
    db = Database("competitors.db")
    analyzer = CompetitorAnalyzer()
    scraper = WebScraper()
    pricing_scraper = PricingScraper()
    hiring_tracker = HiringTracker()
    alert_manager = AlertManager(db)
    return db, analyzer, scraper, pricing_scraper, hiring_tracker, alert_manager

db, analyzer, scraper, pricing_scraper, hiring_tracker, alert_manager = init_components()

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
                db.add_competitor(comp_name, comp_website, comp_linkedin, comp_twitter)
                st.success(f"✅ Added {comp_name}")
                st.rerun()
            else:
                st.error("Please fill in required fields")
    
    st.divider()
    
    # Alert settings
    st.subheader("🔔 Alert Settings")
    alert_email = st.text_input("Alert Email", value=os.getenv("ALERT_EMAIL", ""))
    alert_frequency = st.selectbox("Check Frequency", ["Hourly", "6-Hourly", "Daily", "Weekly"])
    
    # Feature toggles
    st.subheader("📊 Monitoring Features")
    col1, col2 = st.columns(2)
    with col1:
        monitor_pricing = st.checkbox("💰 Pricing", value=True)
        monitor_social = st.checkbox("📱 Social Media", value=True)
    with col2:
        monitor_hiring = st.checkbox("👥 Hiring Activity", value=True)
        monitor_products = st.checkbox("🚀 Product Launches", value=True)
    
    st.divider()
    
    # API Configuration
    st.subheader("🔑 API Keys")
    openai_key = st.text_input("OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
    
    if st.button("💾 Save Settings"):
        st.success("Settings saved!")

# ==================== MAIN DASHBOARD ====================
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.markdown('<h1 class="header-title">🔍 Competitor Intelligence</h1>', unsafe_allow_html=True)

with col2:
    st.metric("Competitors Tracked", len(db.get_competitors()))

with col3:
    last_scan = db.get_last_scan_time()
    if last_scan:
        time_ago = datetime.now(pytz.UTC) - last_scan
        hours_ago = time_ago.total_seconds() / 3600
        st.metric("Last Scan", f"{int(hours_ago)}h ago" if hours_ago < 24 else "1d+ ago")
    else:
        st.metric("Last Scan", "Never")

# ==================== TABS ====================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Dashboard",
    "🌐 Website Monitoring",
    "💰 Pricing Intelligence",
    "👥 Hiring Activity",
    "🚀 Product Launches",
    "📧 Alerts & Reports"
])

# ==================== TAB 1: DASHBOARD ====================
with tab1:
    st.markdown("## Executive Summary")
    
    competitors = db.get_competitors()
    
    if not competitors:
        st.info("👈 Add competitors from the sidebar to get started")
    else:
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            active_changes = len(db.get_recent_changes(days=7))
            st.metric("🔴 Changes (7d)", active_changes)
        
        with col2:
            price_changes = len(db.get_price_changes())
            st.metric("💲 Price Changes", price_changes)
        
        with col3:
            job_openings = len(db.get_all_job_openings())
            st.metric("📋 Job Openings", job_openings)
        
        with col4:
            product_launches = len(db.get_product_launches())
            st.metric("🚀 New Products", product_launches)
        
        st.divider()
        
        # Recent activity
        st.markdown("### 📈 Recent Activity")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Latest Changes")
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
        
        with col2:
            st.markdown("#### Competitor Health")
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
        
        st.divider()
        
        # Alerts
        st.markdown("### 🔔 Active Alerts")
        alerts = db.get_all_alerts()
        if alerts:
            for alert in alerts[:5]:
                if alert['severity'] == 'high':
                    st.markdown(f'<div class="alert-box">⚠️ **{alert["competitor_name"]}**: {alert["description"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="success-box">ℹ️ **{alert["competitor_name"]}**: {alert["description"]}</div>', unsafe_allow_html=True)
        else:
            st.success("✅ No alerts at this time")

# ==================== TAB 2: WEBSITE MONITORING ====================
with tab2:
    st.markdown("## Website Monitoring")
    st.write("Track website changes, new features, and content updates")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        selected_competitor = st.selectbox(
            "Select Competitor",
            [c['name'] for c in competitors] if competitors else []
        )
    
    with col2:
        if st.button("🔄 Scan Now"):
            with st.spinner("Scanning website..."):
                if selected_competitor:
                    comp = next((c for c in competitors if c['name'] == selected_competitor), None)
                    if comp:
                        try:
                            website_data = scraper.scrape_website(comp['website_url'])
                            analysis = analyzer.analyze_website_changes(website_data, comp['name'])
                            db.add_change(comp['id'], 'website_update', analysis)
                            st.success("✅ Website scan complete")
                        except Exception as e:
                            st.error(f"Scan failed: {str(e)}")
    
    st.divider()
    
    # Website monitoring results
    if selected_competitor:
        comp = next((c for c in competitors if c['name'] == selected_competitor), None)
        if comp:
            changes = db.get_competitor_changes(comp['id'], days=30)
            website_changes = [c for c in changes if c['change_type'] == 'website_update']
            
            if website_changes:
                for change in website_changes[:10]:
                    with st.expander(f"📄 {change['detected_at'][:10]} - Website Update"):
                        st.write(change['description'])
                        
                        # AI Analysis
                        with st.spinner("Analyzing..."):
                            ai_insight = analyzer.generate_insight(change['description'])
                            st.markdown("**🤖 AI Analysis:**")
                            st.write(ai_insight)
            else:
                st.info("No website changes detected yet")

# ==================== TAB 3: PRICING INTELLIGENCE ====================
with tab3:
    st.markdown("## Pricing Intelligence")
    st.write("Monitor pricing changes, plans, and offers")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        pricing_competitor = st.selectbox(
            "Select Competitor",
            [c['name'] for c in competitors] if competitors else [],
            key="pricing_select"
        )
    
    with col2:
        if st.button("💰 Check Pricing"):
            with st.spinner("Checking pricing..."):
                if pricing_competitor:
                    comp = next((c for c in competitors if c['name'] == pricing_competitor), None)
                    if comp:
                        try:
                            pricing_data = pricing_scraper.get_pricing(comp['website_url'])
                            db.add_price_change(comp['id'], json.dumps(pricing_data))
                            st.success("✅ Pricing updated")
                        except Exception as e:
                            st.error(f"Failed: {str(e)}")
    
    with col3:
        if st.button("📊 Generate Report"):
            st.info("Report generation in progress...")
    
    st.divider()
    
    # Pricing history
    if pricing_competitor:
        comp = next((c for c in competitors if c['name'] == pricing_competitor), None)
        if comp:
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

# ==================== TAB 4: HIRING ACTIVITY ====================
with tab4:
    st.markdown("## Hiring Activity Tracking")
    st.write("Monitor job postings and hiring trends")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        hiring_competitor = st.selectbox(
            "Select Competitor",
            [c['name'] for c in competitors] if competitors else [],
            key="hiring_select"
        )
    
    with col2:
        if st.button("👥 Scan Jobs"):
            with st.spinner("Scanning job postings..."):
                if hiring_competitor:
                    comp = next((c for c in competitors if c['name'] == hiring_competitor), None)
                    if comp:
                        try:
                            jobs = hiring_tracker.get_job_postings(comp['name'])
                            for job in jobs:
                                db.add_job_opening(comp['id'], job['title'], job['department'], job.get('description', ''))
                            st.success(f"✅ Found {len(jobs)} job openings")
                        except Exception as e:
                            st.error(f"Failed: {str(e)}")
    
    st.divider()
    
    # Job listings
    if hiring_competitor:
        comp = next((c for c in competitors if c['name'] == hiring_competitor), None)
        if comp:
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

# ==================== TAB 5: PRODUCT LAUNCHES ====================
with tab5:
    st.markdown("## Product Launch Tracker")
    st.write("Detect new features, products, and announcements")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        product_competitor = st.selectbox(
            "Select Competitor",
            [c['name'] for c in competitors] if competitors else [],
            key="product_select"
        )
    
    with col2:
        if st.button("🚀 Check Launches"):
            with st.spinner("Checking for product launches..."):
                if product_competitor:
                    comp = next((c for c in competitors if c['name'] == product_competitor), None)
                    if comp:
                        try:
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
    if product_competitor:
        comp = next((c for c in competitors if c['name'] == product_competitor), None)
        if comp:
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

# ==================== TAB 6: ALERTS & REPORTS ====================
with tab6:
    st.markdown("## Alerts & Reports")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📧 Send Alert Email"):
            with st.spinner("Sending alerts..."):
                try:
                    alert_manager.send_daily_digest(alert_email or "admin@example.com")
                    st.success("✅ Alerts sent successfully")
                except Exception as e:
                    st.error(f"Failed to send: {str(e)}")
    
    with col2:
        if st.button("📊 Generate Report"):
            st.info("Generating comprehensive report...")
    
    with col3:
        report_format = st.selectbox("Format", ["PDF", "Excel", "JSON"])
    
    st.divider()
    
    # Alert settings
    st.markdown("### 🔔 Alert Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        alert_types = st.multiselect(
            "Alert Types",
            ["Price Changes", "Hiring Activity", "Product Launches", "Website Changes"],
            default=["Price Changes", "Hiring Activity", "Product Launches"]
        )
    
    with col2:
        severity_filter = st.selectbox(
            "Severity Level",
            ["All", "High", "Medium", "Low"]
        )
    
    st.divider()
    
    # Alert history
    st.markdown("### Alert History")
    alerts = db.get_all_alerts()
    
    if alerts:
        alerts_df = pd.DataFrame(alerts)
        alerts_df['triggered_at'] = pd.to_datetime(alerts_df['triggered_at']).dt.strftime('%Y-%m-%d %H:%M')
        
        st.dataframe(
            alerts_df[['competitor_name', 'description', 'severity', 'triggered_at']],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No alerts yet")

# ==================== FOOTER ====================
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; margin-top: 30px;'>
    <p>🚀 Competitor Intelligence Agent v1.0 | Powered by OpenAI & Streamlit</p>
    <p style='font-size: 12px;'>Built with ❤️ for founders and marketers</p>
</div>
""", unsafe_allow_html=True)
