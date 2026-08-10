# 🧪 Guide Swagger - Tester l'API

## 🚀 Accès Rapide

### Option 1 : Swagger Live (Recommandé)

1. **Démarrer le backend :**
   ```bash
   cd backend
   start_swagger.bat
   ```
   OU
   ```bash
   py -m uvicorn app.main:app --reload
   ```

2. **Ouvrir Swagger UI :**
   http://localhost:8000/docs

### Option 2 : Documentation Standalone

Ouvrez directement le fichier : `backend/api_documentation.html`

---

## 🎯 Utilisation de Swagger UI

### 1️⃣ **Explorer les Endpoints**

Swagger affiche tous les endpoints organisés par **tags** :
- 🔐 **Authentication** - Login, Register, Refresh
- 👤 **Profile** - Profil utilisateur
- 📚 **Subjects** - Gestion des matières
- 📅 **Study Plans** - Génération de plannings
- 🕐 **Availabilities** - Disponibilités
- 🚫 **Constraints** - Contraintes
- 📝 **Exams** - Examens
- 📊 **Grades** - Notes
- 🔔 **Notifications** - Notifications
- 🏢 **Admin** - Plateforme admin (RBAC)

### 2️⃣ **Tester un Endpoint**

#### Exemple : Créer un utilisateur

1. **Cliquez sur** `POST /api/v1/auth/register`
2. **Cliquez sur** le bouton **"Try it out"**
3. **Modifiez le JSON** :
   ```json
   {
     "email": "test@example.com",
     "password": "password123",
     "full_name": "Test User"
   }
   ```
4. **Cliquez sur** **"Execute"**
5. **Voir la réponse** en bas (code 201 = succès)

### 3️⃣ **S'Authentifier avec JWT**

#### Étape 1 : Obtenir un Token

1. Allez sur `POST /api/v1/auth/login`
2. Cliquez **"Try it out"**
3. Remplissez :
   ```
   username: test@example.com
   password: password123
   ```
4. Cliquez **"Execute"**
5. **Copiez le `access_token`** de la réponse

#### Étape 2 : Utiliser le Token

1. **Cliquez sur le bouton** 🔒 **"Authorize"** en haut à droite
2. **Collez votre token** dans le champ :
   ```
   Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```
   ⚠️ **N'oubliez pas** le mot "Bearer" avant le token !
3. **Cliquez sur** **"Authorize"**
4. **Fermez la popup**

✅ Maintenant tous les endpoints protégés sont accessibles !

### 4️⃣ **Tester un Endpoint Protégé**

Exemple : Créer une matière

1. Allez sur `POST /api/v1/subjects`
2. Cliquez **"Try it out"**
3. Modifiez le JSON :
   ```json
   {
     "name": "Mathématiques Avancées",
     "ects_credits": 6,
     "difficulty": 8,
     "priority": 9,
     "semester": 3,
     "hours_per_week": 10
   }
   ```
4. Cliquez **"Execute"**
5. ✅ Vous devriez recevoir un code 201 avec la matière créée

### 5️⃣ **Générer un Planning d'Études**

1. Assurez-vous d'avoir :
   - ✅ Au moins 1 matière créée
   - ✅ Des disponibilités définies
   - ✅ Être authentifié

2. Allez sur `POST /api/v1/study-plans/generate`
3. Cliquez **"Try it out"**
4. Modifiez le JSON :
   ```json
   {
     "week_start": "2026-07-14",
     "preferences": {
       "max_hours_per_day": 8,
       "preferred_study_times": ["morning", "afternoon"]
     }
   }
   ```
5. Cliquez **"Execute"**
6. ✅ Le planning est généré avec toutes les sessions

---

## 🔧 Fonctionnalités Swagger

### ✅ **Ce que vous pouvez faire :**

| Fonctionnalité | Description |
|----------------|-------------|
| 📖 **Voir la documentation** | Chaque endpoint a une description complète |
| 🧪 **Tester les endpoints** | Bouton "Try it out" sur chaque endpoint |
| 🔐 **Authentification JWT** | Bouton "Authorize" pour les tokens |
| 📥 **Voir les schémas** | Modèles de requête/réponse détaillés |
| 💾 **Télécharger OpenAPI** | Export du schéma complet |
| 📋 **Copier curl** | Commande curl générée automatiquement |
| ⚙️ **Voir les paramètres** | Query params, path params, body |
| ✨ **Validation en direct** | Erreurs de validation affichées |

### 🎨 **Personnalisation**

Vous pouvez personnaliser Swagger dans `app/main.py` :

