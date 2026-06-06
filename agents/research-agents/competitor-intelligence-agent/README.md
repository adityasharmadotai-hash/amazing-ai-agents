# 🔍 Competitor Intelligence Agent

A production-ready AI-powered competitive intelligence platform built with Python, Streamlit, and OpenAI. Monitor competitors across pricing, hiring, product launches, and social media in real-time.

**Current Version:** 1.0.0 | **Status:** Production-Ready

---

## 📊 Key Features

### 🌐 **Website Monitoring**
- Real-time website change detection
- Content hashing for efficient comparison
- New section/feature identification
- Automated change analysis with AI
- Historical snapshots and version tracking

### 💰 **Pricing Intelligence**
- Automatic pricing page scraping
- Plan comparison tracking
- Price change detection and alerts
- Historical pricing data
- Competitive pricing analysis

### 👥 **Hiring Activity Tracking**
- Job opening discovery from multiple sources
  - LinkedIn
  - Built-in Jobs
  - AngelList
  - Company careers pages
- Department-level hiring insights
- Hiring intensity analysis (Normal/Medium/High)
- Role-based growth pattern detection

### 🚀 **Product Launch Detection**
- New feature and product announcements
- Launch date tracking
- AI-powered product strategy analysis
- Competitive feature comparison

### 📱 **Social Media Monitoring**
- Twitter/X activity tracking
- LinkedIn company updates
- GitHub repository activity
- Engagement metrics
- Follower growth tracking

### 📧 **Intelligent Alerts**
- Real-time high-priority notifications
- Daily digest emails
- Weekly comprehensive reports
- Customizable alert rules
- Email template system

### 📊 **Interactive Dashboard**
- Real-time metrics and KPIs
- Competitor health scores
- Activity timeline
- Multi-competitor comparison
- Export capabilities (PDF, Excel, JSON)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- OpenAI API key
- SMTP email credentials (Gmail recommended)
- SQLite3 (included with Python)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/competitor-intelligence-agent.git
cd competitor-intelligence-agent
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your API keys and credentials
nano .env
```

### Required Environment Variables

```bash
# Critical
OPENAI_API_KEY=sk-your-key
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password
ALERT_EMAIL=alerts@yourcompany.com

# Optional but recommended
LINKEDIN_EMAIL=your-linkedin-email
TWITTER_API_KEY=your-twitter-key
```

### Launch the Application

```bash
streamlit run app.py
```

Open your browser to `http://localhost:8501`

---

## 📋 How to Use

### 1. **Add Competitors**
- Go to the sidebar
- Fill in competitor name, website URL, and optional social media handles
- Click "Add Competitor"

### 2. **Monitor Website Changes**
- Select competitor in "Website Monitoring" tab
- Click "Scan Now" to analyze current website
- View change history and AI-powered insights

### 3. **Track Pricing**
- Select competitor in "Pricing Intelligence" tab
- Click "Check Pricing" to extract pricing data
- View pricing timeline and compare plans

### 4. **Monitor Hiring**
- Select competitor in "Hiring Activity" tab
- Click "Scan Jobs" to find open positions
- Analyze by department and role

### 5. **Detect Product Launches**
- Select competitor in "Product Launches" tab
- Click "Check Launches" to find new products
- Review launch details and competitive impact

### 6. **Configure Alerts**
- Set your alert email in sidebar
- Choose monitoring features to enable
- Select alert frequency
- Receive daily digests and weekly reports

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Streamlit UI Layer                      │
│        (Dashboard, Tabs, Forms, Visualizations)          │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
    ┌────────┐  ┌──────────┐  ┌──────────┐
    │ Scraper│  │ AI Engine│  │ Alerts   │
    │ Module │  │ (OpenAI) │  │ Module   │
    └────────┘  └──────────┘  └──────────┘
        │              │              │
        └──────────────┼──────────────┘
                       │
                ┌──────▼──────┐
                │  Database   │
                │  (SQLite)   │
                └─────────────┘
