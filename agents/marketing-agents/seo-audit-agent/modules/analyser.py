"""
analyser.py — Rule-based SEO analysis. Scores each category 0-100.
"""

import re
from collections import Counter

STOP_WORDS = set("""a about above after again against all also an and any are aren't as at be
because been before being below between both but by can't cannot could couldn't did didn't do
does doesn't doing don't down during each few for from further get got had hadn't has hasn't
have haven't having he he'd he'll he's her here here's hers herself him himself his how how's
i i'd i'll i'm i've if in into is isn't it it's its itself let's me more most mustn't my
myself no nor not of off on once only or other ought our ours ourselves out over own same
shan't she she'd she'll she's should shouldn't so some such than that that's the their theirs
them themselves then there there's these they they'd they'll they're they've this those through
to too under until up us very was wasn't we we'd we'll we're we've were weren't what what's
when when's where where's which while who who's whom why why's will with won't would wouldn't
you you'd you'll you're you've your yours yourself yourselves""".split())


def _score(passed: int, total: int) -> int:
    return round((passed / total) * 100) if total else 0


def _issue(severity: str, message: str, fix: str = "") -> dict:
    return {"severity": severity, "message": message, "fix": fix}


# ── 1. Meta Tags ──────────────────────────────────────────────────────────────

def analyse_meta(d: dict) -> dict:
    issues, ok, total = [], 0, 9
    title = d.get("title", "")
    desc  = d.get("description", "")
    canon = d.get("canonical_url", "")
    vp    = d.get("viewport", "")
    robots= d.get("robots", "").lower()
    og    = d.get("og_tags", {})
    tw    = d.get("twitter_tags", {})

    # Title
    tl = len(title)
    if not title:
        issues.append(_issue("critical","No <title> tag","Add a 50-60 char title with your primary keyword."))
    elif tl < 30:
        issues.append(_issue("warning",f"Title too short ({tl} chars)","Expand to 50-60 characters."))
    elif tl > 60:
        issues.append(_issue("warning",f"Title too long ({tl} chars)","Trim to under 60 chars."))
    else:
        ok += 1; issues.append(_issue("pass",f"Title OK — {tl} chars: \"{title[:50]}\""))

    # Meta description
    dl = len(desc)
    if not desc:
        issues.append(_issue("critical","No meta description","Add 150-160 char description for better CTR."))
    elif dl < 70:
        issues.append(_issue("warning",f"Description too short ({dl} chars)","Expand to 150-160 characters."))
    elif dl > 160:
        issues.append(_issue("warning",f"Description too long ({dl} chars)","Trim to under 160 chars."))
    else:
        ok += 1; issues.append(_issue("pass",f"Description OK — {dl} chars"))

    # Canonical
    if not canon:
        issues.append(_issue("warning","No canonical URL","Add <link rel='canonical'> to prevent duplicate content."))
    else:
        ok += 1; issues.append(_issue("pass","Canonical URL set"))

    # Viewport
    if not vp:
        issues.append(_issue("critical","No viewport meta tag","Add <meta name='viewport' content='width=device-width, initial-scale=1'>"))
    else:
        ok += 1; issues.append(_issue("pass","Viewport tag present"))

    # Robots
    if "noindex" in robots:
        issues.append(_issue("critical","Page is NOINDEX","Remove noindex to allow search engine indexing!"))
    elif "nofollow" in robots:
        issues.append(_issue("warning","Page is NOFOLLOW","Links won't be followed by search engines."))
    else:
        ok += 1

    # OG tags
    og_ok = all(og.get(k) for k in ["og:title","og:description","og:image"])
    if not og_ok:
        miss = [k for k in ["og:title","og:description","og:image"] if not og.get(k)]
        issues.append(_issue("warning",f"Missing OG tags: {', '.join(miss)}","Add Open Graph tags for social sharing."))
    else:
        ok += 1; issues.append(_issue("pass","Open Graph tags complete"))

    # Twitter card
    if not tw:
        issues.append(_issue("info","No Twitter Card tags","Add twitter:card tags for Twitter sharing."))
    else:
        ok += 1; issues.append(_issue("pass","Twitter Card tags present"))

    # HTTPS (also checked in technical but mention here)
    if d.get("is_https"):
        ok += 1

    return {"score": _score(ok, total), "issues": issues,
            "title": title, "title_length": len(title),
            "description": desc, "description_length": dl,
            "canonical_url": canon, "og_tags": og, "twitter_tags": tw}


