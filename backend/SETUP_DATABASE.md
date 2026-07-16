# 🗄️ Setup Base de Données

## Méthode Recommandée : Script Python

Le script `create_database.py` détecte automatiquement l'utilisateur PostgreSQL de Laragon et crée la base de données.

### Utilisation

```bash
# Depuis le dossier backend
python create_database.py
```

### Ce que fait le script

1. ✅ Détecte automatiquement l'utilisateur Windows (pour Laragon)
2. ✅ Essaie plusieurs utilisateurs PostgreSQL (Windows user, postgres, user)
3. ✅ Vérifie si la base existe déjà
4. ✅ Crée la base de données `ai_study_planner`
5. ✅ Affiche la configuration DATABASE_URL à utiliser

### Avantages

- **Automatique** : Pas besoin de connaître l'utilisateur PostgreSQL
- **Intelligent** : Essaie plusieurs utilisateurs possibles
- **Sûr** : Ne crée pas la base si elle existe déjà
- **Informatif** : Affiche toutes les informations nécessaires

---

## Méthodes Alternatives

### Option A : Script Batch (Windows)

```bash
# Double-clic sur le fichier
create_database.bat
```

### Option B : Ligne de Commande Directe

```bash
# Avec votre nom d'utilisateur Windows
psql -U %USERNAME% -c "CREATE DATABASE ai_study_planner;"

# Ou avec postgres
psql -U postgres -c "CREATE DATABASE ai_study_planner;"
```

---

## Workflow Complet d'Installation

### 1️⃣ Créer la base de données
```bash
python create_database.py
```

### 2️⃣ Configurer .env
Vérifier que `DATABASE_URL` dans `.env` correspond à l'utilisateur affiché par le script :
```
DATABASE_URL=postgresql+psycopg://VOTRE_USER@localhost:5432/ai_study_planner
```

### 3️⃣ Appliquer les migrations
```bash
alembic upgrade head
```

### 4️⃣ Créer le compte Super Admin
```bash
python scripts\seed_admin.py
```

### 5️⃣ Démarrer le serveur
```bash
uvicorn app.main:app --reload
```

---

## Dépannage

### Erreur : "role does not exist"
**Cause** : L'utilisateur spécifié n'existe pas dans PostgreSQL

**Solution** : Le script Python essaie automatiquement plusieurs utilisateurs. Si ça échoue :
1. Vérifier que PostgreSQL est démarré dans Laragon
2. Essayer manuellement avec votre nom d'utilisateur Windows

### Erreur : "connection refused"
**Cause** : PostgreSQL n'est pas démarré

**Solution** :
1. Ouvrir Laragon
2. Cliquer sur "Tout démarrer"
3. Vérifier que PostgreSQL est en vert
4. Réessayer

### Erreur : "database already exists"
**Ce n'est pas une erreur !** La base existe déjà, vous pouvez passer à l'étape suivante.

---

## Vérification

Pour vérifier que la base de données existe :

```bash
# Python
python -c "import psycopg; conn = psycopg.connect('postgresql://VOTRE_USER@localhost/ai_study_planner'); print('✓ Connexion OK'); conn.close()"

# Ou psql
psql -U VOTRE_USER -l | findstr ai_study_planner
```

---

## Configuration pour Différents Environnements

### Laragon (Développement)
```
DATABASE_URL=postgresql+psycopg://VOTRE_USERNAME_WINDOWS@localhost:5432/ai_study_planner
```

### PostgreSQL Standard (Avec mot de passe)
```
DATABASE_URL=postgresql+psycopg://postgres:VOTRE_MDP@localhost:5432/ai_study_planner
```

### Production
```
DATABASE_URL=postgresql+psycopg://user:password@host:5432/ai_study_planner
```
