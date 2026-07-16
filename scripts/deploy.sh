#!/bin/bash
# ═══════════════════════════════════════════════════════════
# Fetal Medical System - Automated Deployment Script
# ═══════════════════════════════════════════════════════════
#
# Usage: sudo bash deploy.sh
#
# This script automates the full deployment of the Fetal Medical
# System on an Ubuntu/Debian server using Docker Compose.
#
# Prerequisites:
#   - Ubuntu 22.04+ or Debian 12+
#   - Run as root (sudo)
#   - Internet connection
#   - Repository cloned to current directory
#
# What it does:
#   1. Checks prerequisites (OS, RAM, disk, software)
#   2. Installs missing dependencies
#   3. Configures environment variables
#   4. Builds Docker images
#   5. Starts all services
#   6. Runs database migrations
#   7. Collects static files
#   8. Runs health checks
#   9. Prints deployment summary
# ═══════════════════════════════════════════════════════════

set -euo pipefail

# ─── Colors and Formatting ───
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ─── Logging ───
LOG_FILE="deploy_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

# ─── Configuration ───
APP_NAME="Fetal Medical System"
BACKEND_DIR="Backend"
COMPOSE_FILE="docker-compose.yml"
REQUIRED_PYTHON_VERSION="3.11"
REQUIRED_NODE_VERSION="18"
MIN_RAM_MB=3800    # ~4GB
MIN_DISK_MB=20000  # ~20GB

# ═══════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo ""
    echo -e "${BOLD}${CYAN}══ $1 ══${NC}"
    echo ""
}

check_exit_code() {
    if [ $? -eq 0 ]; then
        log_success "$1"
        return 0
    else
        log_error "$1"
        return 1
    fi
}

# ═══════════════════════════════════════════════════════════
# BANNER
# ═══════════════════════════════════════════════════════════

print_banner() {
    echo ""
    echo -e "${BOLD}${CYAN}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║                                                          ║"
    echo "║       FETAL MEDICAL SYSTEM - DEPLOYMENT SCRIPT           ║"
    echo "║                                                          ║"
    echo "║       Automated Production Deployment                    ║"
    echo "║       Version 1.0.0                                      ║"
    echo "║       $(date '+%Y-%m-%d %H:%M:%S')                            ║"
    echo "║                                                          ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# ═══════════════════════════════════════════════════════════
# PREREQUISITE CHECKS
# ═══════════════════════════════════════════════════════════

check_os() {
    log_step "Checking Operating System"

    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS_NAME="${NAME}"
        OS_VERSION="${VERSION_ID}"
        log_info "OS: ${OS_NAME} ${OS_VERSION}"

        if [[ "$ID" != "ubuntu" && "$ID" != "debian" ]]; then
            log_warn "This script is optimized for Ubuntu/Debian. Continuing anyway..."
        fi
    else
        log_error "Cannot determine OS. This script requires Linux (Ubuntu/Debian)."
        exit 1
    fi
}

check_ram() {
    log_info "Checking RAM..."
    TOTAL_RAM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    TOTAL_RAM_MB=$((TOTAL_RAM_KB / 1024))

    if [ "$TOTAL_RAM_MB" -ge "$MIN_RAM_MB" ]; then
        log_success "RAM: ${TOTAL_RAM_MB} MB (minimum: ${MIN_RAM_MB} MB)"
    else
        log_error "Insufficient RAM: ${TOTAL_RAM_MB} MB (minimum: ${MIN_RAM_MB} MB)"
        exit 1
    fi
}

check_disk() {
    log_info "Checking disk space..."
    AVAILABLE_DISK_MB=$(df -m / | awk 'NR==2 {print $4}')

    if [ "$AVAILABLE_DISK_MB" -ge "$MIN_DISK_MB" ]; then
        log_success "Available disk: ${AVAILABLE_DISK_MB} MB (minimum: ${MIN_DISK_MB} MB)"
    else
        log_error "Insufficient disk space: ${AVAILABLE_DISK_MB} MB (minimum: ${MIN_DISK_MB} MB)"
        exit 1
    fi
}

check_root() {
    log_step "Checking Permissions"

    if [ "$EUID" -ne 0 ]; then
        log_error "This script must be run as root (use sudo)"
        echo "Usage: sudo bash deploy.sh"
        exit 1
    fi
    log_success "Running as root"
}

check_directory() {
    log_step "Checking Project Directory"

    if [ ! -d "$BACKEND_DIR" ]; then
        log_error "Backend directory not found: $BACKEND_DIR"
        log_error "Please run this script from the project root directory"
        exit 1
    fi
    log_success "Backend directory found: $BACKEND_DIR"

    if [ ! -f "$BACKEND_DIR/docker-compose.yml" ] && [ ! -f "$BACKEND_DIR/$COMPOSE_FILE" ]; then
        # Check if we're already inside Backend
        if [ -f "$COMPOSE_FILE" ]; then
            BACKEND_DIR="."
            log_info "Running from within Backend directory"
        else
            log_error "docker-compose.yml not found"
            exit 1
        fi
    fi
}

# ═══════════════════════════════════════════════════════════
# SOFTWARE INSTALLATION
# ═══════════════════════════════════════════════════════════

install_docker() {
    log_step "Installing Docker"

    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version)
        log_success "Docker already installed: $DOCKER_VERSION"
        return 0
    fi

    log_info "Installing Docker..."
    apt-get update -qq
    apt-get install -y -qq ca-certificates curl gnupg lsb-release > /dev/null 2>&1

    # Add Docker GPG key
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc 2>/dev/null || \
    curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc 2>/dev/null || \
    { log_error "Failed to download Docker GPG key"; return 1; }
    chmod a+r /etc/apt/keyrings/docker.asc

    # Add Docker repository
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null 2>/dev/null || \
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
        $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null 2>/dev/null

    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin > /dev/null 2>&1

    if command -v docker &> /dev/null; then
        log_success "Docker installed: $(docker --version)"
    else
        log_error "Docker installation failed"
        return 1
    fi
}

