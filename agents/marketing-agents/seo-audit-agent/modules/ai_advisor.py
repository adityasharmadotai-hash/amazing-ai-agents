"""
ai_advisor.py — OpenAI GPT-4o powered SEO recommendations.
Five focused API calls each returning clean structured JSON.
"""

import json
import os
import re

import streamlit as st
from openai import OpenAI


def _client() -> OpenAI:
    try:
        key = st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY","")
    except Exception:
        key = os.environ.get("OPENAI_API_KEY","")
    return OpenAI(api_key=key)


def is_configured() -> bool:
    try:
        key = st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY","")
    except Exception:
        key = os.environ.get("OPENAI_API_KEY","")
    return bool(key)


def _call(system: str, user: str, tokens: int = 1500) -> str:
    r = _client().chat.completions.create(
        model="gpt-4o",
        max_tokens=tokens,
        messages=[{"role":"system","content":system},{"role":"user","content":user}]
    )
    return r.choices[0].message.content.strip()


def _json(text: str):
    return json.loads(re.sub(r"```(?:json)?|```","",text).strip())


# ── 1. SEO Improvement Plan ───────────────────────────────────────────────────

def seo_improvements(raw: dict, audit: dict) -> dict:
    meta = audit.get("meta",{}); kw = audit.get("keywords",{}); tech = audit.get("technical",{})
    criticals = [i["message"] for cat in audit.values() if isinstance(cat,dict)
                 for i in cat.get("issues",[]) if i.get("severity")=="critical"][:6]
    user = f"""Website: {raw.get('url','')}
SEO Score: {audit.get('overall_score',0)}/100
Title: {meta.get('title','')} ({meta.get('title_length',0)} chars)
Description: {meta.get('description','')} ({meta.get('description_length',0)} chars)
Word count: {kw.get('word_count',0)}
Top keywords: {[k for k,_ in kw.get('top_keywords',[])[:8]]}
Load time: {tech.get('load_time_seconds',0)}s | HTTPS: {tech.get('is_https',False)}
Critical issues: {criticals}

Return ONLY this JSON:
{{
  "executive_summary": "2-3 sentences on SEO health",
  "overall_grade": "A/B/C/D/F",
  "quick_wins": [{{"action":"...","impact":"High/Medium/Low","effort":"Low","detail":"..."}}],
  "short_term": [{{"action":"...","impact":"High/Medium/Low","effort":"Medium","detail":"..."}}],
  "long_term": [{{"action":"...","impact":"High/Medium/Low","effort":"High","detail":"..."}}],
  "top_3_priorities": ["Priority 1","Priority 2","Priority 3"]
}}
quick_wins: 4 items fixable immediately. short_term: 4 items 1-4 weeks. long_term: 3 strategic items."""
    try:
        return _json(_call("You are a world-class SEO expert. Return ONLY valid JSON.", user, 2000))
    except Exception as e:
        return {"error":str(e),"executive_summary":"AI unavailable","quick_wins":[],"short_term":[],"long_term":[],"top_3_priorities":[]}


# ── 2. Content Optimisation ───────────────────────────────────────────────────

def content_optimisation(raw: dict, audit: dict) -> dict:
    kw = audit.get("keywords",{}); meta = audit.get("meta",{})
    user = f"""Website: {raw.get('url','')}
Current title: {meta.get('title','')}
Current description: {meta.get('description','')}
Top keywords: {[k for k,_ in kw.get('top_keywords',[])[:6]]}
Content snippet: {raw.get('body_text','')[:700]}

Return ONLY this JSON:
{{
  "title_options": ["50-60 char title 1","title 2","title 3"],
  "description_options": ["150-160 char desc 1","desc 2","desc 3"],
  "content_suggestions": ["suggestion 1","suggestion 2","suggestion 3","suggestion 4","suggestion 5"],
  "cta_improvements": ["CTA idea 1","CTA idea 2","CTA idea 3"],
  "primary_keyword": "best keyword to target",
  "keyword_reasoning": "why this keyword",
  "content_gaps": ["missing topic 1","missing topic 2","missing topic 3"]
}}"""
    try:
        return _json(_call("You are an expert SEO copywriter. Return ONLY valid JSON.", user, 1500))
    except Exception as e:
        return {"error":str(e),"title_options":[],"description_options":[],"content_suggestions":[],"cta_improvements":[]}


