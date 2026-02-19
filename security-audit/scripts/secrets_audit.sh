#!/bin/bash
# WALI Secrets Audit Script
# Checks for hardcoded secrets and configuration issues

set -e

echo "🔐 WALI Secrets Audit"
echo "====================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FOUND=0
WARNINGS=0

# Check for secrets in Python code
echo "📋 Checking for hardcoded secrets in Python code..."

PATTERNS=(
    "password\s*=\s*['\"][^'\"]+['\"]"
    "secret\s*=\s*['\"][^'\"]+['\"]"
    "api_key\s*=\s*['\"][^'\"]+['\"]"
    "AKIA[0-9A-Z]{16}"
    "sk_live_[a-zA-Z0-9]{24,}"
    "ghp_[a-zA-Z0-9]{36}"
    "private_key\s*=\s*['\"]"
    "BEGIN\s+(RSA|DSA|EC|OPENSSH)\s+PRIVATE\s+KEY"
)

for pattern in "${PATTERNS[@]}"; do
    matches=$(grep -r -E "$pattern" python-services/ --include="*.py" 2>/dev/null | \
        grep -v "getenv\|environ\|os.env\|example\|test\|mock\|__pycache__" || true)
    
    if [ -n "$matches" ]; then
        echo -e "${RED}⚠️  Potential secret found:${NC}"
        echo "$matches" | head -5
        FOUND=$((FOUND + 1))
    fi
done

if [ $FOUND -eq 0 ]; then
    echo -e "${GREEN}✅ No hardcoded secrets found in Python code${NC}"
else
    echo -e "${RED}❌ $FOUND potential secrets found - review immediately!${NC}"
fi

# Check for secrets in JavaScript/TypeScript
echo ""
echo "📋 Checking for secrets in frontend code..."

JS_PATTERNS=(
    "apiKey\s*:\s*['\"][^'\"]+['\"]"
    "secret\s*:\s*['\"][^'\"]+['\"]"
    "password\s*:\s*['\"][^'\"]+['\"]"
    "AWS_ACCESS_KEY_ID\s*[=:]\s*['\"]AKIA"
)

for pattern in "${JS_PATTERNS[@]}"; do
    matches=$(grep -r -E "$pattern" typescript-apps/pwa/ --include="*.ts" --include="*.tsx" --include="*.js" 2>/dev/null | \
        grep -v "process.env\|NEXT_PUBLIC\|example\|test\|.next\|node_modules" || true)
    
    if [ -n "$matches" ]; then
        echo -e "${RED}⚠️  Potential secret in frontend:${NC}"
        echo "$matches" | head -3
        FOUND=$((FOUND + 1))
    fi
done

# Check .env files
echo ""
echo "📋 Checking .env files..."

ENV_FILES=$(find . -name ".env" -o -name ".env.local" -o -name ".env.production" 2>/dev/null | grep -v node_modules | grep -v ".next" || true)

if [ -n "$ENV_FILES" ]; then
    echo "Found .env files:"
    echo "$ENV_FILES"
    
    # Check if .env is in .gitignore
    if [ -f ".gitignore" ]; then
        if grep -q "\.env" .gitignore; then
            echo -e "${GREEN}✅ .env files are in .gitignore${NC}"
        else
            echo -e "${RED}❌ WARNING: .env files may not be in .gitignore!${NC}"
            WARNINGS=$((WARNINGS + 1))
        fi
    fi
else
    echo -e "${YELLOW}⚠️  No .env files found (may use environment variables directly)${NC}"
fi

# Check for Fly secrets
echo ""
echo "📋 Checking Fly.io secrets..."

if command -v fly &> /dev/null; then
    SERVICES=("wali-policy-service" "wali-claims-service" "wali-payment-gateway")
    
    for service in "${SERVICES[@]}"; do
        if fly apps list 2>/dev/null | grep -q "$service"; then
            secrets_count=$(fly secrets list --app "$service" 2>/dev/null | wc -l)
            if [ "$secrets_count" -gt 1 ]; then
                echo -e "${GREEN}✅ $service has secrets configured ($secrets_count secrets)${NC}"
            else
                echo -e "${YELLOW}⚠️  $service may not have secrets configured${NC}"
                WARNINGS=$((WARNINGS + 1))
            fi
        else
            echo -e "${YELLOW}⚠️  $service app not found${NC}"
        fi
    done
else
    echo -e "${YELLOW}⚠️  Fly CLI not installed, skipping Fly secrets check${NC}"
fi

# Check git history for secrets
echo ""
echo "📋 Checking git history for secrets (this may take a while)..."

if command -v git &> /dev/null; then
    # Simple check for common patterns in git log
    suspicious_commits=$(git log --all --full-history -p -- . 2>/dev/null | \
        grep -E "(password|secret|key|token)\s*=\s*['\"][^'\"]{8,}" | \
        head -10 || true)
    
    if [ -n "$suspicious_commits" ]; then
        echo -e "${YELLOW}⚠️  Found potential secrets in git history:${NC}"
        echo "$suspicious_commits"
        echo "Consider using git-filter-repo to remove them if confirmed"
        WARNINGS=$((WARNINGS + 1))
    else
        echo -e "${GREEN}✅ No obvious secrets in recent git history${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Git not available${NC}"
fi

# Summary
echo ""
echo "====================="
echo "📊 Audit Summary"
echo "====================="

if [ $FOUND -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed!${NC}"
    exit 0
elif [ $FOUND -eq 0 ]; then
    echo -e "${YELLOW}⚠️  $WARNINGS warnings found (review recommended)${NC}"
    exit 0
else
    echo -e "${RED}❌ $FOUND issues found - immediate action required!${NC}"
    exit 1
fi
