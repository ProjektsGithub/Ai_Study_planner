# 🧠 Explication de l'Architecture & du Code Backend — AI Study Planner

Ce document a pour but d'expliquer de manière claire et accessible le fonctionnement du **backend** de l'application **AI Study Planner**, les choix technologiques majeurs (comme FastAPI et Alembic), ainsi que la structure des fonctionnalités clés implémentées.

---

## 🏛️ 1. Vue d'ensemble de l'Architecture Backend

Le backend est conçu selon une architecture moderne en couches séparées. Cette séparation garantit que chaque partie du code a une responsabilité unique, ce qui facilite la maintenance, les tests et les futures évolutions.

```
┌────────────────────────────────────────────────────────┐
│                   COUCHE API (FastAPI)                 │
│  - Réception des requêtes HTTP (Frontend)              │
│  - Validation automatique des données (Pydantic)       │
│  - Documentation Swagger accessible en temps réel      │
└────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│               COUCHE MIDDLEWARE (Sécurité)             │
│  - Vérification des tokens de connexion (JWT)          │
│  - Contrôle d'accès selon les rôles (RBAC)             │
└────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│               COUCHE SERVICES (Logique Métier)         │
│  - Moteur de planification (Planning Engine)           │
│  - Service d'Intelligence Artificielle (AI Service)    │
│  - Export PDF, Notifications, Validation, Audit        │
└────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│                COUCHE ORM (SQLAlchemy)                 │
│  - Traduction des objets Python en requêtes SQL        │
│  - Gestion des relations complexes (30+ tables)        │
└────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│             BASE DE DONNÉES (PostgreSQL)               │
│  - Stockage persistant et sécurisé des données         │
└────────────────────────────────────────────────────────┘
```

---

## 🛠️ 2. Les Technologies Clés & Leurs Rôles

