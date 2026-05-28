"""
modules/demo_data.py
--------------------
Realistic demo emails, contacts, and calendar events for testing
without connecting a real Gmail account.
"""
from __future__ import annotations
from datetime import datetime, timedelta
import random

_NOW = datetime.now()


def get_demo_emails() -> list[dict]:
    return [
        {
            "id": "demo_001", "thread_id": "t001",
            "subject": "Q3 Product Roadmap Review — Need your input by Friday",
            "from": "Sarah Chen <sarah.chen@techcorp.com>", "sender": "Sarah Chen <sarah.chen@techcorp.com>",
            "to": "you@company.com",
            "date": (_NOW - timedelta(hours=2)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "date_str": (_NOW - timedelta(hours=2)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "snippet": "Hi, I wanted to follow up on the Q3 roadmap we discussed last week. Could you review the attached doc and share your thoughts before Friday's leadership sync? Key areas needing input...",
            "body": "Hi,\n\nI wanted to follow up on the Q3 roadmap we discussed last week. Could you review the attached doc and share your thoughts before Friday's leadership sync?\n\nKey areas needing your input:\n1. Feature prioritization for the mobile app\n2. Resource allocation between teams A and B\n3. Go-to-market timeline for the API launch\n\nThe leadership meeting is at 2pm Friday so I need your feedback by Thursday EOD.\n\nThanks,\nSarah",
            "labels": ["INBOX", "UNREAD", "IMPORTANT"], "is_unread": True, "is_important": True, "is_starred": False,
            "_ai_priority": "critical", "_ai_urgency": 9, "_ai_category": "task",
        },
        {
            "id": "demo_002", "thread_id": "t002",
            "subject": "Re: Partnership proposal — next steps",
            "from": "Marcus Williams <m.williams@partnerco.com>", "sender": "Marcus Williams <m.williams@partnerco.com>",
            "to": "you@company.com",
            "date": (_NOW - timedelta(hours=5)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "date_str": (_NOW - timedelta(hours=5)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "snippet": "Thanks for the detailed proposal. Our team reviewed it and we're very interested. A few questions before we can move forward — can we schedule a 30-min call this week?",
            "body": "Hi,\n\nThanks for the detailed proposal. Our team reviewed it and we're very interested in moving forward.\n\nA few questions before we can proceed:\n1. What's the minimum contract term?\n2. Do you offer white-labeling?\n3. What does the onboarding process look like?\n\nCan we schedule a 30-minute call this week to discuss? I'm free Thursday afternoon or Friday morning.\n\nBest,\nMarcus",
            "labels": ["INBOX", "UNREAD"], "is_unread": True, "is_important": False, "is_starred": True,
            "_ai_priority": "high", "_ai_urgency": 8, "_ai_category": "meeting",
        },
        {
            "id": "demo_003", "thread_id": "t003",
            "subject": "Action required: Sign the updated NDA before Monday",
            "from": "Legal Team <legal@company.com>", "sender": "Legal Team <legal@company.com>",
            "to": "you@company.com",
            "date": (_NOW - timedelta(hours=8)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "date_str": (_NOW - timedelta(hours=8)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "snippet": "Please review and sign the updated NDA attached. This is required for the upcoming vendor meeting. Deadline: Monday 9am. Use DocuSign link below.",
            "body": "Hi,\n\nPlease review and sign the updated NDA attached to this email.\n\nThis is required for the upcoming vendor meeting on Tuesday. The signed document must be submitted by Monday 9am.\n\nDocuSign link: [link]\n\nIf you have any questions about the document, please contact legal@company.com.\n\nRegards,\nLegal Team",
            "labels": ["INBOX", "UNREAD", "IMPORTANT"], "is_unread": True, "is_important": True, "is_starred": False,
            "_ai_priority": "critical", "_ai_urgency": 9, "_ai_category": "task",
        },
        {
            "id": "demo_004", "thread_id": "t004",
            "subject": "Team lunch this Thursday — confirming attendance?",
            "from": "Priya Patel <priya@company.com>", "sender": "Priya Patel <priya@company.com>",
            "to": "you@company.com",
            "date": (_NOW - timedelta(hours=10)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "date_str": (_NOW - timedelta(hours=10)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "snippet": "Hey! Just checking — are you coming to the team lunch on Thursday at noon? We're going to that new Italian place on 5th. Let me know so I can give the restaurant an accurate count.",
            "body": "Hey!\n\nJust checking — are you coming to the team lunch this Thursday at noon? We're going to Ristorante Marco on 5th Ave.\n\nLet me know so I can give them an accurate headcount by Wednesday.\n\nCheers,\nPriya",
            "labels": ["INBOX", "UNREAD"], "is_unread": True, "is_important": False, "is_starred": False,
            "_ai_priority": "medium", "_ai_urgency": 5, "_ai_category": "social",
        },
        {
            "id": "demo_005", "thread_id": "t005",
            "subject": "Monthly newsletter: Industry insights — May 2025",
            "from": "TechInsider <newsletter@techinsider.io>", "sender": "TechInsider <newsletter@techinsider.io>",
            "to": "you@company.com",
            "date": (_NOW - timedelta(days=1)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "date_str": (_NOW - timedelta(days=1)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "snippet": "This month: AI in enterprise, top SaaS funding rounds, 5 tools your team should be using, and an interview with the CEO of DataLabs.",
            "body": "Hello,\n\nThis month's highlights:\n- AI adoption in enterprise: what's actually working\n- Top SaaS funding rounds: $2.1B raised in May\n- 5 tools your team should be using in 2025\n- Exclusive interview with DataLabs CEO\n\nRead the full newsletter at techinsider.io\n\nUnsubscribe | Manage preferences",
            "labels": ["INBOX"], "is_unread": True, "is_important": False, "is_starred": False,
            "_ai_priority": "low", "_ai_urgency": 2, "_ai_category": "marketing",
        },
        {
            "id": "demo_006", "thread_id": "t006",
            "subject": "Budget approval needed — Q2 marketing spend",
            "from": "Finance <finance@company.com>", "sender": "Finance <finance@company.com>",
            "to": "you@company.com",
            "date": (_NOW - timedelta(days=1, hours=3)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "date_str": (_NOW - timedelta(days=1, hours=3)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "snippet": "The Q2 marketing budget ($45,000) is pending your approval. Please review and approve in the finance portal by EOD Friday to avoid a hold on planned campaigns.",
            "body": "Hi,\n\nThe Q2 marketing budget ($45,000) is pending your approval in the finance portal.\n\nPlease review and approve by EOD Friday. If not approved, planned campaigns will be placed on hold starting Monday.\n\nPortal: finance.company.com/approvals\n\nSummary:\n- Digital ads: $25,000\n- Events: $12,000\n- Content creation: $8,000\n\nRegards,\nFinance Team",
            "labels": ["INBOX", "UNREAD", "IMPORTANT"], "is_unread": True, "is_important": True, "is_starred": False,
            "_ai_priority": "high", "_ai_urgency": 8, "_ai_category": "task",
        },
        {
            "id": "demo_007", "thread_id": "t007",
            "subject": "Great meeting today — following up on action items",
            "from": "David Kim <d.kim@clientco.com>", "sender": "David Kim <d.kim@clientco.com>",
            "to": "you@company.com",
            "date": (_NOW - timedelta(days=2)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "date_str": (_NOW - timedelta(days=2)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "snippet": "Great discussion today. Following up on the action items we discussed: 1) You'll send the revised proposal by Wednesday 2) We'll review internally and respond by Friday 3) Next sync scheduled for next Tuesday.",
            "body": "Hi,\n\nGreat discussion today! Here's a recap of our action items:\n\n1. You'll send the revised proposal by Wednesday EOD\n2. We'll review internally and respond by Friday\n3. Next sync scheduled for Tuesday at 10am\n\nLet me know if I missed anything.\n\nLooking forward to moving this forward!\n\nDavid",
            "labels": ["INBOX"], "is_unread": False, "is_important": False, "is_starred": True,
            "_ai_priority": "high", "_ai_urgency": 7, "_ai_category": "task",
        },
        {
            "id": "demo_008", "thread_id": "t008",
            "subject": "Interview feedback request — Senior Engineer candidate",
            "from": "HR Team <hr@company.com>", "sender": "HR Team <hr@company.com>",
            "to": "you@company.com",
            "date": (_NOW - timedelta(days=2, hours=5)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "date_str": (_NOW - timedelta(days=2, hours=5)).strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "snippet": "Please submit your feedback for Alex Thompson's interview in the ATS portal. We need all feedback by tomorrow 5pm to make a hiring decision this week.",
            "body": "Hi,\n\nPlease submit your interview feedback for Alex Thompson (Senior Engineer candidate) in the ATS portal.\n\nWe need all panelist feedback by tomorrow 5pm to make a hiring decision this week.\n\nPortal: ats.company.com/feedback/AT2025\n\nThank you,\nHR Team",
            "labels": ["INBOX", "UNREAD"], "is_unread": True, "is_important": False, "is_starred": False,
            "_ai_priority": "high", "_ai_urgency": 7, "_ai_category": "task",
        },
    ]


def get_demo_contacts() -> list[dict]:
    return [
        {"email": "sarah.chen@techcorp.com", "name": "Sarah Chen", "company": "TechCorp",
         "email_count": 24, "last_contact": "2 hours ago",
         "ai_summary": "Sarah is a Product Director at TechCorp. She frequently reaches out about roadmap planning and cross-functional alignment. Communication style is direct and detail-oriented. Key stakeholder for Q3 planning."},
        {"email": "m.williams@partnerco.com", "name": "Marcus Williams", "company": "PartnerCo",
         "email_count": 12, "last_contact": "5 hours ago",
         "ai_summary": "Marcus leads partnerships at PartnerCo. Relationship is at proposal stage with strong mutual interest. Responsive and business-focused. Potential high-value partner."},
        {"email": "d.kim@clientco.com", "name": "David Kim", "company": "ClientCo",
         "email_count": 31, "last_contact": "2 days ago",
         "ai_summary": "David is a key client contact at ClientCo. Active engagement on ongoing projects. Very organized — always follows up with written summaries. High-priority relationship."},
        {"email": "priya@company.com", "name": "Priya Patel", "company": "Your Company",
         "email_count": 45, "last_contact": "10 hours ago",
         "ai_summary": "Priya is a colleague on the marketing team. Frequent social and logistical coordination. Friendly communication style. Part of core team network."},
    ]


def get_demo_events() -> list[dict]:
    today = datetime.now()
    return [
        {
            "id": "evt_001", "title": "Q3 Leadership Sync",
            "start": (today.replace(hour=14, minute=0)).isoformat(),
            "end": (today.replace(hour=15, minute=0)).isoformat(),
            "attendees": ["sarah.chen@techcorp.com", "cto@company.com", "cpo@company.com", "you@company.com"],
            "location": "Google Meet", "meet_link": "https://meet.google.com/abc-defg-hij",
            "description": "Quarterly leadership sync to review Q3 roadmap, discuss priorities, and align on resource allocation.",
            "organizer": "sarah.chen@techcorp.com",
        },
        {
            "id": "evt_002", "title": "Partnership Call — PartnerCo",
            "start": (today + timedelta(days=1)).replace(hour=10, minute=0).isoformat(),
            "end": (today + timedelta(days=1)).replace(hour=10, minute=30).isoformat(),
            "attendees": ["m.williams@partnerco.com", "you@company.com"],
            "location": "Zoom", "meet_link": "",
            "description": "30-minute call to discuss partnership proposal terms and next steps.",
            "organizer": "you@company.com",
        },
        {
            "id": "evt_003", "title": "Team Lunch 🍕",
            "start": (today + timedelta(days=3)).replace(hour=12, minute=0).isoformat(),
            "end": (today + timedelta(days=3)).replace(hour=13, minute=30).isoformat(),
            "attendees": ["priya@company.com", "team@company.com"],
            "location": "Ristorante Marco, 5th Ave", "meet_link": "",
            "description": "Monthly team lunch.",
            "organizer": "priya@company.com",
        },
        {
            "id": "evt_004", "title": "ClientCo Project Review",
            "start": (today + timedelta(days=6)).replace(hour=10, minute=0).isoformat(),
            "end": (today + timedelta(days=6)).replace(hour=11, minute=0).isoformat(),
            "attendees": ["d.kim@clientco.com", "you@company.com", "pm@company.com"],
            "location": "Google Meet", "meet_link": "https://meet.google.com/xyz-123",
            "description": "Weekly project review with ClientCo. Discuss revised proposal and next steps.",
            "organizer": "d.kim@clientco.com",
        },
    ]
