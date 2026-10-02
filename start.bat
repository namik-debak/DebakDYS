@echo off
title DYS - Dokuman Yonetim Sistemi
cd /d "%~dp0"

echo ========================================================
echo   DEBAK DIJITAL - DOKUMAN YONETIM SISTEMI (DYS)
echo ========================================================
echo.

if not exist .env (
    if exist .env.example (
        echo [BILGI] .env dosyasi bulunamadi, .env.example kopyalaniyor...
        copy .env.example .env >nul
    )
)

echo [1/3] Sanal ortam kontrol ediliyor...
if exist .venv\Scripts\activate.bat (
    echo [BILGI] .venv aktif ediliyor...
    call .venv\Scripts\activate.bat
) else if exist venv\Scripts\activate.bat (
    echo [BILGI] venv aktif ediliyor...
    call venv\Scripts\activate.bat
) else if exist env\Scripts\activate.bat (
    echo [BILGI] env aktif ediliyor...
    call env\Scripts\activate.bat
) else (
    echo [UYARI] Sanal ortam bulunamadi, varsayilan Python kullanilacak.
)

echo.
echo [2/3] Tarayici 2 saniye sonra otomatik acilacak...
start "" powershell -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:5000'"

echo [3/3] DYS Sunucusu Baslatiliyor (Waitress WSGI)...
echo.
echo ========================================================
echo   Uygulama Adresi : http://127.0.0.1:5000
echo   Kapatmak icin   : Bu pencerede Ctrl + C tuslarina basin
echo ========================================================
echo.

python start_dys.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [HATA] Uygulama beklenmedik sekilde durdu. Hata Kodu: %ERRORLEVEL%
    pause
)