# ── 2. Headings ───────────────────────────────────────────────────────────────

def analyse_headings(d: dict) -> dict:
    h = d.get("headings", {})
    issues, ok, total = [], 0, 6
    h1s = h.get("h1", []); h2s = h.get("h2", []); h3s = h.get("h3", [])

    if not h1s:
        issues.append(_issue("critical","No H1 tag","Add exactly one H1 with your primary keyword."))
    elif len(h1s) > 1:
        issues.append(_issue("warning",f"{len(h1s)} H1 tags found","Use only one H1 per page."))
    else:
        ok += 1; issues.append(_issue("pass",f"H1: \"{h1s[0][:60]}\""))

    if len(h1s) == 1 and len(h1s[0]) <= 70:
        ok += 1
    elif h1s and len(h1s[0]) > 70:
        issues.append(_issue("warning",f"H1 too long ({len(h1s[0])} chars)","Keep H1 under 70 chars."))

    if not h2s:
        issues.append(_issue("warning","No H2 tags","Use H2 tags to structure your content."))
    else:
        ok += 1; issues.append(_issue("pass",f"{len(h2s)} H2 tag(s) found"))

    total_h = sum(len(v) for v in h.values())
    if total_h == 0:
        issues.append(_issue("critical","No heading tags found","Add proper heading structure for SEO."))
    else:
        ok += 1

    empty = [lvl for lvl, tags in h.items() for t in tags if not t.strip()]
    if empty:
        issues.append(_issue("warning",f"Empty headings: {empty}","Remove or fill empty heading tags."))
    else:
        ok += 1; issues.append(_issue("pass","No empty heading tags"))

    if h2s:
        ok += 1

    return {"score": _score(ok, total), "issues": issues, "headings": h,
            "h1_count": len(h1s), "h2_count": len(h2s), "h3_count": len(h3s),
            "total_headings": total_h, "h1_text": h1s[0] if h1s else ""}


# ── 3. Keywords ───────────────────────────────────────────────────────────────

def analyse_keywords(d: dict) -> dict:
    text  = d.get("body_text","")
    title = d.get("title","")
    desc  = d.get("description","")
    h     = d.get("headings",{})
    wc    = d.get("word_count", 0)
    issues = []

    clean = re.sub(r"[^a-zA-Z\s]"," ", text.lower())
    words = [w for w in clean.split() if len(w) > 3 and w not in STOP_WORDS]
    freq  = Counter(words)
    top   = freq.most_common(20)

    title_words = set(re.sub(r"[^a-zA-Z\s]"," ", title.lower()).split())
    desc_words  = set(re.sub(r"[^a-zA-Z\s]"," ", desc.lower()).split())
    h1s = h.get("h1", [])
    h1_words = set(re.sub(r"[^a-zA-Z\s]"," ", (h1s[0] if h1s else "").lower()).split())

    kw_in_title = [k for k,_ in top[:5] if k in title_words]
    kw_in_desc  = [k for k,_ in top[:5] if k in desc_words]
    kw_in_h1    = [k for k,_ in top[:5] if k in h1_words]

    if not kw_in_title:
        issues.append(_issue("warning","Top keywords not in title","Include primary keyword in title."))
    else:
        issues.append(_issue("pass",f"Keywords in title: {kw_in_title}"))

    if not kw_in_desc:
        issues.append(_issue("info","Top keywords not in meta description","Naturally include keywords in description."))
    else:
        issues.append(_issue("pass",f"Keywords in description: {kw_in_desc}"))

    if not kw_in_h1:
        issues.append(_issue("warning","Primary keyword not in H1","Include main keyword in H1."))
    elif kw_in_h1:
        issues.append(_issue("pass",f"Keywords in H1: {kw_in_h1}"))

    density_issues = []
    for kw, count in top[:3]:
        if wc > 0:
            d_ = round(count/wc*100,2)
            if d_ > 5:
                density_issues.append(f"'{kw}' at {d_}% (stuffing risk)")
            elif d_ < 0.3:
                density_issues.append(f"'{kw}' at {d_}% (too low)")

    if wc < 300:
        issues.append(_issue("warning",f"Low word count: {wc}","Aim for 500+ words. 1500+ for best rankings."))
    elif wc >= 1500:
        issues.append(_issue("pass",f"Excellent content length: {wc} words"))
    else:
        issues.append(_issue("info",f"Content length: {wc} words (aim for 1500+)"))

    score = 60
    score += 10 if kw_in_title else 0
    score += 5  if kw_in_desc else 0
    score += 5  if kw_in_h1 else 0
    score += 10 if wc >= 500 else 0
    score += 10 if not density_issues else 0
    score = min(100, max(0, score))

    return {"score": score, "issues": issues, "top_keywords": top,
            "word_count": wc, "density_issues": density_issues,
            "keywords_in_title": kw_in_title, "keywords_in_desc": kw_in_desc}


