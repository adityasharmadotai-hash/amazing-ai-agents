"""
scraper.py — Fetch and parse a webpage for SEO data.
Uses requests + BeautifulSoup. Returns a structured raw data dict.
"""

import re
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
TIMEOUT = 20


def normalise_url(url: str) -> str:
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def fetch_page(url: str) -> dict:
    url = normalise_url(url)
    start = time.time()
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        load_time = round(time.time() - start, 3)
        soup = BeautifulSoup(resp.text, "html.parser")
        return {
            "url": resp.url,
            "status_code": resp.status_code,
            "load_time_seconds": load_time,
            "content_length_bytes": len(resp.content),
            "html": resp.text,
            "soup": soup,
            "headers": dict(resp.headers),
            "redirect_chain": [r.url for r in resp.history],
            "is_https": resp.url.startswith("https://"),
            "domain": urlparse(resp.url).netloc,
        }
    except requests.exceptions.SSLError:
        return {"error": "SSL certificate error on this domain."}
    except requests.exceptions.ConnectionError:
        return {"error": f"Could not connect to {url}. Check the URL."}
    except requests.exceptions.Timeout:
        return {"error": f"Request timed out after {TIMEOUT}s."}
    except Exception as e:
        return {"error": str(e)}


def extract_raw_data(page: dict) -> dict:
    if "error" in page:
        return page

    soup: BeautifulSoup = page["soup"]
    html: str = page["html"]

    # Meta
    def get_meta(name_re=None, prop=None):
        if name_re:
            t = soup.find("meta", attrs={"name": re.compile(name_re, re.I)})
        else:
            t = soup.find("meta", property=prop)
        return (t.get("content", "") if t else "").strip()

    title_tag = soup.find("title")
    title     = title_tag.get_text(strip=True) if title_tag else ""

    # OG tags
    og_tags = {t.get("property", ""): t.get("content", "")
               for t in soup.find_all("meta", property=re.compile(r"^og:"))}
    tw_tags = {t.get("name", ""): t.get("content", "")
               for t in soup.find_all("meta", attrs={"name": re.compile(r"^twitter:")})}

    # Headings
    headings = {f"h{i}": [t.get_text(strip=True) for t in soup.find_all(f"h{i}")]
                for i in range(1, 7)}

    # Images
    images = [{"src": img.get("src",""), "alt": img.get("alt",""),
               "loading": img.get("loading",""), "width": img.get("width",""),
               "height": img.get("height","")}
              for img in soup.find_all("img")]

    # Links
    base_domain = urlparse(page["url"]).netloc
    internal_links, external_links = [], []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        text = a.get_text(strip=True)
        full = urljoin(page["url"], href)
        parsed = urlparse(full)
        entry = {"href": full, "text": text, "rel": a.get("rel", [])}
        if parsed.netloc == base_domain or not parsed.netloc:
            internal_links.append(entry)
        elif parsed.scheme in ("http", "https"):
            external_links.append(entry)

    # Body text
    for tag in soup(["script","style","noscript"]):
        tag.decompose()
    body_text  = soup.get_text(separator=" ", strip=True)
    word_count = len(body_text.split())

    lang_tag  = soup.find("html")
    canonical = soup.find("link", rel="canonical")
    favicon   = soup.find("link", rel=re.compile(r"icon", re.I))

    return {
        "url":                  page["url"],
        "status_code":          page["status_code"],
        "load_time_seconds":    page["load_time_seconds"],
        "content_length_bytes": page["content_length_bytes"],
        "is_https":             page["is_https"],
        "domain":               page["domain"],
        "redirect_chain":       page["redirect_chain"],
        "response_headers":     page["headers"],
        "title":                title,
        "title_length":         len(title),
        "description":          get_meta(r"description"),
        "keywords_meta":        get_meta(r"keywords"),
        "robots":               get_meta(r"robots"),
        "canonical_url":        canonical.get("href","") if canonical else "",
        "viewport":             get_meta(r"viewport"),
        "html_lang":            lang_tag.get("lang","") if lang_tag else "",
        "og_tags":              og_tags,
        "twitter_tags":         tw_tags,
        "headings":             headings,
        "images":               images,
        "internal_links":       internal_links,
        "external_links":       external_links,
        "body_text":            body_text[:6000],
        "word_count":           word_count,
        "has_schema":           bool(soup.find_all("script", type="application/ld+json")),
        "has_favicon":          favicon is not None,
        "html_size_kb":         round(len(html.encode()) / 1024, 1),
    }
