@echo off
chcp 65001 >nul
cd /d "%~dp0"

set PORT=8765
set URL=http://127.0.0.1:%PORT%/

echo.
echo  Bozdemir Makine — Uretim Planlama
echo  --------------------------------
echo  Klasor: %cd%
echo  Adres:  %URL%
echo.
echo  Durdurmak icin bu pencerede Ctrl+C
echo.

REM Eski / takili sunucu varsa portu bosalt
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT% " ^| findstr LISTENING') do (
  echo [!] Port %PORT% kullanimda — PID %%a sonlandiriliyor...
  taskkill /PID %%a /F >nul 2>&1
)

where python >nul 2>&1
if not errorlevel 1 (
  set PY=python
  goto :run
)

where py >nul 2>&1
if not errorlevel 1 (
  set PY=py
  goto :run
)

echo [HATA] Python bulunamadi. https://www.python.org/downloads/
pause
exit /b 1

:run
timeout /t 1 /nobreak >nul
start "" "%URL%"
%PY% -m http.server %PORT%
if errorlevel 1 (
  echo.
  echo [HATA] Sunucu baslatilamadi.
  pause
  exit /b 1
)
