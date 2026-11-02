#!/usr/bin/env python3
"""Résumés prudents en français : pas de traduction inventée, pas de titre recopié."""
import json
import re
import unicodedata
from pathlib import Path

path = Path("articles.json")
data = json.loads(path.read_text(encoding="utf-8"))
def norm(value):
    return "".join(c for c in unicodedata.normalize("NFKD", value.lower()) if not unicodedata.combining(c))
def french(text):
    return len(re.findall(r"\b(?:le|la|les|des|une|dans|pour|avec|est|sont|sur|qui|que|cette|aux|leur|plus|par)\b", text.lower())) >= 2
def usable(text, title):
    if len(text) < 105 or not french(text):
        return False
    if re.search(r"\b(?:the|with|which|launched|launches|best deals|first promos|has been)\b", text, re.I):
        return False
    if re.match(r"\s*(?:titre|title|description|summary)\s*:", text, re.I):
        return False
    words = set(re.findall(r"[a-z]{5,}", norm(title)))
    summary_words = re.findall(r"[a-z]{5,}", norm(text))
    if summary_words and sum(w in words for w in summary_words) / len(summary_words) > .58:
        return False
    return norm(text).strip(" .") != norm(title).strip(" .")
count = 0
removed = 0
for article in data.get("articles", []):
    title = article.get("title", "")
    description = re.sub(r"\s+", " ", article.get("description", "")).strip()
    existing = article.get("ai_summary", "")
    if existing and not usable(existing, title):
        article.pop("ai_summary", None)
        removed += 1
    article.pop("auto_summary", None)
    if article.get("ai_summary") or not usable(description, title):
        continue
    sentences = re.split(r"(?<=[.!?])\s+", description)
    excerpt = " ".join(sentences[:3]).strip()
    if len(excerpt) > 420:
        excerpt = excerpt[:417].rsplit(" ", 1)[0] + "…"
    if usable(excerpt, title):
        article["auto_summary"] = excerpt
        count += 1
path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Résumés français validés : {count} ; résumés IA douteux supprimés : {removed}")