```

### Components

| Component | Purpose | Technology |
|-----------|---------|-----------|
| **app.py** | Main Streamlit application | Streamlit, Plotly |
| **database.py** | Data persistence | SQLite, Python sqlite3 |
| **scraper.py** | Web data collection | BeautifulSoup, Requests |
| **ai_analysis.py** | Intelligence & insights | OpenAI GPT-4o |
| **alerts.py** | Notifications & reports | SMTP, Jinja2 |

---

## 📊 Data Models

### Competitors Table
```sql
- id (INTEGER PRIMARY KEY)
- name (TEXT UNIQUE)
- website_url (TEXT)
- linkedin_url (TEXT)
- twitter_handle (TEXT)
- added_at (TIMESTAMP)
- last_scanned (TIMESTAMP)
```

### Changes Table
```sql
- id (INTEGER PRIMARY KEY)
- competitor_id (FOREIGN KEY)
- change_type (TEXT) -- 'website_update', 'pricing_change', 'hiring', 'product_launch'
- description (TEXT)
- detected_at (TIMESTAMP)
- severity (TEXT) -- 'high', 'medium', 'low'
```

### Price Changes Table
```sql
- id (INTEGER PRIMARY KEY)
- competitor_id (FOREIGN KEY)
- pricing_data (TEXT - JSON)
- detected_at (TIMESTAMP)
```

### Job Openings Table
```sql
- id (INTEGER PRIMARY KEY)
- competitor_id (FOREIGN KEY)
- title (TEXT)
- department (TEXT)
- description (TEXT)
- discovered_at (TIMESTAMP)
- url (TEXT)
```

### Alerts Table
```sql
- id (INTEGER PRIMARY KEY)
- competitor_id (FOREIGN KEY)
- description (TEXT)
- severity (TEXT)
- triggered_at (TIMESTAMP)
- sent (BOOLEAN)
```

---

## 🤖 AI Features

### OpenAI Integration
The system uses GPT-4o for:

1. **Website Analysis**
   - Automatic change summarization
   - Feature extraction
   - Strategic implication analysis

2. **Pricing Analysis**
   - Price change implications
   - Strategy detection
   - Competitive positioning insights

3. **Hiring Intelligence**
   - Growth area identification
   - Strategic direction prediction
   - Organizational focus analysis

4. **Threat Assessment**
   - Competitive threat identification
   - Vulnerability analysis
   - Recommended counter-strategies

5. **Report Generation**
   - Executive summaries
   - Threat reports
   - Market analysis
   - Actionable recommendations

### Fallback Mechanisms
- Uses basic NLP when API fails
- Cached results for reliability
- Graceful degradation with informative messages

---

## 📧 Email Alert System

### Alert Types

| Alert Type | Trigger | Severity |
|-----------|---------|----------|
| Price Change | Pricing modification detected | High |
| New Job Posting | Job opening discovered | Medium |
| Product Launch | New feature/product announced | High |
| Website Update | Content changes detected | Medium |
| Hiring Spike | Unusual hiring activity | High |

### Email Templates

- **Real-time Alert**: Immediate notification for high-priority events
- **Daily Digest**: Summary of all changes in last 24 hours
- **Weekly Report**: Comprehensive competitive landscape analysis
- **Threat Alert**: Specific competitive threats identified

### Configuration

```python
# Receive daily digest at 9 AM
alert_frequency = "Daily"

# Weekly report every Monday
report_frequency = "Weekly"

# Custom alert rules
enable_price_alerts = True
enable_hiring_alerts = True
price_alert_threshold = 5  # percent change
```

---

## 🔄 Automated Monitoring

### Scheduled Tasks (Configurable)

```python
PRICE_CHECK_INTERVAL = 24  # hours
HIRING_CHECK_INTERVAL = 12  # hours
WEBSITE_CHECK_INTERVAL = 6  # hours
SOCIAL_CHECK_INTERVAL = 24  # hours
```

To enable scheduled monitoring:

```python
# scheduler.py (example)
import schedule
import time

def run_scheduler():
    schedule.every(24).hours.do(check_pricing)
    schedule.every(12).hours.do(check_hiring)
    schedule.every(6).hours.do(check_websites)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    run_scheduler()
