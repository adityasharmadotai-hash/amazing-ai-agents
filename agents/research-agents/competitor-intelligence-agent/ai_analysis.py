"""
AI Analysis Module - OpenAI integration for competitor intelligence
Generates insights, analyzes changes, and detects product launches
"""

import os
import json
import logging
from datetime import datetime

from openai import OpenAI

logger = logging.getLogger(__name__)

# Default model. Override with the OPENAI_MODEL environment variable or the
# Settings page in the app.
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")


class CompetitorAnalyzer:
    """AI-powered competitor analysis using OpenAI"""

    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or DEFAULT_MODEL
        self.client = self._build_client()

    def _build_client(self):
        """Create an OpenAI client when a key is available, else None.

        Keeping the client optional lets the app start and degrade gracefully
        (falling back to basic analysis) until a key is configured.
        """
        if not self.api_key:
            return None
        try:
            return OpenAI(api_key=self.api_key)
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI client: {str(e)}")
            return None

    def configure(self, api_key=None, model=None):
        """Update credentials/model at runtime (used by the Settings page)."""
        if api_key is not None:
            self.api_key = api_key
        if model is not None:
            self.model = model
        self.client = self._build_client()
        return self.client is not None

    def _complete(self, system, prompt, max_tokens=300, temperature=0.7):
        """Send a single-turn request to OpenAI and return the response text.

        Raises if the client is unavailable or the API call fails, so callers
        can decide how to fall back.
        """
        if not self.client:
            raise RuntimeError("OPENAI_API_KEY is not configured")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return (response.choices[0].message.content or "").strip()

    def analyze_website_changes(self, website_data, competitor_name):
        """Analyze website changes using AI"""
        if not website_data:
            return "Unable to analyze website"

        prompt = f"""
        Analyze these website changes for competitor '{competitor_name}':

        Title: {website_data.get('title')}
        Meta Description: {website_data.get('meta_description')}
        New Sections: {', '.join(website_data.get('headings', [])[:5])}
        Content Length: {website_data.get('text_length')} characters

        Provide a concise 1-2 sentence analysis of what's changed and why it matters.
        Focus on business implications.
        """

        try:
            return self._complete(
                "You are a competitive intelligence analyst. Provide concise, actionable insights.",
                prompt,
                max_tokens=150,
            )
        except Exception as e:
            logger.warning(f"AI analysis failed: {str(e)}")
            return self._fallback_analysis(website_data)

    def _fallback_analysis(self, website_data):
        """Fallback analysis when API fails"""
        changes = []

        headings = website_data.get('headings', [])
        if headings:
            changes.append(f"Website now features sections: {', '.join(headings[:3])}")

        text_length = website_data.get('text_length', 0)
        if text_length > 50000:
            changes.append("Content is extensive, indicating detailed product information")

        return ". ".join(changes) if changes else "Website content updated"

    def detect_product_launches(self, competitor_name):
        """Detect product launches using AI"""
        prompt = f"""
        Based on publicly available information about {competitor_name},
        list any recent product launches, features, or major announcements from the past 6 months.

        Format as JSON array with objects containing: name, description, announcement_date
        If you don't have specific information, return an empty array.
        Return only the JSON array, with no other text.
        """

        try:
            response_text = self._complete(
                "You are a product researcher. Return only JSON, no other text.",
                prompt,
                max_tokens=500,
                temperature=0.3,
            )

            # Extract JSON from response, tolerating Markdown code fences.
            response_text = (
                response_text.strip()
                .removeprefix("```json")
                .removeprefix("```")
                .removesuffix("```")
                .strip()
            )
            try:
                launches = json.loads(response_text)
                return launches if isinstance(launches, list) else []
            except json.JSONDecodeError:
                return []

        except Exception as e:
            logger.warning(f"Product launch detection failed: {str(e)}")
            return []

    def analyze_pricing_changes(self, old_pricing, new_pricing, competitor_name):
        """Analyze pricing changes"""
        prompt = f"""
        Compare the pricing for {competitor_name}:

        Previous Pricing: {json.dumps(old_pricing, indent=2)}
        New Pricing: {json.dumps(new_pricing, indent=2)}

        Provide a brief analysis (2-3 sentences) of:
        1. What changed
        2. Potential strategy behind the change
        3. Competitive implications
        """

        try:
            return self._complete(
                "You are a pricing strategy analyst.",
                prompt,
                max_tokens=200,
            )
        except Exception as e:
            logger.warning(f"Pricing analysis failed: {str(e)}")
            return "Unable to analyze pricing changes"

    def analyze_hiring_patterns(self, job_data, competitor_name):
        """Analyze hiring patterns to predict strategy"""
        prompt = f"""
        Analyze the hiring activity for {competitor_name}:

        Job Titles: {', '.join([j.get('title', '') for j in job_data[:10]])}
        Departments: {', '.join(set([j.get('department', '') for j in job_data]))}
        Total Open Positions: {len(job_data)}

        What does this hiring activity suggest about:
        1. Areas of growth
        2. Potential product/feature focus
        3. Strategic direction

        Keep response to 2-3 sentences.
        """

        try:
            return self._complete(
                "You are an organizational strategy analyst.",
                prompt,
                max_tokens=200,
            )
        except Exception as e:
            logger.warning(f"Hiring analysis failed: {str(e)}")
            return "Unable to analyze hiring patterns"

    def generate_competitive_summary(self, competitor_data):
        """Generate comprehensive competitive summary"""
        prompt = f"""
        Create a brief competitive summary for {competitor_data.get('name')}:

        Website: {competitor_data.get('website_url')}
        Recent Changes: {competitor_data.get('recent_changes', 'None detected')}
        Job Openings: {competitor_data.get('open_positions', 0)}
        Recent Products: {competitor_data.get('products', 'None')}

        Provide a 3-4 sentence executive summary of their current strategic focus
        and competitive positioning.
        """

        try:
            return self._complete(
                "You are an executive competitive intelligence analyst. Be concise and actionable.",
                prompt,
                max_tokens=300,
            )
        except Exception as e:
            logger.warning(f"Summary generation failed: {str(e)}")
            return "Unable to generate summary"

    def generate_insight(self, description):
        """Generate quick AI insight from any description"""
        prompt = f"""
        Provide a brief business insight (1-2 sentences) about this competitive intelligence finding:

        {description}

        Focus on strategic implications and what actions this might suggest.
        """

        try:
            return self._complete(
                "You are a strategic advisor providing actionable insights.",
                prompt,
                max_tokens=100,
            )
        except Exception as e:
            logger.warning(f"Insight generation failed: {str(e)}")
            return "Additional analysis needed"

    def identify_threats(self, competitor_data):
        """Identify potential threats from competitor activity"""
        prompt = f"""
        Based on this competitor intelligence, identify potential business threats:

        Competitor: {competitor_data.get('name')}
        Recent Activity: {json.dumps(competitor_data.get('activity', []), indent=2)}

        List 2-3 specific threats and recommended counter-strategies.
        Be direct and actionable.
        """

        try:
            return self._complete(
                "You are a strategic threat analyst. Identify real, actionable threats.",
                prompt,
                max_tokens=400,
            )
        except Exception as e:
            logger.warning(f"Threat analysis failed: {str(e)}")
            return "Unable to analyze threats"

    def get_market_positioning(self, competitor_name, market_context):
        """Analyze competitor's market positioning"""
        prompt = f"""
        Analyze the market positioning of {competitor_name} in the {market_context} market:

        Provide analysis of:
        1. Positioning vs competitors
        2. Unique value propositions
        3. Target audience
        4. Competitive advantages
        5. Vulnerabilities

        Keep to 4-5 sentences, be specific.
        """

        try:
            return self._complete(
                "You are a market strategy analyst with deep industry knowledge.",
                prompt,
                max_tokens=400,
            )
        except Exception as e:
            logger.warning(f"Positioning analysis failed: {str(e)}")
            return "Unable to analyze positioning"