install_dependencies() {
    log_step "Installing System Dependencies"

    log_info "Updating package list..."
    apt-get update -qq

    PACKAGES="curl git openssl"
    for pkg in $PACKAGES; do
        if dpkg -s "$pkg" &> /dev/null; then
            log_success "$pkg already installed"
        else
            log_info "Installing $pkg..."
            apt-get install -y -qq "$pkg" > /dev/null 2>&1
            log_success "$pkg installed"
        fi
    done
}

# ═══════════════════════════════════════════════════════════
# ENVIRONMENT CONFIGURATION
# ═══════════════════════════════════════════════════════════

generate_secret_key() {
    python3 -c "import secrets; print(secrets.token_urlsafe(64))" 2>/dev/null || \
    openssl rand -base64 64
}

generate_password() {
    openssl rand -base64 48
}

configure_environment() {
    log_step "Configuring Environment Variables"

    cd "$BACKEND_DIR"

    ENV_FILE=".env.production"

    if [ -f "$ENV_FILE" ]; then
        log_warn "$ENV_FILE already exists"
        read -p "Overwrite existing $ENV_FILE? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Keeping existing $ENV_FILE"
            cd ..
            return 0
        fi
    fi

    log_info "Generating secure credentials..."

    # Generate values
    SECRET_KEY=$(generate_secret_key)
    DB_PASSWORD=$(generate_password)

    # Prompt for domain
    read -p "Enter your domain name (e.g., fetalmedical.example.com): " DOMAIN
    if [ -z "$DOMAIN" ]; then
        DOMAIN="localhost"
        log_warn "No domain entered, using localhost"
    fi

    # Prompt for email
    read -p "Enter admin email: " ADMIN_EMAIL
    if [ -z "$ADMIN_EMAIL" ]; then
        ADMIN_EMAIL="admin@localhost"
        log_warn "No email entered, using $ADMIN_EMAIL"
    fi

    # Prompt for database name
    read -p "Enter database name [fetal_medical_prod]: " DB_NAME
    DB_NAME=${DB_NAME:-fetal_medical_prod}

    # Prompt for database user
    read -p "Enter database user [fetal_admin]: " DB_USER
    DB_USER=${DB_USER:-fetal_admin}

    log_info "Writing $ENV_FILE..."

    cat > "$ENV_FILE" << ENVEOF
# ═══════════════════════════════════════════════════════════
# FETAL MEDICAL SYSTEM - PRODUCTION ENVIRONMENT
# ═══════════════════════════════════════════════════════════
# Generated: $(date '+%Y-%m-%d %H:%M:%S')
# ⚠️  KEEP THIS FILE SECURE - DO NOT COMMIT TO GIT
# ═══════════════════════════════════════════════════════════

# ========== DJANGO SETTINGS ==========
DEBUG=False
SECRET_KEY=${SECRET_KEY}
ALLOWED_HOSTS=${DOMAIN},www.${DOMAIN},localhost

# ========== DATABASE ==========
DB_ENGINE=django.db.backends.postgresql
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
DB_HOST=db
DB_PORT=5432

# ========== CORS AND CSRF ==========
CORS_ALLOWED_ORIGINS=https://${DOMAIN},https://www.${DOMAIN}
CSRF_TRUSTED_ORIGINS=https://${DOMAIN},https://www.${DOMAIN}

# ========== SECURITY ==========
CSRF_COOKIE_SECURE=True
SESSION_COOKIE_SECURE=True
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# ========== EMAIL CONFIGURATION ==========
EMAIL_HOST=smtp.${DOMAIN}
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=notifications@${DOMAIN}
EMAIL_HOST_PASSWORD=CHANGE_THIS_EMAIL_PASSWORD

# ========== MONITORING ==========
LOG_LEVEL=WARNING
SENTRY_DSN=
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1

# ========== AI SERVICE ==========
AI_SERVICE_URL=http://ia_service:8001
AI_SERVICE_TIMEOUT=30

# ========== SESSION ==========
SESSION_COOKIE_AGE=3600
SESSION_EXPIRE_AT_BROWSER_CLOSE=True
ENVEOF

    # Secure the file
    chmod 600 "$ENV_FILE"

    log_success "$ENV_FILE created and secured"
    log_info "IMPORTANT: Update EMAIL_HOST_PASSWORD and SENTRY_DSN manually if needed"

    cd ..
}

