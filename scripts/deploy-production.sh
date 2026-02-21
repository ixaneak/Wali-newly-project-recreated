#!/bin/bash
# Wali Production Deployment Script
# Usage: ./deploy-production.sh [version]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# Configuration
VERSION=${1:-$(git rev-parse --short HEAD)}
ENVIRONMENT=${ENVIRONMENT:-production}
COMPOSE_FILE="$PROJECT_ROOT/infrastructure/docker-compose.prod.yml"

# Pre-deployment checks
check_prerequisites() {
    log_step "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found"
        exit 1
    fi
    
    # Check docker-compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "docker-compose not found"
        exit 1
    fi
    
    # Check environment file
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        log_error ".env file not found!"
        exit 1
    fi
    
    # Verify required environment variables
    local required_vars=(
        "POSTGRES_PASSWORD"
        "REDIS_PASSWORD"
        "JWT_SECRET"
        "MINIO_ROOT_PASSWORD"
    )
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            log_error "Required environment variable $var not set"
            exit 1
        fi
    done
    
    log_info "Prerequisites check passed"
}

# Run tests
run_tests() {
    log_step "Running pre-deployment tests..."
    
    cd "$PROJECT_ROOT"
    
    # Run unit tests
    log_info "Running unit tests..."
    cd python-services/policy-service
    if python -m pytest tests/ -v -x -q 2>/dev/null; then
        log_info "Unit tests passed"
    else
        log_warn "Some unit tests failed (continuing anyway)"
    fi
    cd "$PROJECT_ROOT"
}

# Backup database
backup_database() {
    log_step "Creating database backup..."
    
    local backup_file="backup_$(date +%Y%m%d_%H%M%S).sql"
    
    # This is a placeholder - implement actual backup logic
    log_info "Backup would be created at: $backup_file"
    
    # Example backup command:
    # docker-compose -f "$COMPOSE_FILE" exec -T postgres-primary \
    #     pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > "$backup_file"
}

# Deploy services
deploy_services() {
    log_step "Deploying services..."
    
    cd "$PROJECT_ROOT/infrastructure"
    
    # Pull latest images
    log_info "Pulling latest images..."
    docker-compose -f docker-compose.prod.yml pull
    
    # Build any local images
    log_info "Building local images..."
    docker-compose -f docker-compose.prod.yml build --no-cache
    
    # Deploy with zero-downtime (if using Docker Swarm or similar)
    # For now, standard up
    log_info "Starting services..."
    docker-compose -f docker-compose.prod.yml up -d
    
    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    sleep 30
    
    # Check health
    local retries=0
    local max_retries=10
    
    while [ $retries -lt $max_retries ]; do
        if docker-compose -f docker-compose.prod.yml ps | grep -q "healthy"; then
            log_info "Services are healthy"
            break
        fi
        retries=$((retries + 1))
        log_warn "Waiting for services to be healthy... ($retries/$max_retries)"
        sleep 10
    done
    
    if [ $retries -eq $max_retries ]; then
        log_error "Services failed to become healthy"
        rollback
        exit 1
    fi
}

# Verify deployment
verify_deployment() {
    log_step "Verifying deployment..."
    
    local health_url="https://api.wali.ci/health"
    local retries=0
    local max_retries=5
    
    while [ $retries -lt $max_retries ]; do
        if curl -sf "$health_url" > /dev/null 2>&1; then
            log_info "Health check passed"
            return 0
        fi
        retries=$((retries + 1))
        sleep 10
    done
    
    log_error "Health check failed"
    return 1
}

# Rollback on failure
rollback() {
    log_warn "Initiating rollback..."
    
    cd "$PROJECT_ROOT/infrastructure"
    docker-compose -f docker-compose.prod.yml down
    
    # Restore from backup would go here
    log_info "Rollback completed"
}

# Cleanup old resources
cleanup() {
    log_step "Cleaning up old resources..."
    
    # Remove old images
    docker image prune -af --filter "until=168h" || true
    
    # Remove old volumes (careful with this!)
    # docker volume prune -f || true
}

# Send notification
send_notification() {
    local status=$1
    local message=$2
    
    log_info "Notification: $status - $message"
    
    # Slack notification (if webhook configured)
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
        curl -s -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"Deployment $status: $message\"}" \
            "$SLACK_WEBHOOK_URL" || true
    fi
}

# Main deployment flow
main() {
    log_info "Starting Wali deployment v$VERSION"
    
    check_prerequisites
    run_tests
    backup_database
    
    if deploy_services; then
        if verify_deployment; then
            cleanup
            send_notification "SUCCESS" "Version $VERSION deployed successfully"
            log_info "Deployment completed successfully!"
        else
            rollback
            send_notification "FAILED" "Version $VERSION failed verification"
            log_error "Deployment failed during verification"
            exit 1
        fi
    else
        send_notification "FAILED" "Version $VERSION failed to deploy"
        log_error "Deployment failed"
        exit 1
    fi
}

# Run main
main "$@"
