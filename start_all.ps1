# AutoJobApply — Quick Start All Services
# Run this from the project root: .\start_all.ps1

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "   AutoJobApply - Starting All Services  " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

$root = $PSScriptRoot
$venvPython = "$root\.venv\Scripts\python.exe"

# 1. Node.js Backend (Port 3000)
Write-Host "[1/9] Starting Node.js Backend (Port 3000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\backend'; Write-Host 'Node.js Backend - Port 3000' -ForegroundColor Cyan; node server.js"
Start-Sleep -Seconds 3

# 2. Flask Automation Service (Port 5001)
Write-Host "[2/9] Starting Flask Automation Service (Port 5001)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\automation'; Write-Host 'Flask Automation - Port 5001' -ForegroundColor Cyan; & '$venvPython' app.py"
Start-Sleep -Seconds 2

# 3. Job Search Agent (Port 5003)
Write-Host "[3/9] Starting Job Search Agent (Port 5003)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\backend\agents\job_search_agent'; Write-Host 'Job Search Agent - Port 5003' -ForegroundColor Cyan; & '$venvPython' main.py"
Start-Sleep -Seconds 1

# 4. Job Matching Agent (Port 5004)
Write-Host "[4/9] Starting Job Matching Agent (Port 5004)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\backend\agents\job_matching_agent'; Write-Host 'Job Matching Agent - Port 5004' -ForegroundColor Cyan; & '$venvPython' main.py"
Start-Sleep -Seconds 1

# 5. Browser Agent (Port 5005)
Write-Host "[5/9] Starting Browser Agent (Port 5005)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\backend\agents\browser_agent'; Write-Host 'Browser Agent - Port 5005' -ForegroundColor Cyan; & '$venvPython' main.py"
Start-Sleep -Seconds 1

# 6. Form Filling Agent (Port 5006)
Write-Host "[6/9] Starting Form Filling Agent (Port 5006)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\backend\agents\form_agent'; Write-Host 'Form Filling Agent - Port 5006' -ForegroundColor Cyan; & '$venvPython' main.py"
Start-Sleep -Seconds 1

# 7. LangGraph Orchestrator (Port 5007)
Write-Host "[7/9] Starting LangGraph Orchestrator (Port 5007)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\backend\agents\orchestrator'; Write-Host 'LangGraph Orchestrator - Port 5007' -ForegroundColor Cyan; & '$venvPython' main.py"
Start-Sleep -Seconds 1

# 8. Memory Agent (Port 5008)
Write-Host "[8/9] Starting Memory Agent (Port 5008)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\backend\agents\memory_agent'; Write-Host 'Memory Agent - Port 5008' -ForegroundColor Cyan; & '$venvPython' main.py"
Start-Sleep -Seconds 1

# 9. AI Platform & MCP Server (Port 5009) + Career Copilot (Port 5010)
Write-Host "[9/9] Starting AI Platform (5009) and Career Copilot (5010)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\backend\ai_platform'; Write-Host 'AI Platform & MCP - Port 5009' -ForegroundColor Cyan; & '$venvPython' main.py"
Start-Sleep -Seconds 1
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\backend\career_copilot'; Write-Host 'Career Copilot - Port 5010' -ForegroundColor Cyan; & '$venvPython' main.py"

Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host "  All services launched in separate windows  " -ForegroundColor Green
Write-Host "                                             " -ForegroundColor Green
Write-Host "  Main App:      http://localhost:3000        " -ForegroundColor Green
Write-Host "  Automation:    http://localhost:5001/health " -ForegroundColor Green
Write-Host "  Job Search:    http://localhost:5003/health " -ForegroundColor Green
Write-Host "  Job Matching:  http://localhost:5004/health " -ForegroundColor Green
Write-Host "  Browser Agent: http://localhost:5005/health " -ForegroundColor Green
Write-Host "  Form Agent:    http://localhost:5006/health " -ForegroundColor Green
Write-Host "  Orchestrator:  http://localhost:5007/health " -ForegroundColor Green
Write-Host "  Memory Agent:  http://localhost:5008/health " -ForegroundColor Green
Write-Host "  AI Platform:   http://localhost:5009/health " -ForegroundColor Green
Write-Host "  Career Copilot:http://localhost:5010/health " -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""
