#!/usr/bin/env python3
"""
Pipeline de Inteligencia de Mercado Freelance
Arquitectura: Freelancer.com Public API + Groq AI (análisis)

Fuentes de datos:
  1. Freelancer.com API  — proyectos reales con presupuestos y skills (SIN auth para búsqueda pública)
  2. Groq LLM            — análisis de mercado + síntesis de inteligencia competitiva

Ventaja: No requiere Playwright, no hay anti-bot. Funciona 100% desde servidor Linux.

Requisitos en Proxmox LXC:
    pip install requests python-dotenv google-api-python-client google-auth-oauthlib

Configuración:
    .env con GROQ_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
"""
import os
import re
import json
import time
import random
import smtplib
import ssl
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Google Drive API
try:
    from gdrive_auth import get_drive_service, get_or_create_drive_folder
    GDRIVE_AVAILABLE = True
except ImportError:
    GDRIVE_AVAILABLE = False

# Fiverr DDG Real Scraping
try:
    from fiverr_ddg_scraper import scrape_fiverr_niches, summarize_fiverr_real
    DDG_AVAILABLE = True
except ImportError:
    DDG_AVAILABLE = False

# ─── Cargar credenciales ──────────────────────────────────────────────────────
load_dotenv(Path(__file__).parent / ".env")

GROQ_API_KEY       = os.getenv("GROQ_API_KEY", "").strip('"')
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip('"')
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "").strip('"')
EMAIL_SENDER       = os.getenv("EMAIL_SENDER", "").strip('"')       # tu gmail: xxx@gmail.com
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD", "").strip('"') # App Password de Google
EMAIL_RECIPIENT    = os.getenv("EMAIL_RECIPIENT", "eliutec@gmail.com").strip('"')

if not GROQ_API_KEY or "REEMPLAZAR" in GROQ_API_KEY:
    raise ValueError("❌ GROQ_API_KEY no configurada en .env")

# ─── Configuración ────────────────────────────────────────────────────────────
# Keywords para buscar en Freelancer.com — Alineados con los 10 gigs de Fiverr
SEARCH_QUERIES = [
    # FASE 1 — 4 gigs iniciales (New Seller)
    "proxmox server setup docker",          # Gig 1: Proxmox VPS/Homelab
    "home assistant smart home setup",       # Gig 2: Home Assistant & IoT
    "wordpress elementor website",           # Gig 3: WordPress + Elementor
    "python automation web scraping",        # Gig 4: Python Automation
    # FASE 2 — 6 gigs adicionales (Level 1)
    "ollama ai server setup self hosted",    # Gig 5: AI Server (Ollama)
    "mikrotik fortigate firewall setup",     # Gig 6: Network & Firewall
    "hikvision dahua cctv setup",            # Gig 7: CCTV Security
    "esp32 arduino iot firmware",            # Gig 8: ESP32/Arduino IoT
    "technical seo audit google ads",        # Gig 9: SEO + Google Ads
    "docker devops deployment cicd",         # Gig 10: Docker & DevOps
]

# Nichos de Fiverr a analizar con Groq — Alineados con los 10 gigs
FIVERR_NICHES = [
    # FASE 1
    "Proxmox VPS Homelab Server Setup and Configuration",
    "Home Assistant Smart Home Setup and Automation",
    "WordPress Elementor Website Developer",
    "Python Web Scraping and Automation Scripts",
    # FASE 2
    "Ollama Self-Hosted AI Server Setup (Private LLM)",
    "Mikrotik Fortigate pfSense Network Firewall Configuration",
    "Hikvision Dahua CCTV Remote Setup and Configuration",
    "ESP32 Arduino Custom IoT Firmware Development",
    "Technical SEO Audit and Google Ads Campaign Setup",
    "Docker DevOps CI/CD Deployment Pipeline",
]

GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_URL   = "https://api.groq.com/openai/v1/chat/completions"
OUTPUT_DIR = Path("data/scraping")
GDRIVE_FOLDER_NAME = "scraping_informes"

