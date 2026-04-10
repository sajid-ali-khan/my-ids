"""IDS Store module - SQLite persistence for alerts and configuration."""

from .db import (
    init_db,
    save_alert,
    get_alerts,
    get_alert_stats,
    acknowledge_alert,
    get_whitelist,
    add_whitelist,
    remove_whitelist,
    is_ip_whitelisted,
    get_config,
    set_config,
    export_alerts_csv,
    cleanup_old_alerts
)

__all__ = [
    'init_db',
    'save_alert',
    'get_alerts',
    'get_alert_stats',
    'acknowledge_alert',
    'get_whitelist',
    'add_whitelist',
    'remove_whitelist',
    'is_ip_whitelisted',
    'get_config',
    'set_config',
    'export_alerts_csv',
    'cleanup_old_alerts'
]
