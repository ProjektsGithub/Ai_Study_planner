# 🚀 Setup Rapide AI Study Planner

## Scripts Disponibles

Trois scripts .bat pour faciliter l'installation :

### 1️⃣ `check_postgresql.bat` - Vérifier PostgreSQL
Double-cliquez sur ce fichier pour vérifier si PostgreSQL est installé dans Laragon.

**Ce qu'il fait :**
- Cherche PostgreSQL dans Laragon
- Affiche la version trouvée
- Donne des instructions si PostgreSQL est absent

---

### 2️⃣ `create_database.bat` - Créer la Base de Données
Double-cliquez sur ce fichier pour créer la base de données `ai_study_planner`.

**Ce qu'il fait :**
- Trouve automatiquement PostgreSQL dans Laragon
- Crée la base de données `ai_study_planner`
- Configure la connexion dans `.env`

---

### 3️⃣ `setup_complet.bat` - Installation Complète ⭐
**RECOMMANDÉ** - Double-cliquez sur ce fichier pour tout installer automatiquement !

**Ce qu'il fait :**
1. Vérifie PostgreSQL
2. Crée la base de données
3. Crée l'environnement virtuel Python
4. Installe toutes les dépendances
5. Applique les migrations (crée les tables)
6. Crée le compte Super Admin

**Credentials créés :**
- Email: `admin@example.com`
- Password: `Admin123!`

---

## 📋 Installation Étape par Étape

### Option A : Installation Automatique (RECOMMANDÉ)
1. Double-cliquez sur `setup_complet.bat`
2. Attendez la fin de l'installation (2-5 minutes)
3. Notez les credentials affichés
4. C'est terminé !

### Option B : Installation Manuelle
1. Double-cliquez sur `check_postgresql.bat` pour vérifier PostgreSQL
2. Double-cliquez sur `create_database.bat` pour créer la BD
3. Ouvrir PowerShell dans le dossier backend :
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   alembic upgrade head
   python scripts\seed_admin.py
   ```

---

## 🚀 Démarrer le Serveur

Après l'installation, pour démarrer le backend :

```powershell
cd backend
.\venv\Scripts\activate
uvicorn app.main:app --reload
```

Le serveur démarre sur : http://localhost:8000

API Documentation : http://localhost:8000/api/docs

---

## ❓ Problèmes Courants

### PostgreSQL introuvable
**Erreur :** `PostgreSQL introuvable dans Laragon`

**Solution :**
1. Ouvrir Laragon
2. Menu → Preferences → Services
3. Cocher "PostgreSQL"
4. Redémarrer Laragon
5. Relancer `setup_complet.bat`

---

### Base de données existe déjà
**Message :** `La base existe déjà`

**C'est normal !** Passez directement à la suite.

---

### Python introuvable
**Erreur :** `python n'est pas reconnu`

**Solution :**
1. Installer Python 3.11+ depuis https://www.python.org/
2. Cocher "Add to PATH" pendant l'installation
3. Redémarrer le terminal
4. Relancer `setup_complet.bat`

---

### Mot de passe PostgreSQL demandé
**Si un mot de passe est demandé lors de la création de la BD**

**Solutions :**
1. Essayer sans mot de passe (appuyer sur Entrée)
2. Essayer `postgres` comme mot de passe
3. Modifier `.env` pour ajouter le mot de passe :
   ```
   DATABASE_URL=postgresql+psycopg://postgres:VOTRE_MDP@localhost:5432/ai_study_planner
   ```

---

## 📞 Support

Si un problème persiste :
1. Vérifier les logs affichés dans le terminal
2. Consulter le fichier `.env` 
3. Vérifier que Laragon est démarré
4. Vérifier que PostgreSQL est en cours d'exécution dans Laragon

---

## ✅ Vérification Finale

Pour vérifier que tout fonctionne :

```powershell
cd backend
.\venv\Scripts\activate
python -c "from app.core.database import SessionLocal; db = SessionLocal(); print('✓ Connexion DB OK'); db.close()"
```

Si aucune erreur, tout est prêt ! 🎉
