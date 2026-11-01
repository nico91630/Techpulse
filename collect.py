
import json
import urllib.request
import xml.etree.ElementTree as ET
import datetime
import email.utils
import html
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlparse, quote

# Flux francophones
FEEDS = [
    "https://www.frandroid.com/feed",
    "https://www.lesnumeriques.com/rss-news.xml",
    "https://www.lesnumeriques.com/intelligence-artificielle/rss.xml",
    "https://www.clubic.com/feed/clubic.rss",
    "https://www.numerama.com/feed/",
    "https://www.01net.com/feed/",
    "https://www.journaldugeek.com/feed/",
    "https://www.usinenouvelle.com/rss/",
    "https://www.maddyness.com/feed/",
    "https://www.neozone.org/feed/",
    "https://www.blogdumoderateur.com/feed/",
    "https://www.frandroid.com/produits-android/console/feed",
    "https://www.01net.com/actualites/produits/smartphones-produits/feed/",
    "https://www.clubic.com/feed/antivirus-securite-informatique/rss",
]

# Veille francophone sur les nouveautes industrielles et logiciels SCADA.
SPECIALIZED_SEARCHES = {
    "Automatisme": [
        "WAGO nouvel automate nouveaute",
        "SOFREL tele gestion nouveau produit",
        "Schneider Electric Modicon nouvel automate",
        "Siemens SIMATIC nouvel automate",
        "PCVue supervision SCADA nouvelle version",
        "Codra Panorama supervision nouveaute",
        "TOPKAPI supervision SCADA nouvelle version",
    ],
    "Électricité": [
        "Legrand nouveau disjoncteur appareillage",
        "Schneider Electric nouvelle gamme protection electrique",
        "WAGO nouvelles bornes raccordement alimentation electrique",
        "Phoenix Contact nouveaux blocs alimentation bornes protection",
        "Schneider Electric nouveaux appareillages tableaux electriques",
    ],
}
SPECIALIZED_FEEDS = {}
for category, searches in SPECIALIZED_SEARCHES.items():
    for search in searches:
        url = ("https://news.google.com/rss/search?q="
               + quote(search + " when:30d")
               + "&hl=fr&gl=FR&ceid=FR:fr")
        FEEDS.append(url)
        SPECIALIZED_FEEDS[url] = category

# Classement automatique par mots-cles
KEYWORDS = {
    "Cybersécurité": [
        "cyberattaque", "ransomware", "piratage",
        "malware", "phishing", "vulnerabilite",
        "securite informatique", "fuite de donnees",
    ],
    "Automatisme": [
        "automate programmable", "automatisme",
        "plc", "scada", "supervision industrielle",
        "industrie 4.0", "robot industriel",
        "schneider electric", "siemens s7",
        "wago", "modbus", "codesys",
        "sofrel", "telegestion", "tele gestion",
        "pcvue", "pc vue", "codra", "topkapi",
        "panorama suite", "modicon", "simatic",
        "phoenix contact",
    ],
    "Électricité": [
        "installation electrique", "tableau electrique",
        "disjoncteur", "reseau electrique",
        "distribution electrique", "transformateur",
        "electricien", "triphasé", "triphas",
        "legrand", "hager", "appareillage electrique",
        "phoenix contact", "bornier electrique",
        "bloc alimentation", "protection surtension",
    ],
    "Énergie": [
        "photovoltaique", "panneau solaire",
        "batterie domestique", "nucleaire",
        "eolienne", "energie renouvelable",
        "stockage energie", "pompe a chaleur",
        "electricite verte",
    ],
    "Domotique": [
        "domotique", "maison connectee",
        "home assistant", "matter", "zigbee",
        "thermostat connecte", "alarme connectee",
        "objet connecte", "smart home",
    ],
    "Gaming": [
        "jeu video", "playstation", "xbox",
        "nintendo", "steam", "gaming",
        "console de jeu",
    ],
    "Smartphones": [
        "smartphone", "iphone", "galaxy",
        "android", "pixel", "xiaomi",
        "telephone mobile", "oneplus",
    ],
    "Mobilité": [
        "voiture electrique", "vehicule electrique",
        "tesla", "renault 5", "borne de recharge",
        "mobilite electrique", "velo electrique",
        "trottinette electrique",
    ],
    "IA": [
        "intelligence artificielle", "chatgpt",
        "openai", "gemini", "claude",
        "generative", "llm", "deepseek",
        "mistral ai", "copilot",
    ],
    "Électronique": [
        "microcontroleur", "raspberry pi",
        "arduino", "circuit imprime",
        "semi-conducteur", "composant electronique",
        "capteur electronique",
    ],
    "Informatique": [
        "ordinateur", "processeur", "windows",
        "linux", "macbook", "intel",
        "amd", "stockage ssd", "pc portable",
        "carte graphique",
    ],
    "Innovation": [
        "innovation", "invention", "prototype",
        "nouvelle technologie", "recherche scientifique",
        "decouverte", "startup",
    ],
}

