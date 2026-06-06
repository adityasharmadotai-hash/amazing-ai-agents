"""
Alert Management Module - Email notifications and digest reports
Handles alert creation, sending, and digest generation
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import os
import logging
from jinja2 import Template

logger = logging.getLogger(__name__)

class AlertManager:
    """Manage alerts and notifications"""
    
    def __init__(self, db):
        self.db = db
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.sender_email = os.getenv('SENDER_EMAIL')
        self.sender_password = os.getenv('SENDER_PASSWORD')
    
    def send_alert(self, recipient_email, subject, body, html=False):
        """Send immediate alert email"""
        try:
            if not self.sender_email or not self.sender_password:
                logger.warning("SMTP credentials not configured")
                return False
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            
            if html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to send alert: {str(e)}")
            return False
    
    def send_daily_digest(self, recipient_email):
        \"\"\"Send daily competitor intelligence digest\"\"\"
        try:
            # Get alerts from past 24 hours
            alerts = self.db.get_all_alerts(unsent_only=True)
            
            if not alerts:
                logger.info("No new alerts for digest")
                return True
            
            # Group by competitor
            alerts_by_competitor = {}
            for alert in alerts:
                comp_name = alert['competitor_name']
                if comp_name not in alerts_by_competitor:
                    alerts_by_competitor[comp_name] = []
                alerts_by_competitor[comp_name].append(alert)
            
            # Generate HTML
            html_body = self._generate_digest_html(alerts_by_competitor)
            
            # Send email
            subject = f"🔍 Competitor Intelligence Digest - {datetime.now().strftime('%Y-%m-%d')}"
            success = self.send_alert(recipient_email, subject, html_body, html=True)
            
            if success:
                # Mark alerts as sent
                alert_ids = [a['id'] for a in alerts]
                self.db.mark_alerts_sent(alert_ids)
            
            return success
        
        except Exception as e:
            logger.error(f"Failed to send digest: {str(e)}")
            return False
    
    def send_weekly_report(self, recipient_email):
        \"\"\"Send weekly comprehensive report\"\"\"
        try:
            # Get data from past week
            competitors = self.db.get_competitors()
            
            report_data = {
                'week_start': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                'week_end': datetime.now().strftime('%Y-%m-%d'),
                'competitors_tracked': len(competitors),
                'competitors': []
            }
            
            for comp in competitors:
                comp_changes = self.db.get_competitor_changes(comp['id'], days=7)
                comp_jobs = self.db.get_competitor_job_openings(comp['id'])
                comp_products = self.db.get_competitor_product_launches(comp['id'])
                
                report_data['competitors'].append({
                    'name': comp['name'],
                    'website': comp['website_url'],
                    'changes': len(comp_changes),
                    'job_openings': len(comp_jobs),
                    'product_launches': len(comp_products),
                    'recent_changes': comp_changes[:3]
                })
            
            html_body = self._generate_weekly_report_html(report_data)
            
            subject = f"📊 Weekly Competitor Intelligence Report - {datetime.now().strftime('%Y-W%W')}"
            return self.send_alert(recipient_email, subject, html_body, html=True)
        
        except Exception as e:
            logger.error(f"Failed to send weekly report: {str(e)}")
            return False
    
    def _generate_digest_html(self, alerts_by_competitor):
        \"\"\"Generate HTML for daily digest\"\"\"
        html_template = \"\"\"
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; background-color: #f5f5f5; }
                .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
                .header h1 { margin: 0; font-size: 24px; }
                .competitor-section { margin-bottom: 20px; border-left: 4px solid #667eea; padding-left: 15px; }
                .competitor-section h2 { margin-top: 0; color: #333; }
                .alert-item { background-color: #f9f9f9; padding: 10px; margin-bottom: 10px; border-radius: 4px; border-left: 3px solid #4CAF50; }
                .alert-item.high { border-left-color: #f5576c; background-color: #fff5f7; }
                .alert-item.medium { border-left-color: #f093fb; }
                .footer { text-align: center; color: #999; font-size: 12px; margin-top: 30px; }
            </style>
        </head>
        <body>
            <div class=\"container\">
                <div class=\"header\">
                    <h1>🔍 Competitor Intelligence Digest</h1>
                    <p style=\"margin: 10px 0 0 0;\">{{ date }}</p>
                </div>
                
                {% for competitor, alerts in competitors.items() %}
                <div class=\"competitor-section\">
                    <h2>{{ competitor }}</h2>
                    <p style=\"color: #666; margin-bottom: 15px;\">{{ alerts|length }} new alert(s)</p>
                    
                    {% for alert in alerts %}
                    <div class=\"alert-item {{ alert.severity }}\">
                        <strong>{{ alert.description }}</strong>
                        <br>
                        <small style=\"color: #999;\">{{ alert.triggered_at }}</small>
                    </div>
                    {% endfor %}
                </div>
                {% endfor %}
                
                <div class=\"footer\">
                    <p>Competitor Intelligence Agent | <a href=\"https://github.com/yourusername/competitor-intelligence-agent\">GitHub</a></p>
                </div>
            </div>
        </body>
        </html>
        \"\"\"\n        
        template = Template(html_template)
        return template.render(
            date=datetime.now().strftime('%B %d, %Y'),
            competitors=alerts_by_competitor
        )
    
    def _generate_weekly_report_html(self, report_data):
        \"\"\"Generate HTML for weekly report\"\"\"
        html_template = \"\"\"
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; background-color: #f5f5f5; }
                .container { max-width: 700px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
                .header h1 { margin: 0; font-size: 28px; }
                .stats { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 20px; }
                .stat-box { background-color: #f0f0f0; padding: 15px; border-radius: 8px; text-align: center; border-top: 3px solid #667eea; }
                .stat-box .number { font-size: 24px; font-weight: bold; color: #667eea; }
                .stat-box .label { color: #666; font-size: 12px; margin-top: 5px; }
                .competitor-row { border-bottom: 1px solid #eee; padding: 15px 0; }
                .competitor-row h3 { margin: 0 0 10px 0; color: #333; }
                .metric { display: inline-block; margin-right: 20px; }
                .metric-value { font-weight: bold; color: #667eea; }
                .footer { text-align: center; color: #999; font-size: 12px; margin-top: 30px; }
            </style>
        </head>
        <body>
            <div class=\"container\">
                <div class=\"header\">
                    <h1>📊 Weekly Competitor Report</h1>
                    <p style=\"margin: 10px 0 0 0;\">{{ report.week_start }} to {{ report.week_end }}</p>
                </div>
                
                <div class=\"stats\">
                    <div class=\"stat-box\">
                        <div class=\"number\">{{ report.competitors_tracked }}</div>
                        <div class=\"label\">Competitors Tracked</div>
                    </div>
                    <div class=\"stat-box\">
                        <div class=\"number\">{{ total_changes }}</div>
                        <div class=\"label\">Total Changes</div>
                    </div>
                    <div class=\"stat-box\">
                        <div class=\"number\">{{ total_jobs }}</div>
                        <div class=\"label\">Job Openings</div>
                    </div>
                </div>
                
                <h2>Competitor Overview</h2>
                {% for competitor in report.competitors %}
                <div class=\"competitor-row\">
                    <h3>{{ competitor.name }}</h3>
                    <div class=\"metric\">
                        <span>Changes:</span>
                        <span class=\"metric-value\">{{ competitor.changes }}</span>
                    </div>
                    <div class=\"metric\">
                        <span>Jobs:</span>
                        <span class=\"metric-value\">{{ competitor.job_openings }}</span>
                    </div>
                    <div class=\"metric\">
                        <span>Products:</span>
                        <span class=\"metric-value\">{{ competitor.product_launches }}</span>
                    </div>
                </div>
                {% endfor %}
                
                <div class=\"footer\">
                    <p>Competitor Intelligence Agent | Keep tracking your competitors</p>
                </div>
            </div>
        </body>
        </html>
        \"\"\"\n        
        # Calculate totals
        total_changes = sum(c['changes'] for c in report_data['competitors'])
        total_jobs = sum(c['job_openings'] for c in report_data['competitors'])
        \n        template = Template(html_template)
        return template.render(
            report=report_data,
            total_changes=total_changes,
            total_jobs=total_jobs
        )
    
    def create_high_priority_alert(self, competitor_id, description):
        \"\"\"Create a high-priority alert\"\"\"
        alert_id = self.db.add_alert(
            competitor_id,
            description,
            severity='high'
        )
        
        # Could trigger immediate notification
        logger.warning(f"High priority alert created: {description}")
        return alert_id
    
    def create_price_change_alert(self, competitor_id, change_description):
        \"\"\"Alert when pricing changes detected\"\"\"
        return self.db.add_alert(
            competitor_id,
            f"💰 Pricing change: {change_description}",
            severity='high'
        )
    
    def create_hiring_alert(self, competitor_id, job_count, intensity):
        \"\"\"Alert when significant hiring detected\"\"\"
        description = f\"👥 Hiring intensity: {intensity.upper()} ({job_count} open positions)\"
        
        severity = 'high' if intensity == 'high' else 'medium'
        return self.db.add_alert(
            competitor_id,
            description,
            severity=severity
        )
    
    def create_product_launch_alert(self, competitor_id, product_name):
        \"\"\"Alert when new product/feature launched\"\"\"
        return self.db.add_alert(
            competitor_id,
            f\"🚀 New product/feature: {product_name}\",
            severity='high'
        )
