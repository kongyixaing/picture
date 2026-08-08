@echo off
cd /d "%~dp0"
cls

echo ========================================
echo   Building PictureAndVideos.exe
echo ========================================
echo.

echo Checking PyInstaller...
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found, installing...
    pip install pyinstaller
)

echo.
echo Cleaning previous build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo Building...
python -m PyInstaller pic_app.spec --clean --noconfirm

if errorlevel 1 (
    echo.
    echo ========================================
    echo   Build FAILED!
    echo ========================================
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Build SUCCESS!
echo ========================================
echo.
echo Output: dist\PictureAndVideos.exe
echo.
pause
