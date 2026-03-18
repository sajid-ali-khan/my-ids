# IDS Deployment Guide

This guide covers both installation methods for the Network Intrusion Detection System.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation Method 1: pip (Recommended)](#method-1-pip)
3. [Installation Method 2: Bash Script (Linux)](#method-2-bash)
4. [Installation Method 3: Manual](#method-3-manual)
5. [Post-Installation](#post-installation)
6. [Troubleshooting](#troubleshooting)
7. [Uninstallation](#uninstallation)

---

## Prerequisites

### System Requirements

- **Python:** 3.8 or higher
- **OS:** Linux, Windows, or macOS
- **RAM:** 500MB+ available
- **Disk:** 200MB+ free space
- **Network:** Root/Administrator privileges required for packet capture on Linux/macOS

### Check Python Installation

```bash
# Check Python version
python3 --version

# Should output: Python 3.8.x or higher
```

If Python3 is not installed:

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

**macOS (with Homebrew):**
```bash
brew install python3
```

**Windows:**
Download and install from https://www.python.org/downloads/

---

## Method 1: pip (Recommended)

### Best For
- Python developers
- Cross-platform deployment (Windows, Linux, macOS)
- Virtual environments
- CI/CD pipelines

### Installation Steps

#### 1. Clone or Download Repository

```bash
# Clone from GitHub (requires git)
git clone https://github.com/yourusername/ids-tool.git
cd ids-tool

# Or download and extract ZIP manually
cd ids-tool
```

#### 2. Create Virtual Environment (Optional but Recommended)

```bash
# Create venv
python3 -m venv venv

# Activate venv
# On Linux/macOS:
source venv/bin/activate

# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# On Windows (CMD):
venv\Scripts\activate.bat
```

#### 3. Install Package

```bash
# Install in editable mode (good for development)
pip install -e .

# OR install normally
pip install .
```

#### 4. Verify Installation

```bash
# The ids-cli command should now be available globally
ids-cli --help

# If command not found, add to PATH:
# On Linux/macOS, add to ~/.bashrc or ~/.zshrc:
export PATH="$HOME/.local/bin:$PATH"

# Then reload shell:
source ~/.bashrc  # or source ~/.zshrc
```

#### 5. Initialize Configuration

```bash
ids-cli setup
```

This will guide you through:
- Network interface selection
- Port configuration
- Model directory path
- Debug settings

#### 6. Start the Server

```bash
ids-cli start
```

#### 7. Access Dashboard

Open in browser: **http://localhost:5000**

### Advantages
✅ Cross-platform (Windows, Linux, macOS)
✅ Global `ids-cli` command
✅ Easy dependency management
✅ Professional installation
✅ Works with pip and pipenv

### Example Complete Session

```bash
# Create and enter directory
mkdir ids-deployment
cd ids-deployment

# Clone repo
git clone https://github.com/yourusername/ids-tool.git
cd ids-tool

# Setup venv
python3 -m venv venv
source venv/bin/activate

# Install
pip install .

# Setup
ids-cli setup

# Run
ids-cli start

# Monitor
ids-cli status
ids-cli logs

# Stop
ids-cli stop
```

---

## Method 2: Bash Script (Linux)

### Best For
- Linux sysadmins
- Quick one-command setup
- Users familiar with shell scripts
- Automated deployment scripts

### Installation Steps

#### 1. Clone or Download Repository

```bash
git clone https://github.com/yourusername/ids-tool.git
cd ids-tool

# Or download and extract ZIP, then cd into it
```

#### 2. Run Installation Script

```bash
# Make executable (if not already)
chmod +x install.sh

# Run installer
./install.sh

# OR directly:
bash install.sh
```

#### 3. Follow the Installer Prompts

The script will:
- ✓ Check Python 3 installation
- ✓ Create `~/.ids/` config directory
- ✓ Install all dependencies
- ✓ Create `ids-cli` symlink
- ✓ Update PATH in `.bashrc` and `.zshrc`
- ✓ Test the installation

#### 4. Reload Shell Configuration

```bash
# After installation, reload your shell:
source ~/.bashrc   # for bash
# OR
source ~/.zshrc    # for zsh
```

#### 5. Verify Installation

```bash
# Should output help menu
ids-cli --help

# Or check location
which ids-cli
```

#### 6. Initialize Configuration

```bash
ids-cli setup
```

#### 7. Start the Server

```bash
# May require sudo for packet capture
sudo ids-cli start
```

#### 8. Access Dashboard

Open in browser: **http://localhost:5000**

### Installer Script Features

- **Colored output** for easy reading
- **Error handling** with informative messages
- **Automatic PATH setup** (.bashrc/.zshrc)
- **Root detection** (handles both user and system-wide install)
- **Verification** at each step

### What the Script Does

```bash
# 1. Verifies Python 3 is installed
# 2. Creates ~/.ids/ directory
# 3. Installs Python dependencies via pip
# 4. Creates /usr/local/bin/ids-cli symlink (or ~/.local/bin/)
# 5. Updates ~/.bashrc and ~/.zshrc for PATH
# 6. Tests installation
# 7. Prints setup guide
```

### Advantages
✅ Linux-optimized
✅ Minimal dependencies (only bash, python3, pip)
✅ Automatic PATH configuration
✅ Single command install
✅ User-friendly colored output
✅ Works with/without sudo

### Example Complete Session

```bash
# Clone and enter
git clone https://github.com/yourusername/ids-tool.git
cd ids-tool

# Run installer
bash install.sh

# Reload shell
source ~/.bashrc

# Setup
ids-cli setup

# Run with sudo (for packet capture)
sudo ids-cli start

# Monitor
ids-cli status
```

### Troubleshooting: PATH Not Updating

If `ids-cli` is not found after running the installer:

```bash
# Manually add to PATH
export PATH="/usr/local/bin:$PATH"

# Or add to ~/.bashrc:
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Verify
which ids-cli
ids-cli --help
```

---

## Method 3: Manual

### Best For
- Troubleshooting installation issues
- Understanding the system
- Running without installation
- Development/debugging

### Setup Steps

#### 1. Clone or Download Repository

```bash
git clone https://github.com/yourusername/ids-tool.git
cd ids-tool
```

#### 2. Create Virtual Environment

```bash
# Create venv
python3 -m venv myenv

# Activate
# Linux/macOS:
source myenv/bin/activate

# Windows:
myenv\Scripts\activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Create Config Directory

```bash
mkdir -p ~/.ids
```

#### 5. Run Directly

```bash
# Use Python directly (no symlink needed)
python3 ids_cli.py setup

# Start server
python3 ids_cli.py start

# Status
python3 ids_cli.py status

# Stop
python3 ids_cli.py stop

# Logs
python3 ids_cli.py logs

# View help
python3 ids_cli.py --help
```

### Advantages
✅ No installation needed
✅ Easy to test/debug
✅ Works anywhere
✅ Full control over environment

### Disadvantages
❌ Must use `python3 ids_cli.py` every time
❌ Virtual environment must be activated
❌ No system-wide command

---

## Post-Installation

### Configuration

After choosing your installation method, configure the IDS:

```bash
# Run setup (interactive)
ids-cli setup
```

Or manually edit `~/.ids/config.json`:

```json
{
  "interface": "eth0",
  "port": 5000,
  "model_dir": "./model",
  "debug": false,
  "host": "0.0.0.0"
}
```

### Network Interface Selection

Find your network interface:

**Linux:**
```bash
# List interfaces
ip link show
# or
ifconfig

# Common interfaces: eth0, wlan0, enp0s3
```

**Windows (PowerShell):**
```powershell
Get-NetIPConfiguration
# or
ipconfig
```

**macOS:**
```bash
# List interfaces
ifconfig | grep "^en"
# Common: en0, en1
```

### First Run

```bash
# Setup
ids-cli setup

# Start
ids-cli start

# Check status
ids-cli status

# View dashboard
# Open browser to: http://localhost:5000

# View logs
ids-cli logs

# Stop
ids-cli stop
```

---

## Troubleshooting

### Issue: "ids-cli command not found"

**Solution 1: Activate virtual environment**
```bash
source venv/bin/activate
ids-cli --help
```

**Solution 2: Add to PATH**
```bash
export PATH="$HOME/.local/bin:$PATH"
ids-cli --help
```

**Solution 3: Use full path**
```bash
python3 ids_cli.py --help
```

### Issue: "Permission denied" on Linux

**Solution: Run with sudo**
```bash
# Packet capture requires root
sudo ids-cli start

# Or add user to pcap group (if available)
sudo usermod -aG pcap $USER
```

### Issue: Port 5000 already in use

**Solution 1: Change port in config**
```bash
# Edit ~/.ids/config.json
# Change "port": 5000 to "port": 8080

# Or run setup again
ids-cli setup
```

**Solution 2: Find and kill process using port**
```bash
# Linux/macOS:
lsof -i :5000
kill -9 <PID>

# Windows (PowerShell):
Get-Process -Id (Get-NetTCPConnection -LocalPort 5000).OwningProcess
```

### Issue: Dashboard not loading

**Solution 1: Check server status**
```bash
ids-cli status
```

**Solution 2: Check logs**
```bash
ids-cli logs -n 50
```

**Solution 3: Check firewall**
```bash
# Linux:
sudo ufw status
sudo ufw allow 5000/tcp

# macOS:
# System Preferences → Security & Privacy → Firewall Options
```

### Issue: No predictions showing in dashboard

**Solution 1: Verify network interface**
```bash
ids-cli config

# Check interface is correct and has traffic
# Linux: sudo tcpdump -i <interface> -c 10
```

**Solution 2: Generate test traffic**
```bash
# Ping a server to generate traffic
ping google.com

# Run while server is running
```

### Issue: Model file not found

**Solution: Verify model directory**
```bash
# Check config
ids-cli config

# List model files
ls -la ./model/

# Should contain:
# - random_forest_model.pkl
# - model_columns.joblib
```

---

## Uninstallation

### After pip Installation

```bash
# Deactivate virtual environment
deactivate

# Remove installed package
pip uninstall ids-tool

# Remove virtual environment
rm -rf venv/

# Remove config directory
rm -rf ~/.ids/

# Remove symlink (if system-wide install)
sudo rm /usr/local/bin/ids-cli
```

### After Bash Script Installation

```bash
# Remove symlink
sudo rm /usr/local/bin/ids-cli
# or
rm ~/.local/bin/ids-cli

# Remove config directory
rm -rf ~/.ids/

# Remove project directory
rm -rf ids-tool/

# Clean Python packages (optional)
pip uninstall -r requirements.txt
```

### Clean Up (All Methods)

```bash
# Remove cached Python files
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete

# Remove logs
rm -rf ~/.ids/server.log

# List remaining files
ls -la ~/.ids/
```

---

## Next Steps

1. **Configure:** `ids-cli setup`
2. **Start:** `ids-cli start`
3. **Monitor:** Open http://localhost:5000
4. **Stop:** `ids-cli stop`

## Support

For issues or questions:
- Check logs: `ids-cli logs`
- View config: `ids-cli config`
- Get help: `ids-cli info`
- See README.md for detailed documentation

---

**Installation Guide Complete!** 🎉

Your IDS is now ready for deployment. Choose the installation method that best fits your environment and workflow.
