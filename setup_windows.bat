@echo off
setlocal EnableExtensions
cd /d "%~dp0"
chcp 65001 >nul
title Offline PDF AI Summarizer - Setup

echo ============================================================
echo   Offline PDF AI Summarizer - First-time setup
echo ============================================================
echo.
where py >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python Launcher was not found.
  echo Install Python 3.11 64-bit from https://www.python.org/downloads/windows/
  echo Enable the option to install the Python Launcher during setup.
  pause
  exit /b 1
)
py -3.11 --version >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python 3.11 was not found. Install Python 3.11 64-bit and retry.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  py -3.11 -m venv .venv
  if errorlevel 1 goto :error
)
echo Updating pip...
.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 echo WARNING: pip upgrade failed; continuing.
echo Installing core dependencies...
.venv\Scripts\python.exe -m pip install -r requirements-core.txt
if errorlevel 1 goto :error
echo Installing local llama.cpp runtime (this can take time on some Windows setups)...
.venv\Scripts\python.exe -m pip install "llama-cpp-python>=0.3.0" --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
if errorlevel 1 (
  echo.
  echo WARNING: llama-cpp-python could not be installed automatically.
  echo The graphical app and PDF tools are installed, but AI summaries require this runtime.
  echo See README.md section "Windows llama.cpp installation" for options.
)
if not exist "models" mkdir models
if not exist "temporary" mkdir temporary
if not exist "outputs" mkdir outputs
if not exist "models\README.md" echo Place a compatible GGUF instruct model in this folder. See models\README.md. > models\README.md
 echo.
echo Setup completed.
echo Next steps:
echo   1. Place a compatible .gguf model in models
echo      (or select one from Settings in the app).
echo   2. Double-click run.bat
echo.
echo No API key is needed. The model file itself is not included.
pause
exit /b 0

:error
echo.
echo Setup failed while installing required application dependencies.
echo Check your internet connection for this one-time package installation, then retry.
echo See README.md for troubleshooting.
pause
exit /b 1
