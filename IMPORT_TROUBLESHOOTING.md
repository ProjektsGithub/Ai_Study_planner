# 🔧 Guide de Dépannage - Import Excel

## Problème: L'import se bloque sans message d'erreur

### Symptômes
- Le bouton d'import charge indéfiniment
- Aucun message de succès ou d'erreur
- La console browser montre une **erreur 500**
- Les données semblent importées SAUF les emplois du temps (ClassSchedules)

---

## ✅ Solutions

### Solution 1: Vérifier les logs backend

**Pendant que l'import tourne:**

1. Ouvrir le terminal où le backend Python tourne
2. Regarder les logs en temps réel
3. Noter le message d'erreur complet (souvent plus détaillé que le frontend)

**Erreurs courantes:**
```
❌ UndefinedColumn: la colonne "xxx" n'existe pas
   → CAUSE: Migration Alembic manquante
   → SOLUTION: Redémarrer le backend (applique les migrations auto)

❌ ForeignKeyViolation: viole la contrainte de clé étrangère
   → CAUSE: Référence à une entité inexistante (programme, track, semester)
   → SOLUTION: Vérifier que les noms dans Excel correspondent EXACTEMENT

❌ IntegrityError: duplicate key value violates unique constraint
   → CAUSE: Doublon dans les données
   → SOLUTION: Supprimer les doublons dans Excel
```

### Solution 2: Vérifier les logs browser (F12)

1. Appuyer sur **F12** dans Chrome/Edge
2. Onglet **Console**
3. Refaire l'import
4. Regarder les logs détaillés:

```javascript
❌ IMPORT ERROR: Error: Request failed with status code 500
Response: { data: { detail: "Le message d'erreur ici" } }
```

5. Copier le message `detail` et le partager

### Solution 3: Vérifier le format Excel

**Emplois du temps (ClassSchedules) NE S'IMPORTENT QUE SI:**

✅ Le **nom du programme** existe déjà dans l'onglet `Programs`
✅ Le **nom de la filière** (track) existe dans l'onglet `Tracks`  
✅ Le **numéro de semestre** existe dans l'onglet `Semesters`

**Exemple:**
```
ClassSchedules:
- program_name: "Computer Science"  ← DOIT exister dans Programs
- track_name: "Bachelor CS"          ← DOIT exister dans Tracks
- semester_number: 1                  ← DOIT exister dans Semesters
- course_name: "Mathematics I"
```

### Solution 4: Import en plusieurs étapes

Si l'import complet échoue, importer en 2 fois:

**Étape 1: Structure de base**
```
✅ Garder dans Excel:
   - Universities
   - Campuses
   - Programs
   - Tracks
   - Semesters
   - TeachingUnits
   - Courses
   - Prerequisites

❌ SUPPRIMER temporairement:
   - ClassSchedules (laisser l'onglet vide)
```

**Étape 2: Emplois du temps**
```
Une fois l'étape 1 réussie:
✅ Ajouter les ClassSchedules
✅ Ré-importer le fichier complet
```

### Solution 5: Tester avec un fichier minimal

Télécharger le **modèle Excel démo** depuis l'interface et vérifier qu'il s'importe sans erreur.

Si le modèle marche mais pas ton fichier → problème de format de données.

---

## 🔍 Diagnostic Avancé

### Vérifier la base de données

```bash
cd backend
python test_import_debug.py
```

Ce script teste l'import sans passer par le réseau.

### Vérifier les migrations

```bash
cd backend
alembic current  # Voir la version actuelle
alembic upgrade head  # Appliquer les migrations manquantes
```

### Logs backend détaillés

Si le backend ne montre rien, activer les logs:

```bash
# Dans backend/.env
LOG_LEVEL=DEBUG
```

Redémarrer le backend.

---

## 📋 Checklist de Vérification

Avant de signaler un bug, vérifier:

- [ ] Le backend tourne (http://localhost:8000/docs accessible)
- [ ] Le frontend tourne (http://localhost:5173 accessible)
- [ ] Les logs backend sont visibles dans le terminal
- [ ] La console browser (F12) est ouverte pendant l'import
- [ ] Le fichier Excel suit le format du modèle téléchargé
- [ ] Les noms dans `ClassSchedules` correspondent EXACTEMENT aux noms dans `Programs`/`Tracks`/`Semesters`
- [ ] Pas d'espaces ou caractères spéciaux bizarres dans Excel

---

## 🆘 Support

Si le problème persiste:

1. Copier les logs backend (terminal)
2. Copier les logs frontend (F12 → Console)
3. Partager le fichier Excel (ou une version anonymisée)
4. Indiquer à quelle étape ça bloque (Upload / Validation / Preview / Execution)