# ═══════════════════════════════════════════════════════════
# DOCKER BUILD AND DEPLOY
# ═══════════════════════════════════════════════════════════

build_images() {
    log_step "Building Docker Images"

    cd "$BACKEND_DIR"

    log_info "This may take 10-20 minutes depending on server speed..."
    log_info "Building images..."

    docker compose build --no-cache 2>&1 | tee -a "$LOG_FILE"

    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        log_success "Docker images built successfully"
    else
        log_error "Docker build failed"
        exit 1
    fi

    cd ..
}

start_services() {
    log_step "Starting Services"

    cd "$BACKEND_DIR"

    log_info "Starting all services..."
    docker compose up -d 2>&1 | tee -a "$LOG_FILE"

    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        log_success "Services started"
    else
        log_error "Failed to start services"
        exit 1
    fi

    log_info "Waiting for services to initialize (30 seconds)..."
    for i in $(seq 1 30); do
        echo -ne "${BLUE}.${NC}"
        sleep 1
    done
    echo ""

    # Show running containers
    log_info "Running containers:"
    docker compose ps

    cd ..
}

# ═══════════════════════════════════════════════════════════
# DATABASE INITIALIZATION
# ═══════════════════════════════════════════════════════════

run_migrations() {
    log_step "Running Database Migrations"

    cd "$BACKEND_DIR"

    log_info "Waiting for database to be ready..."
    MAX_RETRIES=30
    RETRY_COUNT=0

    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if docker compose exec -T db pg_isready -q 2>/dev/null; then
            log_success "Database is ready"
            break
        fi
        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo -ne "${BLUE}.${NC}"
        sleep 2
    done
    echo ""

    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        log_error "Database failed to become ready. Check logs:"
        log_error "docker compose logs db"
        exit 1
    fi

    log_info "Running migrations..."
    docker compose exec -T backend python manage.py migrate 2>&1 | tee -a "$LOG_FILE"

    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        log_success "Migrations applied successfully"
    else
        log_error "Migration failed"
        exit 1
    fi

    cd ..
}

