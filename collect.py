
import json
import urllib.request
import xml.etree.ElementTree as ET
import datetime
import email.utils
import html
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlparse, quote, urljoin

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
        "WAGO PFC200 firmware e!COCKPIT CODESYS nouveauté",
        "Schneider Modicon M241 M340 EcoStruxure Machine Expert mise à jour",
        "Sofrel S550 télégestion eau potable nouveautés",
        "PCVue 16 supervision SCADA mise à jour",
        "Codra Panorama Suite Ozone supervision version",
        "Phoenix Contact PLCnext automate industriel nouveautés",
        "SOFREL tele gestion nouveau produit",
        "Schneider Electric Modicon nouvel automate",
        "Siemens SIMATIC nouvel automate",
        "PCVue supervision SCADA nouvelle version",
        "Codra Panorama supervision nouveaute",
        "TOPKAPI supervision SCADA nouvelle version",
        "robotique industrielle cobot nouveau modèle",
        "capteur industriel débitmètre instrumentation nouveau",
        "OPC UA MQTT réseau industriel nouveauté",
        "maintenance prédictive intelligence artificielle industrie",
        "jumeau numérique usine industrie 4.0",
        "SCADA supervision industrielle logiciel nouvelle version",
    ],
    "Domotique": [
        "Matter domotique nouveau produit",
        "Home Assistant nouveautés intégrations",
        "Zigbee Thread maison connectée nouveauté",
    ],
    "IA": [
        "nouvel agent intelligence artificielle outils",
        "intelligence artificielle automatisation industrielle",
    ],
    "Innovation": [
        "nouvelle invention technologie prototype recherche",
        "innovation électronique microcontrôleur processeur",
    ],
    "Cybersécurité": [
        "cybersécurité industrielle OT automate vulnérabilité",
    ],
    "Électricité": [
        "Legrand nouveau disjoncteur appareillage",
        "Schneider Electric nouvelle gamme protection electrique",
        "WAGO nouvelles bornes raccordement alimentation electrique",
        "Phoenix Contact nouveaux blocs alimentation bornes protection",
        "Schneider Electric nouveaux appareillages tableaux electriques",
        "innovation stockage énergie batterie réseau électrique",
        "nouveauté onduleur solaire photovoltaïque",
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
        "phoenix contact", "cobot", "robotique industrielle",
        "maintenance predictive", "maintenance predicitive",
        "jumeau numerique", "opc ua", "mqtt", "iiot",
        "instrumentation industrielle", "debimetre",
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
    return best if scores[best] >= 5 else "Actualités générales"

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

        image = ""
        for node in entry.iter():
            tag = node.tag.lower()
            if tag.endswith("}thumbnail") or tag.endswith("}content") or tag == "enclosure":
                candidate = node.attrib.get("url", "")
                medium = node.attrib.get("medium", "")
                kind = node.attrib.get("type", "")
                if candidate.startswith("http") and (tag.endswith("}thumbnail") or medium == "image" or kind.startswith("image/")):
                    image = candidate
                    break
        results.append({
            "image": image,
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
feed_health = []

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
        feed_health.append({"source": source, "ok": True, "articles": len(found)})

        print("OK", source, len(found))

    except Exception as error:
        feed_health.append({"source": urlparse(url).netloc, "ok": False, "articles": 0})
        print("ERREUR", url, str(error)[:150])

# Si tous les flux echouent, conserver les donnees
# precedentes au lieu de vider le site.
path = Path("articles.json")

if successful == 0:
    print("Aucun flux accessible. Fichier conserve.")
    raise SystemExit(1)

seen = set()
seen_titles = set()
unique = []
def title_fingerprint(value):
    words = re.findall(r"[a-z0-9]{3,}", normalize(value))
    ignored = {"les", "des", "une", "dans", "pour", "avec", "sur", "par", "plus", "son", "ses", "nouveau", "nouvelle", "voici", "comment"}
    return " ".join(sorted(w for w in words if w not in ignored))

# Preserve enriched images across collection runs.
previous_images = {}
previous_summaries = {}
if path.exists():
    try:
        old_articles = json.loads(path.read_text(encoding="utf-8")).get("articles", [])
        previous_images = {a.get("url", "").split("?")[0]: a.get("image") for a in old_articles if a.get("image")}
        previous_summaries = {a.get("url", "").split("?")[0]: a.get("ai_summary") for a in old_articles if a.get("ai_summary")}
    except (OSError, ValueError):
        pass

for article in sorted(
    items,
    key=lambda a: a["date"],
    reverse=True
):
    key = article["url"].split("?")[0]
    fingerprint = title_fingerprint(article["title"])
    if key not in seen and fingerprint not in seen_titles:
        seen.add(key)
        seen_titles.add(fingerprint)
        if not article.get("image") and previous_images.get(key):
            article["image"] = previous_images[key]
        if previous_summaries.get(key):
            article["ai_summary"] = previous_summaries[key]
        unique.append(article)

# Protect the public feed against an abnormally degraded collection.
if path.exists():
    try:
        previous = json.loads(path.read_text(encoding="utf-8"))
        previous_count = len(previous.get("articles", []))
        if previous_count >= 80 and len(unique) < max(25, int(previous_count * 0.25)):
            print("Collecte anormalement faible:", len(unique), "vs", previous_count, "- ancienne version conservée")
            raise SystemExit(1)
    except (OSError, ValueError):
        pass

data = {
    "feed_health": {"checked": len(feed_health), "successful": successful, "failed": len(feed_health) - successful},
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
