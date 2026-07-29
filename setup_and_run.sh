#!/bin/bash

# ============================================================
# E-Ombor Backend — Ishga tushirish skripti
# ============================================================
# Foydalanish:
#   chmod +x setup_and_run.sh
#   ./setup_and_run.sh
#
#   ./setup_and_run.sh backend
#   ./setup_and_run.sh stop
#   ./setup_and_run.sh status
# ============================================================

set -e

# --- Ranglar va belgilar ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
CHECK='\033[0;32m[✓]\033[0m'
WARN='\033[1;33m[!]\033[0m'
INFO='\033[0;36m[i]\033[0m'

# --- O'zgaruvchilar ---
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
PID_FILE_BACKEND="$PROJECT_DIR/.pids/backend.pid"
LOG_BACKEND="$PROJECT_DIR/logs/backend.log"
BACKEND_PORT=3000
BACKEND_PYTHON="$BACKEND_DIR/venv/bin/python"
BACKEND_PIP="$BACKEND_DIR/venv/bin/pip"

# ============================================================
# YORDAMCHI FUNKSIYALAR
# ============================================================

log_info()  { echo -e "${INFO} $1"; }
log_ok()    { echo -e "${CHECK} $1"; }
log_warn()  { echo -e "${WARN} $1"; }
log_error() { echo -e "${RED}✗ $1${NC}" >&2; }

ensure_dirs() {
    mkdir -p "$PROJECT_DIR/.pids"
    mkdir -p "$PROJECT_DIR/logs"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 topilmadi. Iltimos, o'rnating."
        return 1
    fi
    return 0
}

# ============================================================
# BACKEND — O'rnatish va ishga tushirish
# ============================================================

setup_backend() {
    echo ""
    echo -e "${CYAN}════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  ⚙️  Backend tayyorlash bosqichi${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════${NC}"
    echo ""

    cd "$BACKEND_DIR"

    # Python tekshirish
    check_command python3 || return 1

    # Virtual muhit
    if [ ! -d "venv" ]; then
        log_info "Virtual muhit yaratilmoqda..."
        python3 -m venv venv
        log_ok "Virtual muhit yaratildi."
    else
        log_ok "Virtual muhit allaqachon mavjud."
    fi

    # Virtual muhitni yoqish
    source venv/bin/activate

    # Venv ichidagi interpreter va pip dan foydalanamiz
    BACKEND_PYTHON="$BACKEND_DIR/venv/bin/python"
    BACKEND_PIP="$BACKEND_DIR/venv/bin/pip"

    # Pip yangilash
    log_info "Pip yangilanmoqda..."
    "$BACKEND_PIP" install --upgrade pip -q

    # Bog'liqliklarni o'rnatish
    log_info "Bog'liqliklar o'rnatilmoqda..."
    "$BACKEND_PIP" install -r requirements.txt -q
    log_ok "Bog'liqliklar o'rnatildi."

    # .env fayli mavjudligini tekshirish
    if [ ! -f ".env" ]; then
        log_warn ".env fayli topilmadi. Namuna yaratilmoqda..."
        cat > .env << 'EOF'
DEBUG=True
SECRET_KEY=django-insecure-eombor-dev-secret-key-change-in-production
DB_NAME=eombor
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
EOF
        log_ok ".env fayli yaratildi. Sozlamalarni o'zgartiring."
    fi

    # Ma'lumotlar bazasi migratsiyasi
    log_info "Ma'lumotlar bazasi migratsiya qilinmoqda..."
    "$BACKEND_PYTHON" manage.py makemigrations api 2>/dev/null || true
    "$BACKEND_PYTHON" manage.py migrate
    log_ok "Ma'lumotlar bazasi tayyor."

    # Demo ma'lumotlar va loginlar
    log_info "Demo ma'lumotlar yaratilmoqda..."
    "$BACKEND_PYTHON" manage.py seed_demo_data
    log_ok "Demo ma'lumotlar tayyor."

    log_ok "Backend tayyor."
}

