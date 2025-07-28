#!/bin/bash
# ArtTic-LAB Launcher for Linux/macOS

# Source conda.sh to make 'conda activate' available in the script
source "$(conda info --base)/etc/profile.d/conda.sh"

# Activate the dedicated conda environment
conda activate ArtTic-LAB

# Run the main application, passing along all command-line arguments (like --disable-filters)
# The "$@" ensures all arguments are passed correctly
python app.py "$@"

echo ""
echo "ArtTic-LAB has closed."