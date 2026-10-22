<div align="center">

![FreeLanceScrapper banner](assets/banner.png)

# ⚡ FreeLanceScrapper

[![CI](https://github.com/floydiamarkv-byte/FreeLanceScrapper/actions/workflows/ci.yml/badge.svg)](https://github.com/floydiamarkv-byte/FreeLanceScrapper/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
### **Autonomous AI-Powered Market Intelligence & Gig Positioning Pipeline**

[![Floydia Project](https://img.shields.io/badge/Powered%20By-Floydia-10D2AD.svg?style=for-the-badge&logo=crystal&logoColor=white&labelColor=0B111C)](https://floydia.site)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white&labelColor=0B111C)](https://python.org)
[![Groq Llama 3.3](https://img.shields.io/badge/AI%20Engine-Groq%20Llama%203.3%2070B-F55036?style=for-the-badge&logo=groq&logoColor=white&labelColor=0B111C)](https://groq.com)
[![Proxmox Ready](https://img.shields.io/badge/Infrastructure-Proxmox%20LXC-E57000?style=for-the-badge&logo=proxmox&logoColor=white&labelColor=0B111C)](https://proxmox.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-70CBAC?style=for-the-badge&labelColor=0B111C)](LICENSE)

<br/>

> **"Stop bidding blind. Let deterministic scraping and real-time LLM intelligence pinpoint where the highest margins and lowest competition are, every single morning."**

[🚀 Quick Start](#-quick-start) • [🏛️ Architecture](#-architecture--flow) • [📊 Niches Monitored](#-10-technical-niches-monitored) • [📋 Sample Output](#-executive-output-sample) • [🤝 Support](#-author--support)

</div>

---

## 📌 Overview

**FreeLanceScrapper** is an autonomous market intelligence agent designed for software engineers, IT architects, and tech agencies who want an unfair competitive advantage on global freelance platforms.

Instead of spending hours manually browsing listings or undercharging on proposals, FreeLanceScrapper operates as a **24/7 background intelligence officer**:
1. **Pulls Live Market Data**: Scrapes 140+ active projects daily directly from the Freelancer.com API across 10 high-value technical niches.
2. **Runs Deep Strategic Synthesis**: Feeds unstructured client requirements into **Groq's ultralow-latency Llama 3.3 70B Versatile LLM** to quantify pricing tiers, skill scarcity, and proposal win-probability.
3. **Dispatches Multi-Channel Intelligence**: Formats clean executive briefs and structured JSON, dispatching them automatically via Telegram, Email, and Google Drive before your workday starts.

---

## 🏗️ Architecture & Flow

```mermaid
flowchart TD
    subgraph Data Layer
        A[🌐 Freelancer.com API] -->|Raw Projects JSON| B[⚙️ Python Extractor<br/>scraper_sgai.py]
        A2[🔍 DuckDuckGo API] -->|Optional Gigs| B
    end

    subgraph AI Synthesis Engine
        B -->|Curated Structured Batches| C{⚡ Groq LPU Engine<br/>Llama 3.3 70B Versatile}
        C -->|Market Dynamics & Rates| D[📄 Markdown Executive Brief]
        C -->|Raw Intelligence| E[📊 Structured JSON Matrix]
    end

    subgraph Multi-Channel Dispatcher
        D & E --> F[📬 Telegram Bot Channel]
        D & E --> G[📧 Gmail SMTP with Attachments]
        D & E --> H[☁️ Google Drive Archive]
    end

    style A fill:#0B111C,stroke:#10D2AD,color:#fff
    style B fill:#152638,stroke:#10D6BD,color:#fff
    style C fill:#10D2AD,stroke:#0B111C,color:#0B111C
    style D fill:#152638,stroke:#70CBAC,color:#fff
    style E fill:#152638,stroke:#70CBAC,color:#fff
    style F fill:#0B111C,stroke:#10D2AD,color:#fff
    style G fill:#0B111C,stroke:#10D6BD,color:#fff
    style H fill:#0B111C,stroke:#70CBAC,color:#fff
```

---

## 📊 10 Technical Niches Monitored

| # | Niche | Focus & Scraped Parameters |
|---|-------|---------------------------|
| 1 | **Proxmox VPS / Homelab** | Enterprise virtualization, LXC/KVM, clustering & backup storage |
| 2 | **Home Assistant & IoT** | Zigbee/Z-Wave, MQTT brokers, dashboard design & automations |
| 3 | **WordPress & Elementor** | Flexbox containers, speed optimization, custom PHP & landing pages |
| 4 | **Python Automation** | Web scrapers, cron automation, API integrations & data parsers |
| 5 | **Local AI & LLM Servers** | Ollama, vLLM, private OpenAI-compatible API gateways |
| 6 | **MikroTik & Network Firewalls** | WireGuard VPN, VLAN segregation, BGP routing, security audits |
| 7 | **CCTV & Security Systems** | Hikvision, Dahua, RTSP streams, NVR remote integrations |
| 8 | **Embedded IoT Firmware** | ESP32, Arduino, sensor telemetry & low-power communications |
| 9 | **Technical SEO & Growth** | Schema markup, Core Web Vitals, conversion tracking |
| 10 | **DevOps & Docker CI/CD** | GitHub Actions, container orchestration, reverse proxies |

---

## 🚀 Quick Start

### 1. Clone & Install
```bash
git clone https://github.com/floydiamarkv-byte/FreeLanceScrapper.git
cd FreeLanceScrapper
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
```

Fill in your API keys in `.env`:
```env
# Required: Groq AI Engine (Free tier available at console.groq.com)
GROQ_API_KEY=gsk_your_groq_api_key_here

# Optional: Telegram Notifications
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Optional: Email SMTP Reports
EMAIL_SENDER=your_email@gmail.com
EMAIL_APP_PASSWORD=your_gmail_app_password
EMAIL_RECIPIENT=destination@email.com
```

### 3. Run Extraction
```bash
python scraper_sgai.py
```

### 4. Set Daily Cron (Zero Maintenance)
```bash
# Run automatically every morning at 7:00 AM
0 7 * * * cd /path/to/FreeLanceScrapper && /path/to/.venv/bin/python scraper_sgai.py >> scraper.log 2>&1
```

---

## 📋 Executive Output Sample

Every generated report provides immediate actionable clarity:

```markdown
# 📈 Freelance Market Intelligence — Daily Brief

### 🎯 Key Strategic Findings:
- **Top Paying Niche Today**: Local AI Server Setups ($450 - $1,200/proj)
- **Fastest Proposal Turnaround**: MikroTik WireGuard Deployments (<12h close)
- **High-Demand Scarcity Skills**: vLLM Optimization, Home Assistant Lovelace UI, Custom Crawl4AI scrapers.

### 💡 Suggested Positioning Strategy:
> "Target Proxmox + Docker hybrid setups. Clients are struggling with hardware passthrough and GPU allocation for private Ollama nodes. Emphasize turnkey delivery."
```

---

## 👤 Author & Support

Crafted with precision by **[Floydia](https://floydia.site)** — Led by **Eliú Hurtado** (+25 years in IT infrastructure, network security, and applied AI systems).

* 🌐 **Website**: [https://floydia.site](https://floydia.site)
* 💼 **LinkedIn**: [Eliú Hurtado](https://linkedin.com/in/eliutec)
* 🐛 **Issues & Feedback**: [Open a GitHub Issue](https://github.com/floydiamarkv-byte/FreeLanceScrapper/issues)

---

<div align="center">

Distributed under the [MIT License](LICENSE) • **Desde la infraestructura, todo.**

</div>