def normalize(s):
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(
        c for c in s if not unicodedata.combining(c)
    )

def clean(s, limit=320):
    s = html.unescape(s or "")
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip()[:limit]

def get_text(element, names):
    for name in names:
        node = element.find(name)
        if node is not None and node.text:
            return node.text.strip()
    return ""

def category_for(title, description):
    # Donner la priorite aux mots-cles presents dans le titre.
    # Les correspondances doivent etre des mots entiers.
    title_norm = normalize(title)
    description_norm = normalize(description)
    scores = {}
    for category, words in KEYWORDS.items():
        score = 0
        for word in words:
            pattern = r"(?<!\w)" + re.escape(normalize(word)) + r"(?!\w)"
            if re.search(pattern, title_norm):
                score += 5
            elif re.search(pattern, description_norm):
                score += 1
        scores[category] = score
    best = max(scores, key=scores.get)
    return best if scores[best] >= 5 else "Innovation"

def parse_date(value):
    try:
        dt = email.utils.parsedate_to_datetime(value)
        return dt.astimezone(
            datetime.timezone.utc
        ).isoformat()
    except Exception:
        pass

    try:
        dt = datetime.datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.astimezone(
            datetime.timezone.utc
        ).isoformat()
    except Exception:
        return datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat()

def parse_feed(raw, source, forced_category=None):
    root = ET.fromstring(raw)
    entries = (
        root.findall(".//item")
        + root.findall(
            ".//{http://www.w3.org/2005/Atom}entry"
        )
    )

    results = []

    for entry in entries:
        title = clean(get_text(entry, [
            "title",
            "{http://www.w3.org/2005/Atom}title"
        ]), 220)

        description = clean(get_text(entry, [
            "description",
            "{http://www.w3.org/2005/Atom}summary",
            "{http://www.w3.org/2005/Atom}content"
        ]))

        link = get_text(entry, ["link"])

        if not link:
            for node in entry.findall(
                "{http://www.w3.org/2005/Atom}link"
            ):
                if node.attrib.get("rel", "alternate") == "alternate":
                    link = node.attrib.get("href", "")
                    break

        if not title or not link.startswith("http"):
            continue

        date = parse_date(get_text(entry, [
            "pubDate",
            "{http://www.w3.org/2005/Atom}published",
            "{http://www.w3.org/2005/Atom}updated"
        ]))

        results.append({
            "title": title,
            "url": link,
            "category": forced_category or category_for(title, description),
            "source": source,
            "date": date,
            "description": description
        })

    return results

items = []
successful = 0

for url in FEEDS:
    try:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 TechpulsePersonal/1.0",
                "Accept": "application/rss+xml, application/xml, text/xml, */*"
            }
        )

        with urllib.request.urlopen(
            request, timeout=15
        ) as response:
            raw = response.read(2_000_000)

        source = urlparse(url).netloc.replace("www.", "")
        found = parse_feed(raw, source, SPECIALIZED_FEEDS.get(url))
        items.extend(found[:40])
        successful += 1

        print("OK", source, len(found))

    except Exception as error:
        print("ERREUR", url, str(error)[:150])

# Si tous les flux echouent, conserver les donnees
# precedentes au lieu de vider le site.
path = Path("articles.json")

if successful == 0:
    print("Aucun flux accessible. Fichier conserve.")
    raise SystemExit(1)

seen = set()
unique = []

for article in sorted(
    items,
    key=lambda a: a["date"],
    reverse=True
):
    key = article["url"].split("?")[0]
    if key not in seen:
        seen.add(key)
        unique.append(article)

data = {
    "updated_at": datetime.datetime.now(
        datetime.timezone.utc
    ).isoformat(),
    "successful_feeds": successful,
    "articles": unique[:450]
}

path.write_text(
    json.dumps(data, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("Articles:", len(data["articles"]))
print("Flux fonctionnels:", successful)
