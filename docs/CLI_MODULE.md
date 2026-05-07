# IDS CLI Module

This document explains the `ids_cli` module in detail, including its responsibilities, file layout, command behavior, and how it coordinates with the rest of the application.

## Overview

The CLI module provides the operational entry point for the IDS application. It is designed to:

- Install and persist runtime configuration.
- Download and pin the ML model artifacts used by the pipeline.
- Start/stop the IDS server as a background process (cross‑platform).
- Surface server logs and status for quick troubleshooting.

The module is implemented using `click` and is packaged as a console script named `ids-cli`.

## Package Layout (`src/ids_cli`)

- `cli.py`
  - Click command group and subcommands.
  - User‑facing commands for setup, server lifecycle, logs, and configuration.
- `config.py`
  - `ConfigManager` for configuration, PID, and log file management.
  - Ensures config lives in the original user’s home directory even when using `sudo`.
- `daemon.py`
  - `DaemonManager` to run the server in the background and manage its lifecycle.
- `__init__.py`
  - Re‑exports `ConfigManager` and `DaemonManager` for external use.

## Console Entry Point

The CLI is registered in `pyproject.toml` under `[project.scripts]`:

- `ids-cli = ids_cli.cli:main`

`main()` invokes the Click group `cli()`, which exposes all subcommands. This is the entry point used by `pipx` or a standard package installation.

## Commands and Behavior

### `ids-cli setup`

Purpose:
- Initializes configuration and downloads the ML artifacts required by the pipeline.

Key actions:
- Creates `~/.ids/model/` and downloads two files from GitHub releases:
  - `random_forest_model.pkl`
  - `model_columns.joblib`
- Loads current configuration and prompts for:
  - `interface` (network interface)
  - `port` (server port)
- Sets `model_dir` to the auto‑managed `~/.ids/model/` path.
- Saves the configuration with `ConfigManager.update(...)`.

### `ids-cli start`

Purpose:
- Starts the IDS server as a background process.

Key actions:
- Uses `DaemonManager.start()` to spawn a background process.
- Emits a dashboard URL derived from the configured port.
- Writes server output to `~/.ids/server.log`.

### `ids-cli stop`

Purpose:
- Stops the running IDS server.

Key actions:
- Uses `DaemonManager.stop()` to locate the stored PID and terminate the process.
- Clears `~/.ids/server.pid` after termination.

### `ids-cli status`

Purpose:
- Shows whether the server is running and displays key configuration values.

Key actions:
- Uses `DaemonManager.get_status()` to check process liveness.
- Prints interface, port, and model directory.
- Exits with status code `0` if running, `1` otherwise.

### `ids-cli logs`

Purpose:
- Shows recent server log lines.

Key actions:
- `ConfigManager.get_logs(lines)` returns the last N lines from `~/.ids/server.log`.

### `ids-cli config`

Purpose:
- Displays the current configuration.

Key actions:
- Reads `~/.ids/config.json` and prints all keys.

### `ids-cli reset`

Purpose:
- Restores default configuration values.

Key actions:
- Calls `ConfigManager.reset()` and prints the resulting defaults.

### `ids-cli clear-logs`

Purpose:
- Clears the server log file.

Key actions:
- Deletes `~/.ids/server.log` if it exists.

### `ids-cli info`

Purpose:
- Shows product branding and a concise command reference.

Key actions:
- Prints a list of commands and the current dashboard URL.

## Configuration Management (`ConfigManager`)

The `ConfigManager` class centralizes configuration and runtime artifacts in a single directory:

- Config directory: `~/.ids/`
- Config file: `~/.ids/config.json`
- PID file: `~/.ids/server.pid`
- Log file: `~/.ids/server.log`

### Home Directory Handling

When the CLI is run with `sudo`, `ConfigManager.get_user_home()` uses `SUDO_USER` to resolve the original user’s home directory. This ensures configuration is saved in the correct user profile instead of root.

### Default Configuration

Defaults are defined in `ConfigManager.DEFAULTS` and merged into any existing config file:

- `interface`: `wlp3s0`
- `port`: `5000`
- `model_dir`: `./model`
- `debug`: `False`
- `host`: `0.0.0.0`
- `flusher_interval`: `20`
- `idle_timeout`: `30`
- `max_history`: `100`

### Key Methods

- `load()` / `save()` for persistence.
- `update()` to merge partial changes.
- `get()` / `set()` for single key access.
- `reset()` to restore defaults.
- `get_pid()` / `set_pid()` / `clear_pid()` for lifecycle tracking.
- `append_log()` / `get_logs()` / `clear_logs()` for log management.

## Process Management (`DaemonManager`)

`DaemonManager` launches and controls the IDS server as an independent background process. It wraps OS‑specific process management behavior to keep the CLI cross‑platform.

### How the Server Is Started

- Reads configuration (`interface`, `port`, `model_dir`).
- Prepares environment variables for `run_server`:
  - `IDS_INTERFACE`
  - `IDS_PORT`
  - `IDS_MODEL_DIR`
  - `PYTHONUNBUFFERED=1`
- Launches the server with `python -m run_server`.
  - This relies on `scripts/run_server.py` being listed in `pyproject.toml` under `py-modules`.
- Directs stdout/stderr into `~/.ids/server.log`.
- Saves the process ID to `~/.ids/server.pid`.

### Windows vs. Unix Handling

- **Windows**
  - Uses `CREATE_NEW_PROCESS_GROUP` to spawn the process.
  - Stops the process via `taskkill`.
- **Unix/macOS**
  - Uses `os.setsid` when available.
  - Sends `SIGTERM`, then `SIGKILL` if the process is still alive.

### Status Detection

- `get_status()` combines PID lookup with process liveness checks.
- Returns human‑friendly status strings like `Running on http://localhost:5000`.

## Integration with the Server (`scripts/run_server.py`)

When the CLI starts the server, `scripts/run_server.py`:

- Loads configuration via `ConfigManager`.
- Ensures default keys are present in the saved configuration.
- Initializes `PipelineManager` with the configuration values.
- Starts the Flask API app (`ids_api.create_app`).

This connection is why `model_dir` and network settings configured in the CLI directly drive the runtime behavior of the IDS server.

## Operational Notes

- **Network capture permissions**: On Linux, packet capture often requires root privileges. The CLI supports `sudo`, and configuration is still stored in the original user’s home directory.
- **Model downloads**: `ids-cli setup` depends on internet access to fetch model files from GitHub releases.
- **Logging**: All server output is routed to `~/.ids/server.log`. Use `ids-cli logs` or `ids-cli clear-logs` to view or reset logs.

## Summary

The `ids_cli` module provides a complete operational interface for the IDS application. It owns configuration persistence, server lifecycle management, log access, and bootstrapping tasks, while delegating actual IDS execution to `scripts/run_server.py` and the core pipeline. This separation keeps the CLI focused on orchestration and user experience while maintaining cross‑platform compatibility.