collect_static() {
    log_step "Collecting Static Files"

    cd "$BACKEND_DIR"

    log_info "Collecting static files..."
    docker compose exec -T backend python manage.py collectstatic --noinput 2>&1 | tee -a "$LOG_FILE"

    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        log_success "Static files collected"
    else
        log_warn "Static file collection had issues (may be non-critical)"
    fi

    cd ..
}

create_superuser_prompt() {
    log_step "Create Superuser"

    read -p "Create admin superuser now? (Y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        log_info "Skipping superuser creation"
        log_info "Run manually: docker compose exec backend python manage.py createsuperuser"
        return 0
    fi

    cd "$BACKEND_DIR"

    read -p "Superuser email: " SUPERUSER_EMAIL
    if [ -z "$SUPERUSER_EMAIL" ]; then
        SUPERUSER_EMAIL="admin@localhost"
    fi

    log_info "Creating superuser..."
    docker compose exec backend python manage.py createsuperuser --email "$SUPERUSER_EMAIL" --noinput 2>/dev/null || \
    {
        log_info "Interactive mode required. Follow the prompts:"
        docker compose exec backend python manage.py createsuperuser
    }

    cd ..
}

# ═══════════════════════════════════════════════════════════
# HEALTH CHECKS
# ═══════════════════════════════════════════════════════════

run_health_checks() {
    log_step "Running Health Checks"

    PASS=0
    FAIL=0

    # Check Docker is running
    echo -n "  Docker daemon: "
    if docker info > /dev/null 2>&1; then
        echo -e "${GREEN}OK${NC}"
        ((PASS++))
    else
        echo -e "${RED}FAIL${NC}"
        ((FAIL++))
    fi

    # Check all containers are running
    echo -n "  Containers running: "
    RUNNING=$(docker compose -f "$BACKEND_DIR/$COMPOSE_FILE" ps --services --filter "status=running" 2>/dev/null | wc -l)
    if [ "$RUNNING" -gt 0 ]; then
        echo -e "${GREEN}OK ($RUNNING services)${NC}"
        ((PASS++))
    else
        echo -e "${RED}FAIL${NC}"
        ((FAIL++))
    fi

    # Check database connectivity
    echo -n "  Database: "
    if docker compose -f "$BACKEND_DIR/$COMPOSE_FILE" exec -T db pg_isready -q 2>/dev/null; then
        echo -e "${GREEN}OK${NC}"
        ((PASS++))
    else
        echo -e "${RED}FAIL${NC}"
        ((FAIL++))
    fi

    # Check backend API
    echo -n "  Backend API: "
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/health/ 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "403" ]; then
        echo -e "${GREEN}OK (HTTP $HTTP_CODE)${NC}"
        ((PASS++))
    else
        echo -e "${RED}FAIL (HTTP $HTTP_CODE)${NC}"
        ((FAIL++))
    fi

    # Check frontend
    echo -n "  Frontend: "
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:80/ 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}OK (HTTP $HTTP_CODE)${NC}"
        ((PASS++))
    else
        echo -e "${RED}FAIL (HTTP $HTTP_CODE)${NC}"
        ((FAIL++))
    fi

    # Check disk space
    echo -n "  Disk space: "
    DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | tr -d '%')
    if [ "$DISK_USAGE" -lt 80 ]; then
        echo -e "${GREEN}OK (${DISK_USAGE}% used)${NC}"
        ((PASS++))
    elif [ "$DISK_USAGE" -lt 90 ]; then
        echo -e "${YELLOW}WARNING (${DISK_USAGE}% used)${NC}"
        ((PASS++))
    else
        echo -e "${RED}CRITICAL (${DISK_USAGE}% used)${NC}"
        ((FAIL++))
    fi

    # Check memory
    echo -n "  Memory: "
    MEM_USAGE=$(free | awk 'NR==2 {printf "%.0f", $3/$2 * 100}')
    if [ "$MEM_USAGE" -lt 80 ]; then
        echo -e "${GREEN}OK (${MEM_USAGE}% used)${NC}"
        ((PASS++))
    elif [ "$MEM_USAGE" -lt 90 ]; then
        echo -e "${YELLOW}WARNING (${MEM_USAGE}% used)${NC}"
        ((PASS++))
    else
        echo -e "${RED}CRITICAL (${MEM_USAGE}% used)${NC}"
        ((FAIL++))
    fi

    echo ""
    if [ $FAIL -gt 0 ]; then
        echo -e "  ${RED}${BOLD}Results: ${PASS} passed, ${FAIL} FAILED${NC}"
        return 1
    else
        echo -e "  ${GREEN}${BOLD}Results: ${PASS}/${PASS} checks passed${NC}"
        return 0
    fi
}

