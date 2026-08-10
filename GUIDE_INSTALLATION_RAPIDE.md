# 🚀 Guide d'Installation Rapide

## Pour Récupérer et Installer le Projet

### 1️⃣ Récupérer les Mises à Jour depuis GitHub

```bash
cd C:\laragon\www\AIplaning
git pull origin main
```

---

### 2️⃣ Créer la Base de Données (AUTOMATIQUE)

Le script détecte automatiquement votre utilisateur Windows pour Laragon :

```bash
cd backend
python create_database.py
```

**Ce script fait tout automatiquement :**
- ✅ Détecte votre utilisateur PostgreSQL
- ✅ Teste plusieurs utilisateurs possibles
- ✅ Crée la base de données `ai_study_planner`
- ✅ Affiche la configuration à utiliser

---

### 3️⃣ Configuration .env (Vérification)

Le script affiche l'URL à utiliser. Vérifiez que `.env` contient :

```
DATABASE_URL=postgresql+psycopg://VOTRE_USER@localhost:5432/ai_study_planner
```

*(VOTRE_USER = votre nom d'utilisateur Windows)*

---

### 4️⃣ Installation Complète (Suite)

```bash
# 1. Créer l'environnement virtuel (si pas déjà fait)
python -m venv venv

# 2. Activer l'environnement
.\venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Appliquer les migrations (créer les tables)
alembic upgrade head

# 5. Créer le compte Super Admin
python scripts\seed_admin.py
```

---

### 5️⃣ Démarrer le Serveur

```bash
uvicorn app.main:app --reload
```

**Le backend sera accessible sur :**
- http://localhost:8000
- http://localhost:8000/api/docs (documentation)

---

## 🎯 Résumé Ultra-Rapide

```bash
# 1. Récupérer les mises à jour
cd C:\laragon\www\AIplaning
git pull origin main

# 2. Créer la BD (automatique)
cd backend
python create_database.py

# 3. Setup complet
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
python scripts\seed_admin.py

# 4. Démarrer
uvicorn app.main:app --reload
```

---

## 📝 Identifiants Admin Créés

```
Email:    admin@example.com
Password: Admin123!
```

**⚠️ Changez le mot de passe après la première connexion !**

---

## ❓ Problèmes Courants

### "role does not exist"
**Le script Python résout ce problème automatiquement** en testant plusieurs utilisateurs.

### "connection refused"
**PostgreSQL n'est pas démarré**
1. Ouvrir Laragon
2. Cliquer "Tout démarrer"
3. Réessayer

### "database already exists"
**C'est normal !** Passez directement à l'étape suivante.

---

## 📚 Documentation Complète

Pour plus de détails, consultez :
- `backend/SETUP_DATABASE.md` - Documentation complète de la BD
- `backend/SETUP_RAPIDE.md` - Scripts batch Windows
- `README.md` - Documentation générale du projet

---

## 🎬 Commandes Frontend (après le backend)

```bash
cd ..\frontend
npm install
npm run dev
```

Frontend accessible sur : http://localhost:5173

---

**Temps d'installation estimé : 5-10 minutes**
