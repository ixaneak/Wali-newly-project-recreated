# Wali Documentation

Complete documentation for the Wali micro-insurance platform targeting artisans and pharmacies in Côte d'Ivoire.

## 📚 Documentation Structure

### 🚀 [Getting Started](./guides/quickstart.md)
Quick start guide for developers setting up the project locally.

### 🏗️ [Architecture](./architecture/)
Technical architecture and infrastructure documentation.

| Document | Description |
|----------|-------------|
| [Tech Stack](./architecture/tech-stack.md) | Language distribution, frameworks, and standards |
| [Database Pooling](./architecture/database-pooling.md) | Connection pooling implementation and configuration |
| [Production Scaling](./architecture/production-scaling.md) | SRE infrastructure for 10,000 concurrent users |
| [Financial Analytics](./architecture/unified-financial-analytics.md) | Unified financial analytics system |

### 🔒 [Security](./security/)
Security audits, compliance checklists, and implementation guides.

| Document | Description |
|----------|-------------|
| [Audit Complete](./security/audit-complete.md) | Security audit completion summary |
| [Audit Implementation](./security/audit-implementation.md) | Complete security testing implementation guide |
| [CIMA Security Checklist](./security/cima-security-checklist.md) | CIMA regulatory compliance checklist |
| [OWASP Remediation](./security/owasp-remediation-guide.md) | OWASP Top 10 mitigation strategies |
| [Final Compliance Report](./security/final-compliance-report.md) | Compliance audit final report |

### 📖 [Guides](./guides/)
Step-by-step guides for common tasks.

| Document | Description |
|----------|-------------|
| [Quickstart](./guides/quickstart.md) | Developer setup and first run |
| [Login Enhancements](./guides/login-enhancements.md) | Forgot password & help flow implementation |
| [Testing](./guides/testing.md) | Testing commands and procedures |
| [Verification Checklist](./guides/verification-checklist.md) | Admin auth verification steps |

### 💬 [WhatsApp](./whatsapp/)
WhatsApp Business API integration documentation.

| Document | Description |
|----------|-------------|
| [OTP Setup](./whatsapp/otp-setup.md) | WhatsApp OTP configuration |
| [OTP Summary](./whatsapp/otp-summary.md) | WhatsApp OTP implementation summary |
| [Ivory Coast Business Logic](./whatsapp/ivory-coast-business-logic.md) | CI-specific compliance constraints |
| [Service Readme](./whatsapp/service-readme.md) | WhatsApp service architecture |
| [Redis Config](./whatsapp/redis-config.md) | Redis setup for WhatsApp sessions |

### 🔧 [Operations](./operations/)
Production operations, load testing, and infrastructure guides.

| Document | Description |
|----------|-------------|
| [Pooling Guide](./operations/pooling-guide.md) | Database connection pooling guide |
| [CIMA Production Checklist](./operations/cima-production-checklist.md) | Pre-production checklist |

## 🏛️ Project Architecture

```
wali-backend/
├── typescript-apps/     # All TypeScript code
│   ├── pwa/            # Next.js 16 PWA
│   └── notification-service/
├── python-services/     # All Python code
│   ├── policy-service/ # Insurance policy management
│   ├── claims-service/ # Claims processing
│   ├── compliance-service/ # Audit & reporting
│   └── identity-service/ # Authentication
├── go-services/         # All Go code
│   └── payment-service/ # Mobile money integration
├── database/            # Migrations and schemas
├── shared/              # Cross-language contracts
├── infrastructure/      # Docker, Fly.io configs
└── docs/               # This documentation
```

## 🌍 Language Support

- **FR**: French (primary)
- **DY**: Dioula (Jula)
- **BA**: Baoulé

## 🔐 Compliance

- **CIMA**: Insurance regulatory compliance
- **COSUMAF**: Financial authority reporting
- **Loi n°2013-450**: Data protection law
- **TRACFIN**: Anti-money laundering

## 📞 Support

- **Technical Support**: support@wali.ci
- **Security Issues**: security@wali.ci
- **Emergency**: 130 (toll-free)

---

*Last Updated: 2026-02-18*
