@echo off
setlocal enabledelayedexpansion

:: Set the title for the command window
title ArtTic-LAB Installer

:: --- Configuration ---
set "ENV_NAME=ArtTic-LAB"
set "PYTHON_VERSION=3.11"

:: --- Main Script ---
:main
cls
echo =======================================================
echo             ArtTic-LAB Installer for Windows
echo =======================================================
echo.
echo This script will find your Conda installation and prepare
echo the '%ENV_NAME%' environment.
echo.

:: 1. Find and initialize Conda
call :find_conda
if errorlevel 1 (
    echo [ERROR] Conda installation not found. Please ensure Miniconda or Anaconda is installed.
    pause
    exit /b 1
)
echo [SUCCESS] Conda installation detected.

:: 2. Handle environment creation
echo.
echo [INFO] Checking for existing '%ENV_NAME%' environment...
conda env list | findstr /B /C:"%ENV_NAME% " >nul
if not errorlevel 1 (
    echo [WARNING] Environment '%ENV_NAME%' already exists.
    set /p "REINSTALL=Do you want to reinstall it? (y/n): "
    if /i not "!REINSTALL!"=="y" (
        echo [INFO] Skipping environment creation. Will update packages.
        goto install_packages
    )
)

call :create_environment
if errorlevel 1 (
    echo [FATAL ERROR] Could not create the Conda environment.
    pause
    exit /b 1
)

:install_packages
echo.
echo [INFO] Activating environment and installing/updating dependencies...
echo This is the longest step. Please be patient.
call conda activate %ENV_NAME%
if errorlevel 1 (
    echo [ERROR] Failed to activate Conda environment.
    pause
    exit /b 1
)

echo [INFO] Upgrading pip...
python -m pip install --upgrade pip --quiet
if errorlevel 1 ( echo [ERROR] Failed to upgrade pip. & pause & exit /b 1 )

echo.
echo Please select your hardware for PyTorch installation:
echo   1. NVIDIA (CUDA)
echo   2. Intel GPU (XPU)
echo   3. CPU only
echo.
set /p "HARDWARE_CHOICE=Enter your choice (1, 2, or 3): "

if "!HARDWARE_CHOICE!"=="1" (
    pip install torch torchvision torchaudio
) else if "!HARDWARE_CHOICE!"=="2" (
    pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/xpu
    pip install intel-extension-for-pytorch --extra-index-url https://pytorch-extension.intel.com/release-whl/stable/xpu/us/
) else if "!HARDWARE_CHOICE!"=="3" (
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
) else (
    echo [ERROR] Invalid choice. Aborting.
    pause
    exit /b 1
)
if errorlevel 1 ( echo [ERROR] PyTorch installation failed. & pause & exit /b 1 )

echo [INFO] Installing other dependencies from requirements.txt...
pip install -r requirements.txt
if errorlevel 1 ( echo [ERROR] Installation of other dependencies failed. & pause & exit /b 1 )

call :handle_hf_login

echo.
echo =======================================================
echo [SUCCESS] Installation complete!
echo You can now run 'start.bat' to launch ArtTic-LAB.
echo =======================================================
echo.
pause
exit /b 0


:: --- Subroutines ---
:find_conda
:: This robustly finds Conda by checking common paths and initializing the shell
set "FOUND_CONDA="
if defined CONDA_EXE (
    set "FOUND_CONDA=true"
) else (
    if exist "%USERPROFILE%\miniconda3\condabin\conda.bat" (
        call "%USERPROFILE%\miniconda3\Scripts\activate.bat"
        set "FOUND_CONDA=true"
    ) else if exist "%USERPROFILE%\anaconda3\condabin\conda.bat" (
        call "%USERPROFILE%\anaconda3\Scripts\activate.bat"
        set "FOUND_CONDA=true"
    ) else if exist "%ProgramData%\Miniconda3\condabin\conda.bat" (
        call "%ProgramData%\Miniconda3\Scripts\activate.bat"
        set "FOUND_CONDA=true"
    ) else if exist "%ProgramData%\Anaconda3\condabin\conda.bat" (
        call "%ProgramData%\Anaconda3\Scripts\activate.bat"
        set "FOUND_CONDA=true"
    )
)

if defined FOUND_CONDA (
    exit /b 0
) else (
    exit /b 1
)

:create_environment
echo.
echo -------------------------------------------------------
echo [INFO] Creating Conda environment with Python %PYTHON_VERSION%...
echo -------------------------------------------------------
echo [INFO] Removing any previous version of '%ENV_NAME%'...
conda env remove --name "%ENV_NAME%" -y >nul 2>nul
echo [INFO] Creating new Conda environment...
conda create --name "%ENV_NAME%" python=%PYTHON_VERSION% -y
if errorlevel 1 exit /b 1
exit /b 0

:handle_hf_login
echo.
echo -------------------------------------------------------
echo [ACTION REQUIRED] Hugging Face Login
echo -------------------------------------------------------
echo Models like SD3 and FLUX require you to be logged into
echo your Hugging Face account to download base files.
echo.
set /p "LOGIN_CHOICE=Would you like to log in now? (y/n): "
if /i "!LOGIN_CHOICE!"=="y" (
    echo.
    echo [INFO] Please get your Hugging Face User Access Token here:
    echo        https://huggingface.co/settings/tokens
    echo [INFO] The token needs at least 'read' permissions.
    echo.
    huggingface-cli login
    echo.
    echo [IMPORTANT] Remember to visit the model pages on the
    echo Hugging Face website to accept their license agreements:
    echo - SD3: https://huggingface.co/stabilityai/stable-diffusion-3-medium-diffusers
    echo - FLUX: https://huggingface.co/black-forest-labs/FLUX.1-dev
    echo.
) else (
    echo.
    echo [INFO] Skipping Hugging Face login.
    echo You can log in later by opening a terminal, running
    echo 'conda activate %ENV_NAME%' and then 'huggingface-cli login'.
    echo Note: SD3 and FLUX models will not work until you do.
)
exit /b 0