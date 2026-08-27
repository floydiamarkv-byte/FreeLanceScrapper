<div align="center">

![FreeLanceScrapper banner](assets/banner.png)

</div>

# FreeLanceScrapper

**AI-Powered Freelance Market Intelligence Pipeline**

Automated competitive analysis system that scrapes real-time project data from Freelancer.com, analyzes it with Groq LLM, and delivers structured market intelligence reports via Telegram, Email, and Google Drive.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![Groq](https://img.shields.io/badge/AI-Groq%20LLM-orange)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🔥 What It Does

This pipeline runs daily (via `cron`) on a Proxmox LXC container and:

1. **Scrapes** 140+ active projects from Freelancer.com API across 10 technical niches
2. **Analyzes** market demand, pricing, and competition using Groq LLM (Llama 3.3 70B)
3. **Generates** structured Markdown + JSON reports with actionable insights
4. **Delivers** reports automatically via:
   - 📬 Telegram Bot (summary + full report as document)
   - 📧 Gmail (SMTP with attachment)
   - ☁️ Google Drive (auto-upload to shared folder)

## 📊 Niches Monitored

| # | Niche | Data Source |
|---|-------|-------------|
| 1 | Proxmox VPS/Homelab Setup | Freelancer API + Groq |
| 2 | Home Assistant Smart Home | Freelancer API + Groq |
| 3 | WordPress + Elementor | Freelancer API + Groq |
| 4 | Python Automation & Scraping | Freelancer API + Groq |
| 5 | Ollama/LLM AI Server Setup | Freelancer API + Groq |
| 6 | Mikrotik/Fortigate Firewall | Freelancer API + Groq |
| 7 | Hikvision/Dahua CCTV | Freelancer API + Groq |
| 8 | ESP32/Arduino IoT Firmware | Freelancer API + Groq |
| 9 | Technical SEO + Google Ads | Freelancer API + Groq |
| 10 | Docker/DevOps CI/CD | Freelancer API + Groq |

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│ Freelancer.com  │────▶│  Groq LLM    │────▶│  Markdown   │
│   Public API    │     │ (Llama 3.3)  │     │  + JSON     │
└─────────────────┘     └──────────────┘     │  Reports    │
                                              └──────┬──────┘
                                                     │
                              ┌───────────────────────┼───────────────────┐
                              ▼                       ▼                   ▼
                        ┌───────────┐          ┌───────────┐       ┌──────────┐
                        │ Telegram  │          │   Gmail   │       │  Google  │
                        │   Bot     │          │   SMTP    │       │  Drive   │
                        └───────────┘          └───────────┘       └──────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- [Groq API Key](https://console.groq.com/) (free tier available)
- Telegram Bot Token (optional)
- Gmail App Password (optional)
- Google Drive API credentials (optional)

### Installation

```bash
git clone https://github.com/floydiamarkv-byte/FreeLanceScrapper.git
cd FreeLanceScrapper
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
```

### Configuration

Edit `.env` with your credentials:

```env
GROQ_API_KEY=gsk_your_key_here
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
EMAIL_SENDER=your_email@gmail.com
EMAIL_APP_PASSWORD=your_app_password
EMAIL_RECIPIENT=destination@email.com
```

### Run

```bash
python scraper_sgai.py
```

### Cron (Daily Automation)

```bash
# Run daily at 7:00 AM
0 7 * * * cd /path/to/FreeLanceScrapper && /usr/bin/python3 scraper_sgai.py >> scraper.log 2>&1
```

## 📁 Project Structure

```
FreeLanceScrapper/
├── scraper_sgai.py          # Main pipeline (Freelancer API + Groq AI)
├── fiverr_ddg_scraper.py    # Optional: Fiverr gig scraping via DuckDuckGo
├── gdrive_auth.py           # Google Drive authentication helper
├── run_scraper.sh           # Bash wrapper for cron execution
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
├── data/
│   └── scraping/            # Generated reports (Markdown + JSON)
└── README.md
```

## 📋 Sample Output

Each report includes:

- **Market demand** per niche (High/Medium/Low)
- **Price ranges** (min/avg/max in USD)
- **Top skills** in demand
- **Entry difficulty** for new freelancers
- **Positioning advice** from AI analysis
- **Trending niches** for 2025-2026

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.11+ |
| AI Engine | Groq API (Llama 3.3 70B Versatile) |
| Data Source | Freelancer.com Public API |
| Messaging | Telegram Bot API |
| Email | Gmail SMTP (TLS) |
| Cloud Storage | Google Drive API v3 |
| Hosting | Proxmox LXC Container |
| Scheduling | cron |

## 👤 Author

**Floydia / Eliú Hurtado** — Senior Infrastructure & Automation Engineer

- 25+ years in IT infrastructure, network security, and automation
- [GitHub](https://github.com/floydiamarkv-byte)
- [LinkedIn](https://linkedin.com/in/eliutec)

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
