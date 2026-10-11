@echo off
cd /d "%~dp0"
python -m pip install pyinstaller requests beautifulsoup4
if errorlevel 1 goto fail
python -m PyInstaller --noconfirm --clean --onefile --windowed --name web-downloader downloader_gui_exe.py
if errorlevel 1 goto fail
echo.
echo Build complete: dist\web-downloader.exe
pause
exit /b 0
:fail
echo Build failed. Check the error above.
pause
exit /b 1
