# CIMA Security Audit Checklist

**Institution:** WALI Technology SAS  
**License:** CIMA Micro-Insurance  
**Audit Date:** ___________  
**Auditor:** ___________

---

## 1. AUTHENTICATION & AUTHORIZATION (ASVS V2, V4)

### Password Security
- [ ] Minimum password length: 12 characters
- [ ] Password complexity requirements enforced
- [ ] Argon2id password hashing (NOT bcrypt/MD5)
- [ ] Password history prevents reuse (last 5)
- [ ] Account lockout after 5 failed attempts
- [ ] Password reset tokens expire in 1 hour

### Session Management
- [ ] JWT access tokens expire in 15 minutes
- [ ] Refresh tokens expire in 7 days
- [ ] Tokens invalidated on logout
- [ ] Session timeout after 30 minutes inactivity
- [ ] Concurrent session limits per user
- [ ] Secure session cookie attributes (HttpOnly, Secure, SameSite)

### Multi-Factor Authentication
- [ ] MFA required for admin users
- [ ] MFA required for transactions > 500,000 XOF
- [ ] TOTP or SMS OTP implemented
- [ ] Backup recovery codes provided
- [ ] MFA bypass requires manager approval

### Authorization
- [ ] Role-Based Access Control (RBAC) implemented
- [ ] Principle of least privilege enforced
- [ ] Resource-level permissions (user can only see own claims)
- [ ] Admin actions require re-authentication
- [ ] API keys hashed in database (SHA-256)

**Evidence Required:**
- Code review of auth modules
- Penetration test results
- MFA configuration screenshot

---

## 2. DATA PROTECTION (ASVS V6)

### Encryption at Rest
- [ ] AES-256 encryption for database (PostgreSQL TDE)
- [ ] PII fields encrypted (phone, ID number, address)
- [ ] Encryption keys stored in HSM or KMS
- [ ] Key rotation every 90 days
- [ ] Backup encryption verified

### Encryption in Transit
- [ ] TLS 1.3 required (TLS 1.2 minimum)
- [ ] HSTS header with preload
- [ ] Certificate pinning for mobile apps
- [ ] No mixed content (HTTP resources on HTTPS pages)

### Data Classification
- [ ] Data classification policy documented
- [ ] PII identified and inventoried
- [ ] Data retention: 5 years (CIMA requirement)
- [ ] Secure deletion procedures
- [ ] Cross-border transfer restrictions

### Privacy
- [ ] Consent management implemented
- [ ] Right to deletion (GDPR-style)
- [ ] Data portability feature
- [ ] Privacy policy displayed
- [ ] Cookie consent banner

**Evidence Required:**
- Encryption configuration
- Data flow diagram
- Privacy policy document

---

## 3. API SECURITY (ASVS V13)

### Input Validation
- [ ] All inputs validated (whitelist approach)
- [ ] SQL injection prevention (parameterized queries)
- [ ] NoSQL injection prevention
- [ ] XSS prevention (output encoding)
- [ ] File upload restrictions (type, size, virus scan)
- [ ] Rate limiting on all endpoints

### API Standards
- [ ] OpenAPI/Swagger documentation
- [ ] API versioning (/v1/, /v2/)
- [ ] Content-Type validation
- [ ] Request size limits (10MB max)
- [ ] Timeout configuration (30s)

### Authentication
- [ ] OAuth 2.0 / OpenID Connect for third-party
- [ ] API key authentication for service-to-service
- [ ] JWT signature verification
- [ ] Token binding to prevent theft

### Rate Limiting
- [ ] Login: 5 attempts per 5 minutes
- [ ] API general: 100 requests per minute
- [ ] Sensitive operations: 10 per minute
- [ ] Burst handling configured
- [ ] Distributed rate limiting (Redis)

**Evidence Required:**
- API documentation
- Rate limiting configuration
- Penetration test results

---

## 4. INFRASTRUCTURE SECURITY

