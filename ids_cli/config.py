"""Configuration management for IDS CLI"""

import os
import json
import pwd
from pathlib import Path
from typing import Dict, Any, Optional


def get_user_home():
    """Get the original user's home directory, even when running with sudo."""
    # Check if running with sudo
    if 'SUDO_USER' in os.environ:
        # Get the original user's home directory
        try:
            return Path(pwd.getpwnam(os.environ['SUDO_USER']).pw_dir)
        except KeyError:
            pass
    
    # Fall back to current user's home
    return Path.home()


class ConfigManager:
    """Manages IDS configuration stored in user home directory."""
    
    # Always store configuration in user's home directory
    # This works correctly even when running with sudo
    CONFIG_DIR = get_user_home() / '.ids'
    CONFIG_FILE = CONFIG_DIR / 'config.json'
    PID_FILE = CONFIG_DIR / 'server.pid'
    LOG_FILE = CONFIG_DIR / 'server.log'
    
    # Default settings
    DEFAULTS = {
        'interface': 'wlp3s0',
        'port': 5000,
        'model_dir': './model',
        'debug': False,
        'host': '0.0.0.0',
    }
    
    def __init__(self):
        """Initialize config manager and ensure directory exists."""
        self._ensure_config_dir()
    
    @classmethod
    def _ensure_config_dir(cls):
        """Create config directory if it doesn't exist."""
        cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def load(cls) -> Dict[str, Any]:
        """Load configuration from file.
        
        Returns:
            Dict with config values, or defaults if file doesn't exist
        """
        if cls.CONFIG_FILE.exists():
            try:
                with open(cls.CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults (defaults for missing keys)
                    return {**cls.DEFAULTS, **config}
            except Exception as e:
                print(f"Warning: Failed to load config: {e}")
                return cls.DEFAULTS.copy()
        return cls.DEFAULTS.copy()
    
    @classmethod
    def save(cls, config: Dict[str, Any]) -> bool:
        """Save configuration to file.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cls._ensure_config_dir()
            with open(cls.CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error: Failed to save config: {e}")
            return False
    
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        config = cls.load()
        return config.get(key, default)
    
    @classmethod
    def set(cls, key: str, value: Any) -> bool:
        """Set a configuration value.
        
        Args:
            key: Configuration key
            value: Value to set
            
        Returns:
            True if successful, False otherwise
        """
        config = cls.load()
        config[key] = value
        return cls.save(config)
    
    @classmethod
    def update(cls, updates: Dict[str, Any]) -> bool:
        """Update multiple configuration values.
        
        Args:
            updates: Dictionary of key-value pairs to update
            
        Returns:
            True if successful, False otherwise
        """
        config = cls.load()
        config.update(updates)
        return cls.save(config)
    
    @classmethod
    def reset(cls) -> bool:
        """Reset configuration to defaults.
        
        Returns:
            True if successful, False otherwise
        """
        return cls.save(cls.DEFAULTS.copy())
    
    @classmethod
    def get_pid(cls) -> Optional[int]:
        """Get stored process ID.
        
        Returns:
            Process ID or None if not stored
        """
        if cls.PID_FILE.exists():
            try:
                with open(cls.PID_FILE, 'r') as f:
                    return int(f.read().strip())
            except (ValueError, IOError):
                return None
        return None
    
    @classmethod
    def set_pid(cls, pid: int) -> bool:
        """Store process ID.
        
        Args:
            pid: Process ID to store
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cls._ensure_config_dir()
            with open(cls.PID_FILE, 'w') as f:
                f.write(str(pid))
            return True
        except IOError as e:
            print(f"Error: Failed to save PID: {e}")
            return False
    
    @classmethod
    def clear_pid(cls) -> bool:
        """Clear stored process ID.
        
        Returns:
            True if successful or file doesn't exist
        """
        try:
            if cls.PID_FILE.exists():
                cls.PID_FILE.unlink()
            return True
        except IOError as e:
            print(f"Error: Failed to clear PID: {e}")
            return False
    
    @classmethod
    def append_log(cls, message: str) -> bool:
        """Append message to log file.
        
        Args:
            message: Message to log
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cls._ensure_config_dir()
            with open(cls.LOG_FILE, 'a') as f:
                f.write(message + '\n')
            return True
        except IOError as e:
            print(f"Error: Failed to write log: {e}")
            return False
    
    @classmethod
    def get_logs(cls, lines: int = 50) -> str:
        """Get recent log lines.
        
        Args:
            lines: Number of lines to retrieve
            
        Returns:
            Log content (last N lines)
        """
        if not cls.LOG_FILE.exists():
            return "No logs available"
        
        try:
            with open(cls.LOG_FILE, 'r') as f:
                all_lines = f.readlines()
            
            # Get last N lines
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            return ''.join(recent_lines)
        except IOError:
            return "Error reading logs"
    
    @classmethod
    def clear_logs(cls) -> bool:
        """Clear log file.
        
        Returns:
            True if successful or file doesn't exist
        """
        try:
            if cls.LOG_FILE.exists():
                cls.LOG_FILE.unlink()
            return True
        except IOError as e:
            print(f"Error: Failed to clear logs: {e}")
            return False
    
    @classmethod
    def get_config_dir(cls) -> Path:
        """Get configuration directory path.
        
        Returns:
            Path to .ids directory
        """
        return cls.CONFIG_DIR
