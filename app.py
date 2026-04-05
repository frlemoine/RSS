from __future__ import annotations

import argparse
import datetime as dt
import html
import io
import json
import re
import tarfile
import textwrap
from urllib.parse import urljoin
import urllib.request
import xml.etree.ElementTree as ET
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
DOCS_DIR = ROOT_DIR / "docs"
DECISIONS_DIR = DOCS_DIR / "decisions"
ASSETS_DIR = DOCS_DIR / "assets"
STATE_PATH = DATA_DIR / "state.json"

INDEX_URL = "https://echanges.dila.gouv.fr/OPENDATA/JADE/"
ARCHIVE_NAME_RE = re.compile(r"JADE_(\d{8}-\d{6})\.tar\.gz")
ARCHIVE_TIMESTAMP_FORMAT = "%Y%m%d-%H%M%S"
BOOTSTRAP_ARCHIVE_COUNT = 5
FEED_ITEM_LIMIT = 150
REQUEST_TIMEOUT_SECONDS = 120
USER_AGENT = "jade-rss-builder/1.0"

SITE_CSS = """
:root {
  --bg: #f5efe3;
  --bg-deep: #ece1cd;
  --surface: rgba(255, 249, 240, 0.88);
  --surface-strong: #fffaf2;
  --text: #17263f;
  --muted: #5f6d7f;
  --accent: #8b3f2d;
  --accent-soft: #c76d4f;
  --line: rgba(23, 38, 63, 0.12);
  --shadow: 0 22px 60px rgba(23, 38, 63, 0.12);
  --radius: 24px;
}

* {
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
}

body {
  margin: 0;
  min-height: 100vh;
  color: var(--text);
  font-family: "Aptos", "Trebuchet MS", sans-serif;
  background:
    radial-gradient(circle at top left, rgba(255, 252, 245, 0.95), transparent 34%),
    linear-gradient(135deg, var(--bg) 0%, var(--bg-deep) 100%);
}

body::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(90deg, transparent 0, transparent 48px, rgba(255, 255, 255, 0.08) 48px, rgba(255, 255, 255, 0.08) 49px),
    linear-gradient(transparent 0, transparent 48px, rgba(23, 38, 63, 0.02) 48px, rgba(23, 38, 63, 0.02) 49px);
  background-size: 49px 49px;
  opacity: 0.25;
}

a {
  color: var(--accent);
}

.shell {
  width: min(1120px, calc(100% - 32px));
  margin: 0 auto;
  padding: 40px 0 64px;
}

.hero,
.panel,
.decision-card {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  backdrop-filter: blur(10px);
}

.hero {
  position: relative;
  overflow: hidden;
  padding: 28px;
}

.hero::after {
  content: "";
  position: absolute;
  right: -60px;
  top: -60px;
  width: 220px;
  height: 220px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(199, 109, 79, 0.28) 0%, rgba(199, 109, 79, 0) 70%);
}

.eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(23, 38, 63, 0.06);
  color: var(--muted);
  font-size: 0.88rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

h1,
h2,
h3 {
  font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", Palatino, serif;
  line-height: 1.08;
  margin: 0;
}

h1 {
  font-size: clamp(2.3rem, 4vw, 4rem);
  margin-top: 18px;
  max-width: 12ch;
}

.hero p,
.panel p,
.muted {
  color: var(--muted);
}

.hero-copy {
  max-width: 70ch;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 24px;
}

.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 18px;
  border-radius: 999px;
  text-decoration: none;
  font-weight: 600;
  transition: transform 180ms ease, box-shadow 180ms ease;
}

.button:hover {
  transform: translateY(-1px);
}

.button-primary {
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-soft) 100%);
  color: #fff8f0;
  box-shadow: 0 14px 28px rgba(139, 63, 45, 0.25);
}

.button-secondary {
  background: rgba(255, 255, 255, 0.7);
  color: var(--text);
  border: 1px solid var(--line);
}

.meta-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 14px;
  margin-top: 28px;
}

.meta-card {
  padding: 16px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.54);
  border: 1px solid rgba(23, 38, 63, 0.08);
}

.meta-card span {
  display: block;
  font-size: 0.85rem;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.meta-card strong {
  display: block;
  margin-top: 8px;
  font-size: 1.1rem;
}

.layout {
  display: grid;
  gap: 20px;
  margin-top: 24px;
}

.panel {
  padding: 22px;
}

.feed-list {
  display: grid;
  gap: 18px;
}

.decision-card {
  padding: 22px;
}

.decision-card h3 {
  font-size: 1.55rem;
}

.decision-card p {
  margin: 14px 0 0;
}

.decision-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 14px;
}

.tag {
  display: inline-flex;
  align-items: center;
  padding: 7px 12px;
  border-radius: 999px;
  font-size: 0.92rem;
  background: rgba(23, 38, 63, 0.06);
  border: 1px solid rgba(23, 38, 63, 0.08);
}

.decision-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 18px;
}

.decision-page {
  display: grid;
  gap: 20px;
}

.decision-text {
  padding: 24px;
  border-radius: var(--radius);
  background: var(--surface-strong);
  border: 1px solid var(--line);
  box-shadow: var(--shadow);
  line-height: 1.72;
}

.decision-text br {
  content: "";
  display: block;
  margin-top: 10px;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  color: var(--muted);
  text-decoration: none;
}

.footnote {
  margin-top: 32px;
  color: var(--muted);
  font-size: 0.92rem;
}

@media (max-width: 720px) {
  .shell {
    width: min(100% - 20px, 1120px);
    padding-top: 18px;
  }

  .hero,
  .panel,
  .decision-card,
  .decision-text {
    padding: 18px;
  }

  h1 {
    max-width: none;
  }
}
""".strip()


