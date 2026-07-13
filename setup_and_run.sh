#!/bin/bash

# ============================================================
# E-Ombor Platform — To'liq ishga tushirish skripti
# ============================================================
# Foydalanish:
#   chmod +x setup_and_run.sh
#   ./setup_and_run.sh
#
# Yoki faqat backend/frontend:
#   ./setup_and_run.sh backend
#   ./setup_and_run.sh frontend
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
FRONTEND_DIR="$PROJECT_DIR/frontend"
PID_FILE_BACKEND="$PROJECT_DIR/.pids/backend.pid"
PID_FILE_FRONTEND="$PROJECT_DIR/.pids/frontend.pid"
LOG_BACKEND="$PROJECT_DIR/logs/backend.log"
LOG_FRONTEND="$PROJECT_DIR/logs/frontend.log"
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
        log_info "  DRF Swagger: http://localhost:${BACKEND_PORT}/api/schema/swagger-ui/"
        log_info "  Admin panel: http://localhost:${BACKEND_PORT}/admin/"
    else
        log_error "Backend ishga tushmadi. Log: $LOG_BACKEND"
        return 1
    fi
}

# ============================================================
# FRONTEND — O'rnatish va ishga tushirish
# ============================================================

setup_frontend() {
    echo ""
    echo -e "${CYAN}════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  ⚙️  Frontend tayyorlash bosqichi${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════${NC}"
    echo ""

    cd "$FRONTEND_DIR"

    # Node.js tekshirish
    check_command node || return 1
    check_command npm || return 1

    # Bog'liqliklarni o'rnatish
    if [ -d "node_modules" ]; then
        log_ok "node_modules allaqachon mavjud."
    else
        log_info "Bog'liqliklar o'rnatilmoqda..."
        npm install
        log_ok "Bog'liqliklar o'rnatildi."
    fi

    log_ok "Frontend tayyor."
}

run_frontend() {
    ensure_dirs

    if is_frontend_running; then
        log_warn "Frontend allaqachon ishlayapti (PID: $(cat "$PID_FILE_FRONTEND"))."
        return 0
    fi

    cd "$FRONTEND_DIR"

    log_info "Frontend ishga tushirilmoqda... http://localhost:5173"
    npm run dev >> "$LOG_FRONTEND" 2>&1 &
    echo $! > "$PID_FILE_FRONTEND"

    # Server tayyorligini kutish
    sleep 4
    if is_frontend_running; then
        log_ok "Frontend ishga tushdi: http://localhost:5173"
    else
        log_error "Frontend ishga tushmadi. Log: $LOG_FRONTEND"
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

stop_frontend() {
    if is_frontend_running; then
        local pid=$(cat "$PID_FILE_FRONTEND")
        log_info "Frontend to'xtatilmoqda (PID: $pid)..."
        kill "$pid" 2>/dev/null || true
        rm -f "$PID_FILE_FRONTEND"
        log_ok "Frontend to'xtatildi."
    else
        log_warn "Frontend ishlamayapti."
    fi
}

stop_all() {
    log_info "Barcha xizmatlar to'xtatilmoqda..."
    stop_backend
    stop_frontend
    log_ok "Barcha xizmatlar to'xtatildi."
}

status_all() {
    echo ""
    echo -e "${CYAN}════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  📊 E-Ombor — Holat${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════${NC}"
    echo ""

    if is_backend_running; then
        log_ok "Backend:  Ishlayapti (PID: $(cat "$PID_FILE_BACKEND")) — http://localhost:${BACKEND_PORT}"
    else
        log_error "Backend:  Ishlamayapti"
    fi

    if is_frontend_running; then
        log_ok "Frontend: Ishlayapti (PID: $(cat "$PID_FILE_FRONTEND")) — http://localhost:5173"
    else
        log_error "Frontend: Ishlamayapti"
    fi
    echo ""
}

# ============================================================
# TEKSHIRUVLAR
# ============================================================

is_backend_running() {
    [ -f "$PID_FILE_BACKEND" ] && kill -0 "$(cat "$PID_FILE_BACKEND")" 2>/dev/null
}

is_frontend_running() {
    [ -f "$PID_FILE_FRONTEND" ] && kill -0 "$(cat "$PID_FILE_FRONTEND")" 2>/dev/null
}

# ============================================================
# ASOSIY MANTIQ
# ============================================================

print_usage() {
    echo ""
    echo -e "${CYAN}E-Ombor Platform — Boshqaruv skripti${NC}"
    echo ""
    echo "  Foydalanish: $0 [buyruq]"
    echo ""
    echo "  Buyruqlar:"
    echo "    setup     — Backend va frontend tayyorlash (o'rnatish)"
    echo "    run       — Backend va frontend ishga tushirish"
    echo "    all       — Setup + Run (hammasi birga)"
    echo "    backend   — Faqat backend (setup + run)"
    echo "    frontend  — Faqat frontend (setup + run)"
    echo "    stop      — Barcha xizmatlarni to'xtatish"
    echo "    status    — Holatni ko'rsatish"
    echo "    logs      — Loglarni ko'rsatish"
    echo "    clean     — Virtual muhit va node_modulesni o'chirish"
    echo ""
}

case "${1}" in
    setup)
        setup_backend
        setup_frontend
        ;;
    run)
        run_backend
        run_frontend
        ;;
    all)
        setup_backend
        setup_frontend
        run_backend
        run_frontend
        ;;
    backend)
        setup_backend
        run_backend
        ;;
    frontend)
        setup_frontend
        run_frontend
        ;;
    stop)
        stop_all
        ;;
    status)
        status_all
        ;;
    logs)
        echo ""
        echo -e "${CYAN}--- Backend log (oxirgi 30 qator) ---${NC}"
        tail -n 30 "$LOG_BACKEND" 2>/dev/null || echo "Log topilmadi."
        echo ""
        echo -e "${CYAN}--- Frontend log (oxirgi 30 qator) ---${NC}"
        tail -n 30 "$LOG_FRONTEND" 2>/dev/null || echo "Log topilmadi."
        echo ""
        ;;
    clean)
        log_info "Tozalash boshlandi..."
        rm -rf "$BACKEND_DIR/venv"
        rm -f "$BACKEND_DIR/db.sqlite3"
        rm -rf "$FRONTEND_DIR/node_modules"
        rm -rf "$PROJECT_DIR/.pids"
        rm -rf "$PROJECT_DIR/logs"
        log_ok "Tozalash tugallandi."
        ;;
    *)
        print_usage
        ;;
esac
