#!/usr/bin/env python3
"""
WALI Penetration Testing Framework

Automated security testing for CIMA compliance.
Tests OWASP Top 10 vulnerabilities.

Usage:
    python penetration_test.py --target https://api.wali.ci --full
    python penetration_test.py --target http://localhost:8000 --quick

Requirements:
    pip install requests aiohttp
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from typing import Dict, List, Tuple
from urllib.parse import urljoin, urlparse

import requests
import aiohttp

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class SecurityTester:
    """Main security testing framework."""
    
    def __init__(self, target: str, verbose: bool = False):
        self.target = target.rstrip('/')
        self.verbose = verbose
        self.results: List[Dict] = []
        self.session = requests.Session()
        
        # Configure session
        self.session.headers.update({
            'User-Agent': 'WALI-Security-Test/1.0',
            'Accept': 'application/json',
        })
    
    def log(self, message: str, level: str = 'info'):
        """Log message if verbose."""
        if self.verbose:
            getattr(logger, level)(message)
    
    def add_result(self, test_name: str, passed: bool, severity: str, details: str):
        """Add test result."""
        result = {
            'test': test_name,
            'passed': passed,
            'severity': severity,
            'details': details,
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
        }
        self.results.append(result)
        
        status = 'PASS' if passed else 'FAIL'
        logger.info(f"[{status}] {test_name}: {details}")
    
    # ═════════════════════════════════════════════════════════════════
    # TEST CASES
    # ═════════════════════════════════════════════════════════════════
    
    def test_security_headers(self) -> None:
        """Test OWASP security headers (A05)."""
        logger.info("\n=== Testing Security Headers (A05) ===")
        
        try:
            response = self.session.get(f"{self.target}/health")
            headers = response.headers
            
            checks = [
                ('Strict-Transport-Security', 'HSTS'),
                ('X-Frame-Options', 'Clickjacking protection'),
                ('X-Content-Type-Options', 'MIME sniffing protection'),
                ('Content-Security-Policy', 'CSP'),
                ('X-XSS-Protection', 'XSS protection'),
            ]
            
            missing = []
            for header, description in checks:
                if header not in headers:
                    missing.append(f"{header} ({description})")
            
            if missing:
                self.add_result(
                    'Security Headers',
                    False,
                    'high',
                    f"Missing headers: {', '.join(missing)}"
                )
            else:
                self.add_result(
                    'Security Headers',
                    True,
                    'info',
                    'All OWASP security headers present'
                )
                
        except Exception as e:
            self.add_result('Security Headers', False, 'high', f'Error: {e}')
    
    def test_sql_injection(self) -> None:
        """Test SQL injection vulnerability (A03)."""
        logger.info("\n=== Testing SQL Injection (A03) ===")
        
        payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users --",
            "1' AND 1=1 --",
        ]
        
        vulnerable = False
        for payload in payloads:
            try:
                # Test various endpoints
                endpoints = [
                    f"/api/v1/partners/NSIA/enrollments?id={payload}",
                    f"/api/v1/partners/NSIA/incidents?id={payload}",
                ]
                
                for endpoint in endpoints:
                    url = f"{self.target}{endpoint}"
                    response = self.session.get(url, timeout=5)
                    
                    # Check for SQL error indicators
                    error_indicators = [
                        'sql',
                        'mysql',
                        'postgresql',
                        'syntax error',
                        'unexpected',
                    ]
                    
                    response_text = response.text.lower()
                    if any(ind in response_text for ind in error_indicators):
                        vulnerable = True
                        self.log(f"Potential SQL injection: {payload}", 'warning')
                        break
                        
            except Exception as e:
                self.log(f"Error testing payload {payload}: {e}", 'debug')
        
        if vulnerable:
            self.add_result(
                'SQL Injection',
                False,
                'critical',
                'Potential SQL injection vulnerability detected'
            )
        else:
            self.add_result(
                'SQL Injection',
                True,
                'info',
                'No SQL injection vulnerability detected'
            )
    
    def test_xss(self) -> None:
        """Test Cross-Site Scripting (A03)."""
        logger.info("\n=== Testing XSS (A03) ===")
        
        xss_payloads = [
            '<script>alert(1)</script>',
            '<img src=x onerror=alert(1)>',
            'javascript:alert(1)',
            '<body onload=alert(1)>',
        ]
        
        vulnerable = False
        
        # Test claim submission with XSS
        for payload in xss_payloads:
            try:
                data = {
                    'description': payload,
                    'incident_type': 'TEST',
                }
                
                response = self.session.post(
                    f"{self.target}/api/v1/partners/NSIA/incidents/submit-json",
                    json=data,
                    timeout=5
                )
                
                # Check if payload is reflected without encoding
                if payload in response.text and '<script>' in response.text:
                    vulnerable = True
                    break
                    
            except Exception as e:
                self.log(f"Error testing XSS payload: {e}", 'debug')
        
        if vulnerable:
            self.add_result(
                'XSS',
                False,
                'high',
                'Potential XSS vulnerability detected'
            )
        else:
            self.add_result(
                'XSS',
                True,
                'info',
                'No XSS vulnerability detected'
            )
    
    def test_authentication(self) -> None:
        """Test authentication mechanisms (A07)."""
        logger.info("\n=== Testing Authentication (A07) ===")
        
        # Test weak password
        weak_passwords = ['password123', '123456', 'admin', 'wali']
        
        for password in weak_passwords:
            try:
                # Attempt registration/login with weak password
                data = {
                    'phone': '+22501000000',
                    'password': password,
                }
                
                response = self.session.post(
                    f"{self.target}/api/auth/register",
                    json=data,
                    timeout=5
                )
                
                if response.status_code in [200, 201]:
                    self.add_result(
                        'Password Strength',
                        False,
                        'high',
                        f'Weak password accepted: {password}'
                    )
                    return
                    
            except Exception as e:
                self.log(f"Error testing password: {e}", 'debug')
        
        self.add_result(
            'Password Strength',
            True,
            'info',
            'Weak passwords rejected'
        )
    
    def test_rate_limiting(self) -> None:
        """Test rate limiting (A07)."""
        logger.info("\n=== Testing Rate Limiting (A07) ===")
        
        try:
            # Make multiple rapid requests
            responses = []
            for i in range(15):
                response = self.session.get(
                    f"{self.target}/health",
                    timeout=5
                )
                responses.append(response.status_code)
                time.sleep(0.1)  # Small delay
            
            # Check if rate limiting triggered (429 status)
            if 429 in responses:
                self.add_result(
                    'Rate Limiting',
                    True,
                    'info',
                    'Rate limiting is active (429 returned)'
                )
            else:
                self.add_result(
                    'Rate Limiting',
                    False,
                    'medium',
                    'Rate limiting may not be enforced'
                )
                
        except Exception as e:
            self.add_result('Rate Limiting', False, 'medium', f'Error: {e}')
    
    def test_ssrf(self) -> None:
        """Test Server-Side Request Forgery (A10)."""
        logger.info("\n=== Testing SSRF (A10) ===")
        
        ssrf_payloads = [
            'http://localhost:22',
            'http://127.0.0.1:80',
            'http://169.254.169.254/latest/meta-data/',  # AWS metadata
            'file:///etc/passwd',
        ]
        
        vulnerable = False
        
        for payload in ssrf_payloads:
            try:
                # Try to submit URL that should be blocked
                data = {'document_url': payload}
                
                response = self.session.post(
                    f"{self.target}/api/v1/documents/fetch",
                    json=data,
                    timeout=5
                )
                
                # If request succeeds or returns different error, might be vulnerable
                if response.status_code == 200:
                    vulnerable = True
                    break
                    
            except Exception as e:
                self.log(f"SSRF test error: {e}", 'debug')
        
        if vulnerable:
            self.add_result(
                'SSRF',
                False,
                'high',
                'Potential SSRF vulnerability detected'
            )
        else:
            self.add_result(
                'SSRF',
                True,
                'info',
                'No SSRF vulnerability detected'
            )
    
    def test_information_disclosure(self) -> None:
        """Test information disclosure (A01)."""
        logger.info("\n=== Testing Information Disclosure (A01) ===")
        
        try:
            # Check for stack traces in error responses
            response = self.session.get(
                f"{self.target}/api/nonexistent-endpoint-12345",
                timeout=5
            )
            
            error_indicators = [
                'traceback',
                'stack trace',
                'exception',
                'debug',
                'sqlalchemy',
                'django',
                'flask.debug',
            ]
            
            response_text = response.text.lower()
            leaked_info = [ind for ind in error_indicators if ind in response_text]
            
            if leaked_info:
                self.add_result(
                    'Information Disclosure',
                    False,
                    'medium',
                    f'Sensitive info in errors: {", ".join(leaked_info)}'
                )
            else:
                self.add_result(
                    'Information Disclosure',
                    True,
                    'info',
                    'No sensitive information leaked in errors'
                )
                
        except Exception as e:
            self.add_result('Information Disclosure', False, 'medium', f'Error: {e}')
    
    def test_encryption(self) -> None:
        """Test encryption in transit."""
        logger.info("\n=== Testing Encryption in Transit ===")
        
        parsed = urlparse(self.target)
        
        if parsed.scheme != 'https':
            self.add_result(
                'HTTPS',
                False,
                'critical',
                'Target does not use HTTPS - data transmitted in plaintext!'
            )
        else:
            self.add_result(
                'HTTPS',
                True,
                'info',
                'HTTPS is enabled'
            )
    
    # ═════════════════════════════════════════════════════════════════
    # REPORTING
    # ═════════════════════════════════════════════════════════════════
    
    def generate_report(self) -> Dict:
        """Generate test report."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r['passed'])
        failed = total - passed
        
        critical = sum(1 for r in self.results if not r['passed'] and r['severity'] == 'critical')
        high = sum(1 for r in self.results if not r['passed'] and r['severity'] == 'high')
        
        return {
            'summary': {
                'target': self.target,
                'total_tests': total,
                'passed': passed,
                'failed': failed,
                'critical_issues': critical,
                'high_issues': high,
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            },
            'results': self.results,
        }
    
    def print_report(self):
        """Print formatted report."""
        report = self.generate_report()
        summary = report['summary']
        
        print("\n" + "=" * 70)
        print("WALI PENETRATION TEST REPORT")
        print("=" * 70)
        print(f"Target: {summary['target']}")
        print(f"Timestamp: {summary['timestamp']}")
        print("-" * 70)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']} ✓")
        print(f"Failed: {summary['failed']} ✗")
        print(f"Critical Issues: {summary['critical_issues']} 🔴")
        print(f"High Issues: {summary['high_issues']} 🟠")
        print("=" * 70)
        
        # Failed tests
        failed_tests = [r for r in self.results if not r['passed']]
        if failed_tests:
            print("\nFAILED TESTS:")
            for test in failed_tests:
                print(f"  [{test['severity'].upper()}] {test['test']}")
                print(f"    {test['details']}")
        
        print("\n" + "=" * 70)
        
        # Compliance status
        if summary['critical_issues'] > 0:
            print("STATUS: NOT COMPLIANT 🔴")
            print("Critical security issues must be fixed before production!")
        elif summary['high_issues'] > 0:
            print("STATUS: PARTIALLY COMPLIANT 🟠")
            print("High severity issues should be addressed soon.")
        else:
            print("STATUS: COMPLIANT ✓")
            print("No critical or high severity issues found.")
        
        print("=" * 70)
        
        return report
    
    def save_report(self, filename: str):
        """Save report to JSON file."""
        report = self.generate_report()
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Report saved to {filename}")


def main():
    parser = argparse.ArgumentParser(description='WALI Penetration Testing Framework')
    parser.add_argument('--target', '-t', required=True, help='Target URL (e.g., https://api.wali.ci)')
    parser.add_argument('--full', '-f', action='store_true', help='Run full test suite')
    parser.add_argument('--quick', '-q', action='store_true', help='Run quick tests only')
    parser.add_argument('--output', '-o', help='Save report to file (JSON)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    tester = SecurityTester(args.target, verbose=args.verbose)
    
    # Always run these basic tests
    tester.test_encryption()
    tester.test_security_headers()
    tester.test_information_disclosure()
    
    if args.full or not args.quick:
        # Run full test suite
        tester.test_sql_injection()
        tester.test_xss()
        tester.test_authentication()
        tester.test_rate_limiting()
        tester.test_ssrf()
    
    # Generate and print report
    report = tester.print_report()
    
    if args.output:
        tester.save_report(args.output)
    
    # Exit with error code if critical issues found
    if report['summary']['critical_issues'] > 0:
        sys.exit(1)
    
    sys.exit(0)


if __name__ == '__main__':
    main()
