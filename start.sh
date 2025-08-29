#!/bin/bash
# ArtTic-LAB Launcher for Linux/macOS

# --- Function to find Conda installation ---
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

echo "[INFO] Preparing to launch ArtTic-LAB..."

# 1. Find and initialize Conda
if ! find_conda; then
    echo ""
    echo "[ERROR] Conda installation not found." >&2
    echo "Please ensure Miniconda or Anaconda is installed and run install.sh." >&2
    exit 1
fi
echo "[INFO] Conda found at: $CONDA_BASE_PATH"
source "${CONDA_BASE_PATH}/etc/profile.d/conda.sh"

# 2. Check if the environment exists
echo "[INFO] Checking for 'ArtTic-LAB' environment..."
if ! conda env list | grep -q "^ArtTic-LAB "; then
    echo ""
    echo "[ERROR] The 'ArtTic-LAB' environment was not found." >&2
    echo "Please run the './install.sh' script first to set it up." >&2
    exit 1
fi

# 3. Activate the environment
echo "[INFO] Activating environment..."
conda activate ArtTic-LAB
if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Failed to activate the 'ArtTic-LAB' environment." >&2
    echo "The environment may be corrupted. Please try running './install.sh' again." >&2
    exit 1
fi

echo "[SUCCESS] Environment activated. Launching application..."
echo ""
echo "======================================================="
echo "             Launching ArtTic-LAB"
echo "======================================================="
echo ""

# 4. Launch the application
# The "$@" ensures all command-line arguments are passed correctly
python app.py "$@"

echo ""
echo "======================================================="
echo "ArtTic-LAB has closed."
echo "======================================================="
echo ""