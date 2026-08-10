"""Script de migration directe pour les colonnes reset_password_token"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Vérifier si les colonnes existent déjà
    result = conn.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name='users' AND column_name IN ('reset_password_token', 'reset_password_token_expires')"
    ))
    existing = [row[0] for row in result]
    print('Colonnes existantes:', existing)
    
    if 'reset_password_token' not in existing:
        conn.execute(text('ALTER TABLE users ADD COLUMN reset_password_token VARCHAR(255)'))
        print('Colonne reset_password_token ajoutée')
    else:
        print('reset_password_token existe déjà')
    
    if 'reset_password_token_expires' not in existing:
        conn.execute(text('ALTER TABLE users ADD COLUMN reset_password_token_expires TIMESTAMP'))
        print('Colonne reset_password_token_expires ajoutée')
    else:
        print('reset_password_token_expires existe déjà')
    
    # Créer l'index si absent
    try:
        conn.execute(text('CREATE INDEX ix_users_reset_password_token ON users (reset_password_token)'))
        print('Index créé')
    except Exception as e:
        print(f'Index (déjà existant ou ignoré): {e}')
    
    conn.commit()
    print('Migration terminée !')
