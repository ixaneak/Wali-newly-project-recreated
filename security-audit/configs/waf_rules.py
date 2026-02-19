"""
WAF (Web Application Firewall) Rules for WALI

OWASP Core Rule Set (CRS) implementation for Fly.io and Cloudflare.
CIMA Requirement: WAF must protect against OWASP Top 10
"""

from typing import List, Dict, Any, Tuple
import re


class WAFRule:
    """Base WAF rule class."""
    
    def __init__(self, rule_id: str, name: str, severity: str, pattern: str):
        self.rule_id = rule_id
        self.name = name
        self.severity = severity
        self.pattern = pattern


# SQL Injection Rules
SQL_INJECTION_RULES = [
    WAFRule("942100", "SQL Injection via libinjection", "CRITICAL", 
            r"(?i:(?:select\s*\*\s*from|(?:delete|drop|truncate)\s+table|union\s+select))"),
    WAFRule("942110", "SQL Injection Testing", "HIGH",
            r"(?i:(?:sleep\s*\(\s*\d*\s*\)|benchmark\s*\(.*\,.*\)))"),
    WAFRule("942120", "SQL Operator Detected", "HIGH",
            r"(?i:(?:\bor\b|\band\b)\s+(?:\d+|'[^']*')\s*=\s*(?:\d+|'[^']*'))"),
    WAFRule("942150", "SQL Injection", "CRITICAL",
            r"(?i:(?:;\s*(?:drop|delete|truncate|insert|update|select|union)))"),
]

# XSS Rules
XSS_RULES = [
    WAFRule("941100", "XSS Attack Detected", "CRITICAL", r"(?i:<script[^>]*>)"),
    WAFRule("941120", "XSS Event Handler", "HIGH", r"(?i:(?:on\w+\s*=\s*['\"]?[^'\"]*['\"]?))"),
    WAFRule("941130", "XSS URI Vector", "HIGH", r"(?i:(?:javascript:|vbscript:|data:text/html))"),
    WAFRule("941160", "XSS HTML Injection", "CRITICAL", r"(?i:(?:<\s*body[^>]*onload|<\s*img[^>]*onerror))"),
]

# Path Traversal Rules
PATH_TRAVERSAL_RULES = [
    WAFRule("930100", "Path Traversal", "HIGH", r"(?:\.\./|\.\.%2f|%2e%2e/)"),
    WAFRule("930120", "OS File Access", "HIGH", r"(?i:(?:/etc/passwd|/etc/shadow|boot\.ini|\.htaccess))"),
]

# RCE Rules
RCE_RULES = [
    WAFRule("932100", "Unix Command Injection", "CRITICAL", r"(?i:(?:;|\||&&|`)(?:\s*\b(?:cat|ls|whoami|wget|curl|bash)\b))"),
    WAFRule("932110", "Windows Command Injection", "CRITICAL", r"(?i:(?:cmd|powershell)\s+/c)"),
]

# Bot Detection
BOT_DETECTION_RULES = [
    WAFRule("913100", "Bad User Agents", "HIGH", r"(?i:(?:sqlmap|nikto|nmap|burp|metasploit|acunetix))"),
]


def validate_against_waf_rules(value: str, rules: List[WAFRule]) -> Tuple[bool, List[WAFRule]]:
    """Validate input against WAF rules."""
    triggered = []
    for rule in rules:
        if re.search(rule.pattern, value):
            triggered.append(rule)
    return len(triggered) == 0, triggered


def check_all_rules(value: str) -> Tuple[bool, List[WAFRule]]:
    """Check value against all WAF rule categories."""
    all_rules = SQL_INJECTION_RULES + XSS_RULES + PATH_TRAVERSAL_RULES + RCE_RULES
    return validate_against_waf_rules(value, all_rules)


# Cloudflare WAF Config
CLOUDFLARE_WAF_CONFIG = {
    "name": "WALI-OWASP-Rules",
    "rules": [
        {"action": "block", "expression": "(http.request.uri.path contains \"../\")"},
        {"action": "block", "expression": "(http.request.uri.query contains \"<script\")"},
        {"action": "block", "expression": "(http.user_agent contains \"sqlmap\")"},
        {"action": "rate_limit", "expression": "(http.request.uri.path contains \"/login\")", 
         "limit": {"period": 60, "requests": 5}},
    ]
}


def get_cloudflare_waf_config() -> Dict:
    return CLOUDFLARE_WAF_CONFIG


__all__ = ['SQL_INJECTION_RULES', 'XSS_RULES', 'PATH_TRAVERSAL_RULES', 'RCE_RULES',
           'BOT_DETECTION_RULES', 'validate_against_waf_rules', 'check_all_rules',
           'get_cloudflare_waf_config']
