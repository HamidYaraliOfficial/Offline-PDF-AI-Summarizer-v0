@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
if not exist ".venv\Scripts\python.exe" (
  echo Run setup_windows.bat first.
  pause
  exit /b 1
)
echo Installing build tools and the full local AI runtime...
.venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller
if errorlevel 1 (
  echo Dependency installation failed. Check README.md, then retry.
  pause
  exit /b 1
)
echo Building one-folder Windows distribution...
.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --windowed --name OfflinePDFSummarizer --paths . --collect-all llama_cpp app\main.py
if errorlevel 1 goto :error
echo.
if not exist "dist\OfflinePDFSummarizer\models" mkdir "dist\OfflinePDFSummarizer\models"
copy /Y "models\README.md" "dist\OfflinePDFSummarizer\models\README.md" >nul
echo Build complete: dist\OfflinePDFSummarizer\OfflinePDFSummarizer.exe
echo Place a model GGUF in dist\OfflinePDFSummarizer\models or select one in Settings.
echo Test the package on a clean Windows machine before redistributing.
pause
exit /b 0
:error
echo Build failed. See the error output above.
pause
exit /b 1
