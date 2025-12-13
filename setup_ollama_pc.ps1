# Jazz Ollama Setup for Local PC
# Run this script in PowerShell as Administrator

Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Jazz AI - Local PC Ollama Setup                           ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $isAdmin) {
    Write-Host "⚠️  This script should be run as Administrator" -ForegroundColor Yellow
    Write-Host "   Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    Read-Host "Press Enter to continue anyway..."
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "STEP 1: Check if Ollama is installed" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Check if Ollama is installed
$ollamaPath = "C:\Users\$env:USERNAME\AppData\Local\Programs\Ollama\ollama.exe"
$ollamaInPath = $null -ne (Get-Command ollama -ErrorAction SilentlyContinue)

if ($ollamaInPath -or (Test-Path $ollamaPath)) {
    Write-Host "✓ Ollama found on this PC" -ForegroundColor Green
    $ollamaVersion = &ollama --version 2>&1
    Write-Host "  Version: $ollamaVersion" -ForegroundColor Green
} else {
    Write-Host "✗ Ollama not found" -ForegroundColor Red
    Write-Host ""
    Write-Host "To install Ollama:" -ForegroundColor Yellow
    Write-Host "1. Go to https://ollama.com/download" -ForegroundColor Yellow
    Write-Host "2. Download and run the Windows installer" -ForegroundColor Yellow
    Write-Host "3. Restart your PC" -ForegroundColor Yellow
    Write-Host "4. Run this script again" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter once Ollama is installed"
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "STEP 2: Set OLLAMA_HOST environment variable" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Set environment variable for this session
$env:OLLAMA_HOST = "0.0.0.0:11434"
Write-Host "✓ OLLAMA_HOST set to: 0.0.0.0:11434" -ForegroundColor Green

# Permanently set environment variable
Write-Host ""
Write-Host "Setting permanent environment variable..." -ForegroundColor Cyan

try {
    [Environment]::SetEnvironmentVariable("OLLAMA_HOST", "0.0.0.0:11434", "User")
    Write-Host "✓ Permanent setting saved (User profile)" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Could not set User environment variable" -ForegroundColor Yellow
    Write-Host "   You may need to do this manually:" -ForegroundColor Yellow
    Write-Host "   Settings → Environment Variables → Add 'OLLAMA_HOST' = '0.0.0.0:11434'" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "STEP 3: Get your PC's IP address" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Get IP address
$ipAddresses = @()
Get-NetIPAddress -AddressFamily IPv4 -AddressState Preferred | ForEach-Object {
    if ($_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.*") {
        $ipAddresses += $_.IPAddress
        Write-Host "Network: $($_.InterfaceAlias)" -ForegroundColor Cyan
        Write-Host "  IP Address: $($_.IPAddress)" -ForegroundColor Green
    }
}

if ($ipAddresses.Count -eq 0) {
    Write-Host "⚠️  Could not find IP address" -ForegroundColor Yellow
} else {
    $selectedIP = $ipAddresses[0]
    Write-Host ""
    Write-Host "✓ Your PC IP: $selectedIP" -ForegroundColor Green
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "STEP 4: Download and run an AI model" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

Write-Host "Choose a model to download:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. qwen2.5:14b  (Recommended - 8GB RAM, high quality)" -ForegroundColor Yellow
Write-Host "2. qwen2.5:7b   (Medium - 4GB RAM, good balance)" -ForegroundColor Yellow
Write-Host "3. llama3.2:3b  (Small - 2GB RAM, fast)" -ForegroundColor Yellow
Write-Host "4. Skip for now" -ForegroundColor Yellow
Write-Host ""

$choice = Read-Host "Enter your choice (1-4)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "Pulling qwen2.5:14b... (This will take a few minutes)" -ForegroundColor Cyan
        & ollama pull qwen2.5:14b
        Write-Host "✓ Model downloaded!" -ForegroundColor Green
    }
    "2" {
        Write-Host ""
        Write-Host "Pulling qwen2.5:7b... (This will take a few minutes)" -ForegroundColor Cyan
        & ollama pull qwen2.5:7b
        Write-Host "✓ Model downloaded!" -ForegroundColor Green
    }
    "3" {
        Write-Host ""
        Write-Host "Pulling llama3.2:3b... (This will take a few minutes)" -ForegroundColor Cyan
        & ollama pull llama3.2:3b
        Write-Host "✓ Model downloaded!" -ForegroundColor Green
    }
    "4" {
        Write-Host "Skipping model download" -ForegroundColor Yellow
    }
    default {
        Write-Host "Invalid choice" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "STEP 5: Restart Ollama" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

Write-Host "Important: Restart Ollama so the OLLAMA_HOST setting takes effect" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Close Ollama (if running)" -ForegroundColor Cyan
Write-Host "2. Reopen Ollama" -ForegroundColor Cyan
Write-Host ""

$restart = Read-Host "Have you restarted Ollama? (y/n)"
if ($restart -eq "y") {
    Write-Host "✓ Great!" -ForegroundColor Green
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "✅ SETUP COMPLETE!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

Write-Host "Now update your VM's config.json:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  On the VM, edit config.json and change:" -ForegroundColor Cyan
Write-Host "    'ollama_host': 'http://$selectedIP:11434'" -ForegroundColor Green
Write-Host ""

Write-Host "Then on the VM, run:" -ForegroundColor Yellow
Write-Host "  ./start_all.sh" -ForegroundColor Cyan
Write-Host ""

Write-Host "Your VM will now connect to this PC's Ollama for AI responses!" -ForegroundColor Green
Write-Host ""

Read-Host "Press Enter to close"
