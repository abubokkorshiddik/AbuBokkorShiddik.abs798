#!/usr/bin/env python3
"""ResearchRadar AI scheduled scholarly literature collector.

Writes public, browser-readable files into ResearchRadarAI/data/.
OPENAI_API_KEY is optional; it is read only from the GitHub Actions environment.
"""
from __future__ import annotations
import json, os, re, time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote
import requests

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
REPORTS_DIR = DATA_DIR / "reports"
ARTICLES_FILE = DATA_DIR / "articles.json"
REPORTS_FILE = DATA_DIR / "reports.json"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5").strip() or "gpt-5.5"
MAX_PER_QUERY = int(os.getenv("MAX_PER_QUERY", "25"))
MAX_ARTICLES = int(os.getenv("MAX_ARTICLES", "150"))
DAYS_BACK = int(os.getenv("DAYS_BACK", "730"))
QUERIES = [
    "machine learning explainable AI public health",
    "infectious disease prediction epidemiology",
    "climate change health disease risk",
    "dengue malaria spatial modelling geospatial",
    "remote sensing environmental epidemiology",
]
HEADERS = {"User-Agent": "ResearchRadarAI/1.0 (GitHub Actions literature discovery)"}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

def clean_text(value):
    if not value:
        return ""
    if isinstance(value, list):
        value = " ".join(str(v) for v in value)
    return re.sub(r"\s+", " ", str(value)).strip()

def year_from_date(value):
    m = re.search(r"\b(19|20)\d{2}\b", str(value or ""))
    return m.group(0) if m else ""

def openalex_abstract(inv):
    if not isinstance(inv, dict) or not inv:
        return ""
    words = []
    for word, positions in inv.items():
        for pos in positions:
            words.append((pos, word))
    words.sort()
    return " ".join(word for _, word in words)

def fetch_openalex(query, from_date):
    url = "https://api.openalex.org/works"
    params = {
        "search": query,
        "filter": f"from_publication_date:{from_date},type:article|preprint",
        "sort": "publication_date:desc",
        "per-page": min(MAX_PER_QUERY, 50),
        "mailto": os.getenv("OPENALEX_EMAIL", ""),
    }
    try:
        response = SESSION.get(url, params=params, timeout=45)
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        print(f"[WARN] OpenAlex query failed ({query}): {exc}")
        return []
    results = []
    for item in payload.get("results", []):
        title = clean_text(item.get("title"))
        if not title:
            continue
        authors = []
        for a in item.get("authorships", [])[:8]:
            name = (a.get("author") or {}).get("display_name")
            if name:
                authors.append(name)
        primary = item.get("primary_location") or {}
        source = primary.get("source") or {}
        doi = clean_text(item.get("doi"))
        url_out = doi or clean_text(primary.get("landing_page_url")) or clean_text(item.get("id"))
        concepts = item.get("concepts") or []
        topics = [clean_text(c.get("display_name")) for c in concepts[:5] if c.get("display_name")]
        results.append({
            "id": doi or clean_text(item.get("id")) or title,
            "title": title,
            "authors": ", ".join(authors),
            "publication_date": clean_text(item.get("publication_date")),
            "year": year_from_date(item.get("publication_date")),
            "journal": clean_text(source.get("display_name")),
            "doi": doi,
            "url": url_out,
            "abstract": openalex_abstract(item.get("abstract_inverted_index")),
            "topics": topics,
            "source": "OpenAlex",
            "cited_by_count": item.get("cited_by_count", 0),
        })
    return results

def fetch_europepmc(query, from_date):
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    # Europe PMC query syntax; dates are publication dates.
    q = f'({query}) AND FIRST_PDATE:[{from_date} TO 3000-12-31] AND (SRC:MED OR SRC:PPR)'
    params = {"query": q, "format": "json", "pageSize": min(MAX_PER_QUERY, 50),
              "sort": "FIRST_PDATE_D desc"}
    try:
        response = SESSION.get(url, params=params, timeout=45)
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        print(f"[WARN] Europe PMC query failed ({query}): {exc}")
        return []
    results = []
    for item in payload.get("resultList", {}).get("result", []):
        title = clean_text(item.get("title"))
        if not title:
            continue
        doi = clean_text(item.get("doi"))
        pmid = clean_text(item.get("pmid"))
        pmcid = clean_text(item.get("pmcid"))
        url_out = f"https://doi.org/{doi}" if doi else (f"https://europepmc.org/article/MED/{pmid}" if pmid else (f"https://europepmc.org/articles/{pmcid}" if pmcid else ""))
        author_string = clean_text(item.get("authorString"))
        topics = [clean_text(item.get("journalTitle"))] if item.get("journalTitle") else []
        results.append({
            "id": doi or pmid or pmcid or title,
            "title": title,
            "authors": author_string,
            "publication_date": clean_text(item.get("firstPublicationDate") or item.get("journalInfo", {}).get("printPublicationDate")),
            "year": year_from_date(item.get("firstPublicationDate") or item.get("pubYear")),
            "journal": clean_text(item.get("journalTitle")),
            "doi": doi,
            "url": url_out,
            "abstract": clean_text(item.get("abstractText")),
            "topics": topics,
            "source": "Europe PMC",
        })
    return results