def _last_sunday(year: int, month: int) -> dt.date:
    if month == 12:
        next_month = dt.date(year + 1, 1, 1)
    else:
        next_month = dt.date(year, month + 1, 1)
    last_day = next_month - dt.timedelta(days=1)
    days_since_sunday = (last_day.weekday() + 1) % 7
    return last_day - dt.timedelta(days=days_since_sunday)


class EuropeParisFallback(dt.tzinfo):
    def _dst_bounds(self, year: int) -> tuple[dt.datetime, dt.datetime]:
        start_day = _last_sunday(year, 3)
        end_day = _last_sunday(year, 10)
        start = dt.datetime(year, 3, start_day.day, 2, 0, 0)
        end = dt.datetime(year, 10, end_day.day, 3, 0, 0)
        return start, end

    def _is_dst(self, value: dt.datetime | None) -> bool:
        if value is None:
            return False
        naive = value.replace(tzinfo=None)
        start, end = self._dst_bounds(naive.year)
        return start <= naive < end

    def utcoffset(self, value: dt.datetime | None) -> dt.timedelta:
        return dt.timedelta(hours=2 if self._is_dst(value) else 1)

    def dst(self, value: dt.datetime | None) -> dt.timedelta:
        return dt.timedelta(hours=1 if self._is_dst(value) else 0)

    def tzname(self, value: dt.datetime | None) -> str:
        return "CEST" if self._is_dst(value) else "CET"

    def fromutc(self, value: dt.datetime) -> dt.datetime:
        if value.tzinfo is not self:
            raise ValueError("fromutc: tzinfo mismatch")
        naive_utc = value.replace(tzinfo=None)
        provisional = (naive_utc + dt.timedelta(hours=1)).replace(tzinfo=self)
        offset = dt.timedelta(hours=2 if self._is_dst(provisional) else 1)
        return (naive_utc + offset).replace(tzinfo=self)


def get_source_timezone() -> dt.tzinfo:
    try:
        return ZoneInfo("Europe/Paris")
    except Exception:
        return EuropeParisFallback()


SOURCE_TIMEZONE = get_source_timezone()


def fetch_bytes(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "*/*",
        },
    )
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        return response.read()


def fetch_text(url: str) -> str:
    return fetch_bytes(url).decode("utf-8", errors="replace")


