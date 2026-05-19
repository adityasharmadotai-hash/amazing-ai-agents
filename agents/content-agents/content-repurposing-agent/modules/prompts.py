"""
prompts.py — Prompt management system for all content types and writing styles.
Each prompt is a template that accepts {transcript} and {style_instruction}.
"""

# ─────────────────────────────────────────────
# Writing Style Definitions
# ─────────────────────────────────────────────

WRITING_STYLES = {
    "Viral": {
        "icon": "🔥",
        "description": "Punchy, emotional, share-worthy hooks that stop the scroll",
        "instruction": (
            "Write in a VIRAL style: use bold claims, emotional triggers, power numbers, "
            "pattern interrupts, and irresistible curiosity gaps. Start with a scroll-stopping "
            "hook. Use short punchy sentences. Make it impossible NOT to share."
        ),
    },
    "Educational": {
        "icon": "📚",
        "description": "Clear, structured, value-packed content that teaches",
        "instruction": (
            "Write in an EDUCATIONAL style: clear structure, step-by-step breakdown, "
            "practical examples, and actionable takeaways. Use numbered lists where helpful. "
            "Prioritise clarity and real value over entertainment."
        ),
    },
    "Founder": {
        "icon": "🚀",
        "description": "Personal, story-driven, authentic founder perspective",
        "instruction": (
            "Write in a FOUNDER style: personal story, behind-the-scenes insight, "
            "vulnerability mixed with confidence, lessons learned the hard way. "
            "First-person, conversational. Share what you wish someone had told you earlier."
        ),
    },
    "Technical": {
        "icon": "⚙️",
        "description": "Deep, precise, expert-level content for technical audiences",
        "instruction": (
            "Write in a TECHNICAL style: precise terminology, deep insights, "
            "implementation details, code concepts where relevant. "
            "Target experienced professionals. Skip basics. Go deep."
        ),
    },
}

# ─────────────────────────────────────────────
# Content Type Prompts
# ─────────────────────────────────────────────

CONTENT_PROMPTS = {
    "linkedin_post": {
        "label": "LinkedIn Post",
        "icon": "💼",
        "description": "Professional LinkedIn post optimised for engagement",
        "system": """You are an expert LinkedIn content strategist who has written posts 
that generated millions of impressions. You understand the LinkedIn algorithm deeply.""",
        "user": """Based on this YouTube transcript, write a high-performing LinkedIn post.

STYLE: {style_instruction}

RULES:
- 150-300 words ideal
- Start with a hook that stops scrolling (NOT "I" as the first word)
- Use line breaks every 1-2 sentences for readability
- Include 3-5 relevant hashtags at the end
- End with a question or CTA that drives comments
- No emojis in the first line
- Make it feel authentic, not AI-generated

TRANSCRIPT:
{transcript}

Write only the post — no preamble or labels.""",
    },

    "twitter_thread": {
        "label": "Twitter/X Thread",
        "icon": "🐦",
        "description": "Viral Twitter thread optimised for retweets",
        "system": """You are a viral Twitter/X content creator who writes threads 
that regularly hit 1M+ impressions. You know exactly how to hook, retain, and deliver value.""",
        "user": """Based on this YouTube transcript, write a viral Twitter/X thread.

STYLE: {style_instruction}

RULES:
- 8-12 tweets
- Tweet 1: irresistible hook (max 280 chars) — ends with "Thread 🧵" or "A thread:"
- Tweets 2-10: one insight per tweet, max 280 chars each
- Number each tweet: 1/, 2/, 3/ etc.
- Last tweet: summary + follow CTA
- Use line breaks within tweets for scannability
- Bold key phrases with CAPS for emphasis
- End with "Follow @[author] for more"

TRANSCRIPT:
{transcript}

Write the complete numbered thread — no preamble.""",
    },

    "instagram_caption": {
        "label": "Instagram Caption",
        "icon": "📸",
        "description": "Engaging Instagram caption with hashtag strategy",
        "system": """You are an Instagram growth expert who writes captions 
that drive saves, shares, and follower growth.""",
        "user": """Based on this YouTube transcript, write an Instagram caption.

STYLE: {style_instruction}

RULES:
- Hook in line 1 (people see this before "more")
- 100-200 words for the body
- Line breaks every 1-2 sentences
- Add "..." before the fold if needed to encourage tap
- 15-20 hashtags grouped at the end (mix of large, medium, niche)
- End with a save/share CTA
- Feel conversational and authentic

TRANSCRIPT:
{transcript}

Write only the caption — no preamble.""",
    },

    "viral_hooks": {
        "label": "Viral Hooks",
        "icon": "🎣",
        "description": "10 scroll-stopping opening hooks for any platform",
        "system": """You are a world-class copywriter specialising in viral hooks 
and pattern interrupts that stop the scroll instantly.""",
        "user": """Based on this YouTube transcript, generate 10 viral hooks.

STYLE: {style_instruction}

HOOK TYPES to include (mix of these):
1. Controversial/Bold claim hook
2. Number/Statistic hook  
3. Curiosity gap hook
4. Story hook
5. Contrarian hook
6. Fear/Pain hook
7. Promise hook
8. Question hook
9. Before/After hook
10. Secret/Insider hook

FORMAT:
Hook 1 [Type]: [The hook]
Hook 2 [Type]: [The hook]
... etc.

Each hook should be 1-2 sentences max, under 150 chars.

TRANSCRIPT:
{transcript}

Write all 10 hooks — no preamble.""",
    },

    "carousel_slides": {
        "label": "Carousel Slides",
        "icon": "🎠",
        "description": "LinkedIn/Instagram carousel slide content",
        "system": """You are a carousel content strategist who creates high-save, 
high-share slide decks for LinkedIn and Instagram.""",
        "user": """Based on this YouTube transcript, write a 10-slide carousel.

STYLE: {style_instruction}

FORMAT FOR EACH SLIDE:
Slide X:
Headline: [Max 8 words — punchy]
Body: [2-3 bullet points or 2-3 short sentences]
Visual note: [Brief note on what image/graphic would work]

SLIDE STRUCTURE:
- Slide 1: Hook slide (bold claim or question)
- Slides 2-9: One insight per slide
- Slide 10: CTA slide (follow/save/share)

RULES:
- Headlines must be scannable at a glance
- Each slide stands alone
- Progressive value build
- Last slide drives action

TRANSCRIPT:
{transcript}

Write all 10 slides — no preamble.""",
    },

    "blog_summary": {
        "label": "Blog Summary",
        "icon": "📝",
        "description": "SEO-optimised blog article summary",
        "system": """You are an SEO content writer and blogger who writes 
summaries that rank on Google and keep readers engaged.""",
        "user": """Based on this YouTube transcript, write a comprehensive blog summary.

STYLE: {style_instruction}

STRUCTURE:
# [Compelling SEO Title]

## Introduction (2-3 sentences)
[Hook + what reader will learn]

## Key Insights
### [Section 1 Title]
[2-3 paragraphs]

### [Section 2 Title]  
[2-3 paragraphs]

### [Section 3 Title]
[2-3 paragraphs]

## Key Takeaways
- [Bullet 1]
- [Bullet 2]
- [Bullet 3]
- [Bullet 4]
- [Bullet 5]

## Conclusion (2-3 sentences)
[Summary + CTA]

Target: 400-600 words total. Use proper markdown.

TRANSCRIPT:
{transcript}

Write the complete blog summary.""",
    },
}

