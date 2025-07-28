#!/bin/bash
# ArtTic-LAB Installer for Linux/macOS

echo "======================================================="
echo "            ArtTic-LAB Installer"
echo "======================================================="
echo ""
echo "This script will create a dedicated Conda environment"
echo "named 'arttic-lab' and install all dependencies."
echo ""

# --- Check for Conda installation ---
echo "[INFO] Checking for Conda installation..."
if ! command -v conda &> /dev/null
then
    echo ""
    echo "[ERROR] Conda not found in your system's PATH."
    echo "Please install Miniconda (a lightweight version of Anaconda)"
    echo "from: https://docs.conda.io/en/latest/miniconda.html"
    echo "After installation, please close and reopen this terminal and run this script again."
    echo ""
    exit 1
fi

echo "[SUCCESS] Conda detected!"
echo ""

# --- Create the Conda environment ---
echo "[INFO] Creating Conda environment 'ArtTic-LAB' with Python 3.11..."
echo "This may take a moment."
conda create --name ArtTic-LAB python=3.11 -y
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to create Conda environment."
    exit 1
fi

echo ""
echo "[INFO] Activating environment and installing dependencies..."
echo "This is the longest step. Please be patient."
echo ""

# --- Activate and Install ---
# Source conda.sh to make 'conda activate' available in the script
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate artic-lab

pip install --upgrade pip
pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/xpu
pip install intel-extension-for-pytorch diffusers accelerate safetensors gradio invisible-watermark

if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Installation of pip packages failed. Please check the error messages above."
    echo ""
    exit 1
fi

echo ""
echo "======================================================="
echo "[SUCCESS] Installation complete!"
echo "You can now run 'start.sh' to launch ArtTic-LAB."
echo "======================================================="
echo ""