```

---

## 📈 Dashboard Metrics

### Real-time Metrics Displayed

- **Competitors Tracked**: Total number of monitored competitors
- **Changes (7d)**: Activity in the past week
- **Price Changes**: Number of detected pricing updates
- **Job Openings**: Total active job positions
- **New Products**: Recent product launches
- **Last Scan**: Time since last monitoring cycle

### Visualizations

- Activity timeline (all changes)
- Competitor health scores (activity comparison)
- Department breakdown for hiring (pie chart)
- Job titles overview
- Alert severity distribution
- Change type breakdown

---

## 🔐 Security Best Practices

### API Keys & Credentials
- Never commit `.env` file
- Use environment variables for all secrets
- Rotate API keys regularly
- Use app passwords, not main account passwords

### Database Security
- SQLite file permissions: `600`
- Regular backups
- No sensitive data in plain text
- Parameterized queries (prevents SQL injection)

### Email Security
- Use app-specific passwords (Gmail)
- Enable 2FA on email accounts
- SMTP over TLS (port 587)
- Review email logs regularly

### Data Privacy
- Comply with GDPR/CCPA
- Data retention policies
- User consent for monitoring
- Transparent competitor tracking

---

## 🧪 Testing

### Run Unit Tests
```bash
pytest tests/
```

### Test Coverage
```bash
pytest --cov=. tests/
```

### Sample Test Data
```bash
python scripts/generate_test_data.py
```

---

## 📊 Sample Data Generation

Generate test competitors and data:

```bash
python scripts/generate_test_data.py --competitors 5 --days 30
```

This creates:
- 5 sample competitors
- 30 days of historical data
- Mock pricing changes
- Job opening samples
- Product launch examples

---

## 🚀 Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["streamlit", "run", "app.py"]
```

```bash
docker build -t competitor-intelligence .
docker run -p 8501:8501 --env-file .env competitor-intelligence
```

### Cloud Deployment

#### Streamlit Cloud
1. Push to GitHub
2. Go to https://share.streamlit.io
3. Connect your repo
4. Set environment variables in app settings
5. Deploy!

#### AWS/Heroku/DigitalOcean
- See deployment guides in `/docs/deployment/`

---

## 📊 API Reference

### Database Methods

```python
from database import Database

db = Database("competitors.db")

# Competitors
db.add_competitor(name, website_url, linkedin_url, twitter_handle)
db.get_competitors()
db.get_competitor(competitor_id)

# Changes
db.add_change(competitor_id, change_type, description, severity)
db.get_recent_changes(days=30)
db.get_competitor_changes(competitor_id, days=30)

# Pricing
db.add_price_change(competitor_id, pricing_data)
db.get_price_changes(days=30)

# Jobs
db.add_job_opening(competitor_id, title, department, description)
db.get_competitor_job_openings(competitor_id)
db.get_all_job_openings()

# Alerts
db.add_alert(competitor_id, description, severity)
db.get_all_alerts(unsent_only=False)
db.mark_alerts_sent(alert_ids)
```

### Scraper Methods

```python
from scraper import WebScraper, PricingScraper, HiringTracker

# Website scraping
scraper = WebScraper()
data = scraper.scrape_website("https://example.com")
changes = scraper.detect_changes(current_data, previous_data)

# Pricing
pricing = PricingScraper()
prices = pricing.get_pricing("https://example.com")

# Hiring
hiring = HiringTracker()
jobs = hiring.get_job_postings("Company Name")
```

### AI Analysis Methods

```python
from ai_analysis import CompetitorAnalyzer

analyzer = CompetitorAnalyzer()

# Analysis
analysis = analyzer.analyze_website_changes(website_data, competitor_name)
launches = analyzer.detect_product_launches(competitor_name)
summary = analyzer.generate_competitive_summary(competitor_data)
threats = analyzer.identify_threats(competitor_data)
```

---

## 🔧 Configuration Guide

### Monitoring Frequency

Adjust intervals in `.env`:

```bash
# More frequent monitoring = higher API costs
PRICE_CHECK_INTERVAL=6      # Check every 6 hours
HIRING_CHECK_INTERVAL=12    # Check every 12 hours
WEBSITE_CHECK_INTERVAL=24   # Check daily
SOCIAL_CHECK_INTERVAL=12    # Check every 12 hours
```

