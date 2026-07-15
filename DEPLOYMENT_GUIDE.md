# 🚀 Guide de Déploiement Complet - AI Study Planner

Ce guide vous explique **pas à pas** comment installer et démarrer l'application AI Study Planner sur votre ordinateur avec **3 méthodes différentes** selon vos besoins.

---

## 🎯 Quelle méthode choisir ?

| Méthode | Difficulté | Temps Setup | Performance IA | Coût | Recommandé pour |
|---------|------------|-------------|----------------|------|-----------------|
| **🟢 Méthode 1: Laragon (Tout-en-un)** | ⭐ Facile | 20 min | Bonne (GPU local) | Gratuit | **Débutants Windows** |
| **🟡 Méthode 2: Installation manuelle** | ⭐⭐ Moyen | 45 min | Bonne (GPU local) | Gratuit | Développeurs |
| **🔵 Méthode 3: Google Colab (Cloud)** | ⭐⭐⭐ Avancé | 30 min | Excellente (GPU Cloud) | 0-10€/mois | Production/Performance |

---

## 📋 Table des matières

### 🟢 Méthode 1: Installation avec Laragon (Recommandé)
1. [Prérequis Laragon](#-prérequis-méthode-1-laragon)
2. [Installation de Laragon](#-installation-de-laragon)
3. [Configuration de l'environnement](#-configuration-de-lenvironnement-laragon)
4. [Installation d'Ollama (IA locale)](#-installation-dollama-ia-locale)
5. [Installation du projet](#-installation-du-projet-avec-laragon)
6. [Démarrage avec Laragon](#-démarrage-avec-laragon)

### 🟡 Méthode 2: Installation Manuelle
1. [Prérequis Installation Manuelle](#-prérequis-méthode-2-installation-manuelle)
2. [Installation de Python](#-installation-de-python)
3. [Installation de Node.js](#-installation-de-nodejs)
4. [Installation de PostgreSQL](#-installation-de-postgresql)
5. [Installation d'Ollama (IA locale)](#-installation-dollama-ia-locale)
6. [Installation du projet](#-installation-du-projet-manuelle)
7. [Configuration](#-configuration-manuelle)
8. [Démarrage manuel](#-démarrage-manuel)

### 🔵 Méthode 3: Google Colab (IA Cloud)
1. [Configuration Google Colab](#-configuration-google-colab)
2. [Connexion Backend ↔ Colab](#-connexion-backend--colab)
3. [Monitoring et Maintenance](#-monitoring-colab)

### 📚 Sections communes
- [Première utilisation](#-première-utilisation)
- [Résolution des problèmes](#-résolution-des-problèmes)
- [Support et documentation](#-support)

---

# 🟢 MÉTHODE 1: Installation avec Laragon (Recommandé)

## ✅ Prérequis (Méthode 1: Laragon)

Avant de commencer, assurez-vous d'avoir :
- Un ordinateur sous **Windows 10/11** (minimum 8 GB RAM recommandé)
- Une connexion Internet
- Des droits d'administrateur sur votre PC
- **15 GB d'espace disque libre** (pour Laragon + bases de données)

---

## 🔧 Installation de Laragon

Laragon est un environnement de développement tout-en-un qui inclut automatiquement :
- ✅ Apache (serveur web)
- ✅ PHP
- ✅ Node.js
- ✅ Python
- ✅ PostgreSQL / MySQL
- ✅ Git
- ✅ Terminal intégré

### Étape 1 : Télécharger Laragon

1. Allez sur **https://laragon.org/download/**
2. Cliquez sur **"Laragon - Full"** (environ 200 MB)
3. Attendez que le téléchargement se termine

### Étape 2 : Installer Laragon

1. Double-cliquez sur le fichier téléchargé (ex: `laragon-wamp.exe`)
2. **Choisissez le dossier d'installation** : 
   - Recommandé : `C:\laragon`
   - ⚠️ **Évitez les chemins avec des espaces** (ex: "Program Files")
3. Cochez toutes les options :
   - ✅ Run Laragon when Windows starts
   - ✅ Add Laragon to System Path
4. Cliquez sur **"Install"**
5. Attendez la fin de l'installation (2-5 minutes)
6. Cliquez sur **"Finish"**

### Étape 3 : Démarrer Laragon

1. Cherchez "Laragon" dans le menu Démarrer de Windows
2. **Lancez Laragon** (une fenêtre apparaît)
3. Cliquez sur **"Start All"** (en bas à gauche)
4. Attendez que les services démarrent (Apache, PostgreSQL, etc.)
5. Vous devriez voir des icônes **vertes** ✅

### Étape 4 : Vérifier l'installation

1. Dans Laragon, cliquez sur **"Menu"** (en haut à droite)
2. Sélectionnez **"Terminal"**
3. Dans le terminal, tapez ces commandes pour vérifier :

```bash
# Vérifier Python
python --version

# Vérifier Node.js
node --version

# Vérifier npm
npm --version

# Vérifier PostgreSQL
psql --version
```

✅ Si vous voyez les versions, Laragon est correctement installé !

---

## �️ Configuration de l'environnement Laragon

### Étape 1 : Configurer PostgreSQL dans Laragon

1. Dans Laragon, cliquez sur **"Menu" → "PostgreSQL" → "Create Database"**
2. Entrez le nom : **`ai_study_planner`**
3. Cliquez sur **"OK"**

**Ou via le Terminal Laragon :**

```bash
# Ouvrir le terminal Laragon (Menu → Terminal)
psql -U postgres -c "CREATE DATABASE ai_study_planner;"
```

**Informations de connexion PostgreSQL (par défaut Laragon) :**
- **Host** : `localhost`
- **Port** : `5432`
- **User** : `postgres`
- **Password** : (vide par défaut, ou `postgres`)
- **Database** : `ai_study_planner`

### Étape 2 : Vérifier que PostgreSQL fonctionne

```bash
# Dans le terminal Laragon
psql -U postgres -l
```

Vous devriez voir la base de données `ai_study_planner` dans la liste.

---

## 🤖 Installation d'Ollama (IA locale)

Ollama permet d'utiliser des modèles d'IA directement sur votre ordinateur.

### Étape 1 : Télécharger Ollama

1. Allez sur **https://ollama.com/download**
2. Cliquez sur **"Download for Windows"**
3. Attendez le téléchargement

### Étape 2 : Installer Ollama

1. Double-cliquez sur le fichier téléchargé (ex: `OllamaSetup.exe`)
2. L'installation se fait automatiquement
3. Attendez que l'icône Ollama apparaisse dans la barre des tâches (en bas à droite)

### Étape 3 : Télécharger le modèle Llama 3.1

1. Ouvrez le **Terminal Laragon** (Menu → Terminal)
2. Tapez cette commande pour télécharger le modèle (⚠️ Cela peut prendre 10-30 minutes selon votre connexion, ~4.5 GB) :

```bash
ollama pull llama3.1:8b
```

3. Attendez que le téléchargement se termine
4. Vous devriez voir : `success`

### Étape 4 : Vérifier qu'Ollama fonctionne

```bash
# Lister les modèles installés
ollama list
```

Vous devriez voir `llama3.1:8b` dans la liste.

### Étape 5 : Tester Ollama

```bash
# Test rapide de génération
ollama run llama3.1:8b "Hello, how are you?"
```

Si vous voyez une réponse générée, Ollama fonctionne correctement ! Tapez `/bye` pour quitter.

---

## 📦 Installation du projet avec Laragon

### Étape 1 : Cloner ou télécharger le projet

**Option A - Si vous avez Git (inclus dans Laragon) :**

1. Ouvrez le **Terminal Laragon**
2. Allez dans le dossier `www` de Laragon :

```bash
cd C:\laragon\www
```

3. Clonez le projet :

```bash
git clone https://github.com/ProjektsGithub/Ai_Study_planner.git
cd Ai_Study_planner
```

**Option B - Sans Git :**

1. Allez sur https://github.com/ProjektsGithub/Ai_Study_planner
2. Cliquez sur le bouton vert **"Code"**
3. Cliquez sur **"Download ZIP"**
4. Extrayez le fichier ZIP dans `C:\laragon\www\AIplaning`

### Étape 2 : Installer les dépendances Backend

1. Dans le **Terminal Laragon**, allez dans le dossier backend :

```bash
cd C:\laragon\www\AIplaning\backend
```

2. Créez un environnement virtuel Python :

```bash
python -m venv venv
```

3. Activez l'environnement virtuel :

```bash
venv\Scripts\activate
```

*(Vous devriez voir `(venv)` au début de la ligne)*

4. Installez les dépendances :

```bash
pip install -r requirements.txt
```

*(Cela peut prendre quelques minutes)*

✅ Le backend est installé !

### Étape 3 : Installer les dépendances Frontend

1. Ouvrez un **nouveau Terminal Laragon** (Menu → Terminal)
2. Allez dans le dossier frontend :

```bash
cd C:\laragon\www\AIplaning\frontend
```

3. Installez les dépendances :

```bash
npm install
```

*(Cela peut prendre quelques minutes)*

✅ Le frontend est installé !

### Étape 4 : Configurer le Backend

1. Dans le dossier `backend`, copiez le fichier `.env.example` et renommez-le en `.env`
2. Ouvrez le fichier `.env` avec un éditeur de texte (clic droit → Modifier)
3. Modifiez les lignes suivantes :

```env
# Database (Configuration Laragon PostgreSQL)
DATABASE_URL=postgresql://postgres:@localhost:5432/ai_study_planner

# Ollama API (IA locale)
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.1:8b

# AI Service Type
AI_SERVICE_TYPE=ollama

# JWT Secret (générez une clé aléatoire longue)
SECRET_KEY=votre_cle_secrete_super_longue_et_aleatoire_changez_moi_123456789
```

**Notes importantes :**
- Si PostgreSQL dans Laragon a un mot de passe, modifiez : `postgresql://postgres:MOT_DE_PASSE@localhost:5432/ai_study_planner`
- Remplacez `SECRET_KEY` par une longue chaîne aléatoire

4. Sauvegardez le fichier `.env`

### Étape 5 : Initialiser la base de données

1. Dans le **Terminal Laragon**, allez dans le dossier backend :

```bash
cd C:\laragon\www\AIplaning\backend
```

2. Activez l'environnement virtuel (si pas déjà fait) :

```bash
venv\Scripts\activate
```

3. Créez les tables de la base de données :

```bash
alembic upgrade head
```

4. Vous devriez voir des messages indiquant que les migrations ont été appliquées

✅ La base de données est configurée !

---

## 🎯 Démarrage avec Laragon

### Méthode A : Démarrage automatique avec scripts

Le projet inclut des scripts pour simplifier le démarrage.

**1. Démarrer le Backend :**

Double-cliquez sur : `backend\start_backend.bat`

Ou dans le Terminal Laragon :

```bash
cd C:\laragon\www\AIplaning\backend
start_backend.bat
```

**2. Démarrer le Frontend :**

Double-cliquez sur : `frontend\start_frontend.bat`

Ou dans le Terminal Laragon :

```bash
cd C:\laragon\www\AIplaning\frontend
start_frontend.bat
```

### Méthode B : Démarrage manuel

**1. Démarrer le Backend :**

```bash
cd C:\laragon\www\AIplaning\backend
venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Vous devriez voir :
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**2. Démarrer le Frontend :**

Ouvrez un nouveau Terminal Laragon :

```bash
cd C:\laragon\www\AIplaning\frontend
npm run dev
```

Vous devriez voir :
```
VITE ready in XXX ms
➜  Local:   http://localhost:5173/
```

### Étape 3 : Ouvrir l'application

1. Ouvrez votre navigateur (Chrome, Firefox, Edge...)
2. Allez à l'adresse : **http://localhost:5173**
3. 🎉 L'application devrait s'ouvrir !

---

# 🟡 MÉTHODE 2: Installation Manuelle

## ✅ Prérequis (Méthode 2: Installation Manuelle)

Avant de commencer, assurez-vous d'avoir :
- Un ordinateur sous **Windows 10/11** (minimum 8 GB RAM recommandé)
- Une connexion Internet
- Des droits d'administrateur sur votre PC

---

## 🐍 Installation de Python (Méthode Manuelle)

### Étape 1 : Télécharger Python

1. Allez sur https://www.python.org/downloads/
2. Cliquez sur le gros bouton **"Download Python 3.11.x"**
3. Attendez que le téléchargement se termine

### Étape 2 : Installer Python

1. Double-cliquez sur le fichier téléchargé (ex: `python-3.11.x-amd64.exe`)
2. **IMPORTANT** : Cochez la case **"Add Python to PATH"** en bas de la fenêtre
3. Cliquez sur **"Install Now"**
4. Attendez la fin de l'installation
5. Cliquez sur **"Close"**

### Étape 3 : Vérifier l'installation

1. Appuyez sur les touches `Windows + R`
2. Tapez `cmd` et appuyez sur `Entrée`
3. Dans la fenêtre noire qui s'ouvre, tapez :
   ```bash
   python --version
   ```
4. Vous devriez voir : `Python 3.11.x`

✅ Si vous voyez la version, Python est installé correctement !

---

## 🟢 Installation de Node.js (Méthode Manuelle)

### Étape 1 : Télécharger Node.js

1. Allez sur https://nodejs.org/
2. Cliquez sur le bouton **"LTS"** (version recommandée)
3. Attendez le téléchargement

### Étape 2 : Installer Node.js

1. Double-cliquez sur le fichier téléchargé (ex: `node-v20.x.x-x64.msi`)
2. Cliquez sur **"Next"** plusieurs fois
3. Acceptez les conditions et cliquez sur **"Next"**
4. Cliquez sur **"Install"**
5. Attendez la fin de l'installation
6. Cliquez sur **"Finish"**

### Étape 3 : Vérifier l'installation

1. Ouvrez une nouvelle fenêtre `cmd` (voir étape Python)
2. Tapez :
   ```bash
   node --version
   npm --version
   ```
3. Vous devriez voir les versions de Node et npm

✅ Si vous voyez les versions, Node.js est installé correctement !

---

## 🐘 Installation de PostgreSQL (Méthode Manuelle)

### Étape 1 : Télécharger PostgreSQL

1. Allez sur https://www.postgresql.org/download/windows/
2. Cliquez sur **"Download the installer"**
3. Choisissez **PostgreSQL 15.x** pour Windows
4. Téléchargez la version correspondant à votre système (x64 pour 64 bits)

### Étape 2 : Installer PostgreSQL

1. Double-cliquez sur le fichier téléchargé (ex: `postgresql-15.x-windows-x64.exe`)
2. Cliquez sur **"Next"**
3. Laissez le dossier d'installation par défaut, cliquez sur **"Next"**
4. Cochez tous les composants, cliquez sur **"Next"**
5. Laissez le dossier de données par défaut, cliquez sur **"Next"**
6. **IMPORTANT** : Entrez un mot de passe pour l'utilisateur `postgres` (par exemple : `postgres123`)
   - **⚠️ NOTEZ CE MOT DE PASSE, vous en aurez besoin plus tard !**
7. Laissez le port **5432**, cliquez sur **"Next"**
8. Laissez la locale par défaut, cliquez sur **"Next"**
9. Cliquez sur **"Next"** puis **"Install"**
10. Attendez la fin de l'installation
11. Décochez "Stack Builder" et cliquez sur **"Finish"**

### Étape 3 : Créer la base de données

1. Appuyez sur `Windows + R`, tapez `cmd` et appuyez sur `Entrée`
2. Tapez cette commande (remplacez `VOTRE_MOT_DE_PASSE` par le mot de passe que vous avez créé) :
   ```bash
   "C:\Program Files\PostgreSQL\15\bin\psql.exe" -U postgres -c "CREATE DATABASE ai_study_planner;"
   ```
3. Entrez votre mot de passe PostgreSQL quand demandé
4. Vous devriez voir : `CREATE DATABASE`

✅ La base de données est créée !

---

## 📦 Installation du projet (Manuelle)

### Étape 1 : Télécharger le projet

**Option A - Si vous avez Git :**
1. Ouvrez `cmd`
2. Naviguez vers le dossier où vous voulez installer le projet :
   ```bash
   cd C:\Users\VotreNom\Documents
   ```
3. Clonez le projet :
   ```bash
   git clone https://github.com/ProjektsGithub/Ai_Study_planner.git
   cd Ai_Study_planner
   ```

**Option B - Sans Git :**
1. Allez sur https://github.com/ProjektsGithub/Ai_Study_planner
2. Cliquez sur le bouton vert **"Code"**
3. Cliquez sur **"Download ZIP"**
4. Extrayez le fichier ZIP dans `C:\Users\VotreNom\Documents\Ai_Study_planner`

### Étape 2 : Installer les dépendances Backend

1. Ouvrez `cmd`
2. Allez dans le dossier du projet :
   ```bash
   cd C:\Users\VotreNom\Documents\Ai_Study_planner\backend
   ```
3. Créez un environnement virtuel Python :
   ```bash
   python -m venv venv
   ```
4. Activez l'environnement virtuel :
   ```bash
   venv\Scripts\activate
   ```
   *(Vous devriez voir `(venv)` au début de la ligne)*

5. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```
   *(Cela peut prendre quelques minutes)*

✅ Le backend est installé !

### Étape 3 : Installer les dépendances Frontend

1. Ouvrez une **nouvelle** fenêtre `cmd`
2. Allez dans le dossier frontend :
   ```bash
   cd C:\Users\VotreNom\Documents\Ai_Study_planner\frontend
   ```
3. Installez les dépendances :
   ```bash
   npm install
   ```
   *(Cela peut prendre quelques minutes)*

✅ Le frontend est installé !

---

## ⚙️ Configuration (Manuelle)

### Étape 1 : Configurer le Backend

1. Dans le dossier `backend`, vous devriez avoir un fichier `.env.example`
2. Copiez ce fichier et renommez la copie en `.env`
3. Ouvrez le fichier `.env` avec Notepad (clic droit → Ouvrir avec → Bloc-notes)
4. Modifiez les lignes suivantes :

```env
# Database
DATABASE_URL=postgresql://postgres:VOTRE_MOT_DE_PASSE_POSTGRES@localhost:5432/ai_study_planner

# Ollama API (IA locale)
OLLAMA_API_BASE=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# JWT Secret (générez une clé aléatoire)
SECRET_KEY=votre_cle_secrete_super_longue_et_aleatoire_123456789
```

**⚠️ Remplacez :**
- `VOTRE_MOT_DE_PASSE_POSTGRES` par le mot de passe PostgreSQL que vous avez créé
- `votre_cle_secrete_super_longue_et_aleatoire_123456789` par une phrase aléatoire longue

5. Sauvegardez le fichier `.env`

### Étape 2 : Initialiser la base de données

1. Dans `cmd`, allez dans le dossier backend :
   ```bash
   cd C:\Users\VotreNom\Documents\Ai_Study_planner\backend
   ```
2. Activez l'environnement virtuel (si pas déjà fait) :
   ```bash
   venv\Scripts\activate
   ```
3. Créez les tables de la base de données :
   ```bash
   alembic upgrade head
   ```
4. Vous devriez voir des messages indiquant que les migrations ont été appliquées

✅ La base de données est configurée !

---

## 🎯 Démarrage manuel

### Étape 1 : Démarrer Ollama

Ollama devrait démarrer automatiquement avec Windows. Vérifiez qu'il est actif :
1. Regardez dans la barre des tâches (en bas à droite)
2. Vous devriez voir l'icône d'Ollama (un lama)
3. Si vous ne le voyez pas, cherchez "Ollama" dans le menu démarrer et lancez-le

### Étape 2 : Démarrer PostgreSQL

PostgreSQL devrait déjà être démarré automatiquement. Pour vérifier :
1. Appuyez sur `Windows + R`
2. Tapez `services.msc` et appuyez sur `Entrée`
3. Cherchez "postgresql-x64-15"
4. Le statut doit être "En cours d'exécution"

### Étape 3 : Démarrer le Backend

1. Ouvrez `cmd`
2. Allez dans le dossier backend :
   ```bash
   cd C:\Users\VotreNom\Documents\Ai_Study_planner\backend
   ```
3. Activez l'environnement virtuel :
   ```bash
   venv\Scripts\activate
   ```
4. Démarrez le serveur :
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
5. Vous devriez voir :
   ```
   INFO:     Uvicorn running on http://0.0.0.0:8000
   ```

**⚠️ Ne fermez PAS cette fenêtre cmd !**

### Étape 4 : Démarrer le Frontend

1. Ouvrez une **nouvelle** fenêtre `cmd`
2. Allez dans le dossier frontend :
   ```bash
   cd C:\Users\VotreNom\Documents\Ai_Study_planner\frontend
   ```
3. Démarrez le serveur de développement :
   ```bash
   npm run dev
   ```
4. Vous devriez voir :
   ```
   VITE ready in XXX ms
   ➜  Local:   http://localhost:5173/
   ```

**⚠️ Ne fermez PAS cette fenêtre cmd !**

### Étape 5 : Ouvrir l'application

1. Ouvrez votre navigateur (Chrome, Firefox, Edge...)
2. Allez à l'adresse : **http://localhost:5173**
3. 🎉 L'application devrait s'ouvrir !

---

# 🔵 MÉTHODE 3: Google Colab (IA Cloud)

Cette méthode utilise un GPU cloud pour l'IA au lieu d'Ollama local. Idéal pour de meilleures performances.

## 💰 Comparaison des options

| Option | Prix | GPU | Performance IA | Durée session |
|--------|------|-----|----------------|---------------|
| **Colab Free** | Gratuit | T4 (16GB) | Bonne | 12h max |
| **Colab Pro** | 10€/mois | L4 (24GB) / A100 (40GB) | Excellente | 24h max |
| **Ollama Local** | Gratuit | Votre GPU | Variable | Illimitée |

**Recommandation :** Colab Pro pour production / Ollama pour développement

---

## 🚀 Configuration Google Colab

### Prérequis
- Un compte Google
- Le backend et frontend déjà installés (Méthode 1 ou 2)
- Un compte ngrok gratuit

### Étape 1 : Obtenir un token ngrok GRATUIT

1. Allez sur **https://dashboard.ngrok.com/signup**
2. Créez un compte gratuit (connexion Google disponible)
3. Copiez votre **authtoken** depuis https://dashboard.ngrok.com/get-started/your-authtoken
4. **Gardez-le sous la main** pour l'étape 4

### Étape 2 : Ouvrir le notebook Colab

1. Allez dans le dossier `notebooks` de votre projet
2. Ouvrez le fichier **`colab_aiplaning.ipynb`**
3. Faites un clic droit → **"Ouvrir avec Google Colab"**

**Ou directement :**
1. Allez sur https://colab.research.google.com/
2. Cliquez sur **"File" → "Upload notebook"**
3. Uploadez `notebooks/colab_aiplaning.ipynb`

### Étape 3 : Configurer le GPU

1. Dans Colab : **Runtime → Change runtime type**
2. Sélectionnez :
   - **Hardware accelerator : L4 GPU** (recommandé - Colab Pro) ⭐
   - **Hardware accelerator : A100 GPU** (performances max - Colab Pro) 🚀
   - **Hardware accelerator : T4 GPU** (Colab Free) ⚡
3. Cliquez sur **"Save"**

**Recommandations GPU pour Llama 3.1-8B :**

| GPU | VRAM | Vitesse | Latence | Qualité |
|-----|------|---------|---------|---------|
| **L4** | 24 GB | 40-60 tok/s | 5-8s | Excellente ⭐ |
| **A100** | 40 GB | 80-120 tok/s | 3-5s | Maximale 🚀 |
| **T4** | 16 GB | 30-40 tok/s | 8-12s | Bonne ⚡ |

💡 **Meilleur rapport qualité/prix : L4 (Colab Pro 10€/mois)**

### Étape 4 : Exécuter le notebook

1. Cliquez sur **"Runtime → Run all"** (exécuter toutes les cellules)
2. **Cellule 1** : Installation des dépendances (~1 min)
3. **Cellule 2** : Configuration
   - Une **clé API** sera affichée (format: `sk-xxxxx`)
   - **⚠️ COPIEZ CETTE CLÉ !** Vous en aurez besoin
4. **Cellule 3** : Chargement du modèle Llama (~2-3 min première fois)
5. **Cellule 4** : Création du serveur Flask
6. **Cellule 5** : Configuration ngrok
   - **Collez votre token ngrok** quand demandé
   - Attendez l'URL ngrok (~10-20 secondes)
   - **⚠️ COPIEZ L'URL AFFICHÉE !** (format: `https://xxxx.ngrok-free.app`)
7. **Cellule 6** : Test automatique du serveur

**Résultat attendu après la cellule 5 :**

```
======================================================================
🎉 SERVEUR PRÊT !
======================================================================

📋 CONFIGURATION À COPIER dans votre backend/.env :

AI_SERVICE_TYPE=colab
COLAB_API_URL=https://1234-56-78-90-12.ngrok-free.app
COLAB_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

======================================================================
```

---

## 🔗 Connexion Backend ↔ Colab

### Étape 1 : Configurer le backend

1. Ouvrez le fichier `backend/.env`
2. Modifiez/ajoutez ces lignes :

```env
# Passer en mode Google Colab
AI_SERVICE_TYPE=colab

# URL ngrok de votre notebook Colab (COPIEZ depuis la cellule 5)
COLAB_API_URL=https://1234-56-78-90-12.ngrok-free.app

# Clé API générée par le notebook (COPIEZ depuis la cellule 2)
COLAB_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

3. Sauvegardez le fichier `.env`

### Étape 2 : Redémarrer le backend

1. Arrêtez le backend s'il tourne déjà (Ctrl+C dans le terminal)
2. Redémarrez-le :

```bash
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Étape 3 : Tester la connexion

**Méthode A - Script de test :**

```bash
cd backend
python test_colab_connection.py
```

**Résultat attendu :**

```
✅ Connexion au serveur Colab réussie!
📊 Informations du serveur :
   Status: healthy
   Modèle: unsloth/Meta-Llama-3.1-8B-Instruct
   Device: cuda
   GPU: Tesla L4

✅ Génération de texte fonctionnelle!
⏱️  Temps de génération : 0.87s
🔢 Tokens générés: 142
```

**Méthode B - Depuis l'application :**

1. Ouvrez l'application : http://localhost:5173
2. Connectez-vous et allez dans le planificateur
3. Générez un planning
4. Si cela fonctionne, la connexion est OK ! ✅

---

## 📊 Monitoring Colab

### Voir les logs en temps réel

Le notebook Colab affiche :
- Nombre de requêtes reçues
- Temps de génération moyen
- Erreurs éventuelles

### Garder la session active

Colab peut se déconnecter si vous n'interagissez pas. Pour éviter cela :

1. Ajoutez une cellule à la fin du notebook :

```python
# Keep-alive (optionnel)
import time
while True:
    time.sleep(300)  # Ping toutes les 5 minutes
```

2. Exécutez cette cellule

**Note :** Les sessions Colab sont limitées :
- **Colab Free** : ~12h maximum
- **Colab Pro** : ~24h maximum

### Redémarrer après expiration

Si votre session Colab expire :

1. Ré-exécutez toutes les cellules du notebook (Runtime → Run all)
2. **La clé API reste la même** ✅
3. **L'URL ngrok change** ⚠️ → Mettez à jour `COLAB_API_URL` dans `backend/.env`
4. Redémarrez le backend

---

## 🔄 Workflow hybride (Recommandé)

Utilisez le meilleur des deux mondes :

### Mode Développement (Ollama local)
```env
AI_SERVICE_TYPE=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.1:8b
```

**Avantages :**
- ✅ Gratuit
- ✅ Pas de limite de session
- ✅ Plus rapide pour tester

### Mode Production (Google Colab)
```env
AI_SERVICE_TYPE=colab
COLAB_API_URL=https://xxxx.ngrok-free.app
COLAB_API_KEY=sk-xxxxxx
```

**Avantages :**
- ✅ GPU plus puissant
- ✅ Meilleure qualité de génération
- ✅ Pas besoin de GPU local

**Basculement rapide :** Changez juste `AI_SERVICE_TYPE` dans `.env` et redémarrez le backend !

---

# 📚 Sections Communes

## 🎓 Première utilisation

### Créer un compte

1. Sur la page d'accueil, cliquez sur **"Sign Up"** ou **"S'inscrire"**
2. Remplissez le formulaire :
   - Email
   - Mot de passe
   - Nom complet
3. Cliquez sur **"Create Account"**

### Configuration du profil

1. Une fois connecté, allez dans **"Profile"**
2. Remplissez vos informations :
   - Programme d'études
   - Semestre actuel
   - Vos matières
3. Configurez vos disponibilités (quand vous pouvez étudier)
4. Ajoutez vos contraintes (examens, préférences...)

### Générer votre premier planning

1. Allez dans **"Planner"**
2. Cliquez sur **"Generate AI Plan"**
3. Attendez que l'IA génère votre planning (cela peut prendre 1-2 minutes)
4. 🎉 Votre planning personnalisé est prêt !

---

## 🔧 Résolution des problèmes

### Problèmes Laragon

**Problème : Laragon ne démarre pas**
- Vérifiez que le port 80 n'est pas utilisé par un autre programme
- Désactivez Skype (il utilise le port 80)
- Lancez Laragon en tant qu'administrateur

**Problème : PostgreSQL ne démarre pas dans Laragon**
- Vérifiez qu'aucune autre instance de PostgreSQL ne tourne
- Dans Laragon : Menu → PostgreSQL → Remove service, puis Add service

**Problème : Le terminal Laragon ne trouve pas les commandes**
- Redémarrez Laragon
- Vérifiez que "Add to System Path" était coché lors de l'installation

---

### Problèmes Installation Manuelle

**Problème : "Python n'est pas reconnu"**

**Solution :**
1. Réinstallez Python en cochant bien **"Add Python to PATH"**
2. Ou ajoutez manuellement Python au PATH :
   - Recherchez "Variables d'environnement" dans Windows
   - Cliquez sur "Variables d'environnement"
   - Dans "Variables système", trouvez "Path"
   - Ajoutez : `C:\Users\VotreNom\AppData\Local\Programs\Python\Python311`

**Problème : "npm n'est pas reconnu"**

**Solution :**
1. Fermez toutes les fenêtres `cmd`
2. Réouvrez `cmd` et réessayez
3. Si le problème persiste, réinstallez Node.js

**Problème : "Connection refused" lors du démarrage**

**Solution :**
1. Vérifiez que PostgreSQL est démarré (voir services.msc)
2. Vérifiez que le mot de passe dans `.env` est correct
3. Vérifiez que la base de données `ai_study_planner` existe

---

### Problèmes Ollama (Local)

**Problème : Ollama ne répond pas**

**Solution :**
1. Ouvrez `cmd` et tapez :
   ```bash
   ollama serve
   ```
2. Vérifiez que le modèle est téléchargé :
   ```bash
   ollama list
   ```
3. Si le modèle n'est pas là, téléchargez-le à nouveau :
   ```bash
   ollama pull llama3.1:8b
   ```

**Problème : "Model not found"**
- Vérifiez que `OLLAMA_MODEL` dans `.env` correspond au modèle installé
- Listez les modèles : `ollama list`

---

### Problèmes Google Colab

**Problème : "No GPU available"**
→ Vérifiez : **Runtime → Change runtime type → GPU sélectionné**

**Problème : "ngrok not working"**
→ Le tunnel ngrok peut prendre 30 secondes à démarrer. Attendez.

**Problème : "Connection timeout" depuis le backend**
→ Vérifiez que l'URL ngrok est à jour dans `.env` (elle change à chaque redémarrage du notebook)

**Problème : "401 Unauthorized"**
→ Vérifiez que `COLAB_API_KEY` dans `.env` correspond à celle affichée par le notebook

**Problème : Session Colab expirée**
→ Redémarrez le notebook et mettez à jour `COLAB_API_URL` dans `.env`, puis redémarrez le backend

**Problème : "Rate limit exceeded" avec ngrok gratuit**
→ Limite : 40 requêtes/minute en gratuit. Upgrade vers ngrok Pro ($10/mois) ou utilisez Ollama local pour le développement

---

### Problèmes généraux

**Problème : Port 8000 ou 5173 déjà utilisé**

**Solution :**
1. Fermez les applications qui utilisent ces ports
2. Ou changez le port dans les commandes de démarrage :
   - Backend : `--port 8001`
   - Frontend : Modifiez `vite.config.js`

**Problème : L'IA ne génère pas de planning**

**Vérifications (Ollama local) :**
1. ✅ Ollama est démarré (icône dans la barre des tâches)
2. ✅ Le modèle est téléchargé : `ollama list`
3. ✅ Le backend affiche des logs de connexion à Ollama
4. ✅ Votre profil est complété (matières, disponibilités)
5. ✅ `AI_SERVICE_TYPE=ollama` dans `.env`

**Vérifications (Google Colab) :**
1. ✅ Le notebook Colab est en cours d'exécution
2. ✅ L'URL ngrok est à jour dans `.env`
3. ✅ La clé API est correcte dans `.env`
4. ✅ `AI_SERVICE_TYPE=colab` dans `.env`
5. ✅ Test de connexion réussi : `python test_colab_connection.py`

**Problème : Erreur "Module not found"**
→ Réinstallez les dépendances :
- Backend : `pip install -r requirements.txt`
- Frontend : `npm install`

---

## 🔄 Arrêter l'application

### Avec Laragon
1. Dans les fenêtres de terminal : Appuyez sur `Ctrl + C`
2. Dans Laragon : Cliquez sur **"Stop All"**

### Sans Laragon
1. Dans la fenêtre `cmd` du **Frontend** : Appuyez sur `Ctrl + C`
2. Dans la fenêtre `cmd` du **Backend** : Appuyez sur `Ctrl + C`
3. PostgreSQL et Ollama peuvent rester actifs (ils se lancent automatiquement)

### Google Colab
- Le notebook peut rester actif
- Pour économiser les ressources : **Runtime → Disconnect and delete runtime**

---

## ✨ Conseils et bonnes pratiques

### Performances

- **Premier lancement** : Le téléchargement du modèle Ollama peut prendre du temps (4-5 GB)
- **RAM** : Pour de meilleures performances, assurez-vous d'avoir au moins 8 GB de RAM
- **GPU local** : Si vous avez un GPU NVIDIA, Ollama l'utilisera automatiquement
- **Google Colab** : Gardez l'onglet Colab ouvert pour éviter la déconnexion

### Sauvegarde

- Vos données sont stockées dans PostgreSQL et persistent entre les sessions
- Pour sauvegarder : Exportez la base de données via pgAdmin ou `pg_dump`
- Pour restaurer : Utilisez `pg_restore`

### Mises à jour

Pour mettre à jour le projet :

```bash
cd C:\laragon\www\AIplaning  # Ou votre dossier d'installation
git pull
cd backend
pip install -r requirements.txt --upgrade
cd ../frontend
npm install
```

### Développement vs Production

| Environnement | AI Service | Base de données | Debug |
|---------------|------------|-----------------|-------|
| **Développement** | Ollama local | PostgreSQL local | `DEBUG=True` |
| **Test** | Ollama ou Colab | PostgreSQL local | `DEBUG=True` |
| **Production** | Google Colab Pro | PostgreSQL distant | `DEBUG=False` |

### Sécurité

- **Ne commitez JAMAIS** le fichier `.env` dans Git
- **Changez** `SECRET_KEY` en production
- **Utilisez** des mots de passe forts pour PostgreSQL
- **Gardez secrète** votre clé API Colab (`COLAB_API_KEY`)
- **Ne partagez pas** votre URL ngrok publiquement

---

## 🎯 Comparaison des méthodes

| Critère | Laragon | Installation Manuelle | Google Colab |
|---------|---------|----------------------|--------------|
| **Difficulté** | ⭐ Facile | ⭐⭐ Moyen | ⭐⭐⭐ Avancé |
| **Temps setup** | 20 min | 45 min | 30 min |
| **Tout-en-un** | ✅ Oui | ❌ Non | ⚠️ Hybride |
| **Performance IA** | Locale | Locale | Cloud GPU |
| **Coût** | Gratuit | Gratuit | 0-10€/mois |
| **Maintenance** | Faible | Moyenne | Faible |
| **Portabilité** | Windows | Multi-OS | Multi-OS |

**Recommandations :**
- 🏆 **Débutant Windows** : Méthode 1 (Laragon)
- 🏆 **Développeur** : Méthode 2 + Ollama local
- 🏆 **Production** : Méthode 1 ou 2 + Google Colab Pro

---

## 📞 Support

Si vous rencontrez des problèmes non résolus par ce guide :

1. **Vérifiez les logs** dans les fenêtres `cmd` du backend et frontend
2. **Consultez la documentation** :
   - [Architecture du projet](ARCHITECTURE.md)
   - [Guide API](backend/API_DOCUMENTATION.md)
   - [Configuration Google Colab](GOOGLE_COLAB_SETUP.md)
3. **Testez votre configuration** :
   - Backend : `curl http://localhost:8000/api/v1/health`
   - Ollama : `ollama list`
   - Colab : `python backend/test_colab_connection.py`
4. **Contactez le support technique** avec :
   - Version de votre OS
   - Méthode d'installation utilisée (Laragon/Manuelle/Colab)
   - Logs d'erreur complets

---

## 📚 Documentation supplémentaire

### Guides techniques
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Architecture complète du système
- **[API_DOCUMENTATION.md](backend/API_DOCUMENTATION.md)** - Documentation de l'API REST
- **[GOOGLE_COLAB_SETUP.md](GOOGLE_COLAB_SETUP.md)** - Guide détaillé Google Colab

### Fichiers utiles
- **`backend/.env.example`** - Exemple de configuration complète
- **`backend/test_colab_connection.py`** - Script de test Colab
- **`notebooks/colab_aiplaning.ipynb`** - Notebook Colab prêt à l'emploi

### Ressources externes
- [Laragon Documentation](https://laragon.org/docs/)
- [Ollama Documentation](https://github.com/ollama/ollama)
- [Google Colab](https://colab.research.google.com/)
- [ngrok Documentation](https://ngrok.com/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React + Vite](https://vitejs.dev/guide/)

---

## 🚀 Prochaines étapes

Une fois l'application installée et fonctionnelle :

1. **Explorez l'interface** : Familiarisez-vous avec les différentes sections
2. **Configurez votre profil** : Ajoutez vos matières, disponibilités, contraintes
3. **Générez votre premier planning** : Testez l'IA avec différentes configurations
4. **Personnalisez** : Ajustez les paramètres selon vos besoins
5. **Optimisez les performances** :
   - Pour l'IA locale : Testez différents modèles Ollama
   - Pour Google Colab : Testez différents GPU (T4, L4, A100)
6. **Explorez les fonctionnalités avancées** :
   - Analyse de progression
   - Gestion des examens
   - Notifications de révision
   - Export de plannings

---

## 🎓 Scénarios d'utilisation

### Étudiant (Usage personnel)
- **Installation** : Laragon (Méthode 1)
- **IA** : Ollama local avec Llama 3.1:8b
- **Coût** : Gratuit
- **Setup** : 20 minutes

### Groupe d'étudiants (5-10 personnes)
- **Installation** : Serveur avec installation manuelle
- **IA** : Google Colab Free (T4 GPU)
- **Coût** : Gratuit
- **Setup** : 1 heure

### Université (100+ étudiants)
- **Installation** : Serveur dédié avec PostgreSQL distant
- **IA** : Google Colab Pro+ ou serveur GPU dédié
- **Coût** : 50€/mois (Colab Pro+) ou serveur dédié
- **Setup** : 1-2 jours

---

## ⚡ Optimisations avancées

### Pour les performances

**Backend :**
- Augmentez `DATABASE_POOL_SIZE` dans `.env` si vous avez beaucoup d'utilisateurs
- Utilisez Redis pour le cache (optionnel)
- Activez la compression gzip dans Uvicorn

**Frontend :**
- Build de production : `npm run build`
- Servez avec Nginx ou Apache

**IA (Ollama) :**
- Utilisez un modèle plus petit pour plus de rapidité : `llama3.2:3b`
- Ajustez `OLLAMA_NUM_CTX` pour contrôler la mémoire
- Si vous avez un GPU NVIDIA, installez les drivers CUDA

**IA (Colab) :**
- Gardez le notebook actif avec le script keep-alive
- Utilisez Colab Pro pour les sessions plus longues
- Configurez ngrok Pro pour plus de connexions simultanées

### Pour la sécurité

1. **Production** : Passez `DEBUG=False` dans `.env`
2. **HTTPS** : Utilisez un reverse proxy (Nginx + Let's Encrypt)
3. **Firewall** : Limitez l'accès aux ports 8000, 5432
4. **Mots de passe** : Utilisez des mots de passe forts et uniques
5. **Backup** : Configurez des sauvegardes automatiques de PostgreSQL

---

## � Monitoring

### Vérifier la santé du système

**Backend :**
```bash
curl http://localhost:8000/api/v1/health
```

**Base de données :**
```bash
psql -U postgres -d ai_study_planner -c "SELECT COUNT(*) FROM users;"
```

**Ollama :**
```bash
ollama ps  # Voir les modèles en cours d'exécution
```

**Google Colab :**
```bash
python backend/test_colab_connection.py
```

### Logs

**Backend logs :**
- Affichés dans le terminal où `uvicorn` tourne
- Niveau configurable via `LOG_LEVEL` dans `.env`

**Frontend logs :**
- Console du navigateur (F12 → Console)

**PostgreSQL logs :**
- Laragon : `C:\laragon\data\postgresql\pg_log\`
- Installation manuelle : `C:\Program Files\PostgreSQL\15\data\pg_log\`

---

## 🎉 Félicitations !

Vous avez terminé l'installation de **AI Study Planner** !

Vous pouvez maintenant :
- ✅ Créer des plannings d'étude personnalisés avec l'IA
- ✅ Gérer vos matières et disponibilités
- ✅ Suivre votre progression académique
- ✅ Optimiser votre temps d'étude

**Bon planning avec AI Study Planner ! 📚🎓🚀**

---

## 📝 Changelog du guide

### Version 2.0 (Actuelle)
- ✅ Ajout de la méthode Laragon (tout-en-un pour Windows)
- ✅ Documentation complète Google Colab
- ✅ Workflow hybride (Ollama local + Colab)
- ✅ Comparaison détaillée des méthodes
- ✅ Section troubleshooting étendue
- ✅ Guides de monitoring et optimisation

### Version 1.0
- Installation manuelle uniquement
- Ollama local uniquement
- Guide basique

---

**Dernière mise à jour : 2026**
