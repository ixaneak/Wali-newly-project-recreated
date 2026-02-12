"""
WALI Platform Compliance Configuration

Declares business model classification for Label Startup Numérique eligibility.
These flags are used by audit tools, compliance reports, and legal documentation.
"""


# ── Business Model Classification ───────────────────────────────
BUSINESS_MODEL = "B2B_SAAS"
REVENUE_TYPE = "subscription_software"

# ── CIMA Declarations (Ivory Coast Insurance Regulator) ─────────
IS_INSURER = False
IS_INSURANCE_BROKER = False
IS_REINSURER = False

# ── Actual Business Identity ────────────────────────────────────
IS_SOFTWARE_PUBLISHER = True
IS_TECH_CONSULTANT = True
IS_SAAS_PLATFORM = True

# ── Money Handling ──────────────────────────────────────────────
TOUCHES_CUSTOMER_PREMIUMS = False
HOLDS_INSURANCE_RISK = False
EARNS_COMMISSION_ON_PREMIUMS = False

# ── What Wali Actually Does ─────────────────────────────────────
PROVIDES_SOFTWARE_TO_INSURERS = True
ROUTES_PAYMENTS_TO_LICENSED_PARTNERS = True
EARNS_SUBSCRIPTION_REVENUE = True

# ── Label Startup Classification ────────────────────────────────
NAF_CODE = "6201Z"  # Conseil en systèmes et logiciels informatiques
ACTIVITE_PRINCIPALE = (
    "Edition de logiciels SaaS pour le secteur des assurances"
)

# ── Default Partner ─────────────────────────────────────────────
UNDERWRITING_PARTNER = "NSIA"
PARTNER_MONTHLY_LICENSE_FEE = 500_000  # FCFA flat fee
