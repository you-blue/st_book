@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ================================
echo   st_book 配置管理 GUI
echo ================================
echo.

if exist "dist\st_book.exe" (
    start "" /B "dist\st_book.exe"
    exit /b
)

call .venv\Scripts\activate.bat
python config_gui.py
pause
