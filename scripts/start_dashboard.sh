#!/usr/bin/env bash
# Lança o dashboard Streamlit em background de forma persistente.
# Chamado automaticamente pelo devcontainer postStartCommand.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PID_FILE="$PROJECT_DIR/.streamlit_pid"
LOG_FILE="/tmp/signal_hunter_dashboard.log"

# Mata instância anterior se existir
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        kill "$OLD_PID" && echo "[dashboard] processo anterior ($OLD_PID) terminado"
    fi
    rm -f "$PID_FILE"
fi

# Instalar dependências silenciosamente se alguma faltar
cd "$PROJECT_DIR"
pip install -r requirements.txt -q

# Lançar Streamlit em background
nohup streamlit run dashboard/app.py \
    --server.port 8501 \
    --server.headless true \
    --server.address 0.0.0.0 \
    --server.enableCORS false \
    --server.enableXsrfProtection false \
    > "$LOG_FILE" 2>&1 &

echo $! > "$PID_FILE"
echo "[dashboard] iniciado (PID $(cat $PID_FILE)) → porta 8501"

# Aguardar servidor arrancar e forçar porta pública
sleep 6
if gh codespace ports visibility 8501:public -c "${CODESPACE_NAME:-}" 2>/dev/null; then
    echo "[dashboard] porta 8501 → public ✓"
else
    echo "[dashboard] aviso: não foi possível forçar porta pública (normal em rebuild)"
fi

echo "[dashboard] URL: https://${CODESPACE_NAME:-localhost}-8501.app.github.dev"
echo "[dashboard] logs em $LOG_FILE"