# ── 4. Technical ──────────────────────────────────────────────────────────────

def analyse_technical(d: dict) -> dict:
    issues, ok, total = [], 0, 9
    sc    = d.get("status_code", 0)
    lt    = d.get("load_time_seconds", 0)
    redir = d.get("redirect_chain", [])
    hdrs  = d.get("response_headers", {})

    if d.get("is_https"):
        ok += 1; issues.append(_issue("pass","HTTPS enabled"))
    else:
        issues.append(_issue("critical","NOT using HTTPS","Migrate to HTTPS immediately — it's a ranking factor."))

    if sc == 200:
        ok += 1; issues.append(_issue("pass",f"HTTP {sc} OK"))
    elif sc in (301,302):
        issues.append(_issue("info",f"HTTP {sc} redirect","Ensure redirect is intentional."))
    else:
        issues.append(_issue("critical",f"HTTP status: {sc}","Fix the status code error."))

    if len(redir) > 2:
        issues.append(_issue("warning",f"Redirect chain: {len(redir)} hops","Reduce redirect hops."))
    else:
        ok += 1

    if lt < 1.5:
        ok += 1; issues.append(_issue("pass",f"Load time: {lt}s (excellent)"))
    elif lt < 3:
        ok += 1; issues.append(_issue("info",f"Load time: {lt}s (good, aim <1.5s)"))
    elif lt < 5:
        issues.append(_issue("warning",f"Load time: {lt}s (slow)","Optimise images, enable caching, use CDN."))
    else:
        issues.append(_issue("critical",f"Load time: {lt}s (very slow)","Investigate server performance urgently."))

    kb = d.get("html_size_kb",0)
    if kb > 500:
        issues.append(_issue("warning",f"HTML size: {kb} KB","Minimise HTML markup."))
    else:
        ok += 1; issues.append(_issue("pass",f"HTML size: {kb} KB"))

    if d.get("has_schema"):
        ok += 1; issues.append(_issue("pass","Structured data found"))
    else:
        issues.append(_issue("warning","No structured data","Add Schema.org markup for rich results."))

    if d.get("has_favicon"):
        ok += 1; issues.append(_issue("pass","Favicon present"))
    else:
        issues.append(_issue("info","No favicon","Add a favicon."))

    if d.get("html_lang"):
        ok += 1; issues.append(_issue("pass",f"HTML lang='{d['html_lang']}'"))
    else:
        issues.append(_issue("warning","No HTML lang attribute","Add lang='en' to <html>."))

    if hdrs.get("Content-Security-Policy") or hdrs.get("X-Frame-Options"):
        ok += 1; issues.append(_issue("pass","Security headers present"))
    else:
        issues.append(_issue("info","No security headers","Add CSP and X-Frame-Options headers."))

    return {"score": _score(ok, total), "issues": issues,
            "is_https": d.get("is_https"), "status_code": sc,
            "load_time_seconds": lt, "html_size_kb": kb,
            "has_schema": d.get("has_schema"), "redirect_count": len(redir)}


# ── 5. Images ─────────────────────────────────────────────────────────────────

