#!/usr/bin/env python3
"""
Générateur automatique d'articles tech style Korben.info
Design system : MétéoAtlas (Outfit + JetBrains Mono, palette or/crème, glassmorphism)
Utilise Gemini API (gratuit) + RSS feeds publics
"""

import os
import json
import time
import hashlib
import datetime
import feedparser
import google.generativeai as genai
from pathlib import Path

# ─── CONFIG ───────────────────────────────────────────────────────────────────

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
ARTICLES_FILE  = "articles.json"
OUTPUT_HTML    = "index.html"
MAX_ARTICLES   = 30
NEW_PER_RUN    = 5
DELAY_BETWEEN  = 4

RSS_FEEDS = [
    "https://feeds.arstechnica.com/arstechnica/index",
    "https://www.theverge.com/rss/index.xml",
    "https://feeds.wired.com/wired/index",
    "https://hnrss.org/frontpage?points=100",
    "https://rss.slashdot.org/Slashdot/slashdotMain",
    "https://feeds.feedburner.com/TechCrunch",
    "https://www.tomshardware.com/feeds/all",
    "https://www.bleepingcomputer.com/feed/",
    "https://krebsonsecurity.com/feed/",
]

KEYWORDS_WHITELIST = [
    "ai", "hack", "exploit", "linux", "open source", "github", "tool",
    "android", "apple", "google", "microsoft", "chip", "gpu", "cpu",
    "robot", "drone", "space", "nasa", "privacy", "security", "leak",
    "gadget", "hardware", "software", "browser", "data", "cloud",
    "python", "rust", "terminal", "cli", "api", "llm", "model",
    "satellite", "starlink", "quantum", "malware", "ransomware",
    "3d print", "raspberry", "arduino", "diy", "teardown",
]

SYSTEM_PROMPT = """Tu es un blogueur tech français qui écrit dans le style de Korben.info.

STYLE :
- Ton décontracté, direct, parfois cynique ou ironique, toujours passionné
- Tu tutoies le lecteur naturellement
- Humour subtil mais présent, références geek bienvenues
- Phrases courtes et percutantes, pas de jargon corporate
- Tu expliques les choses clairement sans condescendance
- Tu donnes ton avis personnel sans te censurer
- Parfois un peu provocateur mais toujours intelligent
- Tu utilises des expressions françaises familières ("franchement", "clairement", "au final", "bref")
- Tu peux faire des parenthèses humoristiques

STRUCTURE de chaque article :
1. Titre accrocheur en français (max 80 caractères), sans ponctuation finale
2. Un chapeau d'intro qui accroche (1-2 phrases, donne envie de lire)
3. Corps de l'article en 3-5 paragraphes : explication, contexte, impact
4. Une conclusion ou réflexion personnelle courte

FORMAT de réponse — JSON strict, rien d'autre :
{
  "titre": "...",
  "intro": "...",
  "corps": "...",
  "categorie": "IA|Sécurité|Hardware|Logiciel|Internet|Espace|Gadgets|Linux"
}

Le corps peut contenir du HTML basique : <strong>, <em>, <br>, <a href="...">.
"""

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def article_id(url):
    return hashlib.md5(url.encode()).hexdigest()[:12]

def fetch_rss_items():
    items = []
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:15]:
                title   = entry.get("title", "")
                summary = entry.get("summary", "")
                link    = entry.get("link", "")
                text    = (title + " " + summary).lower()
                if any(kw in text for kw in KEYWORDS_WHITELIST):
                    items.append({
                        "id":      article_id(link),
                        "title":   title,
                        "summary": summary[:500],
                        "link":    link,
                        "source":  feed.feed.get("title", feed_url),
                    })
        except Exception as e:
            print(f"  ⚠ Erreur RSS {feed_url}: {e}")
    print(f"  → {len(items)} articles RSS trouvés")
    return items

