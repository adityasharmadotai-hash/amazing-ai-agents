"""
Test Data Generator - Create sample data for development and demos
"""

import sys
import random
from datetime import datetime, timedelta
from database import Database
import json

class TestDataGenerator:
    """Generate realistic test data"""
    
    SAMPLE_COMPETITORS = [
        {
            'name': 'Segment',
            'website': 'https://segment.com',
            'linkedin': 'https://linkedin.com/company/segment',
            'twitter': '@segment'
        },
        {
            'name': 'Mixpanel',
            'website': 'https://mixpanel.com',
            'linkedin': 'https://linkedin.com/company/mixpanel',
            'twitter': '@mixpanel'
        },
        {
            'name': 'Amplitude',
            'website': 'https://amplitude.com',
            'linkedin': 'https://linkedin.com/company/amplitude',
            'twitter': '@AmpAnalytics'
        },
        {
            'name': 'Intercom',
            'website': 'https://intercom.com',
            'linkedin': 'https://linkedin.com/company/intercom',
            'twitter': '@intercom'
        },
        {
            'name': 'Customer.io',
            'website': 'https://customer.io',
            'linkedin': 'https://linkedin.com/company/customer-io',
            'twitter': '@customerio'
        }
    ]
    
    SAMPLE_JOBS = [
        ('Senior Backend Engineer', 'Engineering'),
        ('Product Manager', 'Product'),
        ('Data Scientist', 'Data & Analytics'),
        ('Sales Executive', 'Sales'),
        ('Marketing Manager', 'Marketing'),
        ('DevOps Engineer', 'Engineering'),
        ('UX/UI Designer', 'Design'),
        ('Solutions Architect', 'Engineering'),
        ('Customer Success Manager', 'Customer Success'),
        ('Full Stack Engineer', 'Engineering'),
    ]
    
    SAMPLE_PRODUCTS = [
        ('AI-Powered Insights', 'New AI-driven analytics engine'),
        ('Real-time Dashboard', 'Enhanced real-time visualization'),
        ('Advanced Segmentation', 'ML-based audience segmentation'),
        ('API v3', 'Completely redesigned API'),
        ('Mobile App', 'Native iOS and Android apps'),
    ]
    
    CHANGE_DESCRIPTIONS = [
        'Updated pricing page with new enterprise tier',
        'Added new landing page for vertical solution',
        'Launched new feature in product',
        'Reorganized navigation and information architecture',
        'Added customer testimonials and case studies',
        'Updated company blog with new content',
        'Changed homepage hero section',
        'Added live chat support widget',
        'Updated integration partners list',
        'Added new security certifications',
    ]
    
    def __init__(self, db_path='competitors.db'):
        self.db = Database(db_path)
    
    def generate_all_data(self, num_competitors=5, days=30):
        \"\"\"Generate complete test dataset\"\"\"
        print(f\"Generating test data: {num_competitors} competitors, {days} days history...\")
        
        # Add competitors
        competitor_ids = []
        for i, comp in enumerate(self.SAMPLE_COMPETITORS[:num_competitors]):
            comp_id = self.db.add_competitor(
                comp['name'],
                comp['website'],
                comp['linkedin'],
                comp['twitter']
            )
            competitor_ids.append(comp_id)
            print(f\"  ✓ Added competitor: {comp['name']}\")
        
        # Generate historical data for each competitor
        for comp_id in competitor_ids:
            competitor = self.db.get_competitor(comp_id)
            
            # Add website changes
            self._generate_website_changes(comp_id, days)
            
            # Add pricing changes
            self._generate_pricing_changes(comp_id, days)
            
            # Add job openings
            self._generate_job_openings(comp_id)
            
            # Add product launches
            self._generate_product_launches(comp_id, days)
            
            # Add alerts
            self._generate_alerts(comp_id, days)
            
            print(f\"  ✓ Generated data for {competitor['name']}\")
        
        print(f\"\\n✅ Test data generation complete!\")
        
        # Print statistics
        stats = self.db.get_database_stats()
        print(f\"\\nDatabase Statistics:\")
        for key, value in stats.items():
            print(f\"  {key}: {value}\")
    
    def _generate_website_changes(self, competitor_id, days):
        \"\"\"Generate sample website changes\"\"\"
        for i in range(random.randint(2, 5)):
            days_ago = random.randint(1, days)
            self.db.add_change(
                competitor_id,
                'website_update',
                random.choice(self.CHANGE_DESCRIPTIONS),
                random.choice(['low', 'medium', 'high'])
            )
    
    def _generate_pricing_changes(self, competitor_id, days):
        \"\"\"Generate sample pricing data\"\"\"
        pricing_data = {
            'plans': [
                {
                    'name': 'Starter',
                    'price': random.randint(29, 99),
                    'currency': 'USD',
                    'features': random.randint(3, 5)
                },
                {
                    'name': 'Professional',
                    'price': random.randint(99, 299),
                    'currency': 'USD',
                    'features': random.randint(10, 15)
                },
                {
                    'name': 'Enterprise',
                    'price': 'Custom',
                    'currency': 'USD',
                    'features': None
                }
            ],
            'extracted_at': datetime.now().isoformat()
        }
        
        self.db.add_price_change(competitor_id, json.dumps(pricing_data))
    
    def _generate_job_openings(self, competitor_id):
        \"\"\"Generate sample job openings\"\"\"
        num_jobs = random.randint(3, 12)
        
        for _ in range(num_jobs):
            title, department = random.choice(self.SAMPLE_JOBS)
            self.db.add_job_opening(
                competitor_id,
                title,
                department,
                f'Looking for talented {title.lower()} to join our {department} team.',
                f'https://example.com/jobs/{random.randint(1000, 9999)}'
            )
    
    def _generate_product_launches(self, competitor_id, days):
        \"\"\"Generate sample product launches\"\"\"
        num_launches = random.randint(1, 3)
        
        for _ in range(num_launches):
            product_name, description = random.choice(self.SAMPLE_PRODUCTS)
            self.db.add_product_launch(
                competitor_id,
                product_name,
                description,
                'https://example.com/blog/new-product'
            )
    
    def _generate_alerts(self, competitor_id, days):
        \"\"\"Generate sample alerts\"\"\"
        num_alerts = random.randint(2, 5)
        
        alert_descriptions = [
            '💰 Price change detected on Professional plan',
            '👥 Hiring intensity increased (8 new positions)',
            '🚀 New product launched: AI-Powered Insights',
            '🌐 Website redesign detected',
            '📊 New integration partnerships announced'
        ]
        
        for _ in range(num_alerts):
            self.db.add_alert(
                competitor_id,
                random.choice(alert_descriptions),
                random.choice(['high', 'medium', 'low'])
            )


def main():
    \"\"\"Main entry point\"\"\"
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate test data for competitor intelligence')
    parser.add_argument('--competitors', type=int, default=5, help='Number of competitors (max 5)')
    parser.add_argument('--days', type=int, default=30, help='Days of history to generate')
    parser.add_argument('--db', default='competitors.db', help='Database path')
    parser.add_argument('--clean', action='store_true', help='Clean database before generating')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.competitors > 5:
        print('Warning: Maximum 5 sample competitors available')
        args.competitors = 5
    
    # Clean existing database if requested
    if args.clean:
        import os
        if os.path.exists(args.db):
            os.remove(args.db)
            print(f'Cleaned existing database: {args.db}')
    
    # Generate data
    generator = TestDataGenerator(args.db)
    generator.generate_all_data(args.competitors, args.days)
    
    print(f'\\nDatabase saved to: {args.db}')
    print('Run \"streamlit run app.py\" to start the application')


if __name__ == '__main__':
    main()
