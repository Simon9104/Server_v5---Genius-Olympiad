@echo off
echo ============================================
echo  GreenIOT — Building Windows .exe
echo ============================================

:: Install PyInstaller if missing
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

:: Build single-file executable
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "GreenIOT Server" ^
    --icon "..\server\assets\icon.ico" ^
    --add-data "..\server\server.py;server" ^
    greeniot_launcher.py

echo.
echo Build complete! Find the .exe in the dist\ folder.
pause
