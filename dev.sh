#!/bin/bash
# Local dev menu. Run from the repo root:  ./dev.sh
PORT=8502
CONTAINER=case_study_dashboard
G='\033[0;32m'; R='\033[0;31m'; B='\033[0;34m'; N='\033[0m'

is_running() { docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; }

sync() {
  is_running || { echo -e "${R}Container not running${N}"; return 1; }
  for d in sections utils queries onepager .streamlit; do [ -d "$d" ] && docker cp "$d/." "${CONTAINER}:/app/$d/"; done
  for f in *.py requirements*.txt; do [ -f "$f" ] && docker cp "$f" "${CONTAINER}:/app/$f"; done
  echo -e "${G}Synced${N}"
}

export_text() {
  docker exec ${CONTAINER} env DASHBOARD_URL=http://localhost:8501 python utils/export_dashboard_text.py \
    && docker exec ${CONTAINER} python utils/audit_export.py
}

while true; do
  echo ""; is_running && echo -e "Status: ${G}running${N} -> http://localhost:${PORT}" || echo -e "Status: ${R}stopped${N}"
  echo "1) Start   2) Stop   3) Reload (sync+restart)   4) Rebuild   5) Logs"
  echo "6) Shell   7) Run query blocks   t) Text export + audit   0) Exit"
  read -p "Choose: " c
  case $c in
    1) docker compose up -d && echo -e "${G}http://localhost:${PORT}${N}" ;;
    2) docker compose down ;;
    3) sync && docker compose restart ;;
    4) docker compose build --no-cache ;;
    5) docker compose logs -f ;;
    6) sync && docker exec -it ${CONTAINER} /bin/bash ;;
    7) docker exec -it ${CONTAINER} python queries/runner.py --list
       read -p "Block (empty = all): " q
       docker exec -it ${CONTAINER} python queries/runner.py $q ;;
    t|T) export_text ;;
    0) exit 0 ;;
  esac
done
