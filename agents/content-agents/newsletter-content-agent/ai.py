"""
modules/ai.py
-------------
AI processing layer powered by OpenAI GPT-4o.

Pipeline:
  1. summarize_articles()   -> condense each source into a summary + key point
  2. generate_newsletter()  -> turn the summaries into a structured newsletter

Both calls request strict JSON and parse defensively.
"""

import json
from openai import OpenAI, OpenAIError

MODEL = "gpt-4o"

# Maps the UI length choice -> rough word budget for the body.
LENGTH_GUIDE = {
    "Short": "around 250-350 words total, punchy and skimmable",
    "Medium": "around 500-650 words total, balanced detail",
    "Long": "around 900-1100 words total, in-depth and thorough",
}


class AIError(Exception):
    """Raised when the OpenAI call fails or returns unusable output."""


def _client(api_key: str) -> OpenAI:
    if not api_key:
        raise AIError("Missing OpenAI API key. Add it in Settings.")
    return OpenAI(api_key=api_key)


def _parse_json(text: str):
    """Strip markdown fences and parse JSON, raising AIError on failure."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```", 2)
        cleaned = cleaned[1] if len(cleaned) > 1 else text
        if cleaned.lstrip().startswith("json"):
            cleaned = cleaned.lstrip()[4:]
    cleaned = cleaned.strip().strip("`").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise AIError(f"Model returned unparseable JSON: {exc}") from exc


def summarize_articles(articles: list, api_key: str) -> list:
    """
    Summarize each article. Returns a list of
    {title, summary, key_point, source, url}.
    """
    if not articles:
        raise AIError("No articles to summarize.")

    client = _client(api_key)

    # Compact, numbered source list for the prompt.
    blocks = []
    for i, art in enumerate(articles, 1):
        body = art.get("description") or ""
        extra = art.get("content") or ""
        blocks.append(
            f"[{i}] TITLE: {art['title']}\n"
            f"SOURCE: {art.get('source','')}\n"
            f"TEXT: {body} {extra}".strip()
        )
    sources_text = "\n\n".join(blocks)

    system = (
        "You are a sharp editorial research assistant. You read raw news "
        "snippets and distill them into clean, factual summaries. Never invent "
        "facts that are not present in the provided text."
    )
    user = (
        "Summarize each numbered article below. For every article produce: a "
        "2-3 sentence neutral summary, and one standout key takeaway "
        "(a single sentence).\n\n"
        "Return ONLY valid JSON in this exact shape, with no extra commentary:\n"
        '{ "articles": [ { "index": 1, "summary": "...", "key_point": "..." } ] }\n\n'
        f"ARTICLES:\n{sources_text}"
    )

    try:
        resp = client.chat.completions.create(
            model=MODEL,
            temperature=0.3,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
    except OpenAIError as exc:
        raise AIError(f"OpenAI summarization failed: {exc}") from exc

    parsed = _parse_json(resp.choices[0].message.content)
    items = parsed.get("articles", []) if isinstance(parsed, dict) else []

    # Re-attach source metadata by index.
    summaries = []
    by_index = {item.get("index"): item for item in items if isinstance(item, dict)}
    for i, art in enumerate(articles, 1):
        item = by_index.get(i, {})
        summaries.append({
            "title": art["title"],
            "summary": item.get("summary", art.get("description", "")),
            "key_point": item.get("key_point", ""),
            "source": art.get("source", ""),
            "url": art.get("url", ""),
        })
    return summaries


def generate_newsletter(topic: str, audience: str, style: str, length: str,
                        summaries: list, api_key: str) -> dict:
    """
    Generate a full newsletter from the article summaries.
    Returns a dict with title, subject_line, introduction, key_insights[],
    conclusion, cta.
    """
    if not summaries:
        raise AIError("No summaries available to build a newsletter.")

    client = _client(api_key)
    length_hint = LENGTH_GUIDE.get(length, LENGTH_GUIDE["Medium"])

    research_text = "\n\n".join(
        f"- {s['title']} ({s['source']})\n  Summary: {s['summary']}\n  Key point: {s['key_point']}"
        for s in summaries
    )

    system = (
        "You are an expert newsletter writer who turns research into engaging, "
        "well-structured editions. You match the requested tone precisely and "
        "write only from the provided research — no fabricated statistics."
    )
    user = (
        f"Write a newsletter edition.\n\n"
        f"TOPIC: {topic}\n"
        f"TARGET AUDIENCE: {audience}\n"
        f"WRITING STYLE: {style}\n"
        f"LENGTH: {length_hint}\n\n"
        f"RESEARCH (use these as your sources):\n{research_text}\n\n"
        "Produce a newsletter with: a catchy title, an email subject line, a "
        "warm introduction, 3-5 key insights (each with a short heading and a "
        "paragraph), a concise conclusion, and a single clear call-to-action.\n\n"
        "Return ONLY valid JSON in exactly this shape:\n"
        "{\n"
        '  "title": "...",\n'
        '  "subject_line": "...",\n'
        '  "introduction": "...",\n'
        '  "key_insights": [ { "heading": "...", "body": "..." } ],\n'
        '  "conclusion": "...",\n'
        '  "cta": "..."\n'
        "}"
    )

    try:
        resp = client.chat.completions.create(
            model=MODEL,
            temperature=0.7,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
    except OpenAIError as exc:
        raise AIError(f"OpenAI generation failed: {exc}") from exc

    data = _parse_json(resp.choices[0].message.content)
    if not isinstance(data, dict):
        raise AIError("Newsletter generation returned an unexpected shape.")

    # Normalize key_insights into list[{heading, body}].
    insights = data.get("key_insights", [])
    norm_insights = []
    if isinstance(insights, list):
        for ins in insights:
            if isinstance(ins, dict):
                norm_insights.append({
                    "heading": ins.get("heading", "").strip(),
                    "body": ins.get("body", "").strip(),
                })
            elif isinstance(ins, str):
                norm_insights.append({"heading": "", "body": ins.strip()})
    data["key_insights"] = norm_insights

    for field in ("title", "subject_line", "introduction", "conclusion", "cta"):
        data.setdefault(field, "")
    return data
