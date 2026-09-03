@echo off
cd /d "%~dp0"
echo ========================================
echo Form939 Weekend Autonomous Benchmark
echo ========================================
echo.
echo [1/2] Health check...
python healthcheck.py
echo.
echo [2/2] Starting infinite loop (Ctrl+C to stop)...
echo Results: logs\benchmark_results.csv
echo Log:     logs\weekend_run.log
echo.
python run.py --loops 0 --sleep 300
pause
