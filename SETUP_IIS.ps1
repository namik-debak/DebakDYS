# DYS IIS kurulum — 192.168.0.245
# Yonetici PowerShell: C:\inetpub\wwwroot\debakdys\SETUP_IIS.ps1
# Python yoksa resmi 3.10.11 installer sessiz kurulur (vendor\ veya python.org).

$ErrorActionPreference = "Stop"
$Root = "C:\inetpub\wwwroot\debakdys"
if (-not (Test-Path $Root)) { $Root = Split-Path -Parent $MyInvocation.MyCommand.Path }
Set-Location $Root

function Refresh-ProcessPath {
    $machine = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $user = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machine;$user"
}

function Test-RealPython([string]$Path) {
    if (-not $Path -or -not (Test-Path -LiteralPath $Path)) { return $false }
    if ($Path -match '\\WindowsApps\\') { return $false }
    $item = Get-Item -LiteralPath $Path -ErrorAction SilentlyContinue
    if (-not $item -or $item.Length -lt 1024) { return $false }
    return $true
}

function Get-PythonVersion([string]$Exe) {
    try {
        $out = & $Exe -c "import sys; print('%d.%d.%d' % sys.version_info[:3]); print(64 if sys.maxsize > 2**32 else 32)" 2>$null
        if (-not $out) { return $null }
        $lines = @($out | Where-Object { $_ })
        return @{ Version = [version]$lines[0]; Bits = [int]$lines[1]; Exe = $Exe }
    } catch {
        return $null
    }
}

function Find-SystemPython {
    $candidates = New-Object System.Collections.Generic.List[string]
    if ($env:DYS_PYTHON) { $candidates.Add($env:DYS_PYTHON) }

    foreach ($cmd in @("py", "python", "python3")) {
        $g = Get-Command $cmd -ErrorAction SilentlyContinue
        if ($g -and $g.Source) { $candidates.Add($g.Source) }
    }

    foreach ($p in @(
        "$env:SystemRoot\py.exe",
        "$env:LOCALAPPDATA\Programs\Python\Launcher\py.exe",
        "${env:ProgramFiles}\Python310\python.exe",
        "${env:ProgramFiles}\Python311\python.exe",
        "${env:ProgramFiles}\Python312\python.exe",
        "${env:ProgramFiles}\Python313\python.exe",
        "C:\Python310\python.exe",
        "C:\Python311\python.exe",
        "C:\Python312\python.exe"
    )) { $candidates.Add($p) }

    Get-ChildItem "${env:ProgramFiles}\Python*" -Directory -ErrorAction SilentlyContinue |
        ForEach-Object { $candidates.Add((Join-Path $_.FullName "python.exe")) }
    Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\Python*" -Directory -ErrorAction SilentlyContinue |
        ForEach-Object { $candidates.Add((Join-Path $_.FullName "python.exe")) }
    Get-ChildItem "C:\Users\*\AppData\Local\Programs\Python\Python*" -Directory -ErrorAction SilentlyContinue |
        ForEach-Object { $candidates.Add((Join-Path $_.FullName "python.exe")) }

    foreach ($hive in @("HKLM:\SOFTWARE\Python\PythonCore", "HKLM:\SOFTWARE\WOW6432Node\Python\PythonCore", "HKCU:\SOFTWARE\Python\PythonCore")) {
        if (-not (Test-Path $hive)) { continue }
        Get-ChildItem $hive -ErrorAction SilentlyContinue | ForEach-Object {
            $ip = Join-Path $_.PSPath "InstallPath"
            if (Test-Path $ip) {
                $dir = (Get-ItemProperty $ip -ErrorAction SilentlyContinue)."(default)"
                if ($dir) { $candidates.Add((Join-Path $dir "python.exe")) }
            }
        }
    }

    $best = $null
    foreach ($raw in $candidates) {
        if (-not (Test-RealPython $raw)) { continue }
        $info = $null
        if ([IO.Path]::GetFileName($raw) -ieq "py.exe") {
            foreach ($arg in @("-3.10", "-3.11", "-3.12", "-3.13", "-3")) {
                try {
                    $resolved = & $raw $arg -c "import sys; print(sys.executable)" 2>$null
                    if ($resolved -and (Test-RealPython $resolved.Trim())) {
                        $info = Get-PythonVersion $resolved.Trim()
                        if ($info) { break }
                    }
                } catch { }
            }
        } else {
            $info = Get-PythonVersion $raw
        }
        if (-not $info) { continue }
        if ($info.Version.Major -ne 3 -or $info.Version.Minor -lt 10) { continue }
        if ($info.Bits -lt 64) { continue }
        if (-not $best -or $info.Version -gt $best.Version) { $best = $info }
        if ($info.Version.Minor -eq 10) { return $info }
    }
    return $best
}

