@echo off
cd /d "%~dp0"
echo ========================================
echo Form939 Weekend SUPERVISOR (optimized)
echo ========================================
echo.
echo Pass 1: qwen + llama + gemma4  (60 calls - model comparison)
echo Pass 2-3: qwen + llama only     (40 calls each - consistency)
echo Stall timeout: 30 min (Gemma-safe)  ^|  Resume on restart
echo ETA: ~1.5 hours remaining from restart
echo.
python scripts\supervisor\cli.py --target-iterations 3 --sleep-between-loops 120 --stall-timeout 1800
if %ERRORLEVEL% EQU 0 (echo [DONE]) else (echo [ERROR] code %ERRORLEVEL%)
pause