FREELANCER_API = "https://www.freelancer.com/api"
FREELANCER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; MarketResearch/1.0)",
    "Accept": "application/json",
}


# ─── Freelancer.com API ───────────────────────────────────────────────────────
def search_freelancer_projects(query: str, limit: int = 20) -> list[dict]:
    """
    Busca proyectos activos en Freelancer.com via API pública.
    Devuelve lista de {title, budget_min, budget_max, skills, url, preview_description}.
    """
    url = f"{FREELANCER_API}/projects/0.1/projects/active/"
    params = {
        "query":          query,
        "limit":          limit,
        "offset":         0,
        "job_details":    "true",
        "full_description": "false",
        "compact":        "false",
    }

    try:
        r = requests.get(url, headers=FREELANCER_HEADERS, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()

        projects = data.get("result", {}).get("projects", [])
        results  = []

        for p in projects:
            budget = p.get("budget", {})
            jobs   = p.get("jobs", [])
            skills = [j.get("name", "") for j in jobs] if jobs else []

            results.append({
                "title":       p.get("title", ""),
                "budget_min":  budget.get("minimum"),
                "budget_max":  budget.get("maximum"),
                "currency":    p.get("currency", {}).get("sign", "$"),
                "skills":      skills[:6],
                "url":         f"https://www.freelancer.com/projects/{p.get('seo_url', '')}",
                "preview":     p.get("preview_description", "") or "",
            })

        return results

    except requests.exceptions.HTTPError as e:
        print(f"  ⚠️  Freelancer API HTTP error: {e.response.status_code}")
        return []
    except Exception as e:
        print(f"  ❌ Freelancer API error: {e}")
        return []


# ─── Groq: Analizar proyectos de Freelancer ──────────────────────────────────
def analyze_freelancer_data(projects: list[dict], query: str) -> dict:
    """Usa Groq para extraer insights de los proyectos de Freelancer."""
    if not projects:
        return {}

    formatted = "\n\n".join(
        f"[{i+1}] Título: {p['title']}\n"
        f"    Presupuesto: {p['currency']}{p['budget_min']}–{p['currency']}{p['budget_max']}\n"
        f"    Skills: {', '.join(p['skills'])}\n"
        f"    Preview: {p['preview'][:150]}"
        for i, p in enumerate(projects[:15])
    )

    prompt = f"""Analiza estos {len(projects)} proyectos activos de Freelancer.com para el query "{query}".

{formatted}

Devuelve un objeto JSON con:
- demanda: "Alta" | "Media" | "Baja" (basado en cantidad y variedad de proyectos)
- precio_min_usd: precio mínimo típico en USD (número entero)
- precio_max_usd: precio máximo típico en USD (número entero)
- precio_promedio_usd: precio promedio estimado (número entero)
- skills_mas_demandados: array de 5 strings con las habilidades más frecuentes
- tipo_clientes: descripción de 1 oración del tipo de cliente que busca esto
- oportunidad_entrada: "Fácil" | "Moderada" | "Difícil" (para un nuevo freelancer)
- consejo_posicionamiento: consejo de 1-2 oraciones para posicionarse en este nicho
- resumen: resumen ejecutivo de 2-3 oraciones del estado del mercado

Devuelve SOLO el JSON. Sin texto adicional ni markdown."""

    return _call_groq(prompt, max_tokens=800)


# ─── Groq: Inteligencia de mercado Fiverr (sin scraping) ─────────────────────
def get_fiverr_intelligence(niche: str) -> dict:
    """
    Usa el conocimiento del LLM sobre Fiverr para generar inteligencia de mercado.
    No requiere scraping. El LLM tiene datos de training sobre precios y tendencias.
    """
    prompt = f"""Eres un experto en el mercado freelance de Fiverr con datos actualizados a 2024-2025.

Para el nicho "{niche}" en Fiverr, proporciona un análisis de mercado detallado.

Devuelve un objeto JSON con:
- nicho: "{niche}"
- precio_basico_usd: precio típico del paquete básico en USD (entero)
- precio_estandar_usd: precio típico del paquete estándar en USD (entero)
- precio_premium_usd: precio típico del paquete premium en USD (entero)
- competencia: "Alta" | "Media" | "Baja"
- demanda: "Alta" | "Media" | "Baja"
- rating_promedio_top_sellers: calificación promedio de vendedores top (decimal, ej: 4.9)
- nivel_entrada_recomendado: "New Seller" | "Level 1" | "Level 2"
- tiempo_hasta_primera_venta_dias: estimado en días para un seller nuevo (entero)
- keywords_gig_title: array de 5 keywords clave para el título del gig
- usp_recomendado: propuesta de valor única diferenciadora (1 oración)
- tendencia_2025: "Creciendo" | "Estable" | "Declinando"
- consejo_clave: el consejo más importante para tener éxito en este nicho (2 oraciones)

Devuelve SOLO el JSON válido. Sin texto adicional."""

    return _call_groq(prompt, max_tokens=600)


# ─── Groq helper ─────────────────────────────────────────────────────────────
def _call_groq(prompt: str, max_tokens: int = 800) -> dict:
    """Llama a Groq API y parsea la respuesta JSON."""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model":    GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens":  max_tokens,
    }

    for attempt in range(3):
        try:
            resp = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)

            if resp.status_code == 429:
                retry = int(resp.headers.get("retry-after", 20))
                print(f"  ⏳ Rate limit Groq — esperando {retry}s...")
                time.sleep(retry + 2)
                continue

            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"].strip()

            # Limpiar markdown si viene envuelto en ```json ... ```
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)

            # Extraer primer objeto JSON del texto
            start = content.find("{")
            end   = content.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(content[start:end])

            return json.loads(content)

        except json.JSONDecodeError as e:
            print(f"  ⚠️  JSON inválido intento {attempt+1}: {e}")
        except Exception as e:
            print(f"  ❌ Error Groq intento {attempt+1}: {e}")

        if attempt < 2:
            time.sleep(4)

    return {}


