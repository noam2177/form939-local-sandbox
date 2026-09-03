@echo off
cd /d "%~dp0"
echo ========================================
echo Form939 Weekend SUPERVISOR (recommended)
echo ========================================
echo.
echo This watchdog will:
echo   - Monitor Ollama health every 60s
echo   - Run benchmark loops (qwen + llama + gemma4)
echo   - Restart on crash or stall (10 min no progress)
echo   - Publish reports after each iteration
echo   - Save summary to logs\weekend_final_summary.txt
echo.
echo Logs:      logs\supervisor.log
echo Heartbeat: logs\supervisor_heartbeat.txt
echo State:     logs\supervisor_state.json
echo.
echo TIP: Stop any running run.py first (Ctrl+C in its window).
echo.
python scripts\supervisor\cli.py --target-iterations 0 --stall-timeout 600
pause
