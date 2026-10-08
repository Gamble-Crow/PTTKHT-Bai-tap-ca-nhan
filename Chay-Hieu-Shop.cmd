@echo off
cd /d "%~dp0"
py -c "from PIL import Image" >nul 2>&1
if errorlevel 1 (
  echo Chua co thu vien Pillow. Chay: py -m pip install -r requirements.txt
  pause
  exit /b 1
)
echo Hieu Ecommerce Shop - ban Python
echo Mo http://localhost:4173 tren trinh duyet.
echo Nhan Ctrl+C de dung web.
echo.
py app.py
pause
