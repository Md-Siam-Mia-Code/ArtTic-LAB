#!/bin/bash
# ArtTic-LAB Installer for Linux/macOS

# --- Configuration ---
ENV_NAME="ArtTic-LAB"
PYTHON_VERSIONS_TO_TRY="3.11 3.12 3.10"

# --- Functions ---
print_header() {
    clear
    echo "======================================================="
    echo "            ArtTic-LAB Installer"
    echo "======================================================="
    echo ""
    echo "This script will find your Conda installation and"
    echo "prepare the '$ENV_NAME' environment."
    echo ""
}

find_conda() {
    if command -v conda &> /dev/null; then
        CONDA_BASE_PATH=$(conda info --base) && return 0
    fi
    local common_paths=("$HOME/miniconda3" "$HOME/anaconda3" "/opt/miniconda3" "/opt/anaconda3")
    for path in "${common_paths[@]}"; do
        if [ -f "$path/bin/conda" ]; then
            CONDA_BASE_PATH="$path" && return 0
        fi
    done
    return 1
}

create_environment() {
    local py_ver=$1
    echo ""
    echo "-------------------------------------------------------"
    echo "[ATTEMPT] Trying to create environment with Python $py_ver..."
    echo "-------------------------------------------------------"
    echo "[INFO] Removing any previous version of '$ENV_NAME'..."
    conda env remove --name "$ENV_NAME" -y &> /dev/null
    echo "[INFO] Creating new Conda environment..."
    conda create --name "$ENV_NAME" python="$py_ver" -y
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to create Conda environment with Python $py_ver." >&2
        return 1
    fi
    return 0
}

install_packages() {
    echo ""
    echo "[INFO] Activating environment and installing/updating dependencies..."
    echo "This is the longest step. Please be patient."
    conda activate "$ENV_NAME"
    if [ $? -ne 0 ]; then echo "[ERROR] Failed to activate '$ENV_NAME'." >&2; return 1; fi

    echo "[INFO] Upgrading pip..."
    python -m pip install --upgrade pip --quiet
    if [ $? -ne 0 ]; then echo "[ERROR] Failed to upgrade pip." >&2; return 1; fi

    echo ""
    echo "Please select your hardware for PyTorch installation:"
    select hardware in "NVIDIA (CUDA)" "Apple Silicon (M1/M2/M3)" "Intel GPU (XPU)" "CPU only"; do
        case $hardware in
            "NVIDIA (CUDA)") pip install torch torchvision torchaudio; break;;
            "Apple Silicon (M1/M2/M3)") pip install torch torchvision torchaudio; break;;
            "Intel GPU (XPU)") pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/xpu; pip install intel-extension-for-pytorch --extra-index-url https://pytorch-extension.intel.com/release-whl/stable/xpu/us/; break;;
            "CPU only") pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu; break;;
            *) echo "Invalid choice. Please enter a number from 1-4.";;
        esac
    done
    if [ $? -ne 0 ]; then echo "[ERROR] PyTorch installation failed." >&2; return 1; fi

    echo "[INFO] Installing other dependencies from requirements.txt..."
    # UPDATED: Using requirements.txt for consistency with the .bat script
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then echo "[ERROR] Installation of other dependencies failed." >&2; return 1; fi

    return 0
}

handle_hf_login() {
    echo ""
    echo "-------------------------------------------------------"
    echo "[ACTION REQUIRED] Hugging Face Login"
    echo "-------------------------------------------------------"
    echo "Models like SD3 and FLUX require you to be logged into"
    echo "your Hugging Face account to download base files."
    echo ""
    read -p "Would you like to log in now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "[INFO] Please get your Hugging Face User Access Token here:"
        echo "       https://huggingface.co/settings/tokens"
        echo "[INFO] The token needs at least 'read' permissions."
        echo ""
        huggingface-cli login
        echo ""
        echo "[IMPORTANT] Remember to visit the model pages on the"
        echo "Hugging Face website to accept their license agreements:"
        echo "- SD3: https://huggingface.co/stabilityai/stable-diffusion-3-medium-diffusers"
        echo "- FLUX: https://huggingface.co/black-forest-labs/FLUX.1-dev"
        echo ""
    else
        echo ""
        echo "[INFO] Skipping Hugging Face login."
        echo "You can log in later by activating the environment"
        echo "('conda activate ArtTic-LAB') and running 'huggingface-cli login'."
        echo "Note: SD3 and FLUX models will not work until you do."
    fi
}

# --- Main Script ---
print_header

# 1. Find and initialize Conda
echo "[INFO] Searching for Conda installation..."
if ! find_conda; then echo "[ERROR] Conda not found." >&2; exit 1; fi
echo "[SUCCESS] Conda installation detected at: $CONDA_BASE_PATH"
source "${CONDA_BASE_PATH}/etc/profile.d/conda.sh"

# 2. Handle environment creation
CREATE_ENV=true
if conda env list | grep -q "^${ENV_NAME} "; then
    read -p "[WARNING] Environment '$ENV_NAME' already exists. Reinstall? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "[INFO] Skipping environment creation. Will update packages in the existing environment."
        CREATE_ENV=false
    fi
fi

if [ "$CREATE_ENV" = true ]; then
    ENV_CREATED=false
    for py_version in $PYTHON_VERSIONS_TO_TRY; do
        if create_environment "$py_version"; then
            ENV_CREATED=true
            break
        fi
    done
    if [ "$ENV_CREATED" = false ]; then
        echo ""
        echo "[FATAL ERROR] Could not create the Conda environment after trying all Python versions." >&2
        exit 1
    fi
fi

# 3. Install packages
if install_packages; then
    handle_hf_login

    echo ""
    echo "======================================================="
    echo "[SUCCESS] Installation complete!"
    echo "You can now run './start.sh' to launch ArtTic-LAB."
    echo "======================================================="
    echo ""
    exit 0
else
    echo ""
    echo "[FATAL ERROR] Package installation failed. Please check the errors above." >&2
    exit 1
fi