def deduplicate(records):
    seen, out = set(), []
    for item in sorted(records, key=lambda x: (x.get("publication_date", ""), x.get("title", "")), reverse=True):
        doi = clean_text(item.get("doi")).lower().replace("https://doi.org/", "")
        title = re.sub(r"[^a-z0-9]+", "", item.get("title", "").lower())
        key = "doi:" + doi if doi else "title:" + title
        if not title or key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out

def summarize_with_openai(articles):
    if not OPENAI_API_KEY:
        return None
    selected = articles[:35]
    compact = [{
        "title": a.get("title"), "year": a.get("year"), "authors": a.get("authors"),
        "journal": a.get("journal"), "abstract": (a.get("abstract") or "")[:900],
        "topics": a.get("topics", [])[:4], "url": a.get("url")
    } for a in selected]
    prompt = (
        "Create a cautious daily scholarly literature briefing using ONLY the metadata and abstracts below. "
        "Do not invent study findings, sample sizes, effect sizes, or causal claims. If abstracts are missing, say so. "
        "Separate observed themes from hypotheses. Include: Overview, Emerging themes, Potential questions to investigate, "
        "Limitations of this scan, and a short list of selected papers with their provided URLs. "
        "Do not claim that a research gap is proven. Return readable Markdown. Data:\n" +
        json.dumps(compact, ensure_ascii=False)
    )
    try:
        resp = SESSION.post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            json={"model": OPENAI_MODEL, "input": prompt},
            timeout=120,
        )
        if not resp.ok:
            print(f"[WARN] OpenAI request failed: HTTP {resp.status_code} {resp.text[:500]}")
            return None
        data = resp.json()
        if data.get("output_text"):
            return data["output_text"].strip()
        chunks = []
        for output in data.get("output", []):
            for content in output.get("content", []):
                if content.get("type") == "output_text":
                    chunks.append(content.get("text", ""))
        result = "\n".join(chunks).strip()
        return result or None
    except Exception as exc:
        print(f"[WARN] OpenAI summary failed: {exc}")
        return None

def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    from_date = (now - timedelta(days=DAYS_BACK)).strftime("%Y-%m-%d")
    records = []
    for i, query in enumerate(QUERIES, 1):
        print(f"[INFO] Query {i}/{len(QUERIES)}: {query}")
        records.extend(fetch_openalex(query, from_date))
        records.extend(fetch_europepmc(query, from_date))
        time.sleep(0.25)
    papers = deduplicate(records)[:MAX_ARTICLES]
    stamp = now.strftime("%Y-%m-%d")
    for p in papers:
        p.setdefault("topics", [])
        if not p.get("year"):
            p["year"] = year_from_date(p.get("publication_date"))
    ARTICLES_FILE.write_text(json.dumps({
        "updated_at": now.isoformat(),
        "count": len(papers),
        "queries": QUERIES,
        "articles": papers,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[INFO] Saved {len(papers)} unique papers to {ARTICLES_FILE}")

    ai_report = summarize_with_openai(papers)
    if ai_report:
        report_content = ai_report
        report_title = f"Daily AI literature briefing — {stamp}"
        summary = "AI-assisted synthesis of the latest matching records. Verify claims against the original papers."
    else:
        titles = "\n".join(f"- {p['title']} ({p.get('year') or 'year unknown'}) — {p.get('url','')}" for p in papers[:20])
        report_content = (
            f"# ResearchRadar literature scan — {stamp}\n\n"
            f"## Collection summary\nCollected {len(papers)} unique records from OpenAlex and Europe PMC for the configured queries.\n\n"
            "## Important limitation\nThis is a metadata-based scan, not a systematic review. Without a configured working OpenAI API key, no AI synthesis was generated. "
            "Even with AI enabled, verify every interpretation in the original publication.\n\n"
            f"## Recent matching records\n{titles or 'No records were returned by the data sources.'}\n"
        )
        report_title = f"Literature scan — {stamp}"
        summary = f"{len(papers)} records collected. " + ("AI summary was unavailable; metadata-only report created." if OPENAI_API_KEY else "Metadata-only report; add an API key secret to enable AI synthesis.")
    report = {
        "id": f"report-{stamp}",
        "title": report_title,
        "date": stamp,
        "generated_at": now.isoformat(),
        "summary": summary,
        "content": report_content,
        "article_count": len(papers),
        "ai_generated": bool(ai_report),
    }
    # Keep a dated archive, and publish the newest report first in the manifest.
    archive_path = REPORTS_DIR / f"report-{stamp}.md"
    archive_path.write_text(report_content + "\n", encoding="utf-8")
    existing = []
    if REPORTS_FILE.exists():
        try:
            old = json.loads(REPORTS_FILE.read_text(encoding="utf-8"))
            existing = old if isinstance(old, list) else old.get("reports", [])
        except Exception:
            existing = []
    existing = [r for r in existing if r.get("id") != report["id"]]
    manifest = [report] + existing
    manifest = manifest[:60]
    REPORTS_FILE.write_text(json.dumps({"updated_at": now.isoformat(), "reports": manifest}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[INFO] Report manifest updated. AI generated: {bool(ai_report)}")
    if not papers:
        print("[WARN] No papers returned. The website will show an empty real dataset, not sample data.")

if __name__ == "__main__":
    main()
