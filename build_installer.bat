@echo off
cd /d "%~dp0"
cls

echo ========================================
echo   Build PictureAndVideos Installer
echo ========================================
echo.

set ISCC_PATH=

echo Searching for Inno Setup...

if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" (
    set "ISCC_PATH=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
    goto found
)

if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    goto found
)

if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set "ISCC_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"
    goto found
)

echo.
echo Inno Setup not found!
echo Install it via: winget install JRSoftware.InnoSetup
echo.
pause
exit /b 1

:found
echo Found: %ISCC_PATH%
echo.

if not exist "dist\PictureAndVideos\PictureAndVideos.exe" (
    echo WARNING: dist\PictureAndVideos\PictureAndVideos.exe not found!
    echo Building executable first...
    echo.
    call build_exe.bat
    if errorlevel 1 (
        echo.
        echo Build FAILED!
        pause
        exit /b 1
    )
)

echo Building installer...
echo.

"%ISCC_PATH%" installer.iss

if errorlevel 1 (
    echo.
    echo ========================================
    echo   Installer build FAILED!
    echo ========================================
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Installer build SUCCESS!
echo ========================================
echo.
echo Output: installer_output\PictureAndVideos-Setup-v1.0.0.exe
echo.
pause