run_backend() {
    ensure_dirs

    if is_backend_running; then
        log_warn "Backend allaqachon ishlayapti (PID: $(cat "$PID_FILE_BACKEND"))."
        return 0
    fi

    cd "$BACKEND_DIR"
    source venv/bin/activate

    log_info "Backend ishga tushirilmoqda... http://localhost:${BACKEND_PORT}"
    "$BACKEND_PYTHON" manage.py runserver 0.0.0.0:${BACKEND_PORT} >> "$LOG_BACKEND" 2>&1 &
    echo $! > "$PID_FILE_BACKEND"

    # Server tayyorligini kutish
    sleep 3
    if is_backend_running; then
        log_ok "Backend ishga tushdi: http://localhost:${BACKEND_PORT}"
        log_info "  DRF Swagger: http://localhost:${BACKEND_PORT}/api/docs/"
        log_info "  Admin panel: http://localhost:${BACKEND_PORT}/admin/"
    else
        log_error "Backend ishga tushmadi. Log: $LOG_BACKEND"
        return 1
    fi
}

# ============================================================
# TO'XTATISH VA HOLAT
# ============================================================

stop_backend() {
    if is_backend_running; then
        local pid=$(cat "$PID_FILE_BACKEND")
        log_info "Backend to'xtatilmoqda (PID: $pid)..."
        kill "$pid" 2>/dev/null || true
        rm -f "$PID_FILE_BACKEND"
        log_ok "Backend to'xtatildi."
    else
        log_warn "Backend ishlamayapti."
    fi
}

status_all() {
    echo ""
    echo -e "${CYAN}════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  📊 E-Ombor Backend — Holat${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════${NC}"
    echo ""

    if is_backend_running; then
        log_ok "Backend:  Ishlayapti (PID: $(cat "$PID_FILE_BACKEND")) — http://localhost:${BACKEND_PORT}"
    else
        log_error "Backend:  Ishlamayapti"
    fi
    echo ""
}

# ============================================================
# TEKSHIRUVLAR
# ============================================================

is_backend_running() {
    [ -f "$PID_FILE_BACKEND" ] && kill -0 "$(cat "$PID_FILE_BACKEND")" 2>/dev/null
}

# ============================================================
# ASOSIY MANTIQ
# ============================================================

print_usage() {
    echo ""
    echo -e "${CYAN}E-Ombor Backend — Boshqaruv skripti${NC}"
    echo ""
    echo "  Foydalanish: $0 [buyruq]"
    echo ""
    echo "  Buyruqlar:"
    echo "    setup     — Backend tayyorlash (o'rnatish)"
    echo "    run       — Backend ishga tushirish"
    echo "    all       — Setup + Run (hammasi birga)"
    echo "    backend   — Setup + Run (setup dan alias)"
    echo "    stop      — Backendni to'xtatish"
    echo "    status    — Holatni ko'rsatish"
    echo "    logs      — Loglarni ko'rsatish"
    echo "    clean     — Virtual muhitni o'chirish"
    echo ""
}

case "${1}" in
    setup)
        setup_backend
        ;;
    run)
        run_backend
        ;;
    all|backend)
        setup_backend
        run_backend
        ;;
    stop)
        stop_backend
        ;;
    status)
        status_all
        ;;
    logs)
        echo ""
        echo -e "${CYAN}--- Backend log (oxirgi 30 qator) ---${NC}"
        tail -n 30 "$LOG_BACKEND" 2>/dev/null || echo "Log topilmadi."
        echo ""
        ;;
    clean)
        log_info "Tozalash boshlandi..."
        rm -rf "$BACKEND_DIR/venv"
        rm -f "$BACKEND_DIR/db.sqlite3"
        rm -rf "$PROJECT_DIR/.pids"
        rm -rf "$PROJECT_DIR/logs"
        log_ok "Tozalash tugallandi."
        ;;
    *)
        print_usage
        ;;
esac
