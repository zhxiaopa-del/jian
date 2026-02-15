@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 项目目录: %CD%
echo.
echo 正在启动数字人后端与前端...
echo 若后端窗口报错，请先执行: pip install -r backend/requirements.txt
echo.
start "数字人-后端" cmd /k "cd /d "%~dp0" && python backend/app.py"
timeout /t 4 /nobreak >nul
start "数字人-前端" cmd /k "cd /d "%~dp0frontend" && node server.js"
echo.
echo 后端: http://127.0.0.1:5000  （请确认该窗口无报错）
echo 前端: http://localhost:3000
echo 请在浏览器打开 http://localhost:3000 并允许麦克风。
echo.
pause
