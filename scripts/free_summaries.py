#!/usr/bin/env python3
"""Free extractive summaries from RSS descriptions, no paid API or hallucinations."""
import json
import re
from pathlib import Path

path = Path("articles.json")
data = json.loads(path.read_text(encoding="utf-8"))
count = 0
for article in data.get("articles", []):
    if article.get("ai_summary"):
        continue
    description = re.sub(r"\s+", " ", article.get("description", "")).strip()
    title = article.get("title", "").strip()
    if len(description) < 65:
        continue
    sentences = re.split(r"(?<=[.!?])\s+", description)
    summary = " ".join(sentences[:2]).strip()
    if len(summary) > 270:
        summary = summary[:267].rsplit(" ", 1)[0] + "…"
    if summary and summary.lower().strip(" .") != title.lower().strip(" ."):
        article["auto_summary"] = summary
        count += 1
if count:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Free extractive summaries: {count}")