# ── 3. Technical Guidance ─────────────────────────────────────────────────────

def technical_guidance(raw: dict, audit: dict) -> dict:
    tech = audit.get("technical",{}); imgs = audit.get("images",{})
    user = f"""Technical issues:
HTTPS: {tech.get('is_https',False)} | Load: {tech.get('load_time_seconds',0)}s
HTML: {tech.get('html_size_kb',0)}KB | Schema: {tech.get('has_schema',False)}
Missing alt: {imgs.get('missing_alt',0)} | Redirects: {tech.get('redirect_count',0)}

Return ONLY this JSON:
{{
  "performance_fixes": [{{"fix":"...","instruction":"...","priority":"High/Medium/Low"}}],
  "schema_recommendation": "which schema type and brief example",
  "image_optimisation": ["tip 1","tip 2","tip 3"],
  "core_web_vitals": [{{"metric":"LCP/FID/CLS","tip":"..."}}],
  "robots_txt": "recommendation",
  "sitemap": "recommendation"
}}"""
    try:
        return _json(_call("You are a technical SEO engineer. Return ONLY valid JSON.", user, 1200))
    except Exception as e:
        return {"error":str(e),"performance_fixes":[],"image_optimisation":[],"core_web_vitals":[]}


# ── 4. UX Suggestions ────────────────────────────────────────────────────────

def ux_suggestions(raw: dict, audit: dict) -> dict:
    kw = audit.get("keywords",{}); links = audit.get("links",{})
    user = f"""Website: {raw.get('url','')}
Word count: {kw.get('word_count',0)} | Internal links: {links.get('internal_count',0)}
Content: {raw.get('body_text','')[:500]}
Top keywords: {[k for k,_ in kw.get('top_keywords',[])[:5]]}

Return ONLY this JSON:
{{
  "readability_tips": ["tip 1","tip 2","tip 3"],
  "navigation_suggestions": ["suggestion 1","suggestion 2","suggestion 3"],
  "engagement_improvements": ["improvement 1","improvement 2","improvement 3"],
  "mobile_ux_tips": ["tip 1","tip 2","tip 3"],
  "trust_signals": ["signal 1","signal 2","signal 3"],
  "page_structure_advice": "overall advice on page structure"
}}"""
    try:
        return _json(_call("You are a UX & CRO specialist. Return ONLY valid JSON.", user, 1000))
    except Exception as e:
        return {"error":str(e),"readability_tips":[],"navigation_suggestions":[],"engagement_improvements":[]}


# ── 5. Keyword Strategy ───────────────────────────────────────────────────────

def keyword_strategy(raw: dict, audit: dict) -> dict:
    kw = audit.get("keywords",{})
    user = f"""Website: {raw.get('url','')}
Current top keywords: {[k for k,_ in kw.get('top_keywords',[])[:8]]}
Word count: {kw.get('word_count',0)}

Return ONLY this JSON:
{{
  "primary_keywords": [{{"keyword":"...","type":"informational/transactional/navigational","difficulty":"Low/Medium/High","rationale":"..."}}],
  "long_tail_opportunities": ["phrase 1","phrase 2","phrase 3","phrase 4"],
  "semantic_keywords": ["related 1","related 2","related 3","related 4"],
  "content_ideas": [{{"title":"...","target_keyword":"...","type":"Blog/Landing/FAQ"}}],
  "local_seo_tip": "local SEO recommendation"
}}
primary_keywords: 4 items. content_ideas: 4 items."""
    try:
        return _json(_call("You are an SEO keyword strategist. Return ONLY valid JSON.", user, 1200))
    except Exception as e:
        return {"error":str(e),"primary_keywords":[],"long_tail_opportunities":[],"content_ideas":[]}
