#!/usr/bin/env python3
"""Résumé français à partir du texte intégral accessible publiquement.
Extraction locale gratuite, sans API; ne contourne pas les paywalls.
"""
import json
import re
import math
import unicodedata
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
import trafilatura

FILE = Path("articles.json")
data = json.loads(FILE.read_text(encoding="utf-8"))
articles = data.get("articles", [])
STOP = set("avec dans pour sans cette celui celle elles leurs notre votre aussi comme mais donc puis sont sera être avoir plus moins entre depuis après avant sous vers chez dont ainsi très tous toutes tout nous vous leur quand alors faire fait encore afin même autre autres".split())
def words(text):
    s = "".join(c for c in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(c))
    return [w for w in re.findall(r"[a-z]{4,}", s) if w not in STOP]
def summary(text, title):
    text = re.sub(r"\s+", " ", text).strip()
    sentences = [x.strip() for x in re.split(r"(?<=[.!?])\s+", text) if 65 <= len(x.strip()) <= 340]
    sentences = sentences[:100]
    if len(sentences) < 4:
        return None
    titlewords = set(words(title))
    freq = {}
    for w in words(" ".join(sentences)):
        freq[w] = freq.get(w, 0) + 1
    ranked = []
    for i, sent in enumerate(sentences):
        ws = words(sent)
        if len(ws) < 9 or len(ws) > 65:
            continue
        common = sum(min(freq.get(w, 0), 6) for w in set(ws)) / math.sqrt(len(ws))
        focus = len(titlewords.intersection(ws)) / max(1, len(titlewords))
        boilerplate = bool(re.search(r"abonnez-vous|newsletter|publicité|cookies|partagez|cliquez ici|lire aussi|copyright", sent, re.I))
        ranked.append((common + 3 * focus + (2 if i < 6 else 0) - (12 if boilerplate else 0), i, sent))
    selected = []
    for _, i, sent in sorted(ranked, reverse=True):
        sw = set(words(sent))
        if any(len(sw & set(words(other))) / max(1, min(len(sw), len(set(words(other))))) > .63 for _, other in selected):
            continue
        selected.append((i, sent))
        if len(selected) == 3:
            break
    selected.sort()
    result = " ".join(sent for _, sent in selected)
    if len(result) < 180:
        return None
    return result[:850].rsplit(" ", 1)[0] + ("…" if len(result) > 850 else "")
def fetch(article):
    url = article.get("url", "")
    host = urlparse(url).hostname or ""
    if not url.startswith("https://") or host == "news.google.com" or article.get("full_summary"):
        return None
    try:
        html = trafilatura.fetch_url(url)
        if not html:
            return None
        body = trafilatura.extract(html, include_comments=False, include_tables=False, favor_precision=True)
        if not body or len(body) < 700:
            return None
        result = summary(body, article.get("title", ""))
        return (url, result) if result else None
    except Exception:
        return None
# Priorité au contenu industriel et aux articles récents, maximum 15 par collecte.
candidates = [a for a in articles if not a.get("full_summary") and not (a.get("url", "").startswith("https://news.google.com/"))]
candidates.sort(key=lambda a: (a.get("category") not in ("Automatisme", "IA", "Cybersécurité"), -(len(a.get("description", "")) < 90), a.get("date", "")), reverse=False)
candidates = candidates[:15]
results = {}
with ThreadPoolExecutor(max_workers=4) as pool:
    futures = [pool.submit(fetch, a) for a in candidates]
    for future in as_completed(futures):
        value = future.result()
        if value:
            results[value[0]] = value[1]
for a in articles:
    if a.get("url") in results:
        a["full_summary"] = results[a["url"]]
if results:
    FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Résumés fondés sur le texte intégral : {len(results)}/{len(candidates)}")
