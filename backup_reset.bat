@echo off
title Website Backup and Reset Tool
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "BACKUP_DIR=%SCRIPT_DIR%backup"
set "PASS_FILE=%SCRIPT_DIR%reset_password.txt"
set "DEFAULT_PASS=admin123"

set "DATA_DIRS=user picture comments BanRecord groupchat videos data static\uploads"

cd /d "%SCRIPT_DIR%"

if not exist "%PASS_FILE%" echo %DEFAULT_PASS%>"%PASS_FILE%"

if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

:MENU
cls
echo ========================================
echo   Website Backup and Reset Tool
echo ========================================
echo.
echo   1. Create Backup
echo   2. Restore Backup
echo   3. Reset Entire Website
echo   4. Change Reset Password
echo   5. Exit
echo.
set /p "choice=Please select an option (1-5): "

if "%choice%"=="1" goto CREATE_BACKUP
if "%choice%"=="2" goto RESTORE_BACKUP
if "%choice%"=="3" goto RESET_SITE
if "%choice%"=="4" goto CHANGE_PASSWORD
if "%choice%"=="5" goto EXIT

goto MENU

:CREATE_BACKUP
cls
echo ========================================
echo       Create Backup
echo ========================================
echo.
set "d=%date%"
set "t=%time%"
set "d=%d:/=%"
set "d=%d:-=%"
set "d=%d: =%"
set "t=%t::=%"
set "t=%t:.=%"
set "t=%t: =0%"
set "TIMESTAMP=%d%_%t:~0,6%_%random%"

set "BACKUP_NAME=backup_%TIMESTAMP%"
set "BACKUP_PATH=%BACKUP_DIR%\%BACKUP_NAME%"

echo Creating backup: %BACKUP_NAME%
echo.

mkdir "%BACKUP_PATH%" 2>nul

for %%d in (%DATA_DIRS%) do (
    if exist "%%d" (
        echo Backing up %%d ...
        xcopy "%%d" "%BACKUP_PATH%\%%d\" /E /I /Q /Y >nul
    )
)

echo.
echo Backup complete! Location: %BACKUP_PATH%
echo.
pause
goto MENU

:RESTORE_BACKUP
cls
echo ========================================
echo       Restore Backup
echo ========================================
echo.

set "INDEX=0"

echo Available backups:
echo.

for /d %%d in ("%BACKUP_DIR%\backup_*") do (
    set /a INDEX+=1
    set "BACKUP_LIST[!INDEX!]=%%~nxd"
    echo   !INDEX!. %%~nxd
)

if %INDEX%==0 (
    echo   No backups found
    echo.
    pause
    goto MENU
)

echo.
set /p "sel=Select backup number to restore (0 to cancel): "

if "%sel%"=="0" goto MENU

set "SEL_BACKUP=!BACKUP_LIST[%sel%]!"

if "!SEL_BACKUP!"=="" (
    echo Invalid selection
    pause
    goto RESTORE_BACKUP
)

echo.
set /p "confirm=Confirm restore backup "!SEL_BACKUP!" ? (Y/N): "
if /i not "%confirm%"=="Y" (
    echo Cancelled
    pause
    goto MENU
)

echo.
echo Restoring...

for %%d in (%DATA_DIRS%) do (
    if exist "%%d" (
        rmdir /s /q "%%d" 2>nul
    )
    if exist "%BACKUP_DIR%\!SEL_BACKUP!\%%d" (
        echo Restoring %%d ...
        xcopy "%BACKUP_DIR%\!SEL_BACKUP!\%%d" "%%d\" /E /I /Q /Y >nul
    )
)

echo.
echo Restore complete!
echo.
pause
goto MENU

:RESET_SITE
cls
echo ========================================
echo       Reset Entire Website
echo ========================================
echo.
echo WARNING: This will DELETE ALL DATA!
echo.

set /p "input_pass=Enter reset password: "

set "SAVED_PASS="
for /f "usebackq delims=" %%a in ("%PASS_FILE%") do set "SAVED_PASS=%%a"

if not "%input_pass%"=="%SAVED_PASS%" (
    echo Wrong password!
    pause
    goto MENU
)

echo.
echo Password correct.
echo.
echo Press THREE DIFFERENT keys to confirm reset:
echo.

set "KEY1="
set "KEY2="
set "KEY3="

set /p "KEY1=Confirmation 1 - press any key then Enter: "

:SECOND_KEY
set /p "KEY2=Confirmation 2 - press a DIFFERENT key then Enter: "
if "%KEY2%"=="%KEY1%" (
    echo Must press a different key!
    goto SECOND_KEY
)

:THIRD_KEY
set /p "KEY3=Confirmation 3 - press a DIFFERENT key then Enter: "
if "%KEY3%"=="%KEY1%" (
    echo Must press a different key!
    goto THIRD_KEY
)
if "%KEY3%"=="%KEY2%" (
    echo Must press a different key!
    goto THIRD_KEY
)

echo.
echo Three confirmations complete. Resetting website...
echo.

for %%d in (%DATA_DIRS%) do (
    if exist "%%d" (
        echo Deleting %%d ...
        rmdir /s /q "%%d" 2>nul
    )
)

echo.
echo Recreating data directories...
for %%d in (%DATA_DIRS%) do (
    mkdir "%%d" 2>nul
)

echo.
echo Website has been reset!
echo.
echo Now please set a new reset password.
echo.

:SET_NEW_PASS1
set /p "NEW_PASS1=Enter new reset password: "
if "%NEW_PASS1%"=="" (
    echo Password cannot be empty!
    goto SET_NEW_PASS1
)

:SET_NEW_PASS2
set /p "NEW_PASS2=Enter new reset password again: "
if not "%NEW_PASS2%"=="%NEW_PASS1%" (
    echo Passwords do not match!
    goto SET_NEW_PASS1
)

echo %NEW_PASS1%>"%PASS_FILE%"

echo.
echo New reset password has been set!
echo.
pause
goto MENU

:CHANGE_PASSWORD
cls
echo ========================================
echo       Change Reset Password
echo ========================================
echo.

set /p "old_pass=Enter current reset password: "

set "SAVED_PASS="
for /f "usebackq delims=" %%a in ("%PASS_FILE%") do set "SAVED_PASS=%%a"

if not "%old_pass%"=="%SAVED_PASS%" (
    echo Wrong password!
    pause
    goto MENU
)

echo.

:NEW_PASS1
set /p "new_pass1=Enter new reset password: "
if "%new_pass1%"=="" (
    echo Password cannot be empty!
    goto NEW_PASS1
)

:NEW_PASS2
set /p "new_pass2=Enter new reset password again: "
if not "%new_pass2%"=="%new_pass1%" (
    echo Passwords do not match!
    goto NEW_PASS1
)

echo %new_pass1%>"%PASS_FILE%"

echo.
echo Password changed successfully!
echo.
pause
goto MENU

:EXIT
cls
echo Goodbye!
echo.
pause
exit /b 0
