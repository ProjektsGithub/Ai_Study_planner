"""
Script pour exporter la documentation Swagger en HTML statique
"""
import json
from app.main import app

# Générer le schéma OpenAPI
openapi_schema = app.openapi()

# Créer le HTML avec Swagger UI
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
                layout: "StandaloneLayout"
            }});
        }};
    </script>
</body>
</html>
"""

# Sauvegarder le HTML
with open("api_documentation.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("✅ Documentation HTML exportée dans api_documentation.html")
print("📄 Ouvrez ce fichier dans votre navigateur pour voir la documentation complète")
print("🚀 Vous pouvez héberger ce fichier sur un serveur web statique")
