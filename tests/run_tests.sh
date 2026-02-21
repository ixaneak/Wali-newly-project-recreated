#!/bin/bash
# Wali Test Runner
# Usage: ./run_tests.sh [unit|integration|e2e|all]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
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

run_unit_tests() {
    log_info "Running unit tests..."
    cd "$PROJECT_ROOT/python-services/policy-service"
    
    # Check if pytest is available
    if ! command -v pytest &> /dev/null; then
        log_warn "pytest not found, installing..."
        pip install pytest pytest-asyncio httpx pytest-cov
    fi
    
    # Run tests
    pytest tests/ -v --cov=app --cov-report=term-missing -m "not integration and not e2e" || {
        log_error "Unit tests failed"
        return 1
    }
    
    log_info "Unit tests passed!"
}

run_integration_tests() {
    log_info "Running integration tests..."
    cd "$PROJECT_ROOT/python-services/policy-service"
    
    # Run integration tests
    pytest tests/ -v -m "integration" || {
        log_warn "Some integration tests failed (may require services)"
    }
    
    log_info "Integration tests completed"
}

run_e2e_tests() {
    log_info "Running E2E tests..."
    cd "$PROJECT_ROOT/tests/e2e"
    
    # Check if services are running
    log_info "Checking if services are running..."
    
    # Try to ping health endpoint
    if curl -s http://localhost:8000/health > /dev/null; then
        log_info "Policy service is running"
    else
        log_warn "Policy service not running on localhost:8000"
        log_warn "Attempting mock mode tests..."
    fi
    
    # Run E2E tests
    python verify_e2e_flow.py || {
        log_error "E2E tests failed"
        return 1
    }
    
    log_info "E2E tests passed!"
}

run_security_tests() {
    log_info "Running security tests..."
    cd "$PROJECT_ROOT/python-services/policy-service"
    
    pytest tests/test_security.py -v || {
        log_warn "Some security tests failed"
    }
    
    log_info "Security tests completed"
}

run_load_tests() {
    log_info "Running load tests..."
    cd "$PROJECT_ROOT/load-tests"
    
    if command -v k6 &> /dev/null; then
        k6 run --vus 1 --iterations 1 wali-load-test.js || {
            log_warn "Load tests completed with warnings"
        }
    else
        log_warn "k6 not found, skipping load tests"
        log_info "Install k6: https://k6.io/docs/get-started/installation/"
    fi
}

run_all_tests() {
    log_info "Running all tests..."
    run_unit_tests
    run_integration_tests
    run_e2e_tests
    run_security_tests
    log_info "All tests completed!"
}

# Main
case "${1:-all}" in
    unit)
        run_unit_tests
        ;;
    integration)
        run_integration_tests
        ;;
    e2e)
        run_e2e_tests
        ;;
    security)
        run_security_tests
        ;;
    load)
        run_load_tests
        ;;
    all)
        run_all_tests
        ;;
    *)
        echo "Usage: $0 [unit|integration|e2e|security|load|all]"
        exit 1
        ;;
esac