def archive_timestamp_from_name(name: str) -> dt.datetime:
    match = ARCHIVE_NAME_RE.fullmatch(name)
    if not match:
        raise ValueError(f"Nom d'archive invalide: {name}")
    return dt.datetime.strptime(match.group(1), ARCHIVE_TIMESTAMP_FORMAT).replace(
        tzinfo=SOURCE_TIMEZONE
    )


def parse_archive_listing(index_html: str) -> list[dict[str, str]]:
    seen: set[str] = set()
    archives: list[dict[str, str]] = []
    for match in ARCHIVE_NAME_RE.finditer(index_html):
        archive_name = f"JADE_{match.group(1)}.tar.gz"
        if archive_name in seen:
            continue
        seen.add(archive_name)
        archives.append(
            {
                "name": archive_name,
                "timestamp": archive_timestamp_from_name(archive_name).isoformat(),
                "url": urljoin(INDEX_URL, archive_name),
            }
        )
    archives.sort(key=lambda archive: archive["timestamp"])
    return archives


def inner_xml(element: ET.Element | None) -> str:
    if element is None:
        return ""
    rendered = ET.tostring(element, encoding="unicode", method="html").strip()
    rendered = rendered.removeprefix("<CONTENU>").removesuffix("</CONTENU>")
    return rendered.strip()