```python
app = FastAPI(
    title="AI Study Planner API",
    description="API pour la génération de plannings d'études",
    version="1.0.0",
    docs_url="/docs",           # URL Swagger UI
    redoc_url="/redoc",         # URL ReDoc
    openapi_url="/openapi.json" # URL schéma OpenAPI
)
```

---

## 🧪 Workflow Complet de Test

### Scénario : Nouveau utilisateur qui crée son premier planning

#### 1️⃣ **Créer un compte**
```http
POST /api/v1/auth/register
{
  "email": "student@example.com",
  "password": "SecurePass123",
  "full_name": "Étudiant Test"
}
```

#### 2️⃣ **Se connecter**
```http
POST /api/v1/auth/login
username: student@example.com
password: SecurePass123
```
→ Copier le `access_token`

#### 3️⃣ **Autoriser Swagger**
Cliquer sur 🔒 "Authorize" et coller le token

#### 4️⃣ **Compléter son profil**
```http
PUT /api/v1/profile/me
{
  "student_profile": {
    "current_semester": 3,
    "study_pace": "full_time"
  }
}
```

#### 5️⃣ **Ajouter des matières**
```http
POST /api/v1/subjects
{
  "name": "Algorithmes",
  "ects_credits": 6,
  "difficulty": 8,
  "priority": 9
}
```

#### 6️⃣ **Définir ses disponibilités**
```http
POST /api/v1/availabilities
{
  "day_of_week": "monday",
  "start_time": "09:00",
  "end_time": "17:00",
  "is_available": true
}
```

#### 7️⃣ **Générer un planning**
```http
POST /api/v1/study-plans/generate
{
  "week_start": "2026-07-14"
}
```

#### 8️⃣ **Voir son planning**
```http
GET /api/v1/study-plans/{plan_id}
```

#### 9️⃣ **Exporter en PDF**
```http
GET /api/v1/study-plans/{plan_id}/export
```

---

## 🔍 Codes de Réponse HTTP

| Code | Signification | Quand ? |
|------|---------------|---------|
| **200** | ✅ OK | Succès (GET, PUT) |
| **201** | ✅ Created | Ressource créée (POST) |
| **204** | ✅ No Content | Succès sans contenu (DELETE) |
| **400** | ❌ Bad Request | Données invalides |
| **401** | ❌ Unauthorized | Token manquant/invalide |
| **403** | ❌ Forbidden | Permissions insuffisantes |
| **404** | ❌ Not Found | Ressource inexistante |
| **422** | ❌ Validation Error | Erreur de validation Pydantic |
| **500** | ❌ Server Error | Erreur serveur |

---

## 🛠️ Dépannage

### Problème : "401 Unauthorized"

**Solution :**
1. Vérifiez que vous êtes connecté
2. Cliquez sur 🔒 "Authorize"
3. Collez votre token avec "Bearer " devant
4. Cliquez "Authorize"

### Problème : "422 Validation Error"

**Solution :**
- Vérifiez que tous les champs **required** sont remplis
- Vérifiez le format des données (email, date, etc.)
- Consultez le schéma dans Swagger

### Problème : Token expiré

**Solution :**
- Les tokens expirent après 15 minutes
- Reconnectez-vous pour obtenir un nouveau token
- Utilisez le refresh token si disponible

### Problème : CORS Error

**Solution :**
- Vérifiez que le backend est démarré sur http://localhost:8000
- CORS est déjà configuré pour localhost

---

## 📚 Ressources

- **Swagger UI Official** : https://swagger.io/tools/swagger-ui/
- **FastAPI Docs** : https://fastapi.tiangolo.com/tutorial/metadata/
- **OpenAPI Spec** : https://swagger.io/specification/

---

## 🎯 Raccourcis Clavier Swagger

| Raccourci | Action |
|-----------|--------|
| `Ctrl + F` | Rechercher un endpoint |
| `Esc` | Fermer les popups |
| Cliquer sur un endpoint | Ouvrir/fermer les détails |

---

## 💡 Astuces

1. **Utilisez les exemples** : Swagger affiche des exemples pour chaque schéma
2. **Testez progressivement** : Commencez par Auth, puis Profile, puis features
3. **Gardez Swagger ouvert** : Pendant le développement frontend
4. **Exportez les requêtes** : Utilisez "Copy as cURL" pour reproduire hors Swagger
5. **Consultez les schémas** : Section "Schemas" en bas pour voir tous les modèles

---

**🚀 Prêt à tester votre API !**

Double-cliquez sur `backend/start_swagger.bat` et allez sur http://localhost:8000/docs
