@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo   [CLARITY] 极净奢护 · 收交衣智能检测系统
echo   ========================================
echo.
echo   访问: http://localhost:5000
echo   收衣: http://localhost:5000/intake
echo   交衣: http://localhost:5000/delivery
echo   后台: http://localhost:5000/dashboard
echo.
python app.py
pause