# ─── Reporte Markdown ─────────────────────────────────────────────────────────
def generate_report(
    ts: str,
    freelancer_results: list[dict],
    fiverr_intelligence: list[dict],
    output_dir: Path,
    fiverr_real: dict = None,
) -> Path:
    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M')
    md_file   = output_dir / f"reporte_{timestamp}.md"

    with open(md_file, "w", encoding="utf-8") as f:
        f.write(f"# 📊 Reporte Inteligencia Freelance\n")
        f.write(f"**Fecha:** {ts}  \n")
        f.write(f"**Fuentes:** Freelancer.com API + Groq AI + Fiverr DDG Scraping\n\n")
        f.write("---\n\n")

        # ── Sección 1: Proyectos Freelancer.com ──
        if freelancer_results:
            f.write("## 🌐 Proyectos Activos en Freelancer.com\n\n")
            for item in freelancer_results:
                q    = item["query"]
                data = item["analysis"]
                projs = item["projects"]

                f.write(f"### 🔍 Query: `{q}`\n\n")

                if data:
                    f.write("**Análisis de mercado:**\n\n")
                    f.write(f"| Métrica | Valor |\n|---|---|\n")
                    f.write(f"| Demanda | {data.get('demanda','?')} |\n")
                    f.write(f"| Precio típico | ${data.get('precio_min_usd','?')}–${data.get('precio_max_usd','?')} |\n")
                    f.write(f"| Precio promedio | ${data.get('precio_promedio_usd','?')} |\n")
                    f.write(f"| Dificultad de entrada | {data.get('oportunidad_entrada','?')} |\n")
                    if data.get("skills_mas_demandados"):
                        f.write(f"| Skills clave | {', '.join(data['skills_mas_demandados'])} |\n")
                    f.write("\n")
                    if data.get("consejo_posicionamiento"):
                        f.write(f"> 💡 **Consejo:** {data['consejo_posicionamiento']}\n\n")
                    if data.get("resumen"):
                        f.write(f"{data['resumen']}\n\n")

                if projs:
                    f.write(f"**Top proyectos activos ({len(projs)} encontrados):**\n\n")
                    f.write("| Título | Presupuesto | Skills |\n|---|---|---|\n")
                    for p in projs[:8]:
                        bmin = p.get("budget_min", "?")
                        bmax = p.get("budget_max", "?")
                        skills = ", ".join(p.get("skills", [])[:3])
                        title = p.get("title", "")[:55]
                        f.write(f"| {title} | ${bmin}–${bmax} | {skills} |\n")
                    f.write("\n")

                f.write("---\n\n")

        # ── Sección 2: Inteligencia Fiverr (Groq AI) ──
        if fiverr_intelligence:
            f.write("## 🎯 Inteligencia de Mercado Fiverr (Groq AI)\n\n")
            f.write("*(Análisis basado en datos de mercado 2024-2025 via Groq AI)*\n\n")

            for intel in fiverr_intelligence:
                if not intel:
                    continue
                nicho = intel.get("nicho", "?")
                f.write(f"### {nicho}\n\n")
                f.write(f"| Métrica | Valor |\n|---|---|\n")
                f.write(f"| Precio Básico | ${intel.get('precio_basico_usd','?')} |\n")
                f.write(f"| Precio Estándar | ${intel.get('precio_estandar_usd','?')} |\n")
                f.write(f"| Precio Premium | ${intel.get('precio_premium_usd','?')} |\n")
                f.write(f"| Competencia | {intel.get('competencia','?')} |\n")
                f.write(f"| Demanda | {intel.get('demanda','?')} |\n")
                f.write(f"| Tendencia 2025 | {intel.get('tendencia_2025','?')} |\n")
                f.write(f"| Rating top sellers | {intel.get('rating_promedio_top_sellers','?')}⭐ |\n")
                f.write(f"| Tiempo 1ª venta | ~{intel.get('tiempo_hasta_primera_venta_dias','?')} días |\n")
                if intel.get("keywords_gig_title"):
                    f.write(f"| Keywords título | {', '.join(intel['keywords_gig_title'])} |\n")
                f.write("\n")
                if intel.get("usp_recomendado"):
                    f.write(f"> 🎯 **USP:** {intel['usp_recomendado']}\n\n")
                if intel.get("consejo_clave"):
                    f.write(f"> 💡 **Consejo clave:** {intel['consejo_clave']}\n\n")

        # ── Sección 3: Fiverr Real (DDG Scraping) ──
        if fiverr_real:
            f.write("## 🕵️ Gigs Reales de Fiverr (DuckDuckGo Scraping)\n\n")
            f.write("*(Datos extraídos de resultados reales de búsqueda)*\n\n")

            for niche_id, gigs in fiverr_real.items():
                f.write(f"### 🔎 {niche_id.replace('_', ' ').title()}\n\n")
                if not gigs:
                    f.write("- Sin resultados (DDG bloqueado o sin gigs)\n\n")
                    continue

                f.write("| Gig | Precios | Delivery | Rating |\n|---|---|---|---|\n")
                for g in gigs[:6]:
                    title = g["title"][:50]
                    prices = f"${g['price_min']:.0f}–${g['price_max']:.0f}" if g.get("price_min") else "N/A"
                    delivery = g.get("delivery") or "N/A"
                    rating = f"{g['rating']}⭐" if g.get("rating") else "N/A"
                    f.write(f"| {title} | {prices} | {delivery} | {rating} |\n")
                f.write("\n")

                # Resumen de precios del nicho
                all_prices = [p for g in gigs for p in g.get("prices", [])]
                if all_prices:
                    f.write(f"> 💰 **Rango real:** ${min(all_prices):.0f}–${max(all_prices):.0f} | ")
                    f.write(f"**Promedio:** ${sum(all_prices)/len(all_prices):.0f}\n\n")

    return md_file


