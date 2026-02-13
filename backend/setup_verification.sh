#!/bin/bash

# Setup script for blockchain verification
# Ensures all required packages are installed

echo "🔧 Setting up blockchain verification environment..."
echo ""

# Check if we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: Not in a virtual environment"
    echo "   Consider running: source .venv/bin/activate"
    echo ""
fi

# Check if pip is available
if ! command -v pip &> /dev/null; then
    echo "❌ Error: pip is not installed"
    exit 1
fi

# Install web3 if not present
echo "📦 Checking web3..."
if python -c "import web3" 2>/dev/null; then
    echo "✓ web3 is installed"
else
    echo "Installing web3..."
    pip install web3==6.15.0
fi

# Install colorama for colored output
echo "📦 Checking colorama..."
if python -c "import colorama" 2>/dev/null; then
    echo "✓ colorama is installed"
else
    echo "Installing colorama..."
    pip install colorama
fi

# Check Django
echo "📦 Checking Django..."
if python -c "import django" 2>/dev/null; then
    echo "✓ Django is installed"
else
    echo "❌ Error: Django is not installed"
    echo "   Run: pip install -r requirements.txt"
    exit 1
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To run the verification script:"
echo "   python verify_blockchain_integration.py"
echo ""
echo "For more information, see:"
echo "   VERIFICATION_GUIDE.md"
