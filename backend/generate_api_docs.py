"""
Génération de la documentation API sans démarrer le serveur
"""
import json
import sys
from pathlib import Path

# Essayer d'importer l'app
try:
    from app.main import app
    openapi_schema = app.openapi()
    success = True
except Exception as e:
    print(f"⚠️  Impossible d'importer l'app complète: {e}")
    print("📝 Génération d'un schéma OpenAPI basique...")
    success = False
    
    # Schéma OpenAPI basique si l'import échoue
    openapi_schema = {
        "openapi": "3.1.0",
        "info": {
            "title": "AI Study Planner API",
            "description": """
# API Documentation - AI Study Planner

Application web intelligente pour la génération automatique de plannings d'études personnalisés.

## Fonctionnalités Principales

### 🎓 Gestion Étudiante
- Authentification JWT
- Profils étudiants personnalisés
- Gestion des matières et examens
- Suivi de progression ECTS

### 📅 Planification Intelligente
- Génération automatique de plannings
- Optimisation basée sur IA (Llama 3.2)
- Contraintes et disponibilités
- Historique des plannings

### 🏢 Plateforme Super Admin
- Gestion institutionnelle (universités, programmes, cours)
- Import/Export en masse (CSV/Excel)
- Système d'audit complet
- RBAC (Role-Based Access Control)

### 📊 Analyse & Suivi
- Analyse de risque académique
- Priorisation des matières
- Recommandations personnalisées
- Tracking ECTS

## Authentification

L'API utilise JWT (JSON Web Tokens) pour l'authentification.

**Obtenir un token:**
```bash
POST /api/v1/auth/login
{
  "email": "user@example.com",
  "password": "password"
}
```

**Utiliser le token:**
```
Authorization: Bearer <votre_token>
```

## Environnements

- **Development**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Support

Pour toute question, consultez la documentation complète dans le README.md
            """,
            "version": "1.0.0",
            "contact": {
                "name": "AI Study Planner Team",
                "url": "https://github.com/votre-repo/AIplaning"
            }
        },
        "servers": [
            {"url": "http://localhost:8000", "description": "Development server"},
            {"url": "https://api.aiplaning.com", "description": "Production server"}
        ],
        "paths": {
            "/api/v1/auth/register": {
                "post": {
                    "tags": ["Authentication"],
                    "summary": "Register new user",
                    "description": "Create a new user account",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "email": {"type": "string", "format": "email"},
                                        "password": {"type": "string", "minLength": 8},
                                        "full_name": {"type": "string"}
                                    },
                                    "required": ["email", "password", "full_name"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {"description": "User created successfully"},
                        "400": {"description": "Invalid input"},
                        "409": {"description": "Email already exists"}
                    }
                }
            },
            "/api/v1/auth/login": {
                "post": {
                    "tags": ["Authentication"],
                    "summary": "Login user",
                    "description": "Authenticate and get JWT token",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/x-www-form-urlencoded": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "username": {"type": "string"},
                                        "password": {"type": "string"}
                                    },
                                    "required": ["username", "password"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Login successful, returns JWT token"},
                        "401": {"description": "Invalid credentials"}
                    }
                }
            },
            "/api/v1/study-plans/generate": {
                "post": {
                    "tags": ["Study Plans"],
                    "summary": "Generate study plan",
                    "description": "Generate personalized weekly study plan using AI",
                    "security": [{"bearerAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "week_start": {"type": "string", "format": "date"},
                                        "preferences": {"type": "object"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {"description": "Study plan generated successfully"},
                        "401": {"description": "Unauthorized"},
                        "422": {"description": "Validation error"}
                    }
                }
            },
            "/api/v1/subjects": {
                "get": {
                    "tags": ["Subjects"],
                    "summary": "List subjects",
                    "description": "Get all subjects for the authenticated user",
                    "security": [{"bearerAuth": []}],
                    "responses": {
                        "200": {"description": "List of subjects"},
                        "401": {"description": "Unauthorized"}
                    }
                },
                "post": {
                    "tags": ["Subjects"],
                    "summary": "Create subject",
                    "description": "Add a new subject",
                    "security": [{"bearerAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "ects_credits": {"type": "integer"},
                                        "difficulty": {"type": "integer", "minimum": 1, "maximum": 10},
                                        "priority": {"type": "integer", "minimum": 1, "maximum": 10}
                                    },
                                    "required": ["name", "ects_credits"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {"description": "Subject created"},
                        "401": {"description": "Unauthorized"}
                    }
                }
            },
            "/api/v1/admin/universities": {
                "get": {
                    "tags": ["Admin - Universities"],
                    "summary": "List universities",
                    "description": "Get all universities (Admin only)",
                    "security": [{"bearerAuth": []}],
                    "responses": {
                        "200": {"description": "List of universities"},
                        "401": {"description": "Unauthorized"},
                        "403": {"description": "Forbidden - Admin access required"}
                    }
                },
                "post": {
                    "tags": ["Admin - Universities"],
                    "summary": "Create university",
                    "description": "Add a new university (Admin only)",
                    "security": [{"bearerAuth": []}],
                    "responses": {
                        "201": {"description": "University created"},
                        "403": {"description": "Forbidden"}
                    }
                }
            }
        },
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                }
            }
        },
        "tags": [
            {"name": "Authentication", "description": "User authentication endpoints"},
            {"name": "Study Plans", "description": "Study plan generation and management"},
            {"name": "Subjects", "description": "Subject management"},
            {"name": "Admin - Universities", "description": "University management (Admin)"},
            {"name": "Admin - Programs", "description": "Study program management (Admin)"},
            {"name": "Admin - Courses", "description": "Course catalog management (Admin)"}
        ]
    }

# Sauvegarder le JSON
output_file = Path("openapi.json")
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(openapi_schema, f, indent=2, ensure_ascii=False)

print("✅ Documentation OpenAPI exportée dans openapi.json")
if success:
    print("📊 Schéma complet généré depuis l'application")
else:
    print("📊 Schéma basique généré (démarrez le serveur pour le schéma complet)")

# Générer le HTML
html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Documentation - AI Study Planner</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css">
    <style>
        body {{
            margin: 0;
            padding: 0;
        }}
        .topbar {{
            background-color: #1890ff !important;
        }}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {{
            const spec = {json.dumps(openapi_schema, ensure_ascii=False)};
            
            window.ui = SwaggerUIBundle({{
                spec: spec,
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout",
                displayRequestDuration: true,
                tryItOutEnabled: true
            }});
        }};
    </script>
</body>
</html>
"""

html_file = Path("api_documentation.html")
with open(html_file, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"✅ Documentation HTML exportée dans {html_file}")
print("")
print("📄 Fichiers générés:")
print(f"   1. openapi.json - Schéma OpenAPI pour import")
print(f"   2. api_documentation.html - Documentation interactive")
print("")
print("🚀 Pour voir la documentation complète:")
print("   1. Démarrez le backend: uvicorn app.main:app --reload")
print("   2. Visitez: http://localhost:8000/docs")
