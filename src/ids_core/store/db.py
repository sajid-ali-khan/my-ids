"""SQLite database for persistent alert storage and configuration.

Thread-safe operations with WAL mode for concurrent read/write access.
Classification thread writes alerts, FastAPI reads alerts/stats concurrently.
"""

import sqlite3
import threading
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import time
import logging

logger = logging.getLogger(__name__)

# Database path - /opt/nids/alerts.db
DB_PATH = Path('/opt/nids/alerts.db')
DB_LOCK = threading.RLock()  # Thread-safe access


def ensure_db_dir():
    """Ensure /opt/nids directory exists."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Set directory permissions
    try:
        os.chmod(DB_PATH.parent, 0o755)
    except:
        pass


def init_db():
    """Initialize database with tables if they don't exist.
    
    Creates three tables:
    1. alerts - stores detected attacks
    2. whitelist - IP whitelist for suppressing alerts
    3. config - runtime configuration (sensitivity, thresholds, etc)
    
    Enables WAL mode for concurrent read/write access.
    """
    ensure_db_dir()
    
    with DB_LOCK:
        try:
            conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, timeout=10)
            conn.row_factory = sqlite3.Row
            
            # Enable WAL mode (critical for concurrent access)
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA synchronous=NORMAL')  # Balance safety/performance
            
            cursor = conn.cursor()
            
            # Create alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    src_ip TEXT NOT NULL,
                    dst_ip TEXT NOT NULL,
                    src_port INTEGER NOT NULL,
                    dst_port INTEGER NOT NULL,
                    protocol INTEGER NOT NULL,
                    attack_type TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    severity TEXT NOT NULL,
                    is_aggregated INTEGER DEFAULT 0,
                    flow_count INTEGER DEFAULT 1,
                    acknowledged INTEGER DEFAULT 0,
                    notes TEXT DEFAULT NULL
                )
            ''')
            
            # Create indexes for common queries
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp DESC)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_src_ip ON alerts(src_ip)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_dst_ip ON alerts(dst_ip)')
            
            # Create whitelist table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS whitelist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip TEXT UNIQUE NOT NULL,
                    note TEXT,
                    added_at REAL NOT NULL
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_whitelist_ip ON whitelist(ip)')
            
            # Create config table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info(f'[DB] Initialized database at {DB_PATH}')
            logger.info('[DB] WAL mode enabled for concurrent read/write access')
            
        except Exception as e:
            logger.error(f'[DB] Failed to initialize database: {e}')
            raise


def get_connection():
    """Get a database connection.
    
    Uses thread-safe mode with check_same_thread=False.
    WAL mode ensures concurrent read/write is safe.
    
    Returns:
        sqlite3.Connection
    """
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    # Ensure WAL is enabled for this connection
    conn.execute('PRAGMA journal_mode=WAL')
    return conn


def save_alert(alert: Dict[str, Any]) -> int:
    """Save an alert to the database.
    
    Args:
        alert: Dictionary with keys:
            - timestamp (float): Unix timestamp
            - src_ip (str): Source IP
            - dst_ip (str): Destination IP
            - src_port (int): Source port
            - dst_port (int): Destination port
            - protocol (int): Protocol (6=TCP, 17=UDP)
            - attack_type (str): Type of attack (e.g., 'SSH Brute Force')
            - confidence (float): Confidence 0.0-1.0
            - severity (str): 'critical', 'high', 'medium', 'low'
            - is_aggregated (bool, optional): True if from flow aggregator
            - flow_count (int, optional): Number of flows in aggregation
            
    Returns:
        int: Alert ID
    """
    with DB_LOCK:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO alerts 
                (timestamp, src_ip, dst_ip, src_port, dst_port, protocol, 
                 attack_type, confidence, severity, is_aggregated, flow_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert.get('timestamp', time.time()),
                alert.get('src_ip'),
                alert.get('dst_ip'),
                alert.get('src_port'),
                alert.get('dst_port'),
                alert.get('protocol'),
                alert.get('attack_type'),
                alert.get('confidence'),
                alert.get('severity'),
                alert.get('is_aggregated', 0),
                alert.get('flow_count', 1)
            ))
            
            conn.commit()
            alert_id = cursor.lastrowid
            conn.close()
            
            logger.debug(f'[DB] Alert saved (ID: {alert_id}, Type: {alert.get("attack_type")})')
            return alert_id
            
        except Exception as e:
            logger.error(f'[DB] Failed to save alert: {e}')
            raise


def get_alerts(limit: int = 50, offset: int = 0, severity: Optional[str] = None,
               attack_type: Optional[str] = None, start_time: Optional[float] = None) -> List[Dict]:
    """Retrieve alerts from database.
    
    Args:
        limit: Maximum number of alerts to return
        offset: Number of alerts to skip
        severity: Filter by severity ('critical', 'high', 'medium', 'low')
        attack_type: Filter by attack type
        start_time: Filter by minimum timestamp (Unix time)
        
    Returns:
        List of alert dictionaries
    """
    with DB_LOCK:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            query = 'SELECT * FROM alerts WHERE 1=1'
            params = []
            
            if severity:
                query += ' AND severity = ?'
                params.append(severity)
            
            if attack_type:
                query += ' AND attack_type = ?'
                params.append(attack_type)
            
            if start_time:
                query += ' AND timestamp >= ?'
                params.append(start_time)
            
            query += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?'
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            alerts = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return alerts
            
        except Exception as e:
            logger.error(f'[DB] Failed to retrieve alerts: {e}')
            return []


def get_alert_stats() -> Dict[str, Any]:
    """Get statistics about stored alerts.
    
    Returns:
        Dict with:
        - total_alerts (int)
        - by_severity (dict)
        - by_attack_type (dict)
        - critical_count (int)
        - high_count (int)
        - acknowledged_count (int)
        - today_count (int)
    """
    with DB_LOCK:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Total alerts
            cursor.execute('SELECT COUNT(*) as count FROM alerts')
            total = cursor.fetchone()['count']
            
            # By severity
            cursor.execute('SELECT severity, COUNT(*) as count FROM alerts GROUP BY severity')
            by_severity = {row['severity']: row['count'] for row in cursor.fetchall()}
            
            # By attack type
            cursor.execute('SELECT attack_type, COUNT(*) as count FROM alerts GROUP BY attack_type ORDER BY count DESC LIMIT 10')
            by_attack_type = {row['attack_type']: row['count'] for row in cursor.fetchall()}
            
            # Critical count
            cursor.execute('SELECT COUNT(*) as count FROM alerts WHERE severity = "critical"')
            critical_count = cursor.fetchone()['count']
            
            # High count
            cursor.execute('SELECT COUNT(*) as count FROM alerts WHERE severity = "high"')
            high_count = cursor.fetchone()['count']
            
            # Acknowledged count
            cursor.execute('SELECT COUNT(*) as count FROM alerts WHERE acknowledged = 1')
            acked_count = cursor.fetchone()['count']
            
            # Today's alerts
            today_ts = time.time() - (24 * 3600)  # Last 24 hours
            cursor.execute('SELECT COUNT(*) as count FROM alerts WHERE timestamp >= ?', (today_ts,))
            today_count = cursor.fetchone()['count']
            
            conn.close()
            
            return {
                'total_alerts': total,
                'by_severity': by_severity,
                'by_attack_type': by_attack_type,
                'critical_count': critical_count,
                'high_count': high_count,
                'acknowledged_count': acked_count,
                'today_count': today_count
            }
            
        except Exception as e:
            logger.error(f'[DB] Failed to get alert stats: {e}')
            return {
                'total_alerts': 0,
                'by_severity': {},
                'by_attack_type': {},
                'critical_count': 0,
                'high_count': 0,
                'acknowledged_count': 0,
                'today_count': 0
            }


def acknowledge_alert(alert_id: int, notes: str = None) -> bool:
    """Mark an alert as acknowledged.
    
    Args:
        alert_id: ID of alert to acknowledge
        notes: Optional notes about the alert
        
    Returns:
        bool: True if successful
    """
    with DB_LOCK:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'UPDATE alerts SET acknowledged = 1, notes = ? WHERE id = ?',
                (notes, alert_id)
            )
            
            conn.commit()
            conn.close()
            
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f'[DB] Failed to acknowledge alert: {e}')
            return False


def get_whitelist() -> List[Dict]:
    """Get all whitelisted IPs.
    
    Returns:
        List of whitelist entries
    """
    with DB_LOCK:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM whitelist ORDER BY added_at DESC')
            entries = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return entries
            
        except Exception as e:
            logger.error(f'[DB] Failed to retrieve whitelist: {e}')
            return []


def add_whitelist(ip: str, note: str = None) -> bool:
    """Add an IP to the whitelist.
    
    Args:
        ip: IP address to whitelist
        note: Optional note about why it's whitelisted
        
    Returns:
        bool: True if successful
    """
    with DB_LOCK:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'INSERT INTO whitelist (ip, note, added_at) VALUES (?, ?, ?)',
                (ip, note, time.time())
            )
            
            conn.commit()
            conn.close()
            
            logger.info(f'[DB] IP whitelisted: {ip}')
            return True
            
        except sqlite3.IntegrityError:
            logger.warning(f'[DB] IP already whitelisted: {ip}')
            return False
        except Exception as e:
            logger.error(f'[DB] Failed to add whitelist entry: {e}')
            return False


def remove_whitelist(ip: str) -> bool:
    """Remove an IP from the whitelist.
    
    Args:
        ip: IP address to remove
        
    Returns:
        bool: True if successful
    """
    with DB_LOCK:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM whitelist WHERE ip = ?', (ip,))
            
            conn.commit()
            conn.close()
            
            logger.info(f'[DB] IP removed from whitelist: {ip}')
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f'[DB] Failed to remove whitelist entry: {e}')
            return False


def is_ip_whitelisted(ip: str) -> bool:
    """Check if an IP is whitelisted.
    
    Args:
        ip: IP address to check
        
    Returns:
        bool: True if whitelisted
    """
    with DB_LOCK:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT 1 FROM whitelist WHERE ip = ?', (ip,))
            result = cursor.fetchone() is not None
            conn.close()
            
            return result
            
        except Exception as e:
            logger.error(f'[DB] Failed to check whitelist: {e}')
            return False


def get_config(key: str, default: Any = None) -> Any:
    """Get a configuration value.
    
    Args:
        key: Configuration key
        default: Default value if not found
        
    Returns:
        Configuration value or default
    """
    with DB_LOCK:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT value FROM config WHERE key = ?', (key,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                # Try to parse as float/int if possible
                value = row['value']
                try:
                    return float(value)
                except ValueError:
                    return value
            
            return default
            
        except Exception as e:
            logger.error(f'[DB] Failed to get config: {e}')
            return default


def set_config(key: str, value: Any) -> bool:
    """Set a configuration value.
    
    Args:
        key: Configuration key
        value: Value to set
        
    Returns:
        bool: True if successful
    """
    with DB_LOCK:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)',
                (key, str(value))
            )
            
            conn.commit()
            conn.close()
            
            logger.debug(f'[DB] Config updated: {key} = {value}')
            return True
            
        except Exception as e:
            logger.error(f'[DB] Failed to set config: {e}')
            return False


def export_alerts_csv(filepath: str, severity: Optional[str] = None) -> bool:
    """Export alerts to CSV file.
    
    Args:
        filepath: Path to write CSV to
        severity: Optional filter by severity
        
    Returns:
        bool: True if successful
    """
    try:
        import csv
        
        alerts = get_alerts(limit=10000, severity=severity)
        
        if not alerts:
            logger.warning('[DB] No alerts to export')
            return False
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=alerts[0].keys())
            writer.writeheader()
            writer.writerows(alerts)
        
        logger.info(f'[DB] Exported {len(alerts)} alerts to {filepath}')
        return True
        
    except Exception as e:
        logger.error(f'[DB] Failed to export alerts: {e}')
        return False


def cleanup_old_alerts(days: int = 30) -> int:
    """Delete alerts older than specified days.
    
    Args:
        days: Number of days to keep
        
    Returns:
        int: Number of alerts deleted
    """
    with DB_LOCK:
        try:
            cutoff_time = time.time() - (days * 24 * 3600)
            
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM alerts WHERE timestamp < ?', (cutoff_time,))
            
            conn.commit()
            deleted = cursor.rowcount
            conn.close()
            
            logger.info(f'[DB] Deleted {deleted} alerts older than {days} days')
            return deleted
            
        except Exception as e:
            logger.error(f'[DB] Failed to clean up old alerts: {e}')
            return 0
