#!/usr/bin/env python3
"""Generate concise source-grounded summaries; no API key means a safe no-op."""
import json
import os
import urllib.request
from pathlib import Path

PATH = Path("articles.json")
KEY = os.getenv("OPENAI_API_KEY", "").strip()
if not KEY:
    print("OPENAI_API_KEY absent: AI summaries skipped.")
    raise SystemExit(0)

data = json.loads(PATH.read_text(encoding="utf-8"))
articles = data.get("articles", [])
# Restrict volume and avoid generating summaries from empty descriptions.
targets = [a for a in articles[:35] if not a.get("ai_summary") and len(a.get("description", "")) >= 60]
count = 0
for a in targets[:15]:
    prompt = ("Résume cette actualité en français en 2 phrases courtes (maximum 65 mots). "
              "Utilise uniquement le titre et la description ci-dessous. "
              "N'invente aucun fait et n'affirme pas avoir lu l'article complet. "
              "N'ajoute aucun titre ni préambule.\n"
              f"Titre : {a.get('title','')}\nDescription : {a.get('description','')}")
    payload = json.dumps({"model": "gpt-4.1-mini",
                          "messages": [{"role": "user", "content": prompt}],
                          "max_tokens": 150, "temperature": 0.2}).encode()
    req = urllib.request.Request("https://api.openai.com/v1/chat/completions",
                                 data=payload, headers={"Authorization": "Bearer " + KEY,
                                 "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            result = json.load(response)
        summary = result["choices"][0]["message"]["content"].strip()
        if summary:
            a["ai_summary"] = summary[:550]
            count += 1
    except Exception as e:
        print("AI summary request failed:", str(e)[:180])
        break
if count:
    PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"AI summaries added: {count}")