def html_fragment_to_text(fragment: str) -> str:
    normalized = re.sub(r"<br\s*/?>", "\n", fragment, flags=re.IGNORECASE)
    normalized = re.sub(r"<[^>]+>", " ", normalized)
    normalized = html.unescape(normalized)
    normalized = re.sub(r"[ \t\r\f\v]+", " ", normalized)
    normalized = re.sub(r"\n\s*", "\n", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def summarize_content(fragment: str, limit: int = 420) -> str:
    text = html_fragment_to_text(fragment)
    if len(text) <= limit:
        return text
    shortened = text[:limit].rsplit(" ", 1)[0].strip()
    return f"{shortened}..."


def parse_decision_xml(xml_bytes: bytes, archive: dict[str, str]) -> dict[str, str]:
    root = ET.fromstring(xml_bytes)
    content_html = inner_xml(root.find(".//CONTENU"))

    decision_id = (root.findtext(".//ID") or "").strip()
    decision_title = (root.findtext(".//TITRE") or decision_id).strip()
    decision_date = (root.findtext(".//DATE_DEC") or "").strip()
    jurisdiction = (root.findtext(".//JURIDICTION") or "").strip()
    number = (root.findtext(".//NUMERO") or "").strip()
    formation = (root.findtext(".//FORMATION") or "").strip()
    publication_code = (root.findtext(".//PUBLI_RECUEIL") or "").strip()
    source_xml_path = (root.findtext(".//URL") or "").strip()
    summary = summarize_content(content_html)

    return {
        "id": decision_id,
        "title": decision_title,
        "decision_date": decision_date,
        "published_at": archive["timestamp"],
        "jurisdiction": jurisdiction,
        "number": number,
        "formation": formation,
        "publication_code": publication_code,
        "archive_name": archive["name"],
        "archive_url": archive["url"],
        "source_xml_path": source_xml_path,
        "summary": summary,
        "content_html": content_html,
        "page_path": f"decisions/{decision_id}.html",
    }


def parse_archive(archive_bytes: bytes, archive: dict[str, str]) -> list[dict[str, str]]:
    decisions: list[dict[str, str]] = []
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as tar:
        for member in tar:
            if not member.isfile() or not member.name.endswith(".xml"):
                continue
            extracted = tar.extractfile(member)
            if extracted is None:
                continue
            try:
                decision = parse_decision_xml(extracted.read(), archive)
            except ET.ParseError:
                print(f"XML ignoré car invalide : {member.name}")
                continue
            if decision["id"]:
                decisions.append(decision)
    return decisions


def load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {"processed_archives": [], "items": []}
    with STATE_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_state(state: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with STATE_PATH.open("w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def pick_archives_to_process(
    archives: list[dict[str, str]], processed_archives: list[str]
) -> list[dict[str, str]]:
    if not processed_archives:
        return archives[-BOOTSTRAP_ARCHIVE_COUNT:]
    processed = set(processed_archives)
    return [archive for archive in archives if archive["name"] not in processed]


def decision_sort_key(item: dict[str, str]) -> tuple[str, str]:
    return (item["published_at"], item["id"])


def format_rss_date(value: str) -> str:
    return dt.datetime.fromisoformat(value).strftime("%a, %d %b %Y %H:%M:%S %z")


def display_date(value: str) -> str:
    if not value:
        return "Date non précisée"
    try:
        return dt.date.fromisoformat(value).strftime("%d/%m/%Y")
    except ValueError:
        return value


def display_datetime(value: str) -> str:
    return dt.datetime.fromisoformat(value).astimezone(SOURCE_TIMEZONE).strftime(
        "%d/%m/%Y à %H:%M"
    )


def render_layout(title: str, body: str, css_path: str, rss_url: str) -> str:
    return f"""<!doctype html>
<html lang="fr">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{html.escape(title)}</title>
    <meta name="description" content="Flux RSS quotidien des nouvelles décisions publiées dans le fonds JADE.">
    <link rel="alternate" type="application/rss+xml" title="Flux RSS JADE" href="{html.escape(rss_url)}">
    <link rel="stylesheet" href="{html.escape(css_path)}">
  </head>
  <body>
    {body}
  </body>
</html>
"""


def render_index_page(items: list[dict[str, str]], site_url: str) -> str:
    rss_url = f"{site_url.rstrip('/')}/rss.xml"
    latest_publication = display_datetime(items[0]["published_at"]) if items else "Aucune"
    cards = []
    for item in items:
        subtitle_parts = []
        if item["jurisdiction"]:
            subtitle_parts.append(item["jurisdiction"])
        if item["formation"]:
            subtitle_parts.append(item["formation"])
        subtitle = " • ".join(subtitle_parts) or "Juridiction non précisée"
        number_label = item["number"] or "Numéro non précisé"
        cards.append(
            f"""
        <article class="decision-card">
          <h3>{html.escape(item["title"])}</h3>
          <p class="muted">{html.escape(subtitle)}</p>
          <div class="decision-meta">
            <span class="tag">Décision du {html.escape(display_date(item["decision_date"]))}</span>
            <span class="tag">Publication du {html.escape(display_datetime(item["published_at"]))}</span>
            <span class="tag">N° {html.escape(number_label)}</span>
          </div>
          <p>{html.escape(item["summary"])}</p>
          <div class="decision-actions">
            <a class="button button-primary" href="{html.escape(item["page_path"])}">Lire la décision</a>
            <a class="button button-secondary" href="{html.escape(item["archive_url"])}">Télécharger l'archive source</a>
          </div>
        </article>
"""
        )
    cards_markup = "".join(cards) if cards else "<p>Aucune décision n'a encore été importée.</p>"

    body = f"""
    <main class="shell">
      <section class="hero">
        <span class="eyebrow">JADE • Veille quotidienne</span>
        <h1>Nouvelles décisions du fonds JADE en RSS</h1>
        <p class="hero-copy">
          Cette application surveille les archives quotidiennes publiées par la DILA, extrait les nouvelles décisions du fonds JADE
          et génère un flux RSS directement exploitable dans un lecteur de flux ou une automatisation.
        </p>
        <div class="hero-actions">
          <a class="button button-primary" href="rss.xml">Ouvrir le flux RSS</a>
          <a class="button button-secondary" href="{html.escape(INDEX_URL)}">Voir la source JADE</a>
        </div>
        <div class="meta-grid">
          <div class="meta-card">
            <span>Dernière publication intégrée</span>
            <strong>{html.escape(latest_publication)}</strong>
          </div>
          <div class="meta-card">
            <span>Décisions conservées</span>
            <strong>{len(items)}</strong>
          </div>
          <div class="meta-card">
            <span>Format</span>
            <strong>RSS 2.0 + pages HTML</strong>
          </div>
        </div>
      </section>

      <section class="layout">
        <div class="panel">
          <h2>Décisions récentes</h2>
          <p>Le flux expose les dernières décisions publiées. Chaque entrée pointe vers une page statique avec le texte intégral conservé dans ce site.</p>
          <div class="feed-list">
            {cards_markup}
          </div>
        </div>
      </section>

      <p class="footnote">
        Source des données : fonds JADE sur <a href="{html.escape(INDEX_URL)}">echanges.dila.gouv.fr</a>.
        Le site peut être hébergé gratuitement sur GitHub Pages.
      </p>
    </main>
"""
    return render_layout(
        title="Flux RSS JADE",
        body=body,
        css_path="assets/site.css",
        rss_url=rss_url,
    )


def render_decision_page(item: dict[str, str], site_url: str) -> str:
    number_value = item["number"] or "Numéro non précisé"
    formation_block = (
        f'<span class="tag">Formation : {html.escape(item["formation"])}</span>'
        if item["formation"]
        else ""
    )
    publication_block = (
        f'<span class="tag">Code de publication : {html.escape(item["publication_code"])}</span>'
        if item["publication_code"]
        else ""
    )
    body = f"""
    <main class="shell decision-page">
      <div>
        <a class="back-link" href="../index.html">Retour aux dernières décisions</a>
      </div>
      <section class="hero">
        <span class="eyebrow">Décision publiée dans JADE</span>
        <h1>{html.escape(item["title"])}</h1>
        <p class="hero-copy">{html.escape(item["summary"])}</p>
        <div class="decision-meta">
          <span class="tag">Décision du {html.escape(display_date(item["decision_date"]))}</span>
          <span class="tag">Publication du {html.escape(display_datetime(item["published_at"]))}</span>
          <span class="tag">{html.escape(item["jurisdiction"] or "Juridiction non précisée")}</span>
          <span class="tag">N° {html.escape(number_value)}</span>
          {formation_block}
          {publication_block}
        </div>
        <div class="decision-actions">
          <a class="button button-primary" href="{html.escape(item["archive_url"])}">Télécharger l'archive source</a>
          <a class="button button-secondary" href="{html.escape(site_url.rstrip('/') + '/rss.xml')}">S'abonner au flux RSS</a>
        </div>
      </section>

      <section class="decision-text">
        {item["content_html"] or "<p>Le texte intégral n'a pas pu être extrait.</p>"}
      </section>

      <p class="footnote">
        Identifiant JADE : <strong>{html.escape(item["id"])}</strong>
        {' • Chemin XML : ' + html.escape(item["source_xml_path"]) if item["source_xml_path"] else ''}
      </p>
    </main>
"""
    return render_layout(
        title=item["title"],
        body=body,
        css_path="../assets/site.css",
        rss_url=f"{site_url.rstrip('/')}/rss.xml",
    )


def write_text_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write(content)


def build_rss(items: list[dict[str, str]], site_url: str) -> str:
    root = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(root, "channel")
    ET.SubElement(channel, "title").text = "Nouvelles décisions publiées dans le fonds JADE"
    ET.SubElement(channel, "link").text = site_url.rstrip("/") + "/"
    ET.SubElement(channel, "description").text = (
        "Flux RSS quotidien des nouvelles décisions publiées dans le fonds JADE."
    )
    ET.SubElement(channel, "language").text = "fr"
    ET.SubElement(channel, "lastBuildDate").text = format_rss_date(
        items[0]["published_at"] if items else dt.datetime.now(tz=SOURCE_TIMEZONE).isoformat()
    )

    for item in items:
        item_el = ET.SubElement(channel, "item")
        link = f"{site_url.rstrip('/')}/{item['page_path']}"
        description = textwrap.dedent(
            f"""\
            {item["summary"]}

            Juridiction : {item["jurisdiction"] or "Non précisée"}
            Date de décision : {display_date(item["decision_date"])}
            Numéro : {item["number"] or "Non précisé"}
            Archive source : {item["archive_name"]}
            """
        ).strip()
        ET.SubElement(item_el, "title").text = item["title"]
        ET.SubElement(item_el, "link").text = link
        ET.SubElement(item_el, "guid").text = link
        ET.SubElement(item_el, "pubDate").text = format_rss_date(item["published_at"])
        ET.SubElement(item_el, "description").text = description

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    buffer = io.BytesIO()
    tree.write(buffer, encoding="utf-8", xml_declaration=True)
    return buffer.getvalue().decode("utf-8")


def write_docs(items: list[dict[str, str]], site_url: str) -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    DECISIONS_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    for existing_file in DECISIONS_DIR.glob("*.html"):
        existing_file.unlink()

    write_text_file(ASSETS_DIR / "site.css", SITE_CSS)
    write_text_file(DOCS_DIR / ".nojekyll", "")
    write_text_file(DOCS_DIR / "index.html", render_index_page(items, site_url))
    write_text_file(DOCS_DIR / "rss.xml", build_rss(items, site_url))

    for item in items:
        write_text_file(
            DOCS_DIR / item["page_path"],
            render_decision_page(item, site_url),
        )


def build_site(base_url: str) -> dict[str, int]:
    state = load_state()
    archive_index = parse_archive_listing(fetch_text(INDEX_URL))
    archives_to_process = pick_archives_to_process(
        archive_index, state.get("processed_archives", [])
    )

    items_by_id = {item["id"]: item for item in state.get("items", []) if item.get("id")}

    processed_this_run = 0
    added_or_updated = 0
    for archive in archives_to_process:
        print(f"Traitement de {archive['name']}...")
        decisions = parse_archive(fetch_bytes(archive["url"]), archive)
        processed_this_run += 1
        for decision in decisions:
            current = items_by_id.get(decision["id"])
            if current and decision_sort_key(current) >= decision_sort_key(decision):
                continue
            items_by_id[decision["id"]] = decision
            added_or_updated += 1

    processed_lookup = set(state.get("processed_archives", []))
    processed_lookup.update(archive["name"] for archive in archives_to_process)
    processed_archives = [
        archive["name"] for archive in archive_index if archive["name"] in processed_lookup
    ]

    items = sorted(
        items_by_id.values(),
        key=decision_sort_key,
        reverse=True,
    )[:FEED_ITEM_LIMIT]

    new_state = {
        "processed_archives": processed_archives,
        "items": items,
    }

    save_state(new_state)
    write_docs(items, base_url)

    return {
        "archives_processed": processed_this_run,
        "items_written": len(items),
        "items_added_or_updated": added_or_updated,
    }


def serve_docs(host: str, port: int) -> None:
    class DocsHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, directory=str(DOCS_DIR), **kwargs)

    httpd = ThreadingHTTPServer((host, port), DocsHandler)
    print(f"Serveur local disponible sur http://{host}:{port}")
    print("Ctrl+C pour arrêter.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nArrêt du serveur.")
    finally:
        httpd.server_close()


def build_command(args: argparse.Namespace) -> int:
    stats = build_site(args.base_url)
    print(
        "Build terminé : "
        f"{stats['archives_processed']} archive(s) traitée(s), "
        f"{stats['items_added_or_updated']} décision(s) ajoutée(s) ou mise(s) à jour, "
        f"{stats['items_written']} décision(s) publiées."
    )
    return 0


def serve_command(args: argparse.Namespace) -> int:
    if args.refresh:
        build_site(args.base_url)
    serve_docs(args.host, args.port)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Générateur de flux RSS pour les nouvelles décisions du fonds JADE."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser_ = subparsers.add_parser("build", help="Télécharge les nouveautés et régénère le site statique.")
    build_parser_.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="URL publique de base utilisée dans le flux RSS et les pages HTML.",
    )
    build_parser_.set_defaults(func=build_command)

    serve_parser_ = subparsers.add_parser("serve", help="Lance un serveur local pour le dossier docs/.")
    serve_parser_.add_argument(
        "--host",
        default="127.0.0.1",
        help="Adresse d'écoute locale.",
    )
    serve_parser_.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port HTTP local.",
    )
    serve_parser_.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="URL de base utilisée si la commande doit reconstruire le site avant de servir.",
    )
    serve_parser_.add_argument(
        "--no-refresh",
        action="store_false",
        dest="refresh",
        help="Ne reconstruit pas le site avant de lancer le serveur.",
    )
    serve_parser_.set_defaults(func=serve_command, refresh=True)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
