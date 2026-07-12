@echo off
REM Script Windows pour tester la connexion Google Colab

echo.
echo ========================================
echo   Test de connexion Google Colab
echo ========================================
echo.

cd backend

REM Vérifier si Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installé ou n'est pas dans PATH
    echo.
    pause
    exit /b 1
)

echo [1/2] Validation de la configuration...
echo.
python validate_colab_setup.py
if errorlevel 1 (
    echo.
    echo [ERREUR] Configuration invalide
    echo.
    pause
    exit /b 1
)

echo.
echo [2/2] Test de connexion au serveur Colab...
echo.
python test_colab_connection.py

echo.
pause
