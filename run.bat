@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
if not exist ".venv\Scripts\python.exe" (
  echo Application environment not found. Please run setup_windows.bat first.
  pause
  exit /b 1
)
.venv\Scripts\python.exe -m app.main
if errorlevel 1 (
  echo.
  echo The application exited with an error. See the local log in %%LOCALAPPDATA%%\OfflinePDFSummarizer\logs\app.log
  pause
)
