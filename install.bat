@echo off
setlocal enabledelayedexpansion

REM ArtTic-LAB Installer for Windows
title ArtTic-LAB Installer

:: --- Configuration ---
SET "ENV_NAME=ArtTic-LAB"
SET "PYTHON_VERSIONS_TO_TRY=3.11 3.12 3.10"
SET "PYTORCH_LATEST=torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/xpu"
SET "IPEX_LATEST=intel-extension-for-pytorch --extra-index-url https://pytorch-extension.intel.com/release-whl/stable/xpu/us/"
SET "OTHER_PACKAGES=diffusers accelerate safetensors gradio invisible-watermark"

:main
cls
ECHO.
ECHO =======================================================
ECHO             ArtTic-LAB Installer
ECHO =======================================================
ECHO.
ECHO This script will find your Conda installation and
ECHO prepare the '%ENV_NAME%' environment.
ECHO.

REM =======================================================
REM 1. FIND AND INITIALIZE CONDA
REM =======================================================
ECHO [INFO] Searching for Conda installation...
SET "CONDA_BASE_PATH="
where conda.exe >nul 2>nul && (FOR /F "delims=" %%i IN ('where conda.exe') DO SET "CONDA_EXE_PATH=%%i" & GOTO FoundConda)
IF EXIST "%USERPROFILE%\Miniconda3\condabin\conda.bat" SET "CONDA_BASE_PATH=%USERPROFILE%\Miniconda3" & GOTO FoundConda
IF EXIST "%USERPROFILE%\Anaconda3\condabin\conda.bat" SET "CONDA_BASE_PATH=%USERPROFILE%\Anaconda3" & GOTO FoundConda
IF EXIST "%ProgramData%\Miniconda3\condabin\conda.bat" SET "CONDA_BASE_PATH=%ProgramData%\Miniconda3" & GOTO FoundConda
IF EXIST "%ProgramData%\Anaconda3\condabin\conda.bat" SET "CONDA_BASE_PATH=%ProgramData%\Anaconda3" & GOTO FoundConda
GOTO NoConda

:FoundConda
IF NOT DEFINED CONDA_BASE_PATH ( FOR %%i IN ("%CONDA_EXE_PATH%") DO SET "CONDA_SCRIPTS_DIR=%%~dpi" & FOR %%j IN ("!CONDA_SCRIPTS_DIR!..") DO SET "CONDA_BASE_PATH=%%~fj" )
ECHO [SUCCESS] Conda installation detected at: %CONDA_BASE_PATH%
ECHO.
call "%CONDA_BASE_PATH%\Scripts\activate.bat"
IF %ERRORLEVEL% NEQ 0 ( ECHO [ERROR] Failed to execute Conda's activate.bat script. & GOTO InstallFail )

REM =======================================================
REM 2. HANDLE ENVIRONMENT CREATION LOGIC
REM =======================================================
SET "ENV_EXISTS=0"
conda env list | findstr /I /B "%ENV_NAME% " >nul && SET "ENV_EXISTS=1"

IF "%ENV_EXISTS%"=="1" (
    ECHO [WARNING] Environment '%ENV_NAME%' already exists.
    CHOICE /C YN /M "Do you want to remove it and perform a clean installation?"
    
    REM ################### CRITICAL FIX IS HERE ###################
    REM Use !ERRORLEVEL! because we are inside a code block ().
    REM %ERRORLEVEL% would be evaluated when the block is first read, not after CHOICE runs.
    IF !ERRORLEVEL! EQU 2 (
        ECHO [INFO] Skipping environment creation. Will install/update packages in the existing environment.
        GOTO ActivateAndInstall
    )
    REM If user chose 'Y' (ERRORLEVEL 1), execution continues past this IF block.
)

ECHO [INFO] Starting clean installation of environment '%ENV_NAME%'...
FOR %%P IN (%PYTHON_VERSIONS_TO_TRY%) DO (
    call :CreateEnvironment %%P
    IF !ERRORLEVEL! EQU 0 GOTO ActivateAndInstall
)
GOTO UltimateFail


REM =======================================================
REM 3. ACTIVATE AND INSTALL PACKAGES
REM =======================================================
:ActivateAndInstall
ECHO.
ECHO [INFO] Activating environment and installing/updating dependencies...
ECHO This is the longest step. Please be patient.
call conda activate %ENV_NAME%
IF %ERRORLEVEL% NEQ 0 ( ECHO [ERROR] Failed to activate the '%ENV_NAME%' environment. It may be corrupt. & GOTO InstallFail )

python -m pip install --upgrade pip --quiet
IF %ERRORLEVEL% NEQ 0 ( ECHO [ERROR] Failed to upgrade pip. & GOTO InstallFail )

ECHO [INFO] Installing PyTorch for Intel GPU (XPU)...
python -m pip install %PYTORCH_LATEST%
IF !ERRORLEVEL! NEQ 0 ( ECHO [ERROR] Failed to install PyTorch. & GOTO InstallFail )

ECHO [INFO] Installing Intel Extension for PyTorch (IPEX)...
python -m pip install %IPEX_LATEST%
IF !ERRORLEVEL! NEQ 0 ( ECHO [ERROR] Failed to install IPEX. & GOTO InstallFail )

ECHO [INFO] Installing other dependencies...
pip install %OTHER_PACKAGES%
IF %ERRORLEVEL% NEQ 0 ( ECHO [ERROR] Failed to install other dependencies. & GOTO InstallFail )

GOTO InstallationSucceeded


REM =======================================================
REM SUBROUTINE: CreateEnvironment
REM =======================================================
:CreateEnvironment
ECHO. & ECHO ------------------------------------------------------- & ECHO [ATTEMPT] Trying to create environment with Python %1... & ECHO -------------------------------------------------------
ECHO [INFO] Removing any previous version of '%ENV_NAME%'...
call conda env remove --name %ENV_NAME% -y >nul 2>nul
ECHO [INFO] Creating new Conda environment...
call conda create --name %ENV_NAME% python=%1 -y
IF %ERRORLEVEL% NEQ 0 ( ECHO [ERROR] Failed to create environment with Python %1. & exit /b 1 )
exit /b 0


REM =======================================================
REM FINAL OUTCOMES
REM =======================================================
:InstallationSucceeded
ECHO. & ECHO ======================================================= & ECHO [SUCCESS] Installation complete! & ECHO You can now run 'start.bat' to launch ArtTic-LAB. & ECHO ======================================================= & ECHO. & GOTO End
:NoConda
ECHO. & ECHO [ERROR] Conda not found. Please install Miniconda. & ECHO. & GOTO End
:InstallFail
ECHO. & ECHO [ERROR] An unexpected error occurred during setup. & ECHO. & GOTO End
:UltimateFail
ECHO. & ECHO ======================================================= & ECHO [FATAL ERROR] All installation attempts have failed. & ECHO ======================================================= & ECHO We tried Python versions %PYTHON_VERSIONS_TO_TRY% but could not create a working environment. & ECHO. & GOTO End
:End
pause
endlocal