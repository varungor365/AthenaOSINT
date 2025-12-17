#!/bin/bash
# AthenaOSINT Startup and System Check Script
# Run this to start the full system and verify all services

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║                    AthenaOSINT System Startup                 ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print status
print_status() {
    if [ $2 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${RED}✗${NC} $1"
    fi
}

# 1. System Requirements Check
echo "[1/6] Checking System Requirements..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Python
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    print_status "Python ${PYTHON_VERSION}" 0
else
    print_status "Python 3 - NOT FOUND" 1
    echo -e "${RED}ERROR: Python 3 is required${NC}"
    exit 1
fi

# Pip
if command_exists pip3; then
    print_status "pip3" 0
else
    print_status "pip3 - NOT FOUND" 1
fi

# Git
if command_exists git; then
    print_status "git" 0
else
    print_status "git" 1
fi

echo ""

# 2. Virtual Environment Check
echo "[2/6] Checking Virtual Environment..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠ Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    print_status "Virtual environment created" 0
else
    print_status "Virtual environment exists" 0
fi

# Activate virtual environment
source venv/bin/activate
print_status "Virtual environment activated" 0

echo ""

# 3. Dependencies Check
echo "[3/6] Checking Python Dependencies..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if requirements are installed
MISSING_DEPS=0
pip3 list > /tmp/pip_list.txt

while IFS= read -r package; do
    package_name=$(echo "$package" | cut -d'=' -f1 | sed 's/[>=<].*//g' | xargs)
    if ! grep -qi "^${package_name}" /tmp/pip_list.txt; then
        echo -e "${RED}✗${NC} ${package_name} - MISSING"
        MISSING_DEPS=1
    fi
done < requirements.txt

if [ $MISSING_DEPS -eq 1 ]; then
    echo -e "${YELLOW}⚠ Installing missing dependencies...${NC}"
    pip3 install -r requirements.txt
    print_status "Dependencies installed" 0
else
    print_status "All dependencies installed" 0
fi

echo ""

# 4. Configuration Check
echo "[4/6] Checking Configuration..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f ".env" ]; then
    print_status ".env file exists" 0
    
    # Check for critical API keys
    if grep -q "TELEGRAM_BOT_TOKEN=.\+" .env 2>/dev/null; then
        print_status "Telegram Bot Token configured" 0
    else
        print_status "Telegram Bot Token - NOT SET" 1
    fi
    
    if grep -q "GROQ_API_KEY=.\+" .env 2>/dev/null; then
        print_status "GROQ API Key configured" 0
    else
        print_status "GROQ API Key - NOT SET (AI features disabled)" 1
    fi
else
    print_status ".env file - NOT FOUND" 1
    echo -e "${YELLOW}⚠ Creating .env from template...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_status ".env created from template" 0
        echo -e "${YELLOW}⚠ Please edit .env and add your API keys${NC}"
    fi
fi

echo ""

# 5. External Tools Check
echo "[5/6] Checking External OSINT Tools..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check for external tools
if command_exists subfinder; then
    print_status "subfinder" 0
else
    print_status "subfinder - NOT INSTALLED" 1
fi

if command_exists nuclei; then
    print_status "nuclei" 0
else
    print_status "nuclei - NOT INSTALLED" 1
fi

if command_exists exiftool; then
    print_status "exiftool" 0
else
    print_status "exiftool - NOT INSTALLED" 1
fi

if command_exists tesseract; then
    print_status "tesseract (OCR)" 0
else
    print_status "tesseract - NOT INSTALLED (OCR module disabled)" 1
fi

echo ""

# 6. Service Status
echo "[6/6] Starting Services..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "Select what to start:"
echo "  [1] Web Interface (Dashboard)"
echo "  [2] Telegram Bot"
echo "  [3] Both Web + Bot"
echo "  [4] System Check Only (no start)"
echo ""
read -p "Enter choice [1-4]: " choice

case $choice in
    1)
        echo -e "${GREEN}Starting Web Interface...${NC}"
        print_status "Starting on http://0.0.0.0:5000" 0
        python3 run_web.py
        ;;
    2)
        echo -e "${GREEN}Starting Telegram Bot...${NC}"
        python3 run_bot.py
        ;;
    3)
        echo -e "${GREEN}Starting Web Interface in background...${NC}"
        nohup python3 run_web.py > logs/web.log 2>&1 &
        WEB_PID=$!
        print_status "Web started (PID: $WEB_PID)" 0
        
        echo -e "${GREEN}Starting Telegram Bot...${NC}"
        python3 run_bot.py
        ;;
    4)
        echo -e "${GREEN}System check complete!${NC}"
        echo ""
        echo "Summary:"
        echo "  • Python: $(python3 --version)"
        echo "  • Virtual environment: Active"
        echo "  • Dependencies: Installed"
        echo ""
        echo "To start services manually:"
        echo "  • Web: python run_web.py"
        echo "  • Bot: python run_bot.py"
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                     System Ready! 🦅                          ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
