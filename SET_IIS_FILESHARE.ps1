# DebakDYS — domain hesabini IIS havuz kimligi YAPMA.
# 245 workgroup: SpecificUser (DEBAKAS\Administrator) WAS 5021 ile havuzu kapatir.
# Havuz LocalSystem kalir; dosya erisimi .env / web.config DYS_FILESHARE_* (WNet).

$ErrorActionPreference = "Stop"
$root = "C:\inetpub\wwwroot\debakdys"
$log = Join-Path $root "logs\set_fileshare_identity.log"
$poolName = "DebakDYSPool"

function Write-Log([string]$msg) {
    $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg
    Add-Content -Path $log -Value $line -Encoding UTF8
    Write-Host $line
}

New-Item -ItemType Directory -Force -Path (Join-Path $root "logs") | Out-Null
Import-Module WebAdministration
Set-ItemProperty "IIS:\AppPools\$poolName" -Name processModel.identityType -Value LocalSystem
try { Start-WebAppPool $poolName } catch { Restart-WebAppPool $poolName }
Write-Log "DebakDYSPool=LocalSystem. Dosya paylasimi DYS_FILESHARE_USER (WNet). Domain havuz kimligi kullanilmiyor."