def load_articles():
    if Path(ARTICLES_FILE).exists():
        with open(ARTICLES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_articles(articles):
    with open(ARTICLES_FILE, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

def generate_article(item, model):
    user_prompt = f"""Voici un article tech en anglais. Réécris-le complètement en français dans ton style habituel.

Source : {item['source']}
Titre original : {item['title']}
Résumé : {item['summary']}
URL source : {item['link']}

Génère un article original, pas une traduction mot à mot. Ajoute ton grain de sel."""

    try:
        response = model.generate_content(
            user_prompt,
            generation_config={"temperature": 0.85, "max_output_tokens": 800}
        )
        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw.strip())
        return {
            "id":          item["id"],
            "titre":       data["titre"],
            "intro":       data["intro"],
            "corps":       data["corps"],
            "categorie":   data.get("categorie", "Tech"),
            "source_url":  item["link"],
            "source_name": item["source"],
            "date":        datetime.datetime.utcnow().isoformat(),
        }
    except Exception as e:
        print(f"    ✗ Erreur Gemini pour '{item['title'][:50]}': {e}")
        return None

# ─── DESIGN SYSTEM : palette MétéoAtlas ──────────────────────────────────────

# Couleurs par catégorie (dans la palette or/sauge/alert du site)
CATEGORY_META = {
    "IA":       {"color": "#c9a96a", "icon": "◈"},   # gold
    "Sécurité": {"color": "#c46060", "icon": "◉"},   # alert rouge
    "Hardware": {"color": "#d4a45a", "icon": "◧"},   # warn ocre
    "Logiciel": {"color": "#7a9e80", "icon": "◫"},   # sage vert
    "Internet": {"color": "#9b7d4a", "icon": "◎"},   # gold-dim
    "Espace":   {"color": "#a0b8d0", "icon": "◉"},   # bleu pâle
    "Gadgets":  {"color": "#c9a96a", "icon": "◈"},   # gold
    "Linux":    {"color": "#7bbf84", "icon": "◧"},   # ok vert
    "Tech":     {"color": "#9b7d4a", "icon": "◎"},   # gold-dim
}

def format_date(iso):
    try:
        dt = datetime.datetime.fromisoformat(iso)
        months = ["jan","fév","mar","avr","mai","jun","jul","aoû","sep","oct","nov","déc"]
        return f"{dt.day} {months[dt.month-1]} {dt.year}"
    except:
        return iso[:10]

def build_article_card(a, idx):
    meta    = CATEGORY_META.get(a["categorie"], CATEGORY_META["Tech"])
    color   = meta["color"]
    icon    = meta["icon"]
    date_s  = format_date(a["date"])
    is_hero = (idx == 0)
    cls     = "article-hero" if is_hero else "article-card"
    return f'''
    <article class="{cls}" data-cat="{a["categorie"]}">
      <div class="card-shimmer"></div>
      <div class="card-topline"></div>
      <header class="card-header">
        <span class="cat-badge" style="--cat:{color}">
          <span class="cat-icon">{icon}</span>{a["categorie"]}
        </span>
        <time class="card-date">{date_s}</time>
      </header>
      <h2 class="card-title{"--hero" if is_hero else ""}">{a["titre"]}</h2>
      <p class="card-intro">{a["intro"]}</p>
      <div class="card-body" id="body-{a["id"]}">{a["corps"]}</div>
      <footer class="card-foot">
        <a href="{a["source_url"]}" target="_blank" rel="noopener" class="source-link">
          ↗ {a["source_name"]}
        </a>
        <button class="read-btn" onclick="toggleBody('{a["id"]}')" id="btn-{a["id"]}">
          Lire la suite ↓
        </button>
      </footer>
    </article>'''

def generate_html(articles):
    cards   = "\n".join(build_article_card(a, i) for i, a in enumerate(articles[:MAX_ARTICLES]))
    now     = datetime.datetime.utcnow().strftime("%d/%m/%Y — %H:%Mz")
    cats    = sorted(set(a["categorie"] for a in articles))
    cat_btns = "\n".join(
        f'    <button class="filter-chip" onclick="filterCat(this,\'{c}\')">{c}</button>'
        for c in cats
    )

    return f'''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ByteStream — L'actu tech sans filtre</title>
<meta name="description" content="Tech, hacks, gadgets et mauvaise foi — l'actualité technologique en français, sans bullshit corporate.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
/* ════════════════════════════════════════════════
   PALETTE — MétéoAtlas (tons chauds, or, crème)
════════════════════════════════════════════════ */
:root {{
  --bg:           #0e0c0a;
  --bg2:          #161310;
  --bg3:          #1e1a16;
  --card:         rgba(20,16,11,0.75);
  --card-b:       rgba(210,180,120,0.1);
  --gold:         #c9a96a;
  --gold-dim:     #9b7d4a;
  --gold-glow:    rgba(201,169,106,0.18);
  --sage:         #7a9e80;
  --cream:        #e4d5bb;
  --cream-dim:    rgba(228,213,187,0.55);
  --cream-muted:  rgba(228,213,187,0.28);
  --alert:        #c46060;
  --sans:         'Outfit', sans-serif;
  --mono:         'JetBrains Mono', monospace;
  --r:            18px;
  --r-sm:         10px;
  --fs-xxs:       clamp(10px, 1.15vw, 11px);
  --fs-xs:        clamp(11px, 1.30vw, 12px);
  --fs-sm:        clamp(11.5px, 1.50vw, 13px);
  --fs-base:      clamp(12.5px, 1.70vw, 14px);
}}

*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
html {{ scroll-behavior: smooth; }}
body {{
  font-family: var(--sans);
  background: var(--bg);
  color: var(--cream);
  min-height: 100vh;
  overflow-x: hidden;
}}

/* ════ LUMIÈRES D'AMBIANCE ════ */
.bg-glow {{
  position: fixed; inset: 0; z-index: 0; pointer-events: none;
  background:
    radial-gradient(ellipse 70% 50% at 18% 10%, rgba(180,130,60,0.09) 0%, transparent 65%),
    radial-gradient(ellipse 55% 40% at 82% 85%, rgba(90,130,100,0.07) 0%, transparent 65%),
    radial-gradient(ellipse 45% 55% at 55% 42%, rgba(150,105,45,0.04) 0%, transparent 70%);
  animation: glowDrift 28s ease-in-out infinite alternate;
}}
@keyframes glowDrift {{
  0%   {{ transform: scale(1); }}
  50%  {{ transform: scale(1.06) translateY(-10px); }}
  100% {{ transform: scale(1.03) translateY(5px); }}
}}

/* ════ GRAIN TEXTURE ════ */
.grain {{
  position: fixed; inset: 0; z-index: 1; pointer-events: none; opacity: 0.025;
  background-image: url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><filter id='g'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/><feColorMatrix type='saturate' values='0'/></filter><rect width='200' height='200' filter='url(%23g)'/></svg>");
  background-size: 180px 180px;
}}

/* ════ LAYOUT ════ */
#app {{ position: relative; z-index: 2; max-width: 1100px; margin: 0 auto; padding: 0 24px 80px; }}

/* ════ HEADER ════ */
header {{
  position: sticky; top: 0; z-index: 100;
  margin: 0 -24px; padding: 13px 24px;
  display: flex; align-items: center; gap: 18px;
  background: rgba(14,12,10,0.88);
  backdrop-filter: blur(28px) saturate(160%);
  -webkit-backdrop-filter: blur(28px) saturate(160%);
  border-bottom: 1px solid rgba(201,169,106,0.1);
}}
.logo {{
  font-size: 19px; font-weight: 700; letter-spacing: -0.03em;
  white-space: nowrap; color: var(--cream); text-decoration: none;
}}
.logo em {{ font-style: normal; color: var(--gold); }}
.logo sup {{
  font-size: var(--fs-xs); color: var(--cream-muted); font-weight: 400;
  letter-spacing: 0.08em; font-family: var(--mono);
}}
.header-right {{ margin-left: auto; display: flex; align-items: center; gap: 14px; }}
.updated-time {{
  font-family: var(--mono); font-size: var(--fs-sm);
  color: var(--cream-muted); white-space: nowrap;
}}
.live-dot {{
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--gold); display: inline-block;
  animation: livePulse 2s ease-in-out infinite;
  margin-right: 6px; vertical-align: middle;
}}
@keyframes livePulse {{
  0%,100% {{ opacity: 1; transform: scale(1); }}
  50%      {{ opacity: 0.35; transform: scale(0.7); }}
}}

/* ════ HERO TEXTE ════ */
.site-hero {{
  margin-top: 36px; margin-bottom: 32px;
}}
.site-hero h1 {{
  font-size: clamp(28px, 5vw, 46px); font-weight: 800;
  line-height: 1.12; letter-spacing: -0.03em; margin-bottom: 12px;
  background: linear-gradient(175deg, var(--cream) 30%, var(--gold) 100%);
  -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
}}
.site-hero p {{
  font-size: var(--fs-base); color: var(--cream-dim);
  font-family: var(--mono); max-width: 560px; line-height: 1.7;
}}

/* ════ SECTION TITLE ════ */
.section-title {{
  font-size: var(--fs-xs); font-weight: 700; font-family: var(--mono);
  color: var(--gold-dim); letter-spacing: 0.16em; text-transform: uppercase;
  margin-bottom: 18px; display: flex; align-items: center; gap: 10px;
}}
.section-title::after {{
  content: ''; flex: 1; height: 1px;
  background: linear-gradient(90deg, rgba(201,169,106,0.2), transparent);
}}

/* ════ FILTRES ════ */
.filters-bar {{
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
  margin-bottom: 28px;
}}
.filters-label {{
  font-family: var(--mono); font-size: var(--fs-xs); color: var(--cream-muted);
  letter-spacing: 0.12em; text-transform: uppercase; margin-right: 4px;
}}
.filter-chip {{
  padding: 6px 14px; border-radius: 50px;
  font-size: var(--fs-sm); font-family: var(--mono);
  background: rgba(255,248,220,0.04); border: 1px solid rgba(255,248,220,0.09);
  color: var(--cream-dim); cursor: pointer; transition: all 0.2s;
}}
.filter-chip:hover:not(.active) {{
  background: rgba(201,169,106,0.06); color: var(--cream);
}}
.filter-chip.active {{
  background: rgba(201,169,106,0.14); border-color: rgba(201,169,106,0.4);
  color: var(--gold);
}}
#reset-chip {{
  margin-left: auto; background: none; border: none;
  font-family: var(--mono); font-size: var(--fs-xs);
  color: var(--cream-muted); cursor: pointer; text-decoration: underline;
  transition: color 0.2s;
}}
#reset-chip:hover {{ color: var(--gold); }}

/* ════ GRID ════ */
.articles-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 14px;
}}

/* ════ CARD DE BASE (glassmorphism MétéoAtlas) ════ */
.article-card, .article-hero {{
  background: var(--card);
  border: 1px solid var(--card-b);
  border-radius: var(--r);
  padding: 24px;
  backdrop-filter: blur(22px) saturate(140%);
  -webkit-backdrop-filter: blur(22px) saturate(140%);
  position: relative; overflow: hidden;
  transition: background 0.25s, border-color 0.25s, transform 0.25s, box-shadow 0.25s;
}}
.article-card:hover, .article-hero:hover {{
  background: rgba(26,20,14,0.82);
  border-color: rgba(201,169,106,0.22);
  transform: translateY(-2px);
  box-shadow: 0 12px 40px rgba(0,0,0,0.4);
}}

/* Ligne dorée en haut (effet MétéoAtlas ::before) */
.card-topline {{
  position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent 5%, rgba(255,248,220,0.12) 40%, rgba(255,248,220,0.05) 70%, transparent 95%);
  pointer-events: none;
}}
/* Reflet lumineux subtil (shimmer) */
.card-shimmer {{
  position: absolute; top: -80px; right: -60px;
  width: 220px; height: 220px; border-radius: 50%;
  background: radial-gradient(circle, rgba(201,169,106,0.05) 0%, transparent 70%);
  pointer-events: none;
}}

/* Article hero — pleine largeur, mis en avant */
.article-hero {{
  grid-column: 1 / -1;
  border-color: rgba(201,169,106,0.18);
  background: rgba(22,16,8,0.82);
}}
.article-hero::after {{
  content: ''; position: absolute;
  top: -120px; right: -80px; width: 400px; height: 400px; border-radius: 50%;
  background: radial-gradient(circle, rgba(201,169,106,0.08) 0%, transparent 70%);
  pointer-events: none;
}}

/* ════ CARD HEADER ════ */
.card-header {{
  display: flex; align-items: center; gap: 12px; margin-bottom: 14px;
}}
.cat-badge {{
  display: inline-flex; align-items: center; gap: 5px;
  padding: 3px 10px 3px 8px; border-radius: 6px;
  font-family: var(--mono); font-size: var(--fs-xxs);
  font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase;
  background: rgba(from var(--cat) r g b / 0.12);
  color: var(--cat);
  border: 1px solid rgba(from var(--cat) r g b / 0.22);
}}
.cat-icon {{ font-size: 10px; }}
.card-date {{
  font-family: var(--mono); font-size: var(--fs-xs);
  color: var(--cream-muted); margin-left: auto;
}}

/* ════ TITRES ════ */
.card-title {{
  font-size: 16px; font-weight: 700; line-height: 1.35;
  color: var(--cream); margin-bottom: 10px; letter-spacing: -0.01em;
}}
.card-title--hero {{
  font-size: clamp(20px, 3vw, 28px); letter-spacing: -0.02em;
  margin-bottom: 14px;
}}

/* ════ INTRO ════ */
.card-intro {{
  font-size: var(--fs-base); color: var(--cream-dim);
  line-height: 1.65; margin-bottom: 14px;
}}

/* ════ CORPS ════ */
.card-body {{
  display: none; font-size: var(--fs-sm); line-height: 1.8;
  color: var(--cream-dim); margin-bottom: 14px;
  padding-top: 14px;
  border-top: 1px solid rgba(201,169,106,0.1);
}}
.card-body.open {{ display: block; }}
.card-body strong {{ color: var(--cream); font-weight: 600; }}
.card-body em {{ color: var(--gold-dim); font-style: italic; }}
.card-body a {{ color: var(--gold); text-decoration: none; }}
.card-body a:hover {{ text-decoration: underline; }}

/* ════ FOOTER ════ */
.card-foot {{
  display: flex; align-items: center; justify-content: space-between;
  padding-top: 14px; border-top: 1px solid rgba(255,248,220,0.06);
  margin-top: 4px;
}}
.source-link {{
  font-family: var(--mono); font-size: var(--fs-xs);
  color: var(--cream-muted); text-decoration: none; transition: color 0.2s;
}}
.source-link:hover {{ color: var(--gold); }}
.read-btn {{
  padding: 6px 14px; border-radius: 50px;
  font-size: var(--fs-sm); font-family: var(--mono);
  background: rgba(255,248,220,0.04); border: 1px solid rgba(255,248,220,0.09);
  color: var(--cream-dim); cursor: pointer; transition: all 0.2s;
}}
.read-btn:hover {{
  background: rgba(201,169,106,0.1); border-color: rgba(201,169,106,0.35);
  color: var(--gold);
}}

/* ════ SCROLLBAR GLOBALE ════ */
::-webkit-scrollbar {{ width: 6px; height: 4px; }}
::-webkit-scrollbar-track {{ background: rgba(255,255,255,0.02); border-radius: 4px; }}
::-webkit-scrollbar-thumb {{ background: rgba(201,169,106,0.25); border-radius: 4px; }}

/* ════ FOOTER SITE ════ */
.site-footer {{
  text-align: center; padding: 48px 1rem 32px;
  border-top: 1px solid rgba(201,169,106,0.1);
  margin-top: 48px;
}}
.site-footer p {{
  font-family: var(--mono); font-size: var(--fs-xs);
  color: var(--cream-muted); line-height: 2;
}}
.site-footer a {{ color: var(--gold-dim); text-decoration: none; }}
.site-footer a:hover {{ color: var(--gold); }}

/* ════ BOUTON HAUT ════ */
#topBtn {{
  position: fixed; bottom: 26px; right: 26px; z-index: 500;
  width: 44px; height: 44px; border-radius: 50%;
  border: 1px solid rgba(201,169,106,0.3);
  background: rgba(14,12,10,0.92);
  backdrop-filter: blur(14px); color: var(--gold);
  font-size: 18px; cursor: pointer; display: none;
  align-items: center; justify-content: center;
  box-shadow: 0 4px 22px rgba(0,0,0,0.45);
  transition: all 0.22s; line-height: 1;
}}
#topBtn:hover {{ background: rgba(201,169,106,0.18); }}

/* ════ HIDDEN ════ */
.hidden {{ display: none !important; }}

/* ════ RESPONSIVE ════ */
@media (max-width: 600px) {{
  #app {{ padding: 0 14px 60px; }}
  header {{ margin: 0 -14px; padding: 12px 14px; }}
  .articles-grid {{ grid-template-columns: 1fr; gap: 10px; }}
  .article-hero {{ padding: 20px; }}
}}
</style>
</head>
<body>

<div class="bg-glow"></div>
<div class="grain"></div>

<div id="app">

  <header>
    <a href="/" class="logo">Byte<em>Stream</em><sup>// tech</sup></a>
    <div class="header-right">
      <span class="updated-time">
        <span class="live-dot"></span>{now}
      </span>
    </div>
  </header>

  <section class="site-hero">
    <h1>L'actu tech,<br>sans bullshit.</h1>
    <p>Hacks, gadgets, IA, sécu — les meilleures sources mondiales réécrites en français avec un grain de sel bien dosé.</p>
  </section>

  <div class="section-title">Articles récents</div>

  <div class="filters-bar">
    <span class="filters-label">Filtrer</span>
    <button class="filter-chip active" onclick="filterCat(this,'all')">Tout</button>
{cat_btns}
    <button id="reset-chip" onclick="resetFilter()">réinitialiser</button>
  </div>

  <main class="articles-grid" id="grid">
{cards}
  </main>

</div><!-- #app -->

<footer class="site-footer">
  <p>
    ByteStream — articles générés par IA Gemini · sources originales linkées · aucune pub<br>
    <a href="https://github.com" target="_blank">Code source sur GitHub</a>
  </p>
</footer>

<button id="topBtn" onclick="window.scrollTo({{top:0,behavior:'smooth'}})" title="Remonter" aria-label="Remonter">↑</button>

<script>
// ── Expand/Collapse ──────────────────────────────────────────
function toggleBody(id) {{
  const body = document.getElementById('body-' + id);
  const btn  = document.getElementById('btn-'  + id);
  const open = body.classList.toggle('open');
  btn.textContent = open ? 'Réduire ↑' : 'Lire la suite ↓';
}}

// Ouvrir l'article hero par défaut
document.addEventListener('DOMContentLoaded', () => {{
  const hero = document.querySelector('.article-hero');
  if (hero) {{
    const id = hero.querySelector('.card-body')?.id?.replace('body-','');
    if (id) toggleBody(id);
  }}
}});

// ── Filtres par catégorie ────────────────────────────────────
let currentCat = 'all';

function filterCat(btn, cat) {{
  currentCat = cat;
  document.querySelectorAll('.filter-chip').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('#grid article').forEach(card => {{
    if (cat === 'all' || card.dataset.cat === cat)
      card.classList.remove('hidden');
    else
      card.classList.add('hidden');
  }});
}}

function resetFilter() {{
  currentCat = 'all';
  document.querySelectorAll('.filter-chip').forEach(b => b.classList.remove('active'));
  document.querySelector('.filter-chip').classList.add('active');
  document.querySelectorAll('#grid article').forEach(c => c.classList.remove('hidden'));
}}

// ── Bouton retour en haut ────────────────────────────────────
(function() {{
  const btn = document.getElementById('topBtn');
  window.addEventListener('scroll', () => {{
    btn.style.display = window.scrollY > 320 ? 'flex' : 'none';
  }}, {{passive: true}});
  btn.addEventListener('mouseenter', () => btn.style.background = 'rgba(201,169,106,0.18)');
  btn.addEventListener('mouseleave', () => btn.style.background = 'rgba(14,12,10,0.92)');
}})();
</script>
</body>
</html>'''

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    print("🤖 ByteStream Generator démarré")
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
        "gemini-2.0-flash",
        system_instruction=SYSTEM_PROMPT
    )

    existing     = load_articles()
    existing_ids = {a["id"] for a in existing}
    print(f"  → {len(existing)} articles existants")

    rss_items = fetch_rss_items()
    new_items = [i for i in rss_items if i["id"] not in existing_ids]
    print(f"  → {len(new_items)} nouveaux items RSS")

    if new_items:
        generated = []
        for item in new_items[:NEW_PER_RUN]:
            print(f"  ✍ Génération : {item['title'][:60]}...")
            art = generate_article(item, model)
            if art:
                generated.append(art)
                print(f"    ✓ \"{art['titre'][:55]}\" [{art['categorie']}]")
            time.sleep(DELAY_BETWEEN)

        existing = generated + existing
        existing = existing[:MAX_ARTICLES]
        save_articles(existing)
        print(f"  → {len(generated)} articles générés, {len(existing)} au total")
    else:
        print("  → Rien de nouveau, régénération du HTML uniquement")

    html = generate_html(existing)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ {OUTPUT_HTML} généré ({len(html)//1024} Ko)")

if __name__ == "__main__":
    main()
