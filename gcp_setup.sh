#!/bin/bash
# GCP Confidential VM Setup for Anonymous LLM Client

set -e

echo ">>>>>>>>>>  GCP Intel TDX Setup <<<<<<<<<<"

# detect confidential computing
if sudo dmesg | grep -qi tdx; then
    CC_TYPE="Intel TDX"
    echo "✓ Intel TDX detected - VM memory is hardware-encrypted"
elif sudo dmesg | grep -qi sev; then
    CC_TYPE="AMD SEV-SNP"
    echo "✓ AMD SEV-SNP detected - VM memory is hardware-encrypted"
else
    echo "⚠ Warning: Confidential computing not detected"
    CC_TYPE="Standard VM"
fi

echo "Running on: $CC_TYPE"
echo ""

# update system if needed
echo "[1/3] Updating system..."
sudo apt update
sudo apt upgrade -y

# install dependencies
echo "[2/3] Installing dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    wget

# setup Python environoment
echo "[3/3] Setting up Python environment..."

mkdir -p ~/secure-llm-gcp
cd ~/secure-llm-gcp

python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install \
    requests \
    pysocks \
    cryptography \
    numpy \
    google-genai \
    presidio-anonymizer \
    presidio-analyzer \
    stem

pip install 'requests[socks]'

echo ">>>>>>>>>>  Setup Complete! <<<<<<<<<<"
echo ""
echo "Next steps:"
echo "  1. Change directory to: ~/secure-llm-gcp"
echo "  1. Verify using: ./verify.sh"
echo "  2. Copy securellm.py here"
echo "  3. export GEMINI_API_KEY='your-key'"
echo "  4. Run: python3 securellm.py"