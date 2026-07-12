#!/bin/bash

echo "======================================"
echo "  AI Study Planner - Frontend Server"
echo "======================================"
echo ""

echo "[1/2] Vérification de node_modules..."
if [ ! -d "node_modules" ]; then
    echo "Installation des dépendances..."
    npm install
    if [ $? -ne 0 ]; then
        echo "[ERREUR] Installation des dépendances échouée"
        exit 1
    fi
else
    echo "Dépendances déjà installées"
fi
echo ""

echo "[2/2] Démarrage du serveur de développement..."
echo ""
echo "Frontend disponible sur: http://localhost:5173"
echo ""
echo "Appuyez sur Ctrl+C pour arrêter le serveur"
echo ""

npm run dev
