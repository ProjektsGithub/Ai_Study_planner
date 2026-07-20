# Start Backend Development Server
Write-Host "Starting AI Study Planner Backend..." -ForegroundColor Green

# Check if virtual environment exists
if (!(Test-Path "backend\venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    py -m venv backend\venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& backend\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r backend\requirements.txt

# Force UTF-8 encoding to prevent Windows charmap codec errors with Unicode characters
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

# Start server
Write-Host "Starting FastAPI server on http://localhost:8000" -ForegroundColor Green
Write-Host "API Documentation: http://localhost:8000/api/docs" -ForegroundColor Cyan
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