### Alert Severity

Customize what triggers alerts:

```python
# In app.py
ALERT_RULES = {
    'price_change_threshold': 5,  # percent
    'hiring_threshold': 10,  # openings
    'website_hash_change': True,
    'product_launch': True
}
```

### Email Templates

Customize email templates in `alerts.py`:
- Modify HTML templates for branded emails
- Add company logo
- Customize alert text
- Adjust frequency and triggers

---

## 📚 Advanced Usage

### Custom Scrapers

Add new data sources:

```python
class CustomScraper:
    def scrape_custom_source(self, url):
        # Your custom logic
        return data

# Register in app.py
custom_scraper = CustomScraper()
```

### Integration with Tools

Connect with other platforms:

```python
# Slack notifications
from slack_sdk import WebClient
slack_client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])

# Zapier/IFTTT webhooks
webhook_url = "https://hooks.zapier.com/..."

# HubSpot CRM integration
from hubspot.crm.deals import ApiException
```

### Custom Reports

Generate domain-specific reports:

```python
def generate_sales_report(competitors):
    # Highlight pricing and product changes
    # Focus on sales-relevant intelligence
    pass

def generate_product_report(competitors):
    # Focus on feature launches
    # Competitive feature matrix
    pass
```

---

## 🐛 Troubleshooting

### Common Issues

**Issue**: API rate limit exceeded
- **Solution**: Reduce check frequency, implement caching

**Issue**: Email not sending
- **Solution**: Check SMTP credentials, enable less secure apps, verify firewall

**Issue**: Website scraping fails
- **Solution**: Check if site blocks scraping, use rotating proxies, implement retries

**Issue**: OpenAI API errors
- **Solution**: Verify API key, check quota, review rate limits

### Debug Mode

Enable detailed logging:

```bash
export LOG_LEVEL=DEBUG
streamlit run app.py
```

View logs:
```bash
tail -f competitor_intelligence.log
```

---

## 📈 Performance Optimization

### Database Indexing

```python
# Add indexes for faster queries
CREATE INDEX idx_competitor_id ON changes(competitor_id);
CREATE INDEX idx_detected_at ON changes(detected_at);
CREATE INDEX idx_severity ON alerts(severity);
```

### Caching

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_competitor_summary(competitor_id):
    # Results cached for 1 hour
    pass
```

### Batch Operations

```python
# More efficient than individual inserts
def batch_add_jobs(competitor_id, jobs):
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.executemany('''
            INSERT INTO job_openings (competitor_id, title, department)
            VALUES (?, ?, ?)
        ''', [(competitor_id, j['title'], j['department']) for j in jobs])
        conn.commit()
```

---

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Development Setup

```bash
git clone <your-fork>
cd competitor-intelligence-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Dev tools
```

---

## 📄 License

MIT License - see LICENSE file for details

---

## 📞 Support & Contact

- **GitHub Issues**: Report bugs and request features
- **Email**: support@competitorintelligence.dev
- **Discord**: Join our community server
- **Documentation**: https://docs.competitorintelligence.dev

---

## 🙏 Acknowledgments

Built with:
- [Streamlit](https://streamlit.io) - Amazing Python web framework
- [OpenAI GPT-4o](https://openai.com) - AI intelligence
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) - Web scraping
- [Plotly](https://plotly.com) - Interactive visualizations

---

## 🗺️ Roadmap

- [ ] Webhook integrations (Slack, Teams, Discord)
- [ ] Advanced filtering and custom reports
- [ ] Competitor comparison matrix
- [ ] Market trend analysis
- [ ] Predictive analytics
- [ ] Multi-language support
- [ ] Dark mode
- [ ] Mobile app
- [ ] API for third-party integrations
- [ ] Advanced search and NLP

---

## ⭐ Show Your Support

If this project helped you, please consider giving it a star! ⭐

```
████████████████████████████████████████ 100% Amazing
```

---

**Last Updated**: June 2024 | **Maintained by**: Your Team | **Community**: Growing 📈
