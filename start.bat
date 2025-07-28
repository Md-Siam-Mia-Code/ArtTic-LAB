@echo off
REM ArtTic-LAB Launcher for Windows
title ArtTic-LAB

REM Activate the dedicated conda environment
call conda.bat activate ArtTic-LAB

REM Run the main application, passing along all command-line arguments (like --disable-filters)
python app.py %*

echo.
echo ArtTic-LAB has closed. Press any key to exit this window.
pause >nul