### Network Security
- [ ] VPC configured with private subnets
- [ ] Database not accessible from internet
- [ ] Security groups restrict access
- [ ] DDoS protection enabled (Cloudflare)
- [ ] WAF configured with OWASP rules

### Container Security
- [ ] Non-root user in containers
- [ ] Read-only filesystem where possible
- [ ] No secrets in container images
- [ ] Image scanning (Trivy/Snyk)
- [ ] Distroless or minimal base images

### Cloud Security (Fly.io)
- [ ] Secrets stored in Fly secrets (not env)
- [ ] Private networking between services
- [ ] Auto-scaling configured
- [ ] Health checks on all services
- [ ] Logging to central SIEM

### Database Security
- [ ] SSL required for connections
- [ ] Strong database passwords
- [ ] Least privilege database users
- [ ] Query logging enabled
- [ ] Automated backups (daily)

**Evidence Required:**
- Network architecture diagram
- Security group rules
- Container scan reports

---

## 5. APPLICATION SECURITY

### Code Security
- [ ] SAST tools integrated (Bandit, Semgrep)
- [ ] DAST tools integrated (OWASP ZAP)
- [ ] Dependency scanning (pip-audit)
- [ ] Secrets scanning (GitLeaks)
- [ ] Code review required for all changes

### Secure Headers
- [ ] Content-Security-Policy
- [ ] X-Frame-Options: DENY
- [ ] X-Content-Type-Options: nosniff
- [ ] Strict-Transport-Security
- [ ] Referrer-Policy

### Error Handling
- [ ] No stack traces in production
- [ ] Generic error messages
- [ ] Error logging to SIEM
- [ ] Request ID tracking
- [ ] Fail secure (deny by default)

### File Security
- [ ] File type validation
- [ ] File size limits
- [ ] Malware scanning (ClamAV)
- [ ] Secure storage (S3 with encryption)
- [ ] Path traversal prevention

**Evidence Required:**
- Scan reports
- Security headers test (securityheaders.com)
- Code review logs

---

## 6. MONITORING & LOGGING (ASVS V7)

### Audit Logging
- [ ] All authentication attempts logged
- [ ] All authorization decisions logged
- [ ] Data access logged (who, what, when)
- [ ] Admin actions logged
- [ ] Log integrity protection (hash chain)

### Security Monitoring
- [ ] SIEM implemented (Splunk/ELK)
- [ ] Real-time alerting
- [ ] Dashboard for security team
- [ ] Threat detection rules
- [ ] UEBA (User Entity Behavior Analytics)

### Alerting
- [ ] Brute force detection
- [ ] Unusual login times/locations
- [ ] Privilege escalation attempts
- [ ] Data exfiltration detection
- [ ] System compromise indicators

### Log Retention
- [ ] Security logs: 5 years (CIMA)
- [ ] Application logs: 1 year
- [ ] Access logs: 2 years
- [ ] Immutable log storage
- [ ] Log backup verification

**Evidence Required:**
- SIEM configuration
- Sample security logs
- Alert runbook

---

## 7. COMPLIANCE CONTROLS

### Regulatory Compliance
- [ ] CIMA AML procedures documented
- [ ] SAR filing procedure
- [ ] Customer due diligence (CDD)
- [ ] Enhanced due diligence (EDD)
- [ ] Transaction monitoring

### Data Protection
- [ ] Privacy impact assessment
- [ ] Data processing agreements
- [ ] Breach notification procedure (72 hours)
- [ ] Data protection officer assigned
- [ ] Regular compliance training

### Audit Trail
- [ ] Immutable audit logs
- [ ] Admin action approval workflow
- [ ] Configuration change tracking
- [ ] Access review (quarterly)
- [ ] Privileged access monitoring

### Documentation
- [ ] Information security policy
- [ ] Incident response plan
- [ ] Business continuity plan
- [ ] Disaster recovery plan
- [ ] Risk assessment (annual)

