"""
Web Scraping Module - Collect competitor data from websites
Handles website monitoring, pricing extraction, and job posting discovery
"""

import requests
from bs4 import BeautifulSoup
import json
import hashlib
from urllib.parse import urljoin, urlparse
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class WebScraper:
    """Scrape and monitor competitor websites"""
    
    def __init__(self, timeout=10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scrape_website(self, url):
        """Scrape website content and structure"""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract key information
            data = {
                'url': url,
                'title': soup.title.string if soup.title else 'N/A',
                'meta_description': self._get_meta_description(soup),
                'headings': self._extract_headings(soup),
                'links': self._extract_links(soup, url),
                'content_hash': self._hash_content(response.content),
                'scraped_at': datetime.now().isoformat(),
                'text_length': len(soup.get_text()),
            }
            
            return data
        
        except Exception as e:
            logger.error(f"Failed to scrape {url}: {str(e)}")
            return None
    
    def detect_changes(self, current_data, previous_data):
        """Detect changes between two website states"""
        if not previous_data:
            return {'status': 'first_scan', 'changes': []}
        
        changes = []
        
        # Check for content hash change
        if current_data['content_hash'] != previous_data['content_hash']:
            changes.append({
                'type': 'content_modified',
                'severity': 'high',
                'description': 'Website content has been updated'
            })
        
        # Check for new links
        new_links = set(current_data['links']) - set(previous_data.get('links', []))
        if new_links:
            changes.append({
                'type': 'new_links',
                'severity': 'medium',
                'description': f'Found {len(new_links)} new links',
                'data': list(new_links)[:5]  # Top 5 new links
            })
        
        # Check for heading changes (indicates new sections)
        new_headings = set(current_data['headings']) - set(previous_data.get('headings', []))\n        if new_headings:
            changes.append({
                'type': 'new_sections',
                'severity': 'medium',
                'description': f'Found {len(new_headings)} new sections',
                'data': list(new_headings)[:3]
            })
        
        return {
            'status': 'changes_detected' if changes else 'no_changes',
            'changes': changes
        }
    
    def _get_meta_description(self, soup):
        """Extract meta description"""
        meta = soup.find('meta', attrs={'name': 'description'})
        return meta['content'] if meta else 'N/A'
    
    def _extract_headings(self, soup):
        """Extract all headings"""
        headings = []
        for tag in soup.find_all(['h1', 'h2', 'h3']):
            text = tag.get_text(strip=True)
            if text:
                headings.append(text)
        return headings
    
    def _extract_links(self, soup, base_url):
        """Extract all links"""
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('http'):
                links.append(href)
            elif href.startswith('/'):
                links.append(urljoin(base_url, href))
        return list(set(links))  # Remove duplicates
    
    def _hash_content(self, content):
        """Generate hash of content"""
        return hashlib.md5(content).hexdigest()


class PricingScraper:
    """Extract pricing information from competitor websites"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_pricing(self, url):
        """Extract pricing page content"""
        try:
            # Try common pricing page URLs
            pricing_urls = [
                urljoin(url, '/pricing'),
                urljoin(url, '/plans'),
                urljoin(url, '/pricing/'),
                urljoin(url, '/plans/'),
                url + '/pricing',
            ]
            
            for pricing_url in pricing_urls:
                try:
                    response = self.session.get(pricing_url, timeout=10)
                    if response.status_code == 200:
                        return self._parse_pricing(response.text)
                except:
                    continue
            
            # Fallback to main page
            response = self.session.get(url, timeout=10)
            return self._parse_pricing(response.text)
        
        except Exception as e:
            logger.error(f"Failed to get pricing: {str(e)}")
            return {'error': str(e)}
    
    def _parse_pricing(self, html):
        """Parse pricing from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        
        pricing_data = {
            'plans': [],
            'features': [],
            'extracted_at': datetime.now().isoformat()
        }
        
        # Look for pricing tables or plan cards
        # This is a simplified extraction - adapt based on target websites
        
        # Extract currency and prices
        prices = []
        for element in soup.find_all(['span', 'div', 'p']):
            text = element.get_text(strip=True)
            if '$' in text or '€' in text or '£' in text:
                prices.append(text)
        
        # Extract plan names
        plan_names = []
        for heading in soup.find_all(['h2', 'h3']):
            text = heading.get_text(strip=True)
            if any(plan_keyword in text.lower() for plan_keyword in ['starter', 'pro', 'enterprise', 'basic', 'premium']):
                plan_names.append(text)
        
        pricing_data['prices'] = prices[:10]
        pricing_data['plan_names'] = plan_names
        pricing_data['raw_html_length'] = len(html)
        
        return pricing_data


class HiringTracker:
    """Track hiring activity and job postings"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_job_postings(self, company_name, source='linkedin'):
        """Get job postings for a company"""
        jobs = []
        
        try:
            if source == 'linkedin':
                jobs = self._get_linkedin_jobs(company_name)
            elif source == 'builtin':
                jobs = self._get_builtin_jobs(company_name)
            elif source == 'angel':
                jobs = self._get_angellist_jobs(company_name)
        
        except Exception as e:
            logger.error(f"Failed to get jobs: {str(e)}")
        
        return jobs
    
    def _get_linkedin_jobs(self, company_name):
        \"\"\"Mock LinkedIn jobs extraction\"\"\"
        # In production, use LinkedIn API or web scraping
        # This is a placeholder that returns sample data
        return [
            {
                'title': 'Senior Software Engineer',
                'department': 'Engineering',
                'description': 'We are looking for experienced software engineers...',
                'url': f'https://linkedin.com/jobs/{company_name}',
                'posted_date': datetime.now().isoformat()
            },
            {
                'title': 'Product Manager',
                'department': 'Product',
                'description': 'Lead our product vision...',
                'url': f'https://linkedin.com/jobs/{company_name}',
                'posted_date': datetime.now().isoformat()
            }
        ]
    
    def _get_builtin_jobs(self, company_name):
        \"\"\"Mock BuiltIn jobs extraction\"\"\"
        return []
    
    def _get_angellist_jobs(self, company_name):
        \"\"\"Mock AngelList jobs extraction\"\"\"
        return []
    
    def detect_hiring_intensity(self, job_count, previous_count):
        \"\"\"Determine hiring activity level\"\"\"
        if job_count > previous_count * 1.5:
            return 'high'
        elif job_count > previous_count * 1.1:
            return 'medium'
        else:
            return 'normal'


class SocialMediaMonitor:
    """Monitor social media activity\"\"\"
    
    def __init__(self):
        self.session = requests.Session()
    
    def get_twitter_activity(self, handle):
        \"\"\"Get Twitter activity\"\"\"
        # Placeholder - requires Twitter API
        return {
            'recent_tweets': [],
            'engagement_rate': 0,
            'follower_change': 0
        }
    
    def get_linkedin_activity(self, company_url):
        \"\"\"Get LinkedIn activity\"\"\"
        # Placeholder - requires LinkedIn API or scraping
        return {
            'recent_posts': [],
            'engagement': 0,
            'follower_change': 0
        }
    
    def get_github_activity(self, username):
        \"\"\"Get GitHub activity\"\"\"
        try:
            response = self.session.get(f'https://api.github.com/users/{username}')
            if response.status_code == 200:
                data = response.json()
                return {
                    'repos': data.get('public_repos'),
                    'followers': data.get('followers'),
                    'updated_at': data.get('updated_at')
                }
        except Exception as e:
            logger.error(f"Failed to get GitHub activity: {str(e)}")
        
        return {}


class NewsMonitor:
    """Monitor news mentions of competitors\"\"\"
    
    def get_news_mentions(self, company_name):
        \"\"\"Get news mentions (placeholder)\"\"\"
        # In production, integrate with news APIs:
        # - NewsAPI
        # - Google News RSS
        # - Crunchbase
        return {
            'mentions': [],
            'sentiment': 'neutral'
        }
    
    def get_crunchbase_updates(self, company_name):
        \"\"\"Get Crunchbase updates\"\"\"
        # Requires Crunchbase API key
        return {
            'funding': [],
            'acquisitions': [],
            'key_people': []
        }
