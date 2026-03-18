#!/bin/bash

###############################################################################
# IDS (Intrusion Detection System) Installation Script
# 
# This script provides a convenient one-line installation for Linux systems
# 
# Usage:
#   bash install.sh
#   or
#   chmod +x install.sh && ./install.sh
#
# What it does:
#   - Verifies Python installation
#   - Creates ~/.ids/ configuration directory
#   - Installs Python dependencies
#   - Creates /usr/local/bin/ids-cli symlink
#   - Tests the installation
#   - Prints setup guide
###############################################################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_step() {
    echo -e "\n${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Banner
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║   Network Intrusion Detection System (IDS) Installer      ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"

# Step 1: Check Python
print_step "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed"
    echo "Please install Python 3.8 or later and try again"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
print_success "Python $PYTHON_VERSION found"

# Step 2: Check if running as root (for system-wide install)
if [ "$EUID" -ne 0 ]; then
    print_warning "Not running as root. Installation will be user-specific."
    INSTALL_PREFIX="$HOME/.local"
else
    INSTALL_PREFIX="/usr/local"
    print_success "Running as root. Installation will be system-wide."
fi

# Step 3: Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
print_step "Project directory: $SCRIPT_DIR"

# Step 4: Create config directory
print_step "Creating configuration directory..."
mkdir -p "$HOME/.ids"
print_success "Configuration directory created at ~/.ids"

# Step 5: Install dependencies
print_step "Installing Python dependencies..."
python3 -m pip install --quiet --upgrade pip setuptools wheel 2>/dev/null || true
python3 -m pip install --quiet -r requirements.txt
print_success "Dependencies installed"

# Step 6: Create CLI symlink
print_step "Setting up CLI command..."
mkdir -p "$INSTALL_PREFIX/bin"

# Create wrapper script
cat > "$INSTALL_PREFIX/bin/ids-cli" << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"
python3 ids_cli.py "$@"
EOF

chmod +x "$INSTALL_PREFIX/bin/ids-cli"

# Add to PATH if necessary
if [[ ":$PATH:" != *":$INSTALL_PREFIX/bin:"* ]]; then
    print_warning "Adding $INSTALL_PREFIX/bin to PATH"
    if [ -f "$HOME/.bashrc" ]; then
        echo "export PATH=\"$INSTALL_PREFIX/bin:\$PATH\"" >> "$HOME/.bashrc"
        print_success "Updated ~/.bashrc"
    fi
    if [ -f "$HOME/.zshrc" ]; then
        echo "export PATH=\"$INSTALL_PREFIX/bin:\$PATH\"" >> "$HOME/.zshrc"
        print_success "Updated ~/.zshrc"
    fi
    export PATH="$INSTALL_PREFIX/bin:$PATH"
fi

print_success "CLI symlink created at $INSTALL_PREFIX/bin/ids-cli"

# Step 7: Test installation
print_step "Testing installation..."
if command -v ids-cli &> /dev/null || [ -f "$INSTALL_PREFIX/bin/ids-cli" ]; then
    print_success "CLI command is available"
else
    print_error "CLI command not found in PATH"
    echo "You can still use: python3 ids_cli.py"
fi

# Step 8: Show completion message
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║           Installation Complete! ✓                        ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"

echo ""
echo -e "${GREEN}📖 Next Steps:${NC}"
echo ""
echo "1. Configure the IDS:"
echo "   ids-cli setup"
echo ""
echo "2. Start the server:"
echo "   ids-cli start"
echo ""
echo "3. Open the dashboard:"
echo "   http://localhost:5000"
echo ""
echo "4. Check server status:"
echo "   ids-cli status"
echo ""
echo "5. View logs:"
echo "   ids-cli logs"
echo ""
echo "6. Stop the server:"
echo "   ids-cli stop"
echo ""
echo -e "${GREEN}📁 Configuration stored in:${NC} ~/.ids/"
echo -e "${GREEN}📊 Dashboard URL:${NC} http://localhost:5000"
echo ""
echo "For more information:"
echo "   ids-cli info"
echo ""
