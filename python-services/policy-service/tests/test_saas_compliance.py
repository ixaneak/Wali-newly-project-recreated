import pytest
import asyncio
from unittest.mock import MagicMock, patch
from datetime import date

from app.models.partner import PartnerInvoice
from app.services.saas_billing_service import SaaSBillingService
from app.config import compliance

# Mock DB Session
mock_db = MagicMock()

def test_no_premium_calculator():
    """Ensure we never calculate insurance prices"""
    with pytest.raises(ImportError):
        from app.services import PremiumCalculator

def test_saas_config_flags():
    """Ensure global config enforces SaaS model"""
    assert compliance.IS_SAAS_PLATFORM is True
    assert compliance.IS_INSURER is False
    assert compliance.NAF_CODE == "6201Z"

@pytest.mark.asyncio
async def test_flat_fee_invoicing():
    """Ensure revenue is flat SaaS fee, not commission"""
    # Setup mock partner
    partner_id = "NSIA"
    mock_partner = MagicMock()
    mock_partner.id = partner_id
    mock_partner.monthly_fee = 500000
    
    mock_db.query.return_value.filter.return_value.first.return_value = mock_partner
    
    # Generate invoice
    invoice = SaaSBillingService.generate_monthly_invoice(
        db=mock_db, 
        partner_id=partner_id, 
        period_month=date(2026, 2, 1)
    )
    
    # Must be flat fee
    assert invoice.amount_due == 500000  # Fixed
    assert "commission" not in invoice.description.lower()
    
    # Verify DB add
    mock_db.add.assert_called_once()
    assert mock_db.add.call_args[0][0].amount_due == 500000

