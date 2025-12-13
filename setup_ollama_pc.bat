@echo off
REM Jazz Ollama Setup Launcher
REM This batch file runs the PowerShell setup script

setlocal enabledelayedexpansion

REM Get the directory of this batch file
set "SCRIPT_DIR=%~dp0"

REM Launch PowerShell with the setup script
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%setup_ollama_pc.ps1"

pause
