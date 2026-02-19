#!/bin/bash
# WALI Dependency Security Audit
# Checks all Python and Node.js dependencies for known CVEs

set -e

AUDIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORT_DIR="$AUDIT_DIR/reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "🔒 WALI Security Dependency Audit"
echo "=================================="
echo "Timestamp: $TIMESTAMP"
echo ""

mkdir -p "$REPORT_DIR"

# Function to audit Python service
audit_python_service() {
    local service_name=$1
    local service_path=$2
    
    echo "📦 Auditing $service_name..."
    
    cd "$service_path" || return 1
    
    # Check if requirements.txt exists
    if [ ! -f "requirements.txt" ]; then
        echo "  ⚠️  No requirements.txt found, skipping..."
        return 0
    fi
    
    # Run pip-audit
    if command -v pip-audit &> /dev/null; then
        pip-audit --desc --format=json > "$REPORT_DIR/${service_name}-deps-$TIMESTAMP.json" 2>/dev/null || true
        
        # Check for critical/high severity
        echo "  Checking for HIGH/CRITICAL vulnerabilities..."
        pip-audit --severity=high --desc || {
            echo "  ❌ HIGH/CRITICAL vulnerabilities found in $service_name!"
            return 1
        }
    else
        echo "  ⚠️  pip-audit not installed. Install with: pip install pip-audit"
    fi
    
    echo "  ✅ $service_name audit complete"
    return 0
}

# Function to audit Node.js service
audit_node_service() {
    local service_name=$1
    local service_path=$2
    
    echo "📦 Auditing $service_name..."
    
    cd "$service_path" || return 1
    
    # Check if package.json exists
    if [ ! -f "package.json" ]; then
        echo "  ⚠️  No package.json found, skipping..."
        return 0
    fi
    
    # Run npm audit
    if command -v npm &> /dev/null; then
        npm audit --json > "$REPORT_DIR/${service_name}-deps-$TIMESTAMP.json" 2>/dev/null || true
        
        # Check for high/critical
        echo "  Checking for high/critical vulnerabilities..."
        npm audit --audit-level=high || {
            echo "  ❌ High/Critical vulnerabilities found in $service_name!"
            return 1
        }
    else
        echo "  ⚠️  npm not found"
    fi
    
    echo "  ✅ $service_name audit complete"
    return 0
}

# Audit Python services
echo ""
echo "🔍 Auditing Python Services..."
echo "------------------------------"

SERVICES=(
    "policy-service:python-services/policy-service"
    "claims-service:python-services/claims-service"
    "payment-gateway:python-services/payment-gateway"
    "ai-concierge:python-services/ai-concierge"
)

FAILED=0
for service in "${SERVICES[@]}"; do
    IFS=':' read -r name path <<< "$service"
    if ! audit_python_service "$name" "$AUDIT_DIR/../$path"; then
        FAILED=$((FAILED + 1))
    fi
done

# Audit Node.js services
echo ""
echo "🔍 Auditing Node.js Services..."
echo "-------------------------------"

if ! audit_node_service "pwa" "$AUDIT_DIR/../typescript-apps/pwa"; then
    FAILED=$((FAILED + 1))
fi

# Summary
echo ""
echo "=================================="
echo "📊 Audit Summary"
echo "=================================="
echo "Reports saved to: $REPORT_DIR"
echo "Failed audits: $FAILED"

if [ $FAILED -gt 0 ]; then
    echo "❌ Security audit FAILED - vulnerabilities found!"
    exit 1
else
    echo "✅ Security audit PASSED - no critical vulnerabilities"
    exit 0
fi
