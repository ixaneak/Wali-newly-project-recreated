#!/bin/bash
# ================================================================
# Fly.io Migration Script: EWR → CDG
# Cleans up duplicate claims-service and migrates to Paris (CDG)
# ================================================================

set -e  # Exit on any error

echo "=========================================="
echo "Fly.io Region Migration: EWR → CDG"
echo "=========================================="

# Step 1: Destroy legacy duplicate claims-service
echo ""
echo "Step 1: Destroying legacy 'claims-service' app..."
echo "---------------------------------------------------"
if fly apps list | grep -q "^claims-service "; then
    fly apps destroy claims-service --yes
    echo "✅ Legacy claims-service destroyed"
else
    echo "ℹ️  Legacy claims-service not found, skipping..."
fi

# Step 2: Migrate wali-claims-service from EWR to CDG
echo ""
echo "Step 2: Migrating wali-claims-service EWR → CDG..."
echo "---------------------------------------------------"

APP="wali-claims-service"

# Get current machine IDs in EWR
echo "Finding machines in EWR region..."
EWR_MACHINES=$(fly machines list --app $APP --json | jq -r '.[] | select(.region=="ewr") | .id' 2>/dev/null || echo "")

if [ -z "$EWR_MACHINES" ]; then
    echo "ℹ️  No EWR machines found for $APP"
    # Check if already in CDG
    CDG_COUNT=$(fly machines list --app $APP --json | jq '[.[] | select(.region=="cdg")] | length' 2>/dev/null || echo "0")
    if [ "$CDG_COUNT" -gt 0 ]; then
        echo "✅ Already have $CDG_COUNT machines in CDG"
    fi
else
    echo "Found EWR machines: $EWR_MACHINES"
    
    # Clone each machine to CDG
    echo ""
    echo "Cloning machines to CDG..."
    for id in $EWR_MACHINES; do
        echo "  Cloning machine $id to CDG..."
        fly machine clone "$id" --region cdg --app $APP
        echo "  ✅ Cloned $id"
    done
    
    # Wait for health checks
    echo ""
    echo "Waiting 15 seconds for health checks..."
    sleep 15
    
    # Verify CDG machines are healthy
    echo "Verifying CDG machines..."
    CDG_HEALTHY=$(fly machines list --app $APP --json | jq '[.[] | select(.region=="cdg" and .state=="started")] | length' 2>/dev/null || echo "0")
    echo "Healthy CDG machines: $CDG_HEALTHY"
    
    if [ "$CDG_HEALTHY" -eq 0 ]; then
        echo "❌ ERROR: No healthy CDG machines. Aborting EWR destruction."
        echo "Manual intervention required!"
        exit 1
    fi
    
    # Destroy EWR machines
    echo ""
    echo "Destroying EWR machines..."
    for id in $EWR_MACHINES; do
        echo "  Destroying machine $id..."
        fly machine destroy "$id" --app $APP --force
        echo "  ✅ Destroyed $id"
    done
    
    echo "✅ Migration complete!"
fi

# Step 3: Verify final state
echo ""
echo "Step 3: Verification"
echo "---------------------------------------------------"
echo ""
echo "=== wali-claims-service ==="
fly status --app wali-claims-service

echo ""
echo "=== wali-payment-service ==="
fly status --app wali-payment-service

echo ""
echo "=========================================="
echo "Migration Summary"
echo "=========================================="
echo ""
echo "Expected state:"
echo "  ❌ claims-service      - DESTROYED"
echo "  ✅ wali-claims-service - CDG region"
echo "  ✅ wali-payment-service - CDG region (unchanged)"
echo ""
echo "Don't forget to update fly.toml:"
echo '  primary_region = "cdg"'
echo ""