def analyse_images(d: dict) -> dict:
    imgs = d.get("images", [])
    issues, ok, total = [], 0, 5
    if not imgs:
        return {"score": 85, "issues": [_issue("info","No images found")],
                "total_images":0,"missing_alt":0,"lazy_loaded":0}

    miss_alt  = [i for i in imgs if not i.get("alt")]
    lazy      = [i for i in imgs if i.get("loading")=="lazy"]
    no_size   = [i for i in imgs if not i.get("width") or not i.get("height")]
    pct_alt   = round(len(miss_alt)/len(imgs)*100,1)

    if not miss_alt:
        ok += 1; issues.append(_issue("pass","All images have alt text"))
    elif pct_alt < 20:
        ok += 1; issues.append(_issue("warning",f"{len(miss_alt)} images missing alt ({pct_alt}%)","Add alt text to all images."))
    else:
        issues.append(_issue("critical",f"{len(miss_alt)}/{len(imgs)} images missing alt ({pct_alt}%)","This is a major accessibility issue."))

    pct_lazy = round(len(lazy)/len(imgs)*100,1)
    if pct_lazy > 50:
        ok += 1; issues.append(_issue("pass",f"{len(lazy)}/{len(imgs)} images lazy-loaded ({pct_lazy}%)"))
    else:
        issues.append(_issue("info",f"Only {len(lazy)}/{len(imgs)} images use lazy loading","Add loading='lazy' to below-fold images."))

    if no_size:
        issues.append(_issue("warning",f"{len(no_size)} images missing width/height","Specify dimensions to prevent layout shift (CLS)."))
    else:
        ok += 1; issues.append(_issue("pass","All images have width/height"))

    if len(imgs) <= 30:
        ok += 1; issues.append(_issue("pass",f"{len(imgs)} images (good count)"))
    else:
        issues.append(_issue("warning",f"{len(imgs)} images — high count","Consider reducing images for faster load."))

    if len(miss_alt) == 0:
        ok += 1

    return {"score": _score(ok, total), "issues": issues,
            "total_images": len(imgs), "missing_alt": len(miss_alt),
            "lazy_loaded": len(lazy), "no_size": len(no_size), "sample": imgs[:5]}


# ── 6. Links ──────────────────────────────────────────────────────────────────

def analyse_links(d: dict) -> dict:
    internal = d.get("internal_links", [])
    external = d.get("external_links", [])
    issues, ok, total = [], 0, 5
    GENERIC = {"click here","read more","here","more","link","this","learn more"}

    empty = sum(1 for l in internal+external if not l["text"].strip())
    if empty:
        issues.append(_issue("warning",f"{empty} links have no anchor text","Add descriptive anchor text."))
    else:
        ok += 1; issues.append(_issue("pass","All links have anchor text"))

    generic = sum(1 for l in internal+external if l["text"].strip().lower() in GENERIC)
    if generic:
        issues.append(_issue("info",f"{generic} links use generic text (e.g. 'click here')","Use descriptive anchor text."))
    else:
        ok += 1

    if len(internal) < 3:
        issues.append(_issue("warning",f"Only {len(internal)} internal links","Add internal links for crawlability."))
    elif len(internal) > 100:
        issues.append(_issue("warning",f"{len(internal)} internal links (very high)","Reduce to <100."))
    else:
        ok += 1; issues.append(_issue("pass",f"{len(internal)} internal links"))

    nofollow = sum(1 for l in external if "nofollow" in l.get("rel",[]))
    issues.append(_issue("info",f"{nofollow}/{len(external)} external links are nofollow"))
    ok += 1

    if external:
        ok += 1; issues.append(_issue("info",f"{len(external)} external links"))

    return {"score": _score(ok, total), "issues": issues,
            "internal_count": len(internal), "external_count": len(external),
            "empty_anchor": empty, "generic_anchor": generic, "nofollow_ext": nofollow}


# ── Overall ───────────────────────────────────────────────────────────────────

WEIGHTS = {"meta":0.25,"headings":0.15,"keywords":0.20,"technical":0.20,"images":0.10,"links":0.10}


def calculate_overall(results: dict) -> int:
    return round(sum(results.get(c,{}).get("score",0)*w for c,w in WEIGHTS.items()))


def score_label(score: int) -> tuple:
    if score >= 85: return "Excellent","#22c55e"
    if score >= 70: return "Good","#84cc16"
    if score >= 50: return "Needs Work","#f59e0b"
    return "Poor","#ef4444"


def issue_counts(results: dict) -> dict:
    c = {"critical":0,"warning":0,"info":0,"pass":0}
    for cat in results.values():
        if isinstance(cat, dict):
            for iss in cat.get("issues",[]):
                c[iss.get("severity","info")] = c.get(iss["severity"],0)+1
    return c
