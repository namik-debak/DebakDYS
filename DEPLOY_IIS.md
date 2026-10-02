# DYS — IIS dağıtım (192.168.0.245 / debakdys)
# ==================================================

Ayrıntılı iş planı: `.cursor/plans/iis-debakdys-245.md`

## Hedef
- Paylaşım: `\\192.168.0.245\wwwroot\debakdys`
- Fiziksel (sunucu): `C:\inetpub\wwwroot\debakdys`
- Site: **DebakDYS**, havuz **DebakDYSPool**, önerilen URL: `http://192.168.0.245/`
- DB: `DEBAKNETSIS\DB20` / **DBKDYS**
- Dosyalar: `\\192.168.0.249\kalite\AL DOSYALAR`
- Temp: `C:\inetpub\wwwroot\debakdys\temp`

## 1. Sunucu yazılımları
- IIS (Web Server) + **HttpPlatformHandler 1.2**
- Python 3.10+ (64-bit)
- ODBC Driver 17 for SQL Server
- (İsteğe bağlı) Excel/Word — kontrollü kopya PDF

## 2. Kod
1. Projeyi `\\192.168.0.245\wwwroot\debakdys` kopyala (`.venv` hariç)
2. Sunucuda:
   ```text
   py -3 -m venv .venv
   .\.venv\Scripts\pip install -r requirements.txt
   mkdir logs temp
   ```
3. `.env` koy (`DYS_PREFIX` boş; `DYS_APP_BASE_URL=http://192.168.0.245`)
4. `web.config` içindeki python / PYTHONPATH / log yollarını doğrula

## 3. IIS
1. Havuz `DebakDYSPool`: No Managed Code, 64-bit, **domain servis hesabı**
2. Site `DebakDYS` → `C:\inetpub\wwwroot\debakdys`, binding :80, bu havuz
3. Havuz hesabı: site klasörü + `logs`/`temp` Modify; UNC AL DOSYALAR Okuma+Yazma; SQL DBKDYS yazma

## 4. Smoke
- `http://192.168.0.245/login`
- Doküman listesi / önizleme / kontrollü kopya
- Yeni yükleme → UNC
- App pool recycle sonrası log: `logs\httpplatform*.log`

## 5. Güvenlik
- `.env` git’e girmez
- `sa` yerine uygulama SQL login
- `DYS_SECRET_KEY` production değeri korunur
