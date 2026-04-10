#!/usr/bin/env python3
"""
Dashboard Integration Test
Verifies that all required endpoints and frontend components are in place.
"""

import os
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_frontend_files():
    """Check that all frontend files exist"""
    print("\n✓ Testing Frontend Files...")
    
    frontend_files = {
        'web/index.html': 'Dashboard HTML',
        'web/script.js': 'Dashboard JavaScript',
        'web/style.css': 'Dashboard CSS',
    }
    
    all_exist = True
    for filepath, description in frontend_files.items():
        full_path = project_root / filepath
        exists = full_path.exists()
        status = "✓" if exists else "✗"
        print(f"  {status} {description}: {filepath}")
        all_exist = all_exist and exists
    
    return all_exist


def test_backend_routes():
    """Check that required routes are implemented"""
    print("\n✓ Testing Backend Routes...")
    
    required_routes = [
        '/start',
        '/stop', 
        '/status',
        '/predictions',
        '/flows',
        '/stats',
        '/persistent-alerts',
        '/alert-stats',
        '/config',
    ]
    
    # Check if route exists in routes.py
    with open(project_root / 'ids_api/routes.py', 'r') as f:
        content = f.read()
    
    all_found = True
    for route in required_routes:
        # Check if route is decorated with @api_bp.route
        exists = f"@api_bp.route('{route}'" in content or f'@api_bp.route("{route}"' in content or f"route('{route}" in content
        status = "✓" if exists else "✗"
        print(f"  {status} Route {route} implemented")
        all_found = all_found and exists
    
    return all_found


def test_html_elements():
    """Verify required HTML elements exist"""
    print("\n✓ Testing HTML Elements...")
    
    with open(project_root / 'web/index.html', 'r') as f:
        html_content = f.read()
    
    required_elements = {
        'id="tab-live"': 'Live tab button',
        'id="tab-history"': 'History tab button',
        'id="tab-live-content"': 'Live tab content',
        'id="tab-history-content"': 'History tab content',
        'id="filterSeverity"': 'Severity filter',
        'id="filterAttackType"': 'Attack type filter',
        'id="filterLimit"': 'Result limit filter',
        'id="alertsTable"': 'Alerts table',
        'id="statTotalAlerts"': 'Total alerts stat',
        'id="statCritical"': 'Critical alerts stat',
    }
    
    all_found = True
    for element, description in required_elements.items():
        exists = element in html_content
        status = "✓" if exists else "✗"
        print(f"  {status} {description}: {element}")
        all_found = all_found and exists
    
    return all_found


def test_javascript_functions():
    """Verify required JavaScript functions exist"""
    print("\n✓ Testing JavaScript Functions...")
    
    with open(project_root / 'web/script.js', 'r') as f:
        js_content = f.read()
    
    required_functions = [
        'switchTab',
        'loadAlertHistory',
        'updateAlertTable',
        'updateAlertStats',
        'acknowledgeAlert',
        'exportAlertsCSV',
        'startAutoRefresh',
        'stopAutoRefresh',
        'startPipeline',
        'stopPipeline',
        'escapeHtml',
        'loadSettings',
        'saveSettings',
    ]
    
    all_found = True
    for func in required_functions:
        exists = f'function {func}(' in js_content or f'{func}()' in js_content
        status = "✓" if exists else "✗"
        print(f"  {status} Function: {func}()")
        all_found = all_found and exists
    
    return all_found


def test_css_styles():
    """Verify required CSS classes exist"""
    print("\n✓ Testing CSS Styles...")
    
    with open(project_root / 'web/style.css', 'r') as f:
        css_content = f.read()
    
    required_classes = [
        '.tab-nav',
        '.tab-btn',
        '.tab-btn.active',
        '.filter-grid',
        '.stats-grid',
        '.stat-box',
        '.table-alerts',
        '.severity-critical',
        '.severity-high',
        '.status-acked',
        '.status-pending',
        '.btn-ack',
    ]
    
    all_found = True
    for css_class in required_classes:
        exists = css_class in css_content
        status = "✓" if exists else "✗"
        print(f"  {status} CSS Class: {css_class}")
        all_found = all_found and exists
    
    return all_found


def main():
    """Run all tests"""
    print("=" * 60)
    print("IDS DASHBOARD INTEGRATION TEST")
    print("=" * 60)
    
    results = {
        'Frontend Files': test_frontend_files(),
        'Backend Routes': test_backend_routes(),
        'HTML Elements': test_html_elements(),
        'JavaScript Functions': test_javascript_functions(),
        'CSS Styles': test_css_styles(),
    }
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_pass = all(results.values())
    
    print("\n" + "=" * 60)
    if all_pass:
        print("✓ ALL TESTS PASSED - Dashboard is ready to use!")
    else:
        print("✗ SOME TESTS FAILED - Please review the output above")
    print("=" * 60 + "\n")
    
    return 0 if all_pass else 1


if __name__ == '__main__':
    sys.exit(main())
