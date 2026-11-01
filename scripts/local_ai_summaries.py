#!/usr/bin/env python3
"""Free local generative summaries via a small open-source model on GitHub Actions.
Uses CPU, no paid API or secret. Falls back to existing extractive summaries if unavailable.
"""
import json
import os
from pathlib import Path

path = Path("articles.json")
data = json.loads(path.read_text(encoding="utf-8"))
articles = data.get("articles", [])
targets = [a for a in articles[:45] if not a.get("ai_summary") and len(a.get("description", "")) >= 80][:8]
if not targets:
    print("No new articles to summarize.")
    raise SystemExit(0)

try:
    from transformers import pipeline
    import torch
    torch.set_num_threads(2)
    model = pipeline("text2text-generation", model="google/flan-t5-small", device=-1)
except Exception as exc:
    print("Local model unavailable; free extractive summaries remain:", str(exc)[:250])
    raise SystemExit(0)

count = 0
for a in targets:
    prompt = (
        "Résume en français en une phrase, uniquement avec ces informations. "
        "N'invente aucun détail. "
        "Titre: " + a.get("title", "")[:180] +
        " Description: " + a.get("description", "")[:400]
    )
    try:
        response = model(prompt, max_new_tokens=90, do_sample=False, truncation=True, max_length=512)
        summary = response[0]["generated_text"].strip()
        if len(summary) >= 35 and summary.casefold() != a.get("title", "").casefold():
            a["ai_summary"] = summary[:450]
            count += 1
    except Exception as exc:
        print("Summary failed:", str(exc)[:160])
if count:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Local generative summaries added: {count}/{len(targets)}")
