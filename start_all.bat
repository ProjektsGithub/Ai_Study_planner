@echo off
echo ============================================
echo   AI Study Planner - Demarrage Complet
echo ============================================
echo.

echo Ce script va ouvrir 2 fenetres:
echo   1. Backend (FastAPI sur port 8000)
echo   2. Frontend (React sur port 5173)
echo.
echo Appuyez sur une touche pour continuer...
pause >nul

echo.
echo [1/2] Demarrage du Backend...
start "AI Study Planner - Backend" cmd /k "cd /d %~dp0backend && start_backend.bat"

echo Attente de 3 secondes...
timeout /t 3 /nobreak >nul

echo [2/2] Demarrage du Frontend...
start "AI Study Planner - Frontend" cmd /k "cd /d %~dp0frontend && start_frontend.bat"

echo.
echo ============================================
echo   Serveurs demarres !
echo ============================================
echo.
echo Backend:  http://localhost:8000/docs
echo Frontend: http://localhost:5173
echo.
echo Pour arreter les serveurs, fermez les fenetres
echo ou appuyez sur Ctrl+C dans chaque fenetre.
echo.