function Get-PythonInstaller {
    $name = "python-3.10.11-amd64.exe"
    $paths = @(
        (Join-Path $Root "vendor\$name"),
        (Join-Path $env:TEMP $name)
    )
    foreach ($p in $paths) {
        if ((Test-Path $p) -and (Get-Item $p).Length -gt 20MB) { return $p }
    }

    $dest = Join-Path $env:TEMP $name
    $url = "https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe"
    Write-Host "Python installer indiriliyor: $url"
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing
    if (-not (Test-Path $dest) -or (Get-Item $dest).Length -lt 20MB) {
        throw "Python installer indirilemedi: $url"
    }
    return $dest
}

function Install-Python310 {
    Write-Host "Python 3.10 bulunamadi. Sessiz kurulum basliyor (InstallAllUsers + PATH)..." -ForegroundColor Yellow

    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if ($winget) {
        Write-Host "Deneme: winget Python.Python.3.10"
        try {
            & winget install -e --id Python.Python.3.10 --scope machine --accept-package-agreements --accept-source-agreements
            Refresh-ProcessPath
            if (Find-SystemPython) { return $true }
            Write-Warning "winget sonrasi Python hala yok; resmi installer denenecek."
        } catch {
            Write-Warning "winget basarisiz: $($_.Exception.Message)"
        }
    } else {
        Write-Host "winget yok; resmi python.org installer kullanilacak."
    }

    $installer = Get-PythonInstaller
    Write-Host "Kurulum: $installer"
    $args = @(
        "/quiet",
        "InstallAllUsers=1",
        "PrependPath=1",
        "Include_test=0",
        "Include_doc=0",
        "Include_pip=1",
        "Include_launcher=1",
        "AssociateFiles=0",
        "Shortcuts=0",
        'TargetDir=C:\Program Files\Python310'
    )
    $p = Start-Process -FilePath $installer -ArgumentList $args -Wait -PassThru
    Write-Host "Installer cikis kodu: $($p.ExitCode)"
    if ($p.ExitCode -ne 0) {
        throw "Python sessiz kurulum basarisiz (kod $($p.ExitCode)). Yonetici olarak calistirin."
    }

    Start-Sleep -Seconds 2
    Refresh-ProcessPath
    return $true
}

Write-Host "=== 1) Python venv ===" -ForegroundColor Cyan

$venvPy = Join-Path $Root ".venv\Scripts\python.exe"
$pyInfo = Find-SystemPython
if (-not $pyInfo) {
    Install-Python310 | Out-Null
    Refresh-ProcessPath
    $pyInfo = Find-SystemPython
}

if (-not $pyInfo -and -not (Test-Path $venvPy)) {
    $hint = 'C:\Program Files\Python310\python.exe'
    throw "Python 3.10+ (64-bit) yok. Kuruluysa: `$env:DYS_PYTHON = '$hint'  sonra scripti tekrar calistirin."
}

if ($pyInfo) {
    Write-Host ("Python: {0}  ({1}-bit {2})" -f $pyInfo.Exe, $pyInfo.Bits, $pyInfo.Version)
}

if (-not (Test-Path $venvPy)) {
    Write-Host "venv olusturuluyor..."
    & $pyInfo.Exe -m venv (Join-Path $Root ".venv")
    if ($LASTEXITCODE -ne 0) { throw "venv olusturulamadi." }
}
if (-not (Test-Path $venvPy)) { throw "venv python.exe yok: $venvPy" }

Write-Host "pip + requirements..."
& $venvPy -m pip install -U pip
& $venvPy -m pip install -r (Join-Path $Root "requirements.txt")

New-Item -ItemType Directory -Force -Path (Join-Path $Root "logs"), (Join-Path $Root "temp") | Out-Null

