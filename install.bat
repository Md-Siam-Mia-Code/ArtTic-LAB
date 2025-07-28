@echo off
REM ArtTic-LAB Installer for Windows
title ArtTic-LAB Installer

ECHO.
ECHO =======================================================
ECHO             ArtTic-LAB Installer
ECHO =======================================================
ECHO.
ECHO This script will create a dedicated Conda environment
ECHO named 'arttic-lab' and install all dependencies.
ECHO.

REM --- Check for Conda installation ---
ECHO [INFO] Checking for Conda installation...
conda --version >nul 2>nul
IF %ERRORLEVEL% NEQ 0 GOTO no_conda

ECHO [SUCCESS] Conda detected!
ECHO.

REM --- Create the Conda environment ---
ECHO [INFO] Creating Conda environment 'ArtTic-LAB' with Python 3.11...
ECHO This may take a moment.
conda create --name ArtTic-LAB python=3.11 -y
IF %ERRORLEVEL% NEQ 0 GOTO install_fail

ECHO.
ECHO [INFO] Activating environment and installing dependencies...
ECHO This is the longest step. Please be patient.
ECHO.

REM --- Activate and Install ---
call conda.bat activate artic-lab
IF %ERRORLEVEL% NEQ 0 GOTO install_fail

pip install --upgrade pip
pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/xpu
pip install intel-extension-for-pytorch diffusers accelerate safetensors gradio invisible-watermark
IF %ERRORLEVEL% NEQ 0 GOTO install_fail

ECHO.
ECHO =======================================================
ECHO [SUCCESS] Installation complete!
ECHO You can now run 'start.bat' to launch ArtTic-LAB.
ECHO =======================================================
ECHO.
GOTO end

:no_conda
ECHO.
ECHO [ERROR] Conda not found in your system's PATH.
ECHO Please install Miniconda (a lightweight version of Anaconda)
ECHO from: https://docs.conda.io/en/latest/miniconda.html
ECHO After installation, please close and reopen this terminal and run this script again.
ECHO.
GOTO end

:install_fail
ECHO.
ECHO [ERROR] Installation failed. Please check the error messages above.
ECHO You may need to run this terminal as an Administrator.
ECHO If the problem persists, please check the project's documentation.
ECHO.
GOTO end

:end
pause