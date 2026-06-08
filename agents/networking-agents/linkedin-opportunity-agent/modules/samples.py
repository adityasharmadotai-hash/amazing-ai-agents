"""
samples.py — Realistic sample LinkedIn posts, profiles & companies.

Used by the built-in simulation source so the dashboard is populated and fully
demonstrable without any LinkedIn credentials or paid data provider. Replace the
simulation source (see monitor.set_source) to feed real, compliant data.
"""

SAMPLE_POSTS = [
    {
        "author_name": "Priya Nair",
        "author_headline": "VP Engineering at NimbusAI",
        "company": "NimbusAI",
        "industry": "Artificial Intelligence",
        "url": "https://www.linkedin.com/in/priyanair",
        "text": "We're hiring! NimbusAI is looking for two senior AI Engineers to join "
                "our applied research team — RAG, agents, and eval infrastructure. Remote-first, "
                "competitive equity. If you love shipping LLM products, DM me. #hiring #AIengineering",
    },
    {
        "author_name": "Daniel Okoro",
        "author_headline": "Founder & CEO at LedgerLoop (Fintech)",
        "company": "LedgerLoop",
        "industry": "Fintech",
        "url": "https://www.linkedin.com/in/danielokoro",
        "text": "Thrilled to announce we've raised our $5M seed round led by Northstar Ventures "
                "to reinvent SMB reconciliation. Now hiring across product and growth, and looking "
                "for design partners in the accounting space. Let's build. 🚀",
    },
    {
        "author_name": "Sofia Marchetti",
        "author_headline": "Head of Marketing at BrightPath SaaS",
        "company": "BrightPath",
        "industry": "SaaS",
        "url": "https://www.linkedin.com/in/sofiamarchetti",
        "text": "Looking for solutions: our team is evaluating tools for marketing attribution "
                "and we need something that plays nicely with HubSpot. Any recommendations? Budget "
                "approved for this quarter, hoping to make a decision in the next few weeks.",
    },
    {
        "author_name": "Marcus Webb",
        "author_headline": "Partnerships Lead at CloudForge",
        "company": "CloudForge",
        "industry": "Cloud Infrastructure",
        "url": "https://www.linkedin.com/in/marcuswebb",
        "text": "CloudForge is actively seeking partners for our new integration marketplace. "
                "If you build developer tooling and want a co-marketing + reseller motion, let's "
                "talk. Open to strategic alliances that create real customer value.",
    },
    {
        "author_name": "Aisha Rahman",
        "author_headline": "CTO at MediSync Health",
        "company": "MediSync",
        "industry": "Healthcare",
        "url": "https://www.linkedin.com/in/aisharahman",
        "text": "After a great year we're expanding the engineering team — open roles for "
                "backend and data engineers who care about healthcare. We're also looking for a "
                "consultant to help us with HIPAA-compliant infrastructure. Reach out if interested.",
    },
    {
        "author_name": "Tom Becker",
        "author_headline": "Angel Investor | ex-Stripe",
        "company": "Independent",
        "industry": "Venture Capital",
        "url": "https://www.linkedin.com/in/tombecker",
        "text": "Heading to SaaStr next week and happy to make founder introductions for anyone "
                "raising a pre-seed or seed round in fintech or devtools. Open to connect — drop a "
                "comment and let's grab a coffee chat at the event. #networking #founders",
    },
    {
        "author_name": "Lena Vasquez",
        "author_headline": "Director of Ops at GreenLeaf Retail",
        "company": "GreenLeaf",
        "industry": "Retail",
        "url": "https://www.linkedin.com/in/lenavasquez",
        "text": "We need help with our e-commerce replatforming and are looking for an agency or "
                "experienced freelancer who has migrated from Magento to Shopify Plus. Who can help? "
                "This is urgent — we want to start this month.",
    },
    {
        "author_name": "Hiroshi Tanaka",
        "author_headline": "Founder at DataPilot Analytics",
        "company": "DataPilot",
        "industry": "Data Analytics",
        "url": "https://www.linkedin.com/in/hiroshitanaka",
        "text": "Just wrapped an amazing quarter. Reflecting on lessons learned scaling a data "
                "team from 3 to 30. Grateful for the journey and the people. More thoughts in the "
                "comments. 🙏",
    },
    {
        "author_name": "Grace Adeyemi",
        "author_headline": "COO at Velocity Logistics",
        "company": "Velocity",
        "industry": "Logistics",
        "url": "https://www.linkedin.com/in/graceadeyemi",
        "text": "We just closed a Series A and are now in the market for a modern TMS platform "
                "and a fractional CFO. Vendors — send me your best pitch. Looking to make decisions "
                "before end of quarter as we scale operations across three new regions.",
    },
    {
        "author_name": "Oliver Schmidt",
        "author_headline": "Developer Advocate at OpenStack tools",
        "company": "Stackly",
        "industry": "Developer Tools",
        "url": "https://www.linkedin.com/in/oliverschmidt",
        "text": "Looking for collaborators on a joint webinar about agentic workflows and "
                "developer productivity. If you're building in the AI dev-tools space and want to "
                "co-author content or run a joint session, let's collaborate!",
    },
    {
        "author_name": "Fatima Al-Sayed",
        "author_headline": "Talent Lead at QuantumLeap Robotics",
        "company": "QuantumLeap",
        "industry": "Robotics",
        "url": "https://www.linkedin.com/in/fatimaalsayed",
        "text": "Now hiring: Robotics Software Engineers and an ML Ops lead. We're growing the "
                "team fast after strong customer traction. Apply now or refer a friend — generous "
                "referral bonus. #hiring #robotics #MLOps",
    },
    {
        "author_name": "Carlos Mendes",
        "author_headline": "VP Sales at Apex Cyber",
        "company": "Apex Cyber",
        "industry": "Cybersecurity",
        "url": "https://www.linkedin.com/in/carlosmendes",
        "text": "Genuinely curious — what's the best tool for continuous security posture "
                "management these days? We're shopping for a vendor to replace our current stack "
                "and have budget allocated. Would love honest recommendations from practitioners.",
    },
    {
        "author_name": "Nadia Petrova",
        "author_headline": "Founder at EduSpark (EdTech)",
        "company": "EduSpark",
        "industry": "Education",
        "url": "https://www.linkedin.com/in/nadiapetrova",
        "text": "Big news: EduSpark just raised a $12M Series B to bring adaptive learning to "
                "1M+ students. Hiring across engineering, sales, and customer success — and looking "
                "for content partnerships with universities. Let's change education together.",
    },
    {
        "author_name": "James Whitfield",
        "author_headline": "Head of Growth at FleetWise",
        "company": "FleetWise",
        "industry": "Mobility",
        "url": "https://www.linkedin.com/in/jameswhitfield",
        "text": "Reminder to drink water and take breaks today. Building a startup is a marathon. "
                "Take care of yourselves out there. 💧",
    },
    {
        "author_name": "Mei Lin",
        "author_headline": "Procurement Manager at Horizon Manufacturing",
        "company": "Horizon",
        "industry": "Manufacturing",
        "url": "https://www.linkedin.com/in/meilin",
        "text": "We're issuing an RFP for an IoT monitoring platform for our factory floor. "
                "If your company does predictive maintenance and edge analytics, request the brief "
                "in the comments. Evaluating vendors over the next 6 weeks. Serious inquiries only.",
    },
]

SAMPLE_PROFILES = [
    {
        "name": "Priya Nair",
        "headline": "VP Engineering at NimbusAI",
        "profile_url": "https://www.linkedin.com/in/priyanair",
        "company": "NimbusAI",
        "industry": "Artificial Intelligence",
    },
    {
        "name": "Daniel Okoro",
        "headline": "Founder & CEO at LedgerLoop",
        "profile_url": "https://www.linkedin.com/in/danielokoro",
        "company": "LedgerLoop",
        "industry": "Fintech",
    },
    {
        "name": "Tom Becker",
        "headline": "Angel Investor | ex-Stripe",
        "profile_url": "https://www.linkedin.com/in/tombecker",
        "company": "Independent",
        "industry": "Venture Capital",
    },
]

SAMPLE_COMPANIES = [
    {
        "name": "NimbusAI",
        "page_url": "https://www.linkedin.com/company/nimbusai",
        "industry": "Artificial Intelligence",
    },
    {
        "name": "CloudForge",
        "page_url": "https://www.linkedin.com/company/cloudforge",
        "industry": "Cloud Infrastructure",
    },
    {
        "name": "EduSpark",
        "page_url": "https://www.linkedin.com/company/eduspark",
        "industry": "Education",
    },
]
