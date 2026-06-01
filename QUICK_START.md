# Guide de démarrage rapide - AI Study Planner

## État actuel

✅ **Frontend** : Lancé et fonctionnel sur **http://localhost:5173/**
❌ **Backend** : Nécessite configuration de la base de données

## Frontend (Déjà lancé)

Le frontend React est actuellement en cours d'exécution sur :
- **URL** : http://localhost:5173/
- **Status** : ✅ Opérationnel

Vous pouvez accéder à la démo du calendrier sans backend :
- http://localhost:5173/demo

## Backend (Configuration requise)

Le backend FastAPI nécessite :

### 1. Base de données PostgreSQL

**Option A : Utiliser Laragon (Recommandé)**
```bash
# Démarrer PostgreSQL depuis Laragon
# Puis créer la base de données
cd backend
venv\Scripts\activate
python create_database.py
```

**Option B : Utiliser SQLite (Développement rapide)**
```bash
# Modifier backend/.env
DATABASE_URL=sqlite:///./test.db

# Puis lancer le backend
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Installer les dépendances manquantes

Si vous obtenez des erreurs de modules manquants :
```bash
cd backend
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Lancer le backend

```bash
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Le backend sera accessible sur : **http://localhost:8000**

## Accès à l'application

Une fois le backend lancé :

1. **Page d'accueil** : http://localhost:5173/
2. **Inscription** : http://localhost:5173/register
3. **Connexion** : http://localhost:5173/login
4. **Dashboard** : http://localhost:5173/dashboard (après connexion)
5. **Démo** : http://localhost:5173/demo (sans backend)

## Documentation API

Une fois le backend lancé :
- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc

## Fonctionnalités disponibles

### Sans backend (Démo)
- ✅ Vue du calendrier hebdomadaire
- ✅ Interface utilisateur complète
- ✅ Navigation entre les pages

### Avec backend
- ✅ Inscription et connexion
- ✅ Gestion du profil
- ✅ Gestion des matières
- ✅ Gestion des disponibilités
- ✅ Gestion des contraintes
- ✅ Génération de plans d'étude
- ✅ Édition manuelle des sessions
- ✅ Notifications
- ✅ Dashboard avec statistiques

## Résolution des problèmes

### Le frontend ne se lance pas
```bash
cd frontend
npm install
npm run dev
```

### Le backend ne trouve pas les modules
```bash
cd backend
venv\Scripts\activate
pip install -r requirements.txt
```

### Erreur de connexion à la base de données
1. Vérifier que PostgreSQL est lancé dans Laragon
2. Ou modifier `.env` pour utiliser SQLite
3. Créer la base de données avec `python create_database.py`

### Port déjà utilisé
- Frontend (5173) : Modifier dans `vite.config.js`
- Backend (8000) : Utiliser `--port 8001` dans la commande uvicorn

## Structure du projet

```
AIplaning/
├── frontend/          # Application React
│   ├── src/
│   │   ├── components/  # Composants réutilisables
│   │   ├── pages/       # Pages de l'application
│   │   ├── context/     # Contextes React
│   │   └── api/         # Client API
│   └── package.json
│
├── backend/           # API FastAPI
│   ├── app/
│   │   ├── api/         # Endpoints API
│   │   ├── models/      # Modèles SQLAlchemy
│   │   ├── schemas/     # Schémas Pydantic
│   │   ├── services/    # Logique métier
│   │   └── core/        # Configuration
│   ├── venv/            # Environnement virtuel Python
│   └── requirements.txt
│
└── .kiro/             # Spécifications du projet
```

## Prochaines étapes

1. ✅ Frontend lancé et fonctionnel
2. ⏳ Configurer et lancer le backend
3. ⏳ Créer un compte utilisateur
4. ⏳ Configurer votre profil
5. ⏳ Ajouter vos matières
6. ⏳ Définir vos disponibilités
7. ⏳ Générer votre premier plan d'étude

## Support

Pour plus d'informations :
- `README.md` - Documentation générale
- `backend/DATABASE_SCHEMA.md` - Schéma de la base de données
- `frontend/TESTING_GUIDE.md` - Guide de test
- `ARCHITECTURE_DECISIONS.md` - Décisions d'architecture
