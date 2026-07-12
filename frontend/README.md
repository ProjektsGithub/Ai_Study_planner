# AI Study Planner - Frontend

Interface utilisateur React pour l'application AI Study Planner.

## 🚀 Démarrage Rapide

### Prérequis
- Node.js 18+
- npm ou yarn

### Installation

```bash
# Installer les dépendances
npm install

# Copier le fichier d'environnement
cp .env.example .env

# Démarrer le serveur de développement
npm run dev
```

L'application sera disponible sur http://localhost:5173

## 📁 Structure du Projet

```
src/
├── components/          # Composants réutilisables
│   ├── WeeklyCalendarView.jsx    # Vue calendrier hebdomadaire
│   └── SessionEditor.jsx         # Éditeur de sessions
├── pages/              # Pages de l'application
│   └── PlannerPage.jsx          # Page principale du planificateur
├── App.jsx             # Composant racine
└── main.jsx            # Point d'entrée
```

## 🎨 Composants Principaux

### WeeklyCalendarView
Affiche le calendrier hebdomadaire avec :
- Grille 7 jours × 48 créneaux (30 min)
- Sessions d'étude colorées par matière
- Disponibilités en arrière-plan
- Contraintes visuelles
- Navigation entre semaines

**Props:**
- `sessions`: Array de sessions d'étude
- `availabilities`: Array de disponibilités
- `constraints`: Array de contraintes
- `onSessionClick`: Callback au clic sur une session
- `weekStartDate`: Date de début de semaine (optionnel)

### SessionEditor
Modal pour créer/modifier des sessions :
- Sélection de matière
- Jour de la semaine
- Plage horaire
- Type de tâche
- Notes

**Props:**
- `session`: Session à éditer (null pour création)
- `subjects`: Array de matières disponibles
- `onSave`: Callback de sauvegarde
- `onDelete`: Callback de suppression
- `onClose`: Callback de fermeture
- `isOpen`: État d'ouverture du modal

### PlannerPage
Page principale intégrant :
- Génération de plans
- Affichage du calendrier
- Édition de sessions
- Statistiques

## 🧪 Tests

```bash
# Lancer les tests
npm test

# Tests avec couverture
npm run test:coverage
```

## 🛠️ Scripts Disponibles

```bash
npm run dev          # Serveur de développement
npm run build        # Build de production
npm run preview      # Prévisualiser le build
npm run lint         # Linter le code
```

## 🎨 Styling

Le projet utilise **TailwindCSS** pour le styling. Les classes utilitaires sont utilisées directement dans les composants.

### Couleurs des Matières
Les sessions sont automatiquement colorées selon leur matière :
- Bleu, Vert, Violet, Rose, Jaune, Indigo, Rouge, Teal, Orange, Cyan

## 📡 API Integration

L'application communique avec le backend FastAPI via Axios.

**Configuration:**
- URL de base : `VITE_API_BASE_URL` dans `.env`
- Authentification : JWT token dans `localStorage`

**Endpoints utilisés:**
- `GET /api/v1/study-plans/current` - Plan actuel
- `POST /api/v1/study-plans/generate` - Générer un plan
- `GET /api/v1/subjects` - Liste des matières
- `GET /api/v1/availabilities` - Disponibilités
- `GET /api/v1/constraints` - Contraintes
- `PUT /api/v1/study-plans/{id}/sessions/{session_id}` - Modifier session
- `POST /api/v1/study-plans/{id}/sessions` - Créer session
- `DELETE /api/v1/study-plans/{id}/sessions/{session_id}` - Supprimer session

## 🔧 Configuration

### Variables d'Environnement

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_ENV=development
```

## 📱 Responsive Design

L'interface est responsive et s'adapte aux écrans :
- Desktop (>1024px) : Vue complète
- Tablet (768-1024px) : Vue adaptée
- Mobile (<768px) : Vue mobile optimisée

## 🚀 Déploiement

```bash
# Build de production
npm run build

# Les fichiers sont générés dans dist/
```

## 📝 Notes de Développement

### Gestion des Dates
- Les semaines commencent le lundi
- Format horaire : HH:MM (24h)
- Créneaux de 30 minutes

### Performance
- Mémoïsation avec `useMemo` pour les calculs coûteux
- Rendu optimisé des sessions (uniquement dans le premier créneau)
- Mise à jour locale de l'état avant appel API

### Accessibilité
- Labels ARIA sur les boutons
- Navigation au clavier
- Contraste des couleurs conforme WCAG

## 🐛 Débogage

### Problèmes Courants

**Le calendrier ne s'affiche pas:**
- Vérifier que le backend est démarré
- Vérifier l'URL de l'API dans `.env`
- Vérifier le token d'authentification

**Les sessions ne se sauvegardent pas:**
- Vérifier la console pour les erreurs API
- Vérifier les validations de formulaire
- Vérifier les permissions utilisateur

## 📄 License

Projet académique - Bachelor/Master
