"""Daemon/Process management for IDS server"""

import subprocess
import sys
import os
import signal
import time
from pathlib import Path
from typing import Tuple, Optional

from .config import ConfigManager


class DaemonManager:
    """Manages the IDS Flask server as a background process."""
    
    def __init__(self):
        """Initialize daemon manager."""
        pass  # No project_root needed anymore
    
    def start(self) -> Tuple[bool, str]:
        """Start the IDS server as background process.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        # Check if already running
        if self.is_running():
            return False, "Server is already running"
        
        # Get configuration
        config = ConfigManager.load()
        interface = config.get('interface', 'eth0')
        port = config.get('port', 5000)
        model_dir = config.get('model_dir', './model')
        
        try:
            # Prepare environment
            env = os.environ.copy()
            env['IDS_INTERFACE'] = interface
            env['IDS_PORT'] = str(port)
            env['IDS_MODEL_DIR'] = model_dir  # Already absolute from setup
            env['PYTHONUNBUFFERED'] = '1'
            
            # Determine Python executable
            python_exe = sys.executable
            
            # Start server using -m to run the module
            log_file = ConfigManager.LOG_FILE
            with open(log_file, 'ab') as log:
                if sys.platform == 'win32':
                    proc = subprocess.Popen(
                        [python_exe, '-m', 'run_server'],  # Changed this
                        env=env,
                        stdout=log,
                        stderr=log,
                        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                    )
                else:
                    proc = subprocess.Popen(
                        [python_exe, '-m', 'run_server'],  # Changed this
                        env=env,
                        stdout=log,
                        stderr=log,
                        preexec_fn=os.setsid if hasattr(os, 'setsid') else None
                    )
            
            # Give process time to start
            time.sleep(0.5)
            
            # Check if process is still running
            if proc.poll() is not None:
                return False, f"Server failed to start (exit code: {proc.returncode})"
            
            # Store PID
            ConfigManager.set_pid(proc.pid)
            ConfigManager.append_log(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Server started (PID: {proc.pid})")
            
            return True, f"Server started on http://localhost:{port} (PID: {proc.pid})"
        
        except Exception as e:
            ConfigManager.append_log(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error starting server: {e}")
            return False, f"Failed to start server: {e}"
    
    def stop(self) -> Tuple[bool, str]:
        """Stop the IDS server.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        pid = ConfigManager.get_pid()
        
        if pid is None:
            return False, "Server is not running (no PID found)"
        
        try:
            # Check if process exists
            if not self._process_exists(pid):
                ConfigManager.clear_pid()
                return False, "Server process not found"
            
            # Terminate process
            if sys.platform == 'win32':
                # Windows: use taskkill
                subprocess.run(
                    ['taskkill', '/PID', str(pid), '/F'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                # Unix: use SIGTERM then SIGKILL if needed
                try:
                    os.kill(pid, signal.SIGTERM)
                    time.sleep(1)
                    if self._process_exists(pid):
                        os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            
            # Wait for process to terminate
            time.sleep(0.5)
            
            # Clear PID
            ConfigManager.clear_pid()
            ConfigManager.append_log(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Server stopped (PID was: {pid})")
            
            return True, f"Server stopped (PID was: {pid})"
        
        except Exception as e:
            ConfigManager.append_log(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error stopping server: {e}")
            return False, f"Failed to stop server: {e}"
    
    def is_running(self) -> bool:
        """Check if server is running.
        
        Returns:
            True if server process is running
        """
        pid = ConfigManager.get_pid()
        
        if pid is None:
            return False
        
        return self._process_exists(pid)
    
    def get_status(self) -> Tuple[bool, str]:
        """Get detailed server status.
        
        Returns:
            Tuple of (running: bool, status_message: str)
        """
        pid = ConfigManager.get_pid()
        config = ConfigManager.load()
        
        running = self.is_running()
        
        status = {
            'running': running,
            'pid': pid if running else None,
            'interface': config.get('interface'),
            'port': config.get('port'),
            'url': f"http://localhost:{config.get('port')}" if running else None
        }
        
        if running:
            status_str = f"✓ Running on {status['url']} (PID: {pid})"
        else:
            status_str = "✗ Not running"
        
        return running, status_str
    
    @staticmethod
    def _process_exists(pid: int) -> bool:
        """Check if process with given PID exists.
        
        Args:
            pid: Process ID to check
            
        Returns:
            True if process exists
        """
        if sys.platform == 'win32':
            try:
                subprocess.run(
                    ['tasklist', '/FI', f'PID eq {pid}'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True
                )
                return True
            except subprocess.CalledProcessError:
                return False
        else:
            try:
                os.kill(pid, 0)  # Signal 0 just checks if process exists
                return True
            except (OSError, ProcessLookupError):
                return False
