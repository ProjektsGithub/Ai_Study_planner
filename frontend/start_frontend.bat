@echo off
echo ======================================
echo   AI Study Planner - Frontend Server
echo ======================================
echo.

echo [1/2] Verification de node_modules...
if not exist "node_modules" (
    echo Installation des dependances...
    call npm install
    if errorlevel 1 (
        echo [ERREUR] Installation des dependances echouee
        pause
        exit /b 1
    )
) else (
    echo Dependances deja installees
)
echo.

echo [2/2] Demarrage du serveur de developpement...
echo.
echo Frontend disponible sur: http://localhost:5173
echo.
echo Appuyez sur Ctrl+C pour arreter le serveur
echo.

npm run dev
