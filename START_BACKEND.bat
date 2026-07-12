@echo off
cd /d "%~dp0backend"
start cmd /k start_backend.bat
echo.
echo ======================================
echo   Backend AI Study Planner
echo ======================================
echo.
echo Backend demarre dans une nouvelle fenetre !
echo.
echo URLs disponibles :
echo   - Backend API : http://localhost:8000
echo   - Documentation : http://localhost:8000/docs
echo   - Health Check : http://localhost:8000/health
echo.
echo Configuration actuelle (backend/.env) :
echo   - AI_SERVICE_TYPE=colab
echo   - Base de donnees : PostgreSQL (Laragon)
echo.
echo Pour arreter : Fermez la fenetre du backend ou appuyez sur Ctrl+C
echo.
pause