class ReportGenerator:
    """Generate various reports on competitor intelligence"""

    def __init__(self, db, analyzer):
        self.db = db
        self.analyzer = analyzer

    def generate_executive_summary(self, competitor_id):
        """Generate executive summary report"""
        competitor = self.db.get_competitor(competitor_id)
        recent_changes = self.db.get_competitor_changes(competitor_id, days=30)
        job_openings = self.db.get_competitor_job_openings(competitor_id)
        products = self.db.get_competitor_product_launches(competitor_id)

        report = {
            'title': f'Competitor Intelligence Report: {competitor["name"]}',
            'generated_at': datetime.now().isoformat(),
            'competitor': competitor,
            'summary_stats': {
                'changes_30d': len(recent_changes),
                'open_positions': len(job_openings),
                'recent_products': len(products)
            },
            'recent_changes': recent_changes[:10],
            'hiring_focus': [j['department'] for j in job_openings[:5]],
            'product_launches': products[:5]
        }

        return report

    def generate_threat_report(self, competitor_id):
        """Generate threat analysis report"""
        competitor = self.db.get_competitor(competitor_id)
        changes = self.db.get_competitor_changes(competitor_id, days=90)

        report = {
            'title': f'Threat Analysis: {competitor["name"]}',
            'generated_at': datetime.now().isoformat(),
            'competitor': competitor,
            'threats': [],
            'recommendations': []
        }

        # Analyze high-severity changes
        high_severity = [c for c in changes if c.get('severity') == 'high']
        if high_severity:
            report['threats'].append({
                'level': 'high',
                'description': f'{len(high_severity)} high-severity changes detected',
                'details': high_severity[:3]
            })

        return report

    def generate_market_analysis(self, competitors_list):
        """Generate multi-competitor market analysis"""
        report = {
            'title': 'Market Analysis Report',
            'generated_at': datetime.now().isoformat(),
            'competitors': [],
            'key_insights': []
        }

        for comp_id in competitors_list:
            comp_report = self.generate_executive_summary(comp_id)
            report['competitors'].append(comp_report)

        return report
