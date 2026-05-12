#!/usr/bin/env python3
"""
Fiverr Real Scraping via DuckDuckGo HTML
Busca gigs reales en Fiverr usando DDG site:fiverr.com
Extrae precios, delivery times y tags de los snippets.
"""
import re
import time
import random
import requests
from urllib.parse import urlparse, parse_qs, unquote
from bs4 import BeautifulSoup

UA = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}

# Queries DDG para cada nicho — site:fiverr.com
FIVERR_DDG_QUERIES = {
    "proxmox": [
        'site:fiverr.com proxmox server setup',
        'site:fiverr.com homelab docker setup',
    ],
    "home_assistant": [
        'site:fiverr.com home assistant setup',
        'site:fiverr.com smart home automation',
    ],
    "wordpress": [
        'site:fiverr.com wordpress elementor website',
        'site:fiverr.com elementor expert developer',
    ],
    "python_automation": [
        'site:fiverr.com python web scraping automation',
        'site:fiverr.com python bot automation script',
    ],
    "ollama_ai": [
        'site:fiverr.com ai server setup llm',
        'site:fiverr.com ollama self hosted ai',
    ],
    "network_firewall": [
        'site:fiverr.com mikrotik firewall configuration',
        'site:fiverr.com network security setup',
    ],
    "cctv": [
        'site:fiverr.com cctv camera remote setup',
        'site:fiverr.com hikvision dahua configuration',
    ],
    "esp32_iot": [
        'site:fiverr.com esp32 arduino firmware',
        'site:fiverr.com iot custom device',
    ],
    "seo_ads": [
        'site:fiverr.com technical seo audit',
        'site:fiverr.com google ads campaign setup',
    ],
    "docker_devops": [
        'site:fiverr.com docker devops cicd pipeline',
        'site:fiverr.com kubernetes deployment',
    ],
}


def _clean_ddg_url(raw_url: str) -> str:
    if raw_url.startswith("//"):
        raw_url = "https:" + raw_url
    if "duckduckgo.com/l/?" in raw_url:
        parsed = urlparse(raw_url)
        qs = parse_qs(parsed.query)
        if "uddg" in qs:
            return unquote(qs["uddg"][0])
    return raw_url


def ddg_search(query: str, max_results: int = 8) -> list[dict]:
    """Busca en DuckDuckGo HTML y devuelve resultados."""
    url = "https://html.duckduckgo.com/html/"
    try:
        resp = requests.post(url, data={"q": query}, headers=UA, timeout=30)
        if resp.status_code in (202, 403):
            return []  # CAPTCHA o bloqueado
        resp.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []

    for block in soup.select(".result"):
        a = block.select_one(".result__title a")
        snippet = block.select_one(".result__snippet")
        if not a:
            continue
        href = _clean_ddg_url(a.get("href", "").strip())
        title = " ".join(a.get_text(" ", strip=True).split())
        desc = " ".join(snippet.get_text(" ", strip=True).split()) if snippet else ""

        if href and title and "fiverr.com" in href:
            gig_data = parse_fiverr_snippet(title, desc, href)
            results.append(gig_data)
        if len(results) >= max_results:
            break

    return results


def parse_fiverr_snippet(title: str, snippet: str, url: str) -> dict:
    """Extrae precio, delivery y tags de un snippet de DDG sobre Fiverr."""
    # Extraer precios del snippet/título
    prices = re.findall(r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)', f"{title} {snippet}")
    prices = [float(p.replace(",", "")) for p in prices]

    # Extraer delivery time
    delivery_match = re.search(
        r'(\d+)\s*(?:day|día|days|días|hr|hour)', f"{title} {snippet}", re.I
    )
    delivery = f"{delivery_match.group(1)} days" if delivery_match else None

    # Extraer rating
    rating_match = re.search(r'(\d\.\d)\s*(?:\(|star|⭐)', snippet, re.I)
    rating = float(rating_match.group(1)) if rating_match else None

    # Extraer reviews count
    reviews_match = re.search(r'\((\d+(?:,\d{3})*)\s*(?:review|reseña)', snippet, re.I)
    reviews = int(reviews_match.group(1).replace(",", "")) if reviews_match else None

    # Limpiar título — quitar "Fiverr" prefix
    clean_title = re.sub(r'^.*?(?:I will |I Will )', 'I will ', title)
    if clean_title == title:
        clean_title = re.sub(r'^\s*\w+\s*\|\s*', '', title)

    return {
        "title": clean_title.strip(),
        "url": url,
        "snippet": snippet[:200],
        "prices": prices,
        "price_min": min(prices) if prices else None,
        "price_max": max(prices) if prices else None,
        "delivery": delivery,
        "rating": rating,
        "reviews": reviews,
    }


def scrape_fiverr_niches(delay: float = 3.0) -> dict:
    """
    Busca gigs reales de Fiverr via DDG para todos los nichos.
    Retorna dict {niche_id: [gig_data, ...]}.
    """
    all_results = {}
    ddg_available = True

    for niche_id, queries in FIVERR_DDG_QUERIES.items():
        if not ddg_available:
            print(f"  ⚠️  DDG bloqueado — skip {niche_id}")
            all_results[niche_id] = []
            continue

        print(f"\n  🔍 Nicho: {niche_id}")
        niche_gigs = []

        for query in queries:
            print(f"    🌐 DDG: {query[:60]}...")
            results = ddg_search(query, max_results=5)

            if not results and not niche_gigs:
                # Primer query sin resultados = DDG probablemente bloqueado
                ddg_available = False
                print(f"    ⚠️  DDG sin resultados (posible CAPTCHA)")
                break

            niche_gigs.extend(results)
            time.sleep(delay + random.uniform(1, 3))

        # Deduplicar por URL
        seen = set()
        unique = []
        for g in niche_gigs:
            if g["url"] not in seen:
                seen.add(g["url"])
                unique.append(g)
        all_results[niche_id] = unique

        if unique:
            prices = [p for g in unique for p in g["prices"]]
            print(f"    ✅ {len(unique)} gigs encontrados", end="")
            if prices:
                print(f" | Precios: ${min(prices):.0f}–${max(prices):.0f}")
            else:
                print()

    return all_results, ddg_available


def summarize_fiverr_real(results: dict) -> list[dict]:
    """Resume los resultados reales de Fiverr por nicho."""
    summaries = []
    for niche_id, gigs in results.items():
        if not gigs:
            summaries.append({"niche": niche_id, "gigs_found": 0})
            continue

        prices = [p for g in gigs for p in g["prices"]]
        ratings = [g["rating"] for g in gigs if g["rating"]]
        deliveries = [g["delivery"] for g in gigs if g["delivery"]]

        summaries.append({
            "niche": niche_id,
            "gigs_found": len(gigs),
            "price_min": min(prices) if prices else None,
            "price_max": max(prices) if prices else None,
            "price_avg": round(sum(prices)/len(prices), 2) if prices else None,
            "avg_rating": round(sum(ratings)/len(ratings), 1) if ratings else None,
            "sample_deliveries": deliveries[:3],
            "top_titles": [g["title"][:80] for g in gigs[:5]],
        })
    return summaries
