@echo off
title Weblume AI Company
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo.
  echo   First time? Run the setup steps in README.md first.
  echo.
  pause
  exit /b
)
if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo   Created .env - open it, add your Gemini key, then run start.bat again.
  notepad ".env"
  pause
  exit /b
)
echo.
echo   Weblume AI Company is starting... the dashboard opens in your browser.
echo   Keep this window open. Close it to stop.
echo.
".venv\Scripts\python.exe" server.py
pause
