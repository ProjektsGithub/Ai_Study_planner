#!/bin/bash

echo "======================================"
echo "  AI Study Planner - Backend Server"
echo "======================================"
echo ""

# Activer l'environnement virtuel
source venv/bin/activate

echo "[1/3] Environnement virtuel activé"
echo ""

# Vérifier que la base de données est accessible
echo "[2/3] Vérification de la base de données..."
python -c "from app.core.database import engine; engine.connect()" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[ERREUR] Base de données PostgreSQL non accessible"
    echo "Assurez-vous que PostgreSQL est démarré"
    exit 1
fi
echo "Base de données OK"
echo ""

# Démarrer le serveur FastAPI
echo "[3/3] Démarrage du serveur FastAPI..."
echo ""
echo "Backend disponible sur: http://localhost:8000"
echo "Documentation API: http://localhost:8000/docs"
echo ""
echo "Appuyez sur Ctrl+C pour arrêter le serveur"
echo ""

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
