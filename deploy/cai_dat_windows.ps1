# Cài đặt trên Windows Server/PC. Chạy PowerShell *Run as Administrator* tại thư mục dự án:
#   powershell -ExecutionPolicy Bypass -File deploy\cai_dat_windows.ps1 [-Port 8501] [-DungNSSM]
# Việc làm: tạo .venv, cài thư viện, mở tường lửa, đăng ký chạy nền tự khởi động (Task Scheduler, hoặc NSSM nếu có -DungNSSM).
param([int]$Port = 8501, [switch]$DungNSSM)
$ErrorActionPreference = "Stop"
$App = Split-Path -Parent $PSScriptRoot
Set-Location $App

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Chưa có Python. Cài Python 3.10+ từ python.org (tích Add python.exe to PATH) rồi chạy lại."
}
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
New-Item -ItemType Directory -Force workspace | Out-Null

New-NetFirewallRule -DisplayName "Dutoan $Port" -Direction Inbound -Protocol TCP -LocalPort $Port -Action Allow -ErrorAction SilentlyContinue | Out-Null

$py = Join-Path $App ".venv\Scripts\python.exe"
$args = "-X utf8 -m streamlit run app.py --server.address 0.0.0.0 --server.port $Port --server.headless true --browser.gatherUsageStats false"

if ($DungNSSM) {
    if (-not (Get-Command nssm -ErrorAction SilentlyContinue)) { throw "Chưa có nssm (https://nssm.cc). Cài hoặc bỏ -DungNSSM." }
    nssm install Dutoan $py $args
    nssm set Dutoan AppDirectory $App
    nssm set Dutoan Start SERVICE_AUTO_START
    nssm set Dutoan AppStdout (Join-Path $App "workspace\service.log")
    nssm set Dutoan AppStderr (Join-Path $App "workspace\service.log")
    nssm start Dutoan
} else {
    $action  = New-ScheduledTaskAction -Execute $py -Argument $args -WorkingDirectory $App
    $trigger = New-ScheduledTaskTrigger -AtStartup
    $set     = New-ScheduledTaskSettingsSet -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero)
    Register-ScheduledTask -TaskName "Dutoan" -Action $action -Trigger $trigger -Settings $set -User "SYSTEM" -RunLevel Highest -Force | Out-Null
    Start-ScheduledTask -TaskName "Dutoan"
}
Write-Host "Xong. Truy cập http://localhost:$Port hoặc http://<IP-server>:$Port"