### 🚀 FastAPI
FastAPI est le framework web utilisé pour construire l'API. Ses avantages majeurs pour le projet sont :
* **Performance élevée** : Construit sur des standards asynchrones modernes (ASGI), il est extrêmement rapide.
* **Validation automatique (Pydantic)** : Avant même de traiter une requête, FastAPI vérifie que les données envoyées par le client (ex: format de l'adresse email, valeurs numériques) sont correctes. Si ce n'est pas le cas, il renvoie une erreur claire sans planter.
* **Documentation interactive automatique** : Il génère en temps réel une documentation visuelle de tous les points d'accès (endpoints) de l'API via Swagger (accessible en cours d'exécution sur `/api/docs`).

### 🗄️ SQLAlchemy (ORM)
SQLAlchemy est un **ORM** (*Object-Relational Mapper*). Au lieu d'écrire manuellement des requêtes SQL complexes pour interagir avec la base de données, le code utilise des objets Python. 
* *Exemple :* Pour récupérer un étudiant, au lieu d'écrire `SELECT * FROM users WHERE id = 1`, SQLAlchemy permet d'écrire `db.query(User).filter(User.id == 1).first()`. Cela réduit les risques d'erreurs et rend le code beaucoup plus lisible.

### 📐 Alembic (Gestion des Migrations)
Alembic est l'outil indispensable associé à SQLAlchemy pour gérer l'évolution de la base de données.

#### **Qu'est-ce qu'une migration de base de données ?**
Au cours du développement d'un projet, la structure des tables de la base de données change souvent (ex : ajout d'une colonne "téléphone" dans la table Utilisateurs, création d'une nouvelle table pour les notes). 
Sans outil de migration, il faudrait modifier manuellement la base de données en production, ce qui comporte un risque énorme de perte de données ou d'incohérence entre l'environnement de développement et de production.

#### **Comment fonctionne Alembic dans le projet ?**
1. **Historique / Versionnage** : Alembic fonctionne comme Git, mais pour la base de données. Chaque changement de structure est enregistré dans un fichier de migration Python horodaté (dans le dossier `backend/alembic/versions`).
2. **Automatisation** : Alembic compare automatiquement les modèles définis dans le code Python avec la base de données réelle pour générer le script de mise à jour (`alembic revision --autogenerate`).
3. **Application sécurisée** : Pour appliquer les changements sur n'importe quel ordinateur ou serveur, il suffit de lancer la commande `alembic upgrade head`. Alembic sait exactement quelles migrations ont déjà été appliquées et n'exécute que les nouvelles, sans toucher aux données existantes.
4. **Retour en arrière (Rollback)** : Si une mise à jour pose problème, Alembic permet de revenir facilement à une version précédente du schéma de base de données.

---

## 💡 3. Explication des Fonctionnalités Backend Majeures

Le backend contient plus de 20 services spécialisés qui gèrent la logique métier de l'application. Voici les principaux :

### 🧠 A. Le Moteur de Planification (Planning Engine)
Le fichier `planning_engine.py` est le cœur algorithmique déterministe. Avant d'interroger l'Intelligence Artificielle, ce moteur effectue un travail préparatoire crucial :
1. **Analyse des disponibilités** : Il récupère les créneaux horaires où l'étudiant est libre pour étudier.
2. **Calcul des priorités académiques** : Il attribue un score de priorité à chaque matière en fonction de sa difficulté, du nombre d'ECTS, de l'imminence des examens et du fait que la matière soit obligatoire ou non.
3. **Résolution des conflits** : Il élimine les chevauchements d'horaires et s'assure du respect des contraintes physiques (comme le temps de pause minimum entre deux sessions).

### 🤖 B. Le Service d'Intelligence Artificielle (AI Service)
Le fichier `ai_service.py` gère l'interaction avec le modèle de langage **Llama 3.2**. L'application propose une architecture hybride très intelligente :
* **Mode Production (Google Colab + LoRA)** : Le backend envoie les données de planification formatées à un serveur d'inférence GPU distant. Ce serveur héberge Llama 3.2 spécialement entraîné fin (Fine-tuned avec LoRA) pour structurer des plannings d'études optimisés et adaptés aux universités allemandes.
* **Mode Développement / Fallback (Ollama)** : En local, pour éviter les coûts d'infrastructure, le système peut utiliser **Ollama** pour faire tourner Llama 3.2 directement sur la machine du développeur.
* **Résilience** : En cas de panne ou de déconnexion du service d'IA, le backend possède des mécanismes de secours (fallback) pour générer tout de même un planning fonctionnel via l'algorithme déterministe classique.

### 🔐 C. Le Contrôle d'Accès par Rôles (RBAC Middleware)
Le fichier `rbac.py` gère la sécurité et la restriction des accès selon les droits de l'utilisateur connecté. Quatre rôles principaux sont définis et contrôlés à chaque appel API :
1. **Étudiant (Student)** : Accès uniquement à son propre profil, ses matières et ses plannings.
2. **Coordinateur de programme (Program Coordinator)** : Peut gérer les matières et structures de cours du programme dont il a la charge.
3. **Administrateur d'Université (University Admin)** : Gère les campus et la configuration globale à l'échelle de son institution.
4. **Super Admin** : Contrôle absolu sur l'ensemble de la plateforme (création des universités, gestion des rôles, accès aux journaux d'audit globaux).

### 📄 D. Service d'Export et Rapports (Export Service)
Le fichier `export_service.py` permet de convertir les données de l'application en documents physiques :
* **Export PDF** : Utilise la bibliothèque Python `ReportLab` pour générer des documents de planning esthétiques, professionnels et prêts à l'impression, intégrant des statistiques visuelles sur le temps d'étude.
* **Export Calendrier (iCal)** : Permet aux étudiants d'intégrer leur planning généré directement dans leurs agendas personnels (Google Calendar, Apple Calendar, Outlook).

### 📥 E. Importation en Masse (Bulk Import)
Conçu spécifiquement pour les administrateurs d'universités, ce service permet de charger d'un coup des centaines de cours, semestres et programmes d'études à partir de fichiers Excel :
* **Processus sécurisé en 4 étapes** : Téléchargement du fichier ➔ Validation logique et syntaxique (détection des erreurs) ➔ Prévisualisation des données à importer ➔ Exécution finale en base de données.
* **Rollback automatique** : Si une seule ligne de l'import présente une incohérence grave (ex: dépendance circulaire dans les prérequis de cours), toute l'opération est annulée pour préserver l'intégrité de la base de données.

### 🔔 F. Service de Validation et Notifications
* **Validation Service** : Analyse continuellement la cohérence du cursus de l'étudiant (vérification que le nombre d'ECTS requis pour valider un semestre ou un diplôme respecte bien les règles de l'établissement).
* **Notification Service** : Gère l'envoi d'alertes en temps réel à l'étudiant (notifications dans l'application ou par courriel) pour lui rappeler un examen imminent, un conflit d'emploi du temps ou lui suggérer des réajustements dans ses sessions d'études.

---

## 🔍 4. Explication Détaillée de Quelques Fonctions Clés

Pour illustrer comment le backend traite la logique métier, la sécurité et la cohérence académique, voici l'explication de trois fonctions clés du code :

