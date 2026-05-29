"""
modules/demo_data.py
--------------------
Realistic demo articles for testing without API keys.
"""
from __future__ import annotations
from datetime import datetime, timedelta
import hashlib

_NOW = datetime.now()


def _id(title: str) -> str:
    return hashlib.md5(title.encode()).hexdigest()[:16]


def get_demo_articles() -> list[dict]:
    articles = [
        {
            "id": _id("OpenAI GPT-5 Launches"), "title": "OpenAI Launches GPT-5 with Unprecedented Reasoning Capabilities",
            "source": "TechCrunch", "url": "https://techcrunch.com",
            "published": (_NOW - timedelta(hours=1)).isoformat(),
            "summary": "OpenAI has unveiled GPT-5, demonstrating multi-step reasoning that outperforms human experts in medical diagnosis and complex coding. The model introduces 'chain-of-thought persistence' allowing it to maintain context across 1 million tokens.",
            "full_text": "OpenAI has unveiled GPT-5, a major breakthrough in AI capabilities...",
            "image_url": "", "topics": ["AI", "Technology"],
            "sentiment": "positive", "signal_score": 9.5, "is_duplicate": False,
            "why_matters": "Could reshape the AI competitive landscape and accelerate enterprise adoption.",
        },
        {
            "id": _id("Fed Signals Rate Cuts"), "title": "Federal Reserve Signals Three Rate Cuts in 2025 as Inflation Cools",
            "source": "Reuters", "url": "https://reuters.com",
            "published": (_NOW - timedelta(hours=2)).isoformat(),
            "summary": "The Federal Reserve indicated it will cut interest rates three times in 2025 after inflation dropped to 2.1%, near the 2% target. Markets rallied sharply on the news with the S&P 500 gaining 1.8%.",
            "full_text": "Federal Reserve Chair Jerome Powell signaled...",
            "image_url": "", "topics": ["Finance", "Business"],
            "sentiment": "positive", "signal_score": 9.2, "is_duplicate": False,
            "why_matters": "Lower rates will ease borrowing costs for consumers and businesses, potentially reigniting investment.",
        },
        {
            "id": _id("Apple Vision Pro 2"), "title": "Apple Announces Vision Pro 2 with 8-Hour Battery Life at $2,499",
            "source": "The Verge", "url": "https://theverge.com",
            "published": (_NOW - timedelta(hours=3)).isoformat(),
            "summary": "Apple has unveiled Vision Pro 2, addressing the original's main criticism with an 8-hour battery and a new $2,499 price point. The device features a custom M4 chip and new eye-tracking technology.",
            "full_text": "Apple's second-generation Vision Pro...",
            "image_url": "", "topics": ["Technology", "Business"],
            "sentiment": "positive", "signal_score": 8.7, "is_duplicate": False,
            "why_matters": "Price cut and battery improvement could finally drive mainstream spatial computing adoption.",
        },
        {
            "id": _id("UK AI Regulation"), "title": "UK Passes Landmark AI Safety Act with Mandatory Testing Requirements",
            "source": "BBC News", "url": "https://bbc.co.uk",
            "published": (_NOW - timedelta(hours=4)).isoformat(),
            "summary": "The UK Parliament has passed a comprehensive AI Safety Act requiring all AI models above a compute threshold to undergo mandatory safety testing before deployment. Tech companies have 18 months to comply.",
            "full_text": "The AI Safety Act represents the most comprehensive...",
            "image_url": "", "topics": ["AI", "Politics", "Technology"],
            "sentiment": "neutral", "signal_score": 8.4, "is_duplicate": False,
            "why_matters": "Sets global precedent for AI regulation and may influence EU and US policies.",
        },
        {
            "id": _id("Microsoft Copilot Enterprise"), "title": "Microsoft Copilot Reaches 50 Million Enterprise Users, Announces $30/mo Price Cut",
            "source": "Bloomberg", "url": "https://bloomberg.com",
            "published": (_NOW - timedelta(hours=5)).isoformat(),
            "summary": "Microsoft announced Copilot has reached 50 million monthly active enterprise users and is cutting pricing by 25% to $30/month per user. The company reported $8B in AI-related revenue for Q1.",
            "full_text": "Microsoft's AI-powered productivity suite...",
            "image_url": "", "topics": ["Technology", "Business", "AI"],
            "sentiment": "positive", "signal_score": 8.1, "is_duplicate": False,
            "why_matters": "Demonstrates enterprise AI monetisation is maturing; price cut signals competitive pressure from Google.",
        },
        {
            "id": _id("Tesla Full Self-Driving"), "title": "Tesla's Full Self-Driving 13.0 Achieves Zero Accident Rate in 100M Mile Test",
            "source": "Reuters", "url": "https://reuters.com",
            "published": (_NOW - timedelta(hours=6)).isoformat(),
            "summary": "Tesla's FSD version 13.0 has completed 100 million miles in testing with zero accidents recorded, a milestone that could unlock full regulatory approval. NHTSA is expected to rule within 90 days.",
            "full_text": "Tesla's autonomous driving technology reached...",
            "image_url": "", "topics": ["Technology", "AI"],
            "sentiment": "positive", "signal_score": 7.9, "is_duplicate": False,
            "why_matters": "Regulatory approval would open $500B+ autonomous vehicle market.",
        },
        {
            "id": _id("NVIDIA Q3 Earnings"), "title": "NVIDIA Reports $35B Revenue, Beats Estimates by 18% on AI Chip Demand",
            "source": "CNBC", "url": "https://cnbc.com",
            "published": (_NOW - timedelta(hours=7)).isoformat(),
            "summary": "NVIDIA reported Q3 revenue of $35.1B, beating analyst estimates by 18% driven by insatiable AI infrastructure demand. Gross margins expanded to 74% and the company raised full-year guidance by 22%.",
            "full_text": "NVIDIA's earnings report demonstrated...",
            "image_url": "", "topics": ["Finance", "Technology", "AI"],
            "sentiment": "positive", "signal_score": 8.8, "is_duplicate": False,
            "why_matters": "Signals AI infrastructure investment cycle is far from over; H100/H200 chips still in short supply.",
        },
        {
            "id": _id("Climate Tipping Point"), "title": "Scientists Warn Three Climate Tipping Points 'Will Be Crossed' by 2035",
            "source": "Nature", "url": "https://nature.com",
            "published": (_NOW - timedelta(hours=8)).isoformat(),
            "summary": "A landmark study in Nature warns that the Greenland ice sheet collapse, Amazon dieback, and West Antarctic destabilisation will be irreversibly triggered within a decade if emissions remain at current levels.",
            "full_text": "The study, authored by 87 scientists...",
            "image_url": "", "topics": ["Science", "Energy"],
            "sentiment": "negative", "signal_score": 8.3, "is_duplicate": False,
            "why_matters": "Accelerates corporate and government sustainability timelines; carbon credit markets will reprice.",
        },
        {
            "id": _id("Google Quantum"), "title": "Google Achieves 'Quantum Advantage' with 1000-Qubit Willow Processor",
            "source": "MIT Technology Review", "url": "https://technologyreview.com",
            "published": (_NOW - timedelta(hours=9)).isoformat(),
            "summary": "Google's Quantum AI team demonstrated 'quantum advantage' using their 1000-qubit Willow processor, solving a problem in 4 minutes that would take classical computers 10,000 years.",
            "full_text": "Google's breakthrough in quantum computing...",
            "image_url": "", "topics": ["Technology", "Science"],
            "sentiment": "positive", "signal_score": 9.0, "is_duplicate": False,
            "why_matters": "Could break current encryption standards; major implications for cybersecurity and cryptography.",
        },
        {
            "id": _id("Bitcoin ETF Approval"), "title": "SEC Approves First Bitcoin Spot ETF Options, $2B Flows in First Day",
            "source": "Financial Times", "url": "https://ft.com",
            "published": (_NOW - timedelta(hours=10)).isoformat(),
            "summary": "The SEC approved options trading on spot Bitcoin ETFs, triggering $2 billion in inflows on the first day. Bitcoin's price surged 12% to $78,000 as institutional investors gain new access routes.",
            "full_text": "The regulatory decision marks a new chapter...",
            "image_url": "", "topics": ["Finance", "Crypto"],
            "sentiment": "positive", "signal_score": 7.8, "is_duplicate": False,
            "why_matters": "Unlocks institutional derivatives market for crypto; could trigger next bull cycle.",
        },
        {
            "id": _id("India GDP Overtakes"), "title": "India's GDP Overtakes Japan, Becomes World's 4th Largest Economy",
            "source": "BBC News", "url": "https://bbc.co.uk",
            "published": (_NOW - timedelta(hours=11)).isoformat(),
            "summary": "India's GDP has officially surpassed Japan's, making it the world's fourth largest economy at $4.8 trillion. The milestone reflects India's rapid industrialisation and growing tech export sector.",
            "full_text": "The economic milestone reflects years of growth...",
            "image_url": "", "topics": ["Business", "World"],
            "sentiment": "positive", "signal_score": 7.5, "is_duplicate": False,
            "why_matters": "Shifts global supply chain calculus; companies will accelerate India market entry.",
        },
        {
            "id": _id("OpenAI GPT-5 Release Duplicate"), "title": "OpenAI's New GPT-5 Sets Records in Reasoning Benchmarks",
            "source": "VentureBeat", "url": "https://venturebeat.com",
            "published": (_NOW - timedelta(hours=1, minutes=30)).isoformat(),
            "summary": "Duplicate coverage of GPT-5 launch from VentureBeat perspective.",
            "full_text": "", "image_url": "", "topics": ["AI"],
            "sentiment": "positive", "signal_score": 7.0, "is_duplicate": True,
            "why_matters": "",
        },
        {
            "id": _id("New SpaceX Mission"), "title": "SpaceX Starship Completes First Crewed Mars Orbit Mission",
            "source": "Ars Technica", "url": "https://arstechnica.com",
            "published": (_NOW - timedelta(hours=12)).isoformat(),
            "summary": "SpaceX's Starship completed its first crewed Mars orbit mission with four astronauts aboard, marking humanity's first crewed venture beyond Earth's orbit since the Apollo missions.",
            "full_text": "The historic mission...",
            "image_url": "", "topics": ["Science", "Technology"],
            "sentiment": "positive", "signal_score": 9.8, "is_duplicate": False,
            "why_matters": "Validates commercial spaceflight for deep space and opens door to permanent Mars settlement.",
        },
        {
            "id": _id("Healthcare AI FDA"), "title": "FDA Approves First AI-Only Medical Diagnosis System for Radiology",
            "source": "Healthcare IT News", "url": "https://healthcareit.com",
            "published": (_NOW - timedelta(hours=13)).isoformat(),
            "summary": "The FDA granted approval for the first AI system to diagnose cancer from radiology scans without requiring human physician review. The system showed 97.3% accuracy, surpassing radiologist averages.",
            "full_text": "The approval represents a landmark...",
            "image_url": "", "topics": ["Health", "AI", "Technology"],
            "sentiment": "positive", "signal_score": 8.6, "is_duplicate": False,
            "why_matters": "Could reduce healthcare costs by 30% and address global radiologist shortage of 400,000.",
        },
        {
            "id": _id("Reddit IPO"), "title": "Reddit Shares Surge 40% After Reporting First-Ever Profitable Quarter",
            "source": "CNBC", "url": "https://cnbc.com",
            "published": (_NOW - timedelta(hours=14)).isoformat(),
            "summary": "Reddit reported its first profitable quarter since its 2024 IPO, driven by AI data licensing deals worth $250M and advertising growth of 68% YoY. Shares surged 40% after hours.",
            "full_text": "Reddit's path to profitability...",
            "image_url": "", "topics": ["Business", "Finance", "Technology"],
            "sentiment": "positive", "signal_score": 7.2, "is_duplicate": False,
            "why_matters": "Validates social media AI data licensing as a business model.",
        },
    ]
    return articles


