# IDS Installation Guide

Complete installation guide for the Network Intrusion Detection System. Choose the method that works best for your environment.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Installation Methods](#installation-methods)
4. [Post-Installation](#post-installation)
5. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

- **Python:** 3.8+ 
- **OS:** Linux, Windows, macOS, WSL2
- **Disk:** 200MB+ free space
- **Root/Admin:** Required for packet capture (Linux/macOS)

### Install Python (if needed)

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

**macOS:** `brew install python3`

**Fedora/RHEL:** `sudo dnf install python3 python3-pip python3-venv`

**Windows:** Download from https://www.python.org/downloads/

### Verify

```bash
python3 --version    # Should be 3.8+
pip --version        # Must exist
python3 -m venv --help  # Must work
```

---

## Quick Start

### Linux (bash install.sh)
```bash
git clone https://github.com/sajid-ali-khan/my-ids.git && cd my-ids
bash install.sh && source ~/.bashrc
ids-cli setup && ids-cli start
```

### macOS/Windows (pipx)
```bash
# Install pipx: brew install pipx  (macOS) or pip install --user pipx (Windows)
git clone https://github.com/sajid-ali-khan/my-ids.git && cd my-ids
pipx install . && ids-cli setup && ids-cli start
```

### Traditional (All platforms)
```bash
git clone https://github.com/sajid-ali-khan/my-ids.git && cd my-ids
python3 -m venv venv && source venv/bin/activate
pip install . && ids-cli setup && ids-cli start
```

---

## Installation Methods

### Method 1: bash install.sh (Linux - Easiest)

### Method 1: bash install.sh (Linux - Easiest)

**What it does:** Automatically creates venv, installs dependencies, creates global `ids-cli` command.

```bash
git clone https://github.com/sajid-ali-khan/my-ids.git
cd my-ids
bash install.sh
source ~/.bashrc
ids-cli setup
ids-cli start
```

✅ Auto venv at `~/.ids/venv` • ✅ No PEP 668 errors • ✅ One command

---

### Method 2: pipx (macOS/Windows/Linux - Professional)

**What it does:** Professional approach with isolated virtual environment.

```bash
# Install pipx first:
# macOS: brew install pipx
# Windows: pip install --user pipx
# Ubuntu: sudo apt install pipx

git clone https://github.com/sajid-ali-khan/my-ids.git
cd my-ids
pipx install .
ids-cli setup
ids-cli start
```

✅ Cross-platform • ✅ No PEP 668 errors • ✅ Easy uninstall: `pipx uninstall ids-tool`

---

### Method 3: pip + venv (All Platforms - Traditional)

**What it does:** Manual virtual environment approach, full control.

```bash
git clone https://github.com/sajid-ali-khan/my-ids.git
cd my-ids
python3 -m venv venv
source venv/bin/activate        # Windows: .\venv\Scripts\activate.ps1
pip install .
mkdir -p ~/.ids
ids-cli setup
ids-cli start
```

✅ Standard Python approach • ✅ Project-specific venv • ✅ Cross-platform

**Note:** Must activate venv each time: `source venv/bin/activate`

---

### Method 4: Manual (Testing/Troubleshooting)

**What it does:** No installation, direct execution.

```bash
git clone https://github.com/sajid-ali-khan/my-ids.git
cd my-ids
python3 -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt
mkdir -p ~/.ids
python3 ids_cli.py setup
python3 ids_cli.py start
```

✅ No installation • ✅ Easy testing • ✅ No cleanup needed

**Note:** Use `python3 ids_cli.py` instead of `ids-cli` command

---

## Post-Installation

### Configure

```bash
ids-cli setup
# Prompts for: interface, port, model directory
```

### Find Network Interface

```bash
# Linux/macOS:
ip link show      # or: ifconfig

# Windows (PowerShell):
Get-NetIPConfiguration
```

### Start & Access

```bash
ids-cli start
# Open: http://localhost:5000
```

### Verify Working

```bash
ids-cli status
ids-cli logs
# Generate traffic: ping 8.8.8.8
# Dashboard should show network activity
```

---

## Troubleshooting

### "ids-cli: command not found"

```bash
# bash install.sh:
source ~/.bashrc

# pip + venv:
source venv/bin/activate

# pipx:
pipx list  # Verify installed
```

### "externally-managed-environment" Error

Use any of these methods:
1. **bash install.sh** → Auto creates venv
2. **pipx install .** → Auto creates venv  
3. **Manual venv:** `python3 -m venv venv && source venv/bin/activate && pip install .`

### "python3-venv not installed"

```bash
# Ubuntu/Debian:
sudo apt install python3-venv

# Fedora/RHEL:
sudo dnf install python3-venv
```

### "Permission denied" on Linux

```bash
sudo ids-cli start    # For packet capture
```

### Port Already in Use

```bash
lsof -i :5000         # Find what's using it
ids-cli setup         # Reconfigure with different port
```

### Dashboard Won't Load

```bash
ids-cli status        # Check if running
ids-cli logs          # Check errors
curl http://localhost:5000  # Test manually
```

### No Network Activity

```bash
ids-cli config        # Verify interface
ping 8.8.8.8         # Generate traffic while server running
ids-cli logs          # Check logs
```

---

## Uninstallation

### bash install.sh
```bash
sudo rm /usr/local/bin/ids-cli
rm -rf ~/.ids/
```

### pipx
```bash
pipx uninstall ids-tool
```

### pip + venv
```bash
deactivate
rm -rf venv/
rm -rf ~/.ids/
```

---

## Summary

| Method | Installation | Setup | Global Command | Best For |
|--------|--------------|-------|-----------------|----------|
| bash | `bash install.sh` | Auto | ✅ Yes | Linux users |
| pipx | `pipx install .` | Auto | ✅ Yes | macOS/Windows |
| venv | `pip install .` | Manual | ✅ (when active) | Developers |
| Manual | None | Manual | ❌ No | Testing |

---

**All methods work reliably and without PEP 668 errors!** ✅

Start with your preferred method and refer back to [Troubleshooting](#troubleshooting) if you hit any issues.
