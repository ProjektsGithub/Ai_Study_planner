# 📚 Documentation API

Ce dossier contient les outils pour générer et exporter la documentation de l'API.

## 🚀 Génération Rapide

### Méthode 1 : Script Batch (Windows)
```bash
export_docs.bat
```

### Méthode 2 : Scripts Python
```bash
# OpenAPI JSON + HTML
py generate_api_docs.py

# Markdown
py generate_markdown_docs.py
```

## 📄 Fichiers Générés

| Fichier | Format | Usage |
|---------|--------|-------|
| `openapi.json` | OpenAPI 3.1 | Import dans Postman, Insomnia, etc. |
| `api_documentation.html` | HTML | Documentation interactive (Swagger UI) |
| `API_DOCUMENTATION.md` | Markdown | Documentation GitHub, wiki |

## 🌐 Documentation Live

Pour accéder à la documentation complète et interactive :

1. **Démarrer le backend :**
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Accéder aux interfaces :**
   - **Swagger UI** : http://localhost:8000/docs
   - **ReDoc** : http://localhost:8000/redoc
   - **OpenAPI JSON** : http://localhost:8000/openapi.json

## 📥 Import dans Postman

1. Générer `openapi.json` : `py generate_api_docs.py`
2. Ouvrir Postman
3. File → Import
4. Sélectionner `openapi.json`
5. Une collection complète sera créée avec tous les endpoints

## 📤 Héberger la Documentation

### Option 1 : GitHub Pages

1. Créer un dossier `docs/` à la racine du projet
2. Copier `api_documentation.html` → `docs/index.html`
3. Dans les settings GitHub : Pages → Source : `/docs`
4. Accès via : `https://username.github.io/AIplaning/`

### Option 2 : Serveur Local

```bash
# Depuis le dossier backend
python -m http.server 8001

# Accéder à:
# http://localhost:8001/api_documentation.html
```

### Option 3 : Netlify/Vercel

1. Créer un dossier `public/` à la racine
2. Copier `api_documentation.html` → `public/index.html`
3. Déployer sur Netlify ou Vercel
4. Configuration automatique

## 🔄 Mise à Jour de la Documentation

La documentation est **générée automatiquement** depuis le code :

1. FastAPI lit les **type hints** Python
2. Pydantic valide les **schémas de données**
3. Les **docstrings** deviennent descriptions
4. Les **tags** organisent les endpoints

### Ajouter de la Documentation

Dans vos endpoints :

```python
@router.post("/subjects", response_model=SubjectResponse, tags=["Subjects"])
async def create_subject(
    subject: SubjectCreate,
    current_user: User = Depends(get_current_user)
):
    \"\"\"
    Create a new subject for the authenticated user.
    
    - **name**: Subject name (required)
    - **ects_credits**: ECTS credits (required)
    - **difficulty**: Difficulty level 1-10 (optional)
    - **priority**: Priority level 1-10 (optional)
    
    Returns the created subject with generated ID.
    \"\"\"
    return subject_service.create(subject, current_user.id)
```

## 📊 Formats Supportés

| Format | Outil | Commande |
|--------|-------|----------|
| HTML | generate_api_docs.py | `py generate_api_docs.py` |
| JSON | generate_api_docs.py | `py generate_api_docs.py` |
| Markdown | generate_markdown_docs.py | `py generate_markdown_docs.py` |
| PDF | Pandoc | `pandoc API_DOCUMENTATION.md -o api.pdf` |

## 🛠️ Outils Recommandés

### Visualisation
- **Swagger Editor** : https://editor.swagger.io
- **Swagger UI** : Local (`/docs`)
- **ReDoc** : Local (`/redoc`)

### Testing API
- **Postman** : Import `openapi.json`
- **Insomnia** : Import `openapi.json`
- **HTTPie** : CLI pour tester les endpoints
- **curl** : Ligne de commande

### Conversion
- **Pandoc** : Markdown → PDF, DOCX, etc.
- **wkhtmltopdf** : HTML → PDF
- **redoc-cli** : OpenAPI → HTML statique

## 🔧 Personnalisation

### Ajouter un Logo

Modifiez `generate_api_docs.py` :

```python
openapi_schema["info"]["x-logo"] = {
    "url": "https://example.com/logo.png",
    "altText": "AI Study Planner"
}
```

### Modifier les Couleurs

Dans `api_documentation.html`, ajoutez :

```css
.topbar {
    background-color: #your-color !important;
}
```

### Ajouter des Exemples

Dans vos schémas Pydantic :

```python
class SubjectCreate(BaseModel):
    name: str = Field(..., example="Advanced Mathematics")
    ects_credits: int = Field(..., example=6)
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Machine Learning",
                "ects_credits": 5,
                "difficulty": 9
            }
        }
```

## ❓ FAQ

### Comment obtenir le schéma complet ?

Démarrez le backend et la documentation sera complète avec tous les endpoints.

### Pourquoi "schéma basique généré" ?

Si toutes les dépendances ne sont pas installées, un schéma basique est créé. 
Pour le schéma complet : `pip install -r requirements.txt`

### Comment partager avec l'équipe ?

1. Commitez `API_DOCUMENTATION.md` dans Git
2. Hébergez `api_documentation.html` sur GitHub Pages
3. Partagez l'URL Swagger live quand le serveur est en dev/staging

## 📚 Ressources

- [FastAPI Documentation](https://fastapi.tiangolo.com/tutorial/metadata/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [Swagger UI](https://swagger.io/tools/swagger-ui/)
- [ReDoc](https://github.com/Redocly/redoc)