**Evidence Required:**
- Policy documents
- Training records
- Audit reports

---

## 8. INCIDENT RESPONSE

### Preparation
- [ ] Incident response team defined
- [ ] Response procedures documented
- [ ] Contact list updated
- [ ] Forensic tools available
- [ ] Legal counsel identified

### Detection
- [ ] Automated threat detection
- [ ] 24/7 monitoring coverage
- [ ] Escalation procedures
- [ ] Customer reporting channel
- [ ] Regulatory reporting procedure

### Response
- [ ] Containment procedures
- [ ] Evidence preservation
- [ ] Communication templates
- [ ] Law enforcement liaison
- [ ] Public relations plan

### Recovery
- [ ] System restoration procedures
- [ ] Data recovery tested
- [ ] Lessons learned process
- [ ] Post-incident review
- [ ] Control improvements

**Evidence Required:**
- Incident response plan
- Tabletop exercise results
- Contact list

---

## 9. THIRD-PARTY SECURITY

### Vendor Management
- [ ] Security assessment for all vendors
- [ ] Contractual security requirements
- [ ] Right to audit clauses
- [ ] Incident notification requirements
- [ ] Data processing agreements

### Payment Providers
- [ ] PCI DSS compliance verified (Orange Money)
- [ ] Integration security review
- [ ] Webhook signature verification
- [ ] IP allowlisting
- [ ] Failover procedures

### Cloud Providers
- [ ] Shared responsibility understood
- [ ] Fly.io security configuration
- [ ] AWS/GCP security (if used)
- [ ] Backup provider security
- [ ] Monitoring provider security

**Evidence Required:**
- Vendor security assessments
- Contract review
- Compliance certificates

---

## 10. BUSINESS CONTINUITY

### Availability
- [ ] 99.9% uptime target
- [ ] Redundant infrastructure
- [ ] Auto-failover configured
- [ ] Database replication
- [ ] Regular failover testing

### Backup & Recovery
- [ ] Database backups (daily)
- [ ] Backup encryption
- [ ] Offsite backup storage
- [ ] Recovery time objective (RTO): 4 hours
- [ ] Recovery point objective (RPO): 1 hour

### Disaster Recovery
- [ ] DR site identified
- [ ] DR procedures documented
- [ ] Annual DR drill
- [ ] Communication plan
- [ ] Customer notification procedure

**Evidence Required:**
- BCP/DR documentation
- Test results
- Backup verification logs

---

## SIGN-OFFS

### Technical Team
- [ ] Lead Developer: ___________ Date: _______
- [ ] Security Engineer: ___________ Date: _______
- [ ] DevOps Engineer: ___________ Date: _______

### Management
- [ ] CTO: ___________ Date: _______
- [ ] CISO: ___________ Date: _______
- [ ] Compliance Officer: ___________ Date: _______

### External Audit
- [ ] CIMA Representative: ___________ Date: _______
- [ ] External Auditor: ___________ Date: _______

---

## APPENDIX: Testing Commands

```bash
# 1. Dependency Audit
./security-audit/scripts/dependency_audit.sh

# 2. Security Headers Check
curl -I https://api.wali.ci/health | grep -E "(X-Frame|X-Content|Strict-Transport)"

# 3. SSL Configuration Test
nmap --script ssl-enum-ciphers -p 443 api.wali.ci

# 4. Rate Limiting Test
for i in {1..10}; do curl -s -o /dev/null -w "%{http_code}\n" https://api.wali.ci/login; done

# 5. SQL Injection Test
curl "https://api.wali.ci/claims?id=1' OR '1'='1"
# Should return 400 or empty, not all claims

# 6. XSS Test
curl -X POST https://api.wali.ci/claims \
  -d '{"description": "<script>alert(1)</script>"}'
# Should sanitize or reject
```

---

**Document Control**
- Version: 1.0
- Last Updated: 2026-02-18
- Next Review: 2026-05-18
- Owner: Security Team