# ═══════════════════════════════════════════════════════════
# DEPLOYMENT SUMMARY
# ═══════════════════════════════════════════════════════════

print_summary() {
    log_step "DEPLOYMENT COMPLETE"

    echo -e "${BOLD}${GREEN}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║                                                          ║"
    echo "║           DEPLOYMENT SUCCESSFUL                          ║"
    echo "║                                                          ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    echo -e "${BOLD}Services:${NC}"
    echo "  Backend API:  http://localhost:8000"
    echo "  Frontend:     http://localhost:80"
    echo "  Database:     localhost:5432"
    echo "  Admin Panel:  http://localhost:8000/admin/"
    echo "  API Docs:     http://localhost:8000/api/schema/"
    echo ""

    echo -e "${BOLD}Next Steps:${NC}"
    echo "  1. Configure SSL/TLS with Let's Encrypt:"
    echo "     Install nginx and certbot, then run:"
    echo "     certbot certonly --standalone -d yourdomain.com"
    echo ""
    echo "  2. Set up a reverse proxy (nginx) for HTTPS"
    echo ""
    echo "  3. Configure firewall (UFW):"
    echo "     ufw allow 80/tcp && ufw allow 443/tcp && ufw enable"
    echo ""
    echo "  4. Set up automated backups (see DEPLOYMENT.md)"
    echo ""
    echo "  5. Configure monitoring and alerting"
    echo ""

    echo -e "${BOLD}Useful Commands:${NC}"
    echo "  View logs:         docker compose logs -f"
    echo "  Restart services:  docker compose restart"
    echo "  Stop services:     docker compose down"
    echo "  Run migrations:    docker compose exec backend python manage.py migrate"
    echo "  Django shell:      docker compose exec backend python manage.py shell"
    echo "  DB shell:          docker compose exec db psql -U fetal_admin -d fetal_medical_prod"
    echo ""

    echo -e "${BOLD}Documentation:${NC}"
    echo "  Full guide:   DEPLOYMENT.md"
    echo "  Checklist:    docs/DEPLOYMENT_CHECKLIST.md"
    echo "  Deployment log: $LOG_FILE"
    echo ""

    echo -e "${GREEN}${BOLD}The Fetal Medical System is now deployed!${NC}"
    echo ""
}

# ═══════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════

main() {
    print_banner

    log_info "Deployment log: $LOG_FILE"
    echo ""

    # Phase 1: Prerequisites
    check_root
    check_os
    check_ram
    check_disk
    check_directory

    # Phase 2: Install Dependencies
    install_dependencies
    install_docker

    # Phase 3: Configure
    configure_environment

    # Phase 4: Build and Deploy
    build_images
    start_services

    # Phase 5: Initialize
    run_migrations
    collect_static
    create_superuser_prompt

    # Phase 6: Verify
    run_health_checks || {
        echo ""
        log_error "Some health checks failed. Review the output above."
        log_error "Check logs with: docker compose logs"
        echo ""
    }

    # Phase 7: Summary
    print_summary
}

# Run main function
main "$@"
