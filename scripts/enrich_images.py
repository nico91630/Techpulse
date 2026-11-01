#!/usr/bin/env python3
"""Enrich recent TechPulse articles with their publishers' Open Graph images."""
import concurrent.futures
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import urllib.request
from urllib.parse import urljoin, urlparse

PATH = Path("articles.json")
class Meta(HTMLParser):
    def __init__(self):
        super().__init__()
        self.image = None
    def handle_starttag(self, tag, attrs):
        if tag.lower() != "meta":
            return
        d = dict(attrs)
        key = (d.get("property") or d.get("name") or "").lower()
        if key in ("og:image", "twitter:image", "twitter:image:src") and d.get("content") and not self.image:
            self.image = html.unescape(d["content"])

def image_for(article):
    url = article.get("url", "")
    if urlparse(url).scheme not in ("http", "https"):
        return None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; TechPulseBot/1.0)", "Accept": "text/html"})
        with urllib.request.urlopen(req, timeout=9) as response:
            if "text/html" not in response.headers.get("Content-Type", ""):
                return None
            body = response.read(220000).decode("utf-8", errors="ignore")
        parser = Meta()
        parser.feed(body[:150000])
        if not parser.image:
            return None
        image = urljoin(url, parser.image)
        return image if urlparse(image).scheme in ("https", "http") else None
    except Exception:
        return None

def main():
    data = json.loads(PATH.read_text(encoding="utf-8"))
    articles = data.get("articles", [])
    # Refresh new entries only; keep image data on existing entries.
    targets = [a for a in articles[:120] if not (a.get("image") or a.get("image_url"))]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(image_for, targets))
    count = 0
    for article, image in zip(targets, results):
        if image:
            article["image"] = image
            count += 1
    if count:
        PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Images added: {count}; checked: {len(targets)}")

if __name__ == "__main__":
    main()