# ─────────────────────────────────────────────
# Custom Prompt Templates (user-editable)
# ─────────────────────────────────────────────

DEFAULT_CUSTOM_PROMPTS = {
    "newsletter": {
        "label": "Newsletter Section",
        "icon": "📧",
        "system": "You are an expert newsletter writer with 100k+ subscribers.",
        "user": """Write a newsletter section based on this transcript.

STYLE: {style_instruction}

Format:
- Subject line suggestion
- 150-200 word section
- Key takeaway
- Call to action

TRANSCRIPT:
{transcript}""",
    },
    "youtube_description": {
        "label": "YouTube Description",
        "icon": "▶️",
        "system": "You are a YouTube SEO expert who writes descriptions that rank and convert.",
        "user": """Write a YouTube video description based on this transcript.

STYLE: {style_instruction}

Include:
- 2-3 sentence hook (first 125 chars are critical)
- What viewers will learn (bullet points)
- Timestamps section (estimate 5-7 chapters)
- Relevant hashtags (5-10)
- Subscribe CTA

TRANSCRIPT:
{transcript}""",
    },
}


def build_prompt(content_type: str, transcript: str, style: str) -> dict:
    """
    Build a complete prompt dict for a given content type and style.
    Returns {"system": ..., "user": ...} ready for the OpenAI API.
    """
    style_data = WRITING_STYLES.get(style, WRITING_STYLES["Educational"])
    style_instruction = style_data["instruction"]

    if content_type in CONTENT_PROMPTS:
        template = CONTENT_PROMPTS[content_type]
    elif content_type in DEFAULT_CUSTOM_PROMPTS:
        template = DEFAULT_CUSTOM_PROMPTS[content_type]
    else:
        return {}

    return {
        "system": template["system"],
        "user": template["user"].format(
            style_instruction=style_instruction,
            transcript=transcript,
        ),
    }


def get_all_content_types() -> dict:
    """Return all content types (built-in + custom)."""
    return {**CONTENT_PROMPTS, **DEFAULT_CUSTOM_PROMPTS}