def get_demo_digest() -> dict:
    return {
        "title": f"Morning Intelligence Brief — {datetime.now().strftime('%A, %B %d, %Y')}",
        "overview": "Today's news cycle is dominated by AI breakthroughs, with OpenAI's GPT-5 launch and FDA's landmark AI diagnosis approval redefining capabilities. Financial markets responded positively to Fed rate cut signals, while three major climate tipping points warning adds urgency to ESG strategies.",
        "key_themes": ["AI Capability Leap", "Rate Cut Cycle", "Space Commercialisation", "Climate Urgency", "Enterprise AI Monetisation"],
        "sections": [
            {
                "category": "Technology & AI",
                "headline": "GPT-5 and Quantum Computing Mark a New Technological Epoch",
                "stories": [
                    {"title": "OpenAI launches GPT-5 with record reasoning", "insight": "Multi-step reasoning capabilities may replace knowledge-worker tasks within 24 months."},
                    {"title": "Google achieves quantum advantage with Willow", "insight": "Current encryption infrastructure needs urgent review by security teams."},
                    {"title": "FDA approves AI-only radiology diagnosis", "insight": "Healthcare AI is crossing from decision-support to decision-replacement."},
                ],
                "takeaway": "Allocate AI transformation budget now — the capability curve is steepening faster than enterprise adoption can follow."
            },
            {
                "category": "Markets & Finance",
                "headline": "Fed Pivot and Bitcoin ETF Create Dual Risk-On Tailwinds",
                "stories": [
                    {"title": "Fed signals three 2025 rate cuts", "insight": "Cost of capital falling favours growth equities and real estate."},
                    {"title": "NVIDIA beats estimates by 18%", "insight": "AI capex super-cycle has multiple years to run."},
                    {"title": "Bitcoin ETF options approved", "insight": "Institutional hedging tools now available for crypto exposure."},
                ],
                "takeaway": "Risk-on environment favours tech and growth positioning; review fixed-income duration."
            },
        ],
        "market_signals": ["S&P 500 +1.8% on Fed news", "BTC +12% on ETF approval", "NVDA +8% post-earnings"],
        "action_items": [
            "Review AI strategy roadmap against GPT-5 capability update",
            "Brief board on climate tipping point timeline implications for ESG",
            "Assess encryption infrastructure against quantum computing timeline",
        ],
        "sentiment_overview": "positive",
        "word_of_day": "Breakthrough",
    }
