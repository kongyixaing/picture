@echo off
cd /d "%~dp0"
cls

echo ========================================
echo   Picture Sharing Website
echo ========================================
echo.
echo Default admin: admin / admin123
echo URL: http://localhost:5001/pic
echo.

if exist "PictureAndVideos.exe" (
    echo Starting executable...
    echo.
    PictureAndVideos.exe
    goto end
)

if exist "dist\PictureAndVideos\PictureAndVideos.exe" (
    echo Starting with built executable...
    echo.
    cd dist\PictureAndVideos
    PictureAndVideos.exe
    goto end
)

echo Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python not found!
    echo Please run build_exe.bat first to build the executable,
    echo or install Python and required dependencies.
    echo.
    pause
    exit /b 1
)

python check_env.py
if errorlevel 1 goto error

echo.
echo ========================================
echo   Starting server...
echo ========================================
echo.

python -u pic_app.py

echo.
echo ========================================
echo   Server stopped.
echo ========================================
goto end

:error
echo.
echo ========================================
echo   Startup failed!
echo ========================================

:end
echo.
echo Press any key to close...
pause >nul
