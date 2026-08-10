"""
Script pour exporter la documentation OpenAPI en JSON
"""
import json
from app.main import app

# Générer le schéma OpenAPI
openapi_schema = app.openapi()

# Sauvegarder dans un fichier JSON
with open("openapi.json", "w", encoding="utf-8") as f:
    json.dump(openapi_schema, f, indent=2, ensure_ascii=False)

print("✅ Documentation OpenAPI exportée dans openapi.json")
print("📄 Vous pouvez l'importer dans:")
print("   - Postman (File > Import)")
print("   - Swagger Editor (https://editor.swagger.io)")
print("   - Insomnia")
print("   - API testing tools")
