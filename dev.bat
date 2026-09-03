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
    call weekend_supervisor.bat
    goto :eof
)

if "%1"=="supervise" (
    call weekend_supervisor.bat
    goto :eof
)

if "%1"=="publish" (
    echo Publishing benchmark metrics (dry-run)...
    python scripts\publisher\cli.py --input-dir logs
    goto :eof
)

if "%1"=="publish-write" (
    echo Publishing benchmark metrics to logs\published...
    python scripts\publisher\cli.py --input-dir logs --output-dir logs\published --write
    goto :eof
)

echo Usage:
echo   dev.bat test         - Run pytest suite
echo   dev.bat health       - Run environment health check
echo   dev.bat weekend      - Start supervised weekend loop (recommended)
echo   dev.bat supervise    - Same as weekend
echo   dev.bat publish      - Preview benchmark report (dry-run)
echo   dev.bat publish-write - Write benchmark report to logs\published
echo   dev.bat clean        - Remove Python cache files
