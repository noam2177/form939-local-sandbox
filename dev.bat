@echo off
echo ========================================
echo Form939 Sandbox - Developer Tools
echo ========================================

if "%1"=="test" (
    echo Running all tests...
    pytest
    goto :eof
)

if "%1"=="health" (
    echo Running health check...
    python healthcheck.py
    goto :eof
)

if "%1"=="clean" (
    echo Cleaning cache files...
    rmdir /S /Q .pytest_cache 2>nul
    rmdir /S /Q src\__pycache__ 2>nul
    rmdir /S /Q tests\__pycache__ 2>nul
    echo Done.
    goto :eof
)

if "%1"=="weekend" (
    call weekend.bat
    goto :eof
)

echo Usage:
echo   dev.bat test    - Run pytest suite
echo   dev.bat health  - Run environment health check
echo   dev.bat weekend - Start autonomous weekend benchmark loop
echo   dev.bat clean   - Remove Python cache files
