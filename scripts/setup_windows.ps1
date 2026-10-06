# Windows 11 Automated Setup Script for Strata Desktop MoE (PRJ-17)
# Run from Administrator or Standard PowerShell

$ErrorActionPreference = "Stop"
Write-Host "=== Setting up Strata Desktop MoE on Windows 11 ===" -ForegroundColor Cyan

# 1. Check Python
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Error "Python 3.12+ is required. Please install Python first."
}

# 2. Check NVIDIA Driver
try {
    $nvidiaSmi = & nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
    Write-Host "GPU Detected: $nvidiaSmi" -ForegroundColor Green
} catch {
    Write-Warning "nvidia-smi not detected. Ensure NVIDIA driver 580+ is installed."
}

# 3. Setup Virtual Environment
if (-not (Test-Path ".venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

& .venv\Scripts\pip install --upgrade pip
& .venv\Scripts\pip install -r requirements.txt

# 4. Clone or update Strata upstream engine
if (-not (Test-Path "engine")) {
    Write-Host "Cloning upstream Strata engine..." -ForegroundColor Yellow
    git clone https://github.com/Niko1221/Strata.git engine
}

Write-Host "Setup complete. To launch the Coder MoE profile:" -ForegroundColor Green
Write-Host "cd engine && .\START-HERE.bat --family coder --context 65536 --draft-vocab en --low-ram resident --calibrate" -ForegroundColor Yellow