$webConfig = Join-Path $Root "web.config"
if (Test-Path $webConfig) {
    $xml = New-Object System.Xml.XmlDocument
    $xml.PreserveWhitespace = $true
    $xml.Load($webConfig)
    $hp = $xml.SelectSingleNode("//httpPlatform")
    if ($hp) {
        $logFile = [string](Join-Path $Root "logs\httpplatform")
        $hp.SetAttribute("processPath", [string]$venvPy)
        $hp.SetAttribute("stdoutLogFile", $logFile)
        foreach ($ev in $hp.SelectNodes("environmentVariables/environmentVariable")) {
            if ($ev.GetAttribute("name") -eq "PYTHONPATH") {
                $ev.SetAttribute("value", [string]$Root)
            }
        }
        $xml.Save($webConfig)
        Write-Host "web.config processPath: $venvPy"
    }
}

Write-Host "=== 2) IIS ===" -ForegroundColor Cyan
try {
    Import-Module WebAdministration -ErrorAction Stop
} catch {
    throw "WebAdministration yok. IIS Yonetim Araclari kurulu olmali."
}

$hpp = Get-WebGlobalModule -Name "httpPlatformHandler" -ErrorAction SilentlyContinue
if (-not $hpp) {
    Write-Warning "HttpPlatformHandler yok. https://www.iis.net/downloads/microsoft/httpplatformhandler"
}

$pool = "DebakDYSPool"
$site = "DebakDYS"
$HttpPort = 8081
if (-not (Test-Path "IIS:\AppPools\$pool")) {
    New-WebAppPool -Name $pool | Out-Null
}
Set-ItemProperty "IIS:\AppPools\$pool" -Name managedRuntimeVersion -Value ""
Set-ItemProperty "IIS:\AppPools\$pool" -Name enable32BitAppOnWin64 -Value $false
Set-ItemProperty "IIS:\AppPools\$pool" -Name processModel.idleTimeout -Value ([TimeSpan]::FromMinutes(0))

$existing = Get-Website -Name $site -ErrorAction SilentlyContinue
if (-not $existing) {
    New-Website -Name $site -Port $HttpPort -PhysicalPath $Root -ApplicationPool $pool | Out-Null
} else {
    Set-ItemProperty "IIS:\Sites\$site" -Name physicalPath -Value $Root
    Set-ItemProperty "IIS:\Sites\$site" -Name applicationPool -Value $pool
    $hasPort = Get-WebBinding -Name $site -Protocol http -ErrorAction SilentlyContinue |
        Where-Object { $_.bindingInformation -match ":${HttpPort}:" }
    if (-not $hasPort) {
        New-WebBinding -Name $site -Protocol http -Port $HttpPort -IPAddress "*" | Out-Null
    }
    Get-WebBinding -Name $site -Protocol http -ErrorAction SilentlyContinue |
        Where-Object { $_.bindingInformation -match ':80:' } |
        ForEach-Object { Remove-WebBinding -Name $site -Protocol http -Port 80 -ErrorAction SilentlyContinue }
}
Start-Website -Name $site -ErrorAction SilentlyContinue

if (-not (Get-NetFirewallRule -DisplayName "DebakDYS 8081" -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -DisplayName "DebakDYS 8081" -Direction Inbound -Protocol TCP -LocalPort $HttpPort -Action Allow | Out-Null
    Write-Host "Firewall: TCP $HttpPort acildi."
}

icacls $Root /grant "IIS_IUSRS:(OI)(CI)RX" /T | Out-Null
icacls (Join-Path $Root "logs") /grant "IIS_IUSRS:(OI)(CI)M" /T | Out-Null
icacls (Join-Path $Root "temp") /grant "IIS_IUSRS:(OI)(CI)M" /T | Out-Null

Write-Host "=== 3) Havuz kimligi ===" -ForegroundColor Yellow
Write-Host "UNC AL DOSYALAR icin DebakDYSPool Identity = domain servis hesabi olmali."
Write-Host "IIS Manager > Application Pools > DebakDYSPool > Advanced Settings > Identity"
Write-Host ""
Write-Host "Smoke: http://192.168.0.245:8081/login"
Write-Host "Bitti." -ForegroundColor Green
