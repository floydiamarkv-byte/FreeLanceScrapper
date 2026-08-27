#!/bin/bash
# ===========================================
# Pipeline Inteligencia Freelance
# Arquitectura: Freelancer.com API + Groq AI
# Ejecuta diariamente via cron a las 8AM
# ===========================================

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$PROJECT_DIR/.venv/bin/python"
LOG="$PROJECT_DIR/scraper.log"

echo '========================================' >> "$LOG"
echo "[$(date)] Iniciando pipeline..." >> "$LOG"

cd "$PROJECT_DIR"

# Asegurar que DISPLAY esté disponible (por si Drive necesita refrescar token)
export DISPLAY=:0

"$VENV" scraper_sgai.py >> "$LOG" 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date)] Pipeline completado OK." >> "$LOG"
else
    echo "[$(date)] ERROR: Pipeline falló (exit $EXIT_CODE)" >> "$LOG"
fi

echo '========================================' >> "$LOG"
