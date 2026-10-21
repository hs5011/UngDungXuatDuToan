# Cập nhật bản mới trên Windows (chạy Administrator tại thư mục dự án).
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
git pull
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (Get-Command nssm -ErrorAction SilentlyContinue) { nssm restart Dutoan 2>$null }
if (Get-ScheduledTask -TaskName Dutoan -ErrorAction SilentlyContinue) { Stop-ScheduledTask Dutoan; Start-ScheduledTask Dutoan }
