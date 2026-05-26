#!/bin/bash
# =============================================================================
# Redis Startup Script for Fetal Medical System
# =============================================================================
# Starts Redis server with proper configuration for production use.
# This script handles:
# - Checking if Redis is already running
# - Starting Redis with production-optimized settings
# - Verifying connectivity after startup
# =============================================================================

set -e

# Configuration
REDIS_HOST="${REDIS_HOST:-127.0.0.1}"
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_DB="${REDIS_DB:-1}"
REDIS_LOG_FILE="${REDIS_LOG_FILE:-/var/log/redis/redis-server.log}"
REDIS_DATA_DIR="${REDIS_DATA_DIR:-/var/lib/redis}"
REDIS_PASSWORD="${REDIS_PASSWORD:-}"
REDIS_MAX_MEMORY="${REDIS_MAX_MEMORY:-256mb}"
REDIS_MAX_MEMORY_POLICY="${REDIS_MAX_MEMORY_POLICY:-allkeys-lru}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Redis is already running
check_redis_running() {
    if command -v redis-cli &> /dev/null; then
        if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping &> /dev/null; then
            return 0
        fi
    fi
    return 1
}

# Generate Redis configuration
generate_config() {
    local config_file="/tmp/redis_fetal_medical.conf"

    cat > "$config_file" << EOF
# Fetal Medical System - Redis Configuration
# Generated on $(date)

# Network
bind ${REDIS_HOST}
port ${REDIS_PORT}
protected-mode yes
tcp-backlog 511
timeout 300
tcp-keepalive 300

# General
daemonize yes
supervised no
pidfile /var/run/redis/redis-server.pid
loglevel notice
logfile ${REDIS_LOG_FILE}
databases 16

# Snapshotting
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir ${REDIS_DATA_DIR}

# Memory Management
maxmemory ${REDIS_MAX_MEMORY}
maxmemory-policy ${REDIS_MAX_MEMORY_POLICY}
maxmemory-samples 5

# Security
${REDIS_PASSWORD:+requirepass ${REDIS_PASSWORD}}

# Lazy Freeing
lazyfree-lazy-eviction yes
lazyfree-lazy-expire yes
lazyfree-lazy-server-del yes

# Append Only Mode (AOF)
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb

# Slow Log
slowlog-log-slower-than 10000
slowlog-max-len 128

# Advanced Config
hz 10
dynamic-hz yes
aof-rewrite-incremental-fsync yes
EOF

    echo "$config_file"
}

# Start Redis server
start_redis() {
    local config_file="$1"

    log_info "Starting Redis server..."

    # Create necessary directories
    mkdir -p "$(dirname "$REDIS_LOG_FILE")"
    mkdir -p "$REDIS_DATA_DIR"
    mkdir -p /var/run/redis

    # Start Redis with configuration
    if command -v redis-server &> /dev/null; then
        redis-server "$config_file"
        sleep 2

        # Verify startup
        if check_redis_running; then
            log_info "Redis started successfully on ${REDIS_HOST}:${REDIS_PORT}"
            return 0
        else
            log_error "Redis failed to start. Check logs at ${REDIS_LOG_FILE}"
            return 1
        fi
    else
        log_error "redis-server command not found. Please install Redis first."
        log_info "Installation: sudo apt-get install redis-server (Ubuntu/Debian)"
        log_info "Installation: sudo yum install redis (CentOS/RHEL)"
        log_info "Installation: brew install redis (macOS)"
        return 1
    fi
}

# Test Redis connectivity
test_connection() {
    log_info "Testing Redis connectivity..."

    local cli_args=""
    if [ -n "$REDIS_PASSWORD" ]; then
        cli_args="-a $REDIS_PASSWORD"
    fi

    local response
    response=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" $cli_args ping 2>/dev/null)

    if [ "$response" = "PONG" ]; then
        log_info "Redis connection successful!"

        # Show cache info
        local info
        info=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" $cli_args INFO memory 2>/dev/null | grep -E "used_memory_human|maxmemory_human")
        log_info "Memory usage:"
        echo "$info" | sed 's/^/  /'

        return 0
    else
        log_error "Redis connection failed!"
        return 1
    fi
}

# Main execution
main() {
    log_info "============================================"
    log_info "Fetal Medical System - Redis Startup"
    log_info "============================================"

    # Check if already running
    if check_redis_running; then
        log_warn "Redis is already running on ${REDIS_HOST}:${REDIS_PORT}"
        log_info "Stopping existing instance..."
        redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ${REDIS_PASSWORD:+-a $REDIS_PASSWORD} shutdown nosave 2>/dev/null || true
        sleep 2
    fi

    # Generate configuration
    local config_file
    config_file=$(generate_config)
    log_info "Generated Redis config: $config_file"

    # Start Redis
    start_redis "$config_file"

    # Test connection
    test_connection

    log_info "============================================"
    log_info "Redis is ready for Fetal Medical System!"
    log_info "============================================"
    log_info "Host: ${REDIS_HOST}"
    log_info "Port: ${REDIS_PORT}"
    log_info "Database: ${REDIS_DB}"
    log_info "Max Memory: ${REDIS_MAX_MEMORY}"
    log_info "Eviction Policy: ${REDIS_MAX_MEMORY_POLICY}"
    log_info "============================================"
}

# Run main function
main "$@"