### 📊 A. Calcul des priorités des matières (`PlanningEngine.calculate_priorities`)
Dans le fichier [planning_engine.py](file:///c:/laragon/www/AIplaning/backend/app/services/planning_engine.py#L213-L255), cette fonction calcule un score de priorité sur une échelle de `0.0` à `100.0` pour chaque matière étudiée. 

Voici un résumé simplifié de sa formule de pondération :
```python
# 1. Statut de validation de la matière (Poids : 40% du score)
if subject.validation_status == "failed":
    score += 40.0  # Priorité absolue aux matières échouées précédemment
elif subject.validation_status == "in_progress" and subject.is_mandatory:
    score += 35.0  # Priorité forte aux matières obligatoires en cours
elif subject.validation_status == "in_progress":
    score += 25.0  # Matières facultatives en cours

# 2. Importance académique : ECTS x Coefficient (Poids : 30% du score)
ects_coef_score = ((ects * coef) / max_ects_coef) * 30.0
score += ects_coef_score

# 3. Proximité de l'examen (Poids : 20% du score)
# Plus la date de l'examen approche, plus ce score augmente
exam_score = self._calculate_exam_proximity_score(subject.exam_date) * 0.20
score += exam_score

# 4. Difficulté déclarée et Priorité de base (Poids : 10% du score)
# Prise en compte de la perception de l'étudiant et de sa note de priorité de base
```
* **Pourquoi c'est important ?** Cette fonction permet à l'Intelligence Artificielle de savoir sur quelles matières l'étudiant doit concentrer son temps de révision en priorité.

---

### 🛡️ B. Protection des accès par Rôles (`require_role`)
Dans le fichier [rbac.py](file:///c:/laragon/www/AIplaning/backend/app/middleware/rbac.py#L30-L100), cette fonction est un **décorateur Python**. Elle sert de barrière de sécurité sur les points d'accès de l'API.

```python
def require_role(allowed_roles: List[str]) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            db = kwargs.get('db')
            
            # Vérifier si l'utilisateur possède l'un des rôles autorisés en base de données
            user_roles = db.query(UserRole).filter(
                UserRole.user_id == current_user.id
            ).join(AdminRole).filter(
                AdminRole.name.in_(allowed_roles),
                AdminRole.is_active == True
            ).all()
            
            # Si l'utilisateur n'a aucun des rôles requis
            if not user_roles:
                # 1. Enregistrement de la tentative suspecte dans le journal d'audit
                await _log_access_denial(...)
                # 2. Blocage immédiat avec une erreur HTTP 403 Forbidden
                raise HTTPException(status_code=403, detail="Access denied")
                
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```
* **Comment l'utiliser ?** Il suffit de poser `@require_role(["super_admin", "university_admin"])` au-dessus d'une fonction de route pour que FastAPI bloque automatiquement tout utilisateur non autorisé, tout en gardant une trace d'audit (Audit Log) de la tentative.

---

### 🔄 C. Détection de Dépendances Circulaires (`PrerequisiteService.detect_circular_dependency`)
Dans le fichier [prerequisite_service.py](file:///c:/laragon/www/AIplaning/backend/app/services/prerequisite_service.py#L148-L200), cette fonction empêche les administrateurs de créer des règles de prérequis impossibles (par exemple : le cours A nécessite le cours B, qui nécessite le cours C, qui nécessite le cours A).

Elle utilise un algorithme de parcours de graphe appelé **Recherche en Profondeur (DFS - Depth-First Search)** :
1. **Simulation** : La fonction ajoute temporairement le nouveau lien de prérequis dans une carte virtuelle des cours.
2. **Parcours** : Elle part du cours prérequis proposé et suit récursivement tous ses propres prérequis (ses "parents").
3. **Détection** : Si au cours de ce chemin, elle retombe sur le cours d'origine, c'est qu'il y a un cycle (boucle infinie).
4. **Action** : Si une boucle est détectée, la fonction renvoie la liste complète des cours formant cette boucle pour alerter l'administrateur, et bloque l'insertion en base de données.

* **Pourquoi c'est important ?** Cela garantit que le cursus universitaire reste valide et que les étudiants ne se retrouvent jamais bloqués dans une impasse académique.

---

## 🗂️ 5. Structure des Dossiers du Backend

Pour s'y retrouver dans le code source :
* `backend/alembic/` : Contient l'historique et la configuration des migrations de la base de données.
* `backend/app/main.py` : Point d'entrée de l'application qui démarre le serveur FastAPI et configure les routes.
* `backend/app/api/` : Regroupe tous les contrôleurs de l'API (les points d'accès URL que le frontend appelle).
* `backend/app/core/` : Contient la configuration globale du système, la sécurité (chiffrement, génération de tokens JWT) et la connexion brute à la base de données.
* `backend/app/models/` : Contient les définitions des tables de base de données en langage Python (SQLAlchemy).
* `backend/app/schemas/` : Contient les modèles de validation de données (Pydantic) pour l'entrée et la sortie des API.
* `backend/app/services/` : Contient toute la logique métier complexe (moteur de planification, IA, exports, imports).
* `backend/app/tests/` : Les tests automatisés garantissant qu'aucune mise à jour de code ne casse les fonctionnalités existantes.