# ─── Telegram ─────────────────────────────────────────────────────────────────
def send_telegram(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("  ⚠️  Telegram no configurado")
        return
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"},
            timeout=10,
        )
        if r.status_code == 200:
            print("  📬 Telegram ✅")
        else:
            print(f"  ⚠️  Telegram error {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"  ⚠️  Telegram: {e}")


# ─── Telegram: enviar documento .md ──────────────────────────────────────────
def send_telegram_document(md_file: Path):
    """Sube el reporte .md como documento a Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        with open(md_file, "rb") as f:
            r = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument",
                data={
                    "chat_id":  TELEGRAM_CHAT_ID,
                    "caption":  f"📄 <b>Reporte completo</b> — {md_file.name}",
                    "parse_mode": "HTML",
                },
                files={"document": (md_file.name, f, "text/markdown")},
                timeout=30,
            )
        if r.status_code == 200:
            print("  📎 Telegram documento ✅")
        else:
            print(f"  ⚠️  Telegram documento error {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"  ⚠️  Telegram documento: {e}")


# ─── Google Drive: subir archivos ─────────────────────────────────────────────
def get_or_create_drive_folder(service, folder_name: str) -> str:
    """Busca la carpeta en Drive raíz. Si no existe, la crea. Devuelve el ID."""
    # Buscar carpeta existente
    query = (
        f"name='{folder_name}' and "
        f"mimeType='application/vnd.google-apps.folder' and "
        f"'root' in parents and trashed=false"
    )
    results = service.files().list(
        q=query, fields="files(id, name)", pageSize=1
    ).execute()
    files = results.get("files", [])

    if files:
        return files[0]["id"]

    # Crear carpeta
    metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    folder = service.files().create(body=metadata, fields="id").execute()
    print(f"  📁 Carpeta '{folder_name}' creada en Drive")
    return folder["id"]


def upload_to_drive(files_to_upload: list[Path]):
    """Sube archivos a la carpeta scraping_informes en Google Drive."""
    if not GDRIVE_AVAILABLE:
        print("  ⚠️  Google Drive no configurado (falta gdrive_auth.py o token.json)")
        return

    try:
        from googleapiclient.http import MediaFileUpload

        service = get_drive_service()
        folder_id = get_or_create_drive_folder(service, GDRIVE_FOLDER_NAME)

        for file_path in files_to_upload:
            if not file_path.exists():
                print(f"  ⚠️  Archivo no encontrado: {file_path}")
                continue

            # Determinar MIME type
            suffix = file_path.suffix.lower()
            mime_map = {
                ".json": "application/json",
                ".md":   "text/markdown",
                ".csv":  "text/csv",
                ".txt":  "text/plain",
            }
            mime_type = mime_map.get(suffix, "application/octet-stream")

            metadata = {
                "name":    file_path.name,
                "parents": [folder_id],
            }
            media = MediaFileUpload(
                str(file_path), mimetype=mime_type, resumable=True
            )
            uploaded = service.files().create(
                body=metadata, media_body=media, fields="id, name, webViewLink"
            ).execute()

            print(f"  ☁️  Drive ✅ {uploaded['name']}")
            if uploaded.get("webViewLink"):
                print(f"     🔗 {uploaded['webViewLink']}")

    except Exception as e:
        print(f"  ❌ Error subiendo a Drive: {e}")


# ─── Email: enviar reporte completo ──────────────────────────────────────────
def send_email_report(md_file: Path, ts: str, total_projects: int, total_niches: int):
    """
    Envía el reporte completo por email (Gmail SMTP).
    Requiere en .env:
        EMAIL_SENDER       = tu_correo@gmail.com
        EMAIL_APP_PASSWORD = xxxx xxxx xxxx xxxx   (App Password de Google)
        EMAIL_RECIPIENT    = eliutec@gmail.com
    """
    if not EMAIL_SENDER or not EMAIL_APP_PASSWORD:
        print("  ⚠️  Email no configurado (EMAIL_SENDER / EMAIL_APP_PASSWORD en .env)")
        return

    try:
        # Leer contenido del reporte
        md_content = md_file.read_text(encoding="utf-8")

        # Construir el mensaje
        msg = MIMEMultipart("mixed")
        msg["Subject"] = f"📊 Reporte Freelance Intelligence — {ts[:10]}"
        msg["From"]    = EMAIL_SENDER
        msg["To"]      = EMAIL_RECIPIENT

        # Cuerpo del email en texto plano (resumen)
        body = (
            f"Reporte de Inteligencia Freelance\n"
            f"Fecha: {ts}\n\n"
            f"• {total_projects} proyectos analizados en Freelancer.com\n"
            f"• {total_niches} nichos analizados en Fiverr\n\n"
            f"El reporte completo viene adjunto como archivo Markdown (.md).\n"
            f"Puedes abrirlo con cualquier editor o visor Markdown.\n\n"
            f"---\nGenerado automáticamente por el Pipeline de Inteligencia Freelance"
        )
        msg.attach(MIMEText(body, "plain", "utf-8"))

        # Adjunto: el .md completo
        part = MIMEBase("application", "octet-stream")
        part.set_payload(md_file.read_bytes())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f'attachment; filename="{md_file.name}"',
        )
        msg.attach(part)

        # Enviar via Gmail SMTP con TLS
        context = ssl.create_default_context()
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls(context=context)
            server.login(EMAIL_SENDER, EMAIL_APP_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT, msg.as_bytes())

        print(f"  📧 Email enviado → {EMAIL_RECIPIENT} ✅")

    except smtplib.SMTPAuthenticationError:
        print("  ❌ Email: error de autenticación — verifica EMAIL_APP_PASSWORD en .env")
    except Exception as e:
        print(f"  ❌ Email error: {e}")


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"🚀 Pipeline Inteligencia Freelance — Freelancer.com API + Groq AI")
    print(f"📅 {ts}\n")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    freelancer_results  = []
    fiverr_intelligence = []

    # ── FASE 1: Freelancer.com API (datos reales) ──────────────────────────────
    print("━" * 55)
    print("📡 FASE 1: Freelancer.com API — Proyectos reales")
    print("━" * 55)

    for query in SEARCH_QUERIES:
        print(f"\n🔍 Query: '{query}'")

        projects = search_freelancer_projects(query, limit=20)
        print(f"  📄 {len(projects)} proyectos encontrados")

        analysis = {}
        if projects:
            print(f"  🤖 Analizando con Groq...")
            analysis = analyze_freelancer_data(projects, query)
            if analysis:
                print(
                    f"  ✅ Demanda: {analysis.get('demanda','?')} | "
                    f"Precio: ${analysis.get('precio_min_usd','?')}–${analysis.get('precio_max_usd','?')} | "
                    f"Entrada: {analysis.get('oportunidad_entrada','?')}"
                )
            else:
                print("  ⚠️  Groq no devolvió análisis")
        else:
            print("  ⚠️  Sin proyectos — skip")

        freelancer_results.append({
            "query":    query,
            "projects": projects,
            "analysis": analysis,
        })

        time.sleep(random.uniform(3, 6))

    # ── FASE 2: Inteligencia Fiverr via Groq (sin scraping) ────────────────────
    print("\n")
    print("━" * 55)
    print("🎯 FASE 2: Inteligencia de mercado Fiverr via Groq AI")
    print("━" * 55)

    for niche in FIVERR_NICHES:
        print(f"\n🎯 Nicho: '{niche}'")
        intel = get_fiverr_intelligence(niche)

        if intel:
            print(
                f"  ✅ Precio: ${intel.get('precio_basico_usd','?')}–${intel.get('precio_premium_usd','?')} | "
                f"Competencia: {intel.get('competencia','?')} | "
                f"Tendencia: {intel.get('tendencia_2025','?')}"
            )
        else:
            print("  ⚠️  Sin datos")

        fiverr_intelligence.append(intel)
        time.sleep(random.uniform(2, 4))

    # ── FASE 3: Scraping real de Fiverr via DuckDuckGo ─────────────────────────
    fiverr_real = {}
    ddg_worked = False
    if DDG_AVAILABLE:
        print("\n")
        print("━" * 55)
        print("🕵️ FASE 3: Fiverr Real Scraping via DuckDuckGo")
        print("━" * 55)
        fiverr_real, ddg_worked = scrape_fiverr_niches(delay=3.0)
        if ddg_worked:
            real_summary = summarize_fiverr_real(fiverr_real)
            total_gigs = sum(s["gigs_found"] for s in real_summary)
            print(f"\n  📊 Total: {total_gigs} gigs reales encontrados")
        else:
            print("\n  ⚠️  DDG bloqueado — usando solo Groq AI")
    else:
        print("\n  ⚠️  fiverr_ddg_scraper no disponible — skip FASE 3")

    # ── EXPORTAR ───────────────────────────────────────────────────────────────
    print("\n")
    print("━" * 55)
    print("📊 Generando reporte...")
    print("━" * 55)

    # JSON completo
    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M')
    json_file = OUTPUT_DIR / f"inteligencia_{timestamp}.json"
    export_data = {
        "freelancer": freelancer_results,
        "fiverr_groq": fiverr_intelligence,
    }
    if fiverr_real:
        export_data["fiverr_real"] = {
            k: [{"title": g["title"], "url": g["url"], "prices": g["prices"],
                 "delivery": g["delivery"], "rating": g["rating"]}
                for g in v]
            for k, v in fiverr_real.items()
        }
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    print(f"  💾 JSON → {json_file}")

    # Markdown
    md_file = generate_report(ts, freelancer_results, fiverr_intelligence, OUTPUT_DIR, fiverr_real)
    print(f"  📝 Markdown → {md_file}")

    # ── Telegram resumen ───────────────────────────────────────────────────────
    total_projects = sum(len(r["projects"]) for r in freelancer_results)

    msg = (
        f"📊 <b>Reporte Diario — Freelance Intelligence</b>\n"
        f"🕐 {ts}\n\n"
        f"✅ <b>{total_projects} proyectos</b> analizados en Freelancer.com\n"
        f"🎯 <b>{len(fiverr_intelligence)} nichos</b> analizados en Fiverr\n\n"
        f"<b>Top insights Freelancer:</b>\n"
    )

    for r in freelancer_results[:4]:
        a = r.get("analysis", {})
        if a:
            msg += (
                f"• <b>{r['query']}</b> — "
                f"${a.get('precio_min_usd','?')}–${a.get('precio_max_usd','?')} | "
                f"{a.get('demanda','?')} demanda\n"
            )

    msg += "\n<b>Top insights Fiverr:</b>\n"
    for intel in fiverr_intelligence[:4]:
        if intel:
            msg += (
                f"• <b>{intel.get('nicho','?')}</b> — "
                f"${intel.get('precio_basico_usd','?')}–${intel.get('precio_premium_usd','?')} | "
                f"{intel.get('competencia','?')} competencia | "
                f"{intel.get('tendencia_2025','?')}\n"
            )

    send_telegram(msg)

    # Enviar reporte completo (.md) como documento a Telegram
    send_telegram_document(md_file)

    # Enviar reporte completo por email
    send_email_report(md_file, ts, total_projects, len(fiverr_intelligence))

    # ── Subir a Google Drive ───────────────────────────────────────────────────
    print("\n  ☁️  Subiendo a Google Drive...")
    upload_to_drive([md_file, json_file])

    print(f"\n🏁 Pipeline completado. Reporte en: {md_file}\n")


if __name__ == "__main__":
    main()
