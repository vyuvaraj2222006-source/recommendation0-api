#!/bin/bash

# ============================================
# RECOMMENDATION SYSTEM - INSTALLATION SCRIPT
# ============================================

echo "================================================"
echo "  RECOMMENDATION SYSTEM - INSTALLATION WIZARD"
echo "================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print success message
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print warning message
print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Function to print error message
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# ============================================
# STEP 1: Check Prerequisites
# ============================================

echo "STEP 1: Checking Prerequisites..."
echo "-----------------------------------"

# Check Python
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    print_success "Python installed: $PYTHON_VERSION"
else
    print_error "Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

# Check pip
if command_exists pip3 || command_exists pip; then
    PIP_VERSION=$(pip3 --version 2>&1 || pip --version 2>&1)
    print_success "pip installed: $PIP_VERSION"
    PIP_CMD="pip3"
    if ! command_exists pip3; then
        PIP_CMD="pip"
    fi
else
    print_error "pip not found. Please install pip."
    exit 1
fi

# Check Docker (optional)
if command_exists docker; then
    DOCKER_VERSION=$(docker --version 2>&1)
    print_success "Docker installed: $DOCKER_VERSION"
    DOCKER_AVAILABLE=true
else
    print_warning "Docker not installed (optional for containerization)"
    DOCKER_AVAILABLE=false
fi

echo ""

# ============================================
# STEP 2: Create Virtual Environment (Optional)
# ============================================

echo "STEP 2: Virtual Environment Setup..."
echo "-------------------------------------"

read -p "Do you want to create a virtual environment? (recommended) [Y/n]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists. Skipping creation."
    else
        echo "Creating virtual environment..."
        python3 -m venv venv
        print_success "Virtual environment created"
    fi
    
    echo "Activating virtual environment..."
    source venv/bin/activate
    print_success "Virtual environment activated"
    PIP_CMD="pip"
else
    print_warning "Skipping virtual environment creation"
fi

echo ""

# ============================================
# STEP 3: Install Python Dependencies
# ============================================

echo "STEP 3: Installing Python Dependencies..."
echo "------------------------------------------"

if [ -f "requirements.txt" ]; then
    echo "Installing packages from requirements.txt..."
    $PIP_CMD install -r requirements.txt
    
    if [ $? -eq 0 ]; then
        print_success "All dependencies installed successfully"
    else
        print_error "Failed to install some dependencies"
        exit 1
    fi
else
    print_error "requirements.txt not found!"
    exit 1
fi

echo ""

# ============================================
# STEP 4: Verify Installation
# ============================================

echo "STEP 4: Verifying Installation..."
echo "----------------------------------"

# Check key packages
PACKAGES=("flask" "numpy" "pandas" "scikit-learn" "redis")

for pkg in "${PACKAGES[@]}"; do
    if $PIP_CMD show "$pkg" > /dev/null 2>&1; then
        VERSION=$($PIP_CMD show "$pkg" | grep Version | cut -d' ' -f2)
        print_success "$pkg $VERSION installed"
    else
        print_warning "$pkg not found"
    fi
done

echo ""

# ============================================
# STEP 5: Check Redis (Optional)
# ============================================

echo "STEP 5: Checking Redis..."
echo "-------------------------"

if command_exists redis-server; then
    print_success "Redis server installed"
    
    # Check if Redis is running
    if pgrep -x "redis-server" > /dev/null; then
        print_success "Redis is running"
    else
        print_warning "Redis installed but not running"
        echo "To start Redis:"
        echo "  sudo systemctl start redis    # On Linux"
        echo "  brew services start redis     # On macOS"
    fi
else
    print_warning "Redis not installed (optional but recommended for caching)"
    echo "To install Redis:"
    echo "  Ubuntu/Debian: sudo apt-get install redis-server"
    echo "  macOS: brew install redis"
    echo "  Windows: Download from https://redis.io/download"
fi

echo ""

# ============================================
# STEP 6: Prepare Model Directory
# ============================================

echo "STEP 6: Creating Model Directory..."
echo "------------------------------------"

if [ ! -d "models" ]; then
    mkdir -p models
    print_success "Created models directory"
else
    print_warning "models directory already exists"
fi

echo ""

# ============================================
# STEP 7: Test Model Preparation
# ============================================

echo "STEP 7: Testing Model Preparation..."
echo "-------------------------------------"

if [ -f "step1_model_preparation.py" ]; then
    read -p "Do you want to run model preparation now? [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python3 step1_model_preparation.py
        if [ $? -eq 0 ]; then
            print_success "Model preparation completed"
        else
            print_error "Model preparation failed"
        fi
    else
        print_warning "Skipping model preparation"
    fi
else
    print_error "step1_model_preparation.py not found"
fi

echo ""

# ============================================
# STEP 8: Docker Setup (Optional)
# ============================================

echo "STEP 8: Docker Setup..."
echo "-----------------------"

if [ "$DOCKER_AVAILABLE" = true ]; then
    read -p "Do you want to build Docker image? [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ -f "Dockerfile" ]; then
            echo "Building Docker image..."
            docker build -t recommendation-api .
            if [ $? -eq 0 ]; then
                print_success "Docker image built successfully"
            else
                print_error "Docker build failed"
            fi
        else
            print_error "Dockerfile not found"
        fi
    else
        print_warning "Skipping Docker build"
    fi
else
    print_warning "Docker not available. Skipping Docker setup."
fi

echo ""

# ============================================
# INSTALLATION COMPLETE
# ============================================

echo "================================================"
echo "  INSTALLATION COMPLETE!"
echo "================================================"
echo ""
echo "Next Steps:"
echo "-----------"
echo ""
echo "1. Start the API server:"
echo "   python3 step2_api_service.py"
echo ""
echo "2. Test the API (in another terminal):"
echo "   curl http://localhost:5000/health"
echo ""
echo "3. Get recommendations:"
echo "   curl http://localhost:5000/api/v1/recommendations/user/1?n=10"
echo ""
echo "4. View all available commands:"
echo "   cat QUICK_START.md"
echo ""

if [ "$DOCKER_AVAILABLE" = true ]; then
    echo "5. Run with Docker:"
    echo "   docker-compose up"
    echo ""
fi

echo "For detailed instructions, see:"
echo "  - README.md"
echo "  - QUICK_START.md"
echo "  - INSTALLATION_GUIDE.md"
echo ""
echo "================================================"

# Deactivate virtual environment message
if [[ $VIRTUAL_ENV ]]; then
    echo ""
    echo "Note: Virtual environment is active."
    echo "To deactivate: deactivate"
    echo ""
fi
