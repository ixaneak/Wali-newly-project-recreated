from pydantic import BaseModel, HttpUrl
from typing import Optional, Any, Dict

class WebhookBase(BaseModel):
    transaction_id: str
    status: str
    amount: int
    currency: str = "XOF"
    timestamp: Optional[str] = None
    
# Specific schemas can inherit or just use parsing logic in the service if providers differ wildly.
# For now, let's assume a normalized internal representation, but we might receive different shapes.

class OrangeMoneyWebhook(BaseModel):
    # This structure depends on OM API docs. Assuming a standard structure for now.
    notif_token: str 
    txnid: str
    ref_id: str
    amount: int
    status: str # SUCCESS, FAILED
    
class WaveWebhook(BaseModel):
    id: str
    amount: str
    checkout_status: str # complete
    client_reference: str
    
class MtnMomoWebhook(BaseModel):
    financialTransactionId: str
    externalId: str
    amount: str
    currency: str
    status: str # SUCCESSFUL
