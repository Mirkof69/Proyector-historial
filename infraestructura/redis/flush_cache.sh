#!/bin/bash
# =============================================================================
# Cache Flush Script for Fetal Medical System
# =============================================================================
# Flushes all caches used by the Fetal Medical System.
# This script provides multiple modes:
# - Full flush: Clear all keys in the Redis database
# - Pattern flush: Clear only Fetal Medical System cache keys
# - Selective flush: Clear specific cache types
# =============================================================================

set -e

# Configuration
REDIS_HOST="${REDIS_HOST:-127.0.0.1}"
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_DB="${REDIS_DB:-1}"
REDIS_PASSWORD="${REDIS_PASSWORD:-}"

# Cache key prefixes used by Fetal Medical System
CACHE_PREFIXES=(
    "fetal_medical:*"
    "fetal_sessions:*"
    "fetal_stats:*"
    "fetal_medical_middleware:*"
    "patient_data:*"
    "patient_detail:*"
    "patient_history:*"
    "patient_embarazos:*"
    "patient_stats:*"
    "dashboard_stats:*"
    "dashboard_kpi:*"
    "dashboard_alerts:*"
    "ultrasound_images:*"
    "ecografia_stats:*"
    "embarazo_stats:*"
    "embarazo_data:*"
    "embarazo_controles:*"
    "embarazo_estadisticas:*"
    "report_stats:*"
    "alert_stats:*"
    "general_stats:*"
    "statistics:*"
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# Get Redis CLI arguments
get_redis_cli_args() {
    local args="-h $REDIS_HOST -p $REDIS_PORT -n $REDIS_DB"
    if [ -n "$REDIS_PASSWORD" ]; then
        args="$args -a $REDIS_PASSWORD"
    fi
    echo "$args"
}

# Check Redis connectivity
check_redis() {
    local cli_args
    cli_args=$(get_redis_cli_args)

    if ! command -v redis-cli &> /dev/null; then
        log_error "redis-cli command not found. Please install Redis first."
        return 1
    fi

    local response
    response=$(redis-cli $cli_args ping 2>/dev/null)

    if [ "$response" = "PONG" ]; then
        return 0
    else
        log_error "Cannot connect to Redis at ${REDIS_HOST}:${REDIS_PORT}"
        return 1
    fi
}

# Flush all keys in the database (NUCLEAR OPTION)
flush_all() {
    local cli_args
    cli_args=$(get_redis_cli_args)

    log_warn "============================================"
    log_warn "NUCLEAR OPTION: Flushing ALL keys in database ${REDIS_DB}"
    log_warn "This will clear ALL data, not just Fetal Medical caches!"
    log_warn "============================================"
    echo ""

    read -p "Are you sure you want to continue? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        log_info "Operation cancelled."
        return 0
    fi

    log_info "Flushing all keys..."
    redis-cli $cli_args FLUSHDB 2>/dev/null

    log_info "All keys flushed successfully!"
}

# Flush Fetal Medical System cache keys only
flush_fetal_medical() {
    local cli_args
    cli_args=$(get_redis_cli_args)

    log_info "============================================"
    log_info "Flushing Fetal Medical System cache keys..."
    log_info "============================================"
    echo ""

    local total_deleted=0

    for prefix in "${CACHE_PREFIXES[@]}"; do
        log_debug "Deleting keys matching: $prefix"

        # Use SCAN instead of KEYS for production safety
        local cursor=0
        local deleted=0

        while true; do
            local result
            result=$(redis-cli $cli_args SCAN $cursor MATCH "$prefix" COUNT 100 2>/dev/null)

            # Parse cursor and keys
            cursor=$(echo "$result" | head -n 1)
            local keys
            keys=$(echo "$result" | tail -n +2)

            if [ -n "$keys" ]; then
                # Delete keys in batch
                echo "$keys" | xargs -r redis-cli $cli_args DEL 2>/dev/null > /dev/null
                deleted=$((deleted + $(echo "$keys" | wc -l)))
            fi

            # Exit when cursor returns to 0
            if [ "$cursor" = "0" ]; then
                break
            fi
        done

        if [ $deleted -gt 0 ]; then
            log_info "Deleted $deleted keys matching: $prefix"
        fi

        total_deleted=$((total_deleted + deleted))
    done

    echo ""
    log_info "============================================"
    log_info "Cache flush complete!"
    log_info "Total keys deleted: $total_deleted"
    log_info "============================================"
}

# Flush a specific cache type
flush_specific() {
    local cache_type="$1"
    local cli_args
    cli_args=$(get_redis_cli_args)

    log_info "Flushing cache type: $cache_type"

    local pattern="fetal_medical:*${cache_type}*"
    local deleted=0
    local cursor=0

    while true; do
        local result
        result=$(redis-cli $cli_args SCAN $cursor MATCH "$pattern" COUNT 100 2>/dev/null)

        cursor=$(echo "$result" | head -n 1)
        local keys
        keys=$(echo "$result" | tail -n +2)

        if [ -n "$keys" ]; then
            echo "$keys" | xargs -r redis-cli $cli_args DEL 2>/dev/null > /dev/null
            deleted=$((deleted + $(echo "$keys" | wc -l)))
        fi

        if [ "$cursor" = "0" ]; then
            break
        fi
    done

    log_info "Deleted $deleted keys for cache type: $cache_type"
}

# Show cache statistics
show_stats() {
    local cli_args
    cli_args=$(get_redis_cli_args)

    log_info "============================================"
    log_info "Cache Statistics"
    log_info "============================================"
    echo ""

    # Get memory info
    log_info "Memory Usage:"
    redis-cli $cli_args INFO memory 2>/dev/null | grep -E "used_memory_human|maxmemory_human|used_memory_peak_human" | sed 's/^/  /'

    echo ""
    log_info "Key Count by Pattern:"

    for prefix in "${CACHE_PREFIXES[@]}"; do
        local count
        count=$(redis-cli $cli_args DBSIZE 2>/dev/null | awk '{print $2}')
        log_info "  $prefix: (part of $count total keys)"
    done

    echo ""
    log_info "Hit/Miss Stats:"
    redis-cli $cli_args INFO stats 2>/dev/null | grep -E "keyspace_hits|keyspace_misses" | sed 's/^/  /'
}

# Show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -a, --all          Flush ALL keys in database (nuclear option)"
    echo "  -f, --fetal        Flush only Fetal Medical System cache keys (default)"
    echo "  -s, --specific     Flush specific cache type"
    echo "  -S, --stats        Show cache statistics"
    echo "  -h, --help         Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  REDIS_HOST         Redis host (default: 127.0.0.1)"
    echo "  REDIS_PORT         Redis port (default: 6379)"
    echo "  REDIS_DB           Redis database (default: 1)"
    echo "  REDIS_PASSWORD     Redis password (default: empty)"
    echo ""
    echo "Examples:"
    echo "  $0                         # Flush Fetal Medical caches"
    echo "  $0 --all                   # Flush all keys"
    echo "  $0 --stats                 # Show cache stats"
    echo "  REDIS_HOST=myserver $0     # Use custom host"
}

# Main execution
main() {
    local action="fetal"

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -a|--all)
                action="all"
                shift
                ;;
            -f|--fetal)
                action="fetal"
                shift
                ;;
            -s|--specific)
                action="specific"
                shift
                specific_type="$1"
                shift
                ;;
            -S|--stats)
                action="stats"
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    # Check Redis connectivity
    if ! check_redis; then
        exit 1
    fi

    # Execute action
    case $action in
        all)
            flush_all
            ;;
        fetal)
            flush_fetal_medical
            ;;
        specific)
            if [ -z "$specific_type" ]; then
                log_error "Cache type required for --specific option"
                exit 1
            fi
            flush_specific "$specific_type"
            ;;
        stats)
            show_stats
            ;;
    esac
}

# Run main function
main "$@"
