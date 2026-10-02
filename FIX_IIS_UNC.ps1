# DebakDYS — UNC onizleme icin havuz kimligi
# Domain hesabi (Administrator) workgroup IIS'te 5021/0x80070426 verir.
# Havuz LocalSystem; dosya paylasimi .env DYS_FILESHARE_* ile WNet.

$ErrorActionPreference = "Stop"
Import-Module WebAdministration
$pool = "DebakDYSPool"
Set-ItemProperty "IIS:\AppPools\$pool" -Name processModel.identityType -Value LocalSystem
try { Start-WebAppPool $pool } catch { Restart-WebAppPool $pool }
Write-Host "DebakDYSPool = LocalSystem. Dosya erisimi DYS_FILESHARE_USER ile."
Write-Host "Test: http://192.168.0.245:8081/login"
