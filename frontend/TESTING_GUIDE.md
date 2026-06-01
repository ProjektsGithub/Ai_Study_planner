# Guide de Test - Frontend AI Study Planner

## 🧪 Installation des Dépendances de Test

Avant de lancer les tests, installez les dépendances nécessaires :

```bash
cd frontend
npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom
```

## 🚀 Lancer les Tests

### Mode Watch (Développement)
```bash
npm test
```

### Exécution Unique
```bash
npm test -- --run
```

### Avec Couverture
```bash
npm run test:coverage
```

### Test Spécifique
```bash
npm test WeeklyCalendarView
```

## 📋 Tests Disponibles

### WeeklyCalendarView.test.jsx

**Tests implémentés:**
1. ✅ Rendu du calendrier avec sessions
2. ✅ Affichage de l'état vide
3. ✅ Callback onSessionClick
4. ✅ Navigation vers semaine suivante
5. ✅ Navigation vers semaine précédente
6. ✅ Affichage des 7 jours de la semaine

## 🧪 Test Manuel du Calendrier

### Prérequis
1. Backend démarré sur `http://localhost:8000`
2. Base de données PostgreSQL configurée
3. Utilisateur créé avec profil, matières, disponibilités

### Étapes de Test

#### 1. Démarrer le Frontend
```bash
cd frontend
npm run dev
```

Ouvrir http://localhost:5173

#### 2. Tester la Génération de Plan
1. Cliquer sur "Générer un plan"
2. Vérifier que le calendrier s'affiche
3. Vérifier que les sessions sont colorées
4. Vérifier que les disponibilités sont en vert clair
5. Vérifier que les contraintes sont en rouge clair

#### 3. Tester la Navigation
1. Cliquer sur "Semaine suivante" (→)
2. Vérifier que les dates changent
3. Cliquer sur "Semaine précédente" (←)
4. Cliquer sur "Aujourd'hui"
5. Vérifier le retour à la semaine actuelle

#### 4. Tester l'Édition de Session
1. Cliquer sur une session dans le calendrier
2. Vérifier que le modal s'ouvre
3. Modifier l'heure de début
4. Cliquer sur "Enregistrer"
5. Vérifier que la session est mise à jour

#### 5. Tester l'Ajout de Session
1. Cliquer sur "+ Ajouter une session"
2. Remplir le formulaire :
   - Matière: Sélectionner une matière
   - Jour: Lundi
   - Heure début: 14:00
   - Heure fin: 15:30
   - Type: Exercices
3. Cliquer sur "Enregistrer"
4. Vérifier que la nouvelle session apparaît

#### 6. Tester la Suppression
1. Cliquer sur une session
2. Cliquer sur "Supprimer"
3. Confirmer la suppression
4. Vérifier que la session disparaît

#### 7. Tester les Validations
1. Ouvrir le modal d'édition
2. Essayer de mettre heure fin < heure début
3. Vérifier le message d'erreur
4. Essayer de soumettre sans matière
5. Vérifier le message d'erreur

#### 8. Tester le Responsive
1. Réduire la largeur du navigateur
2. Vérifier l'adaptation mobile
3. Vérifier le scroll horizontal si nécessaire

## 🎯 Cas de Test Spécifiques

### Test 1: Session Multi-Créneaux
**Objectif:** Vérifier que les sessions longues occupent plusieurs créneaux

**Données:**
```javascript
{
  subject_name: "Mathématiques",
  day_of_week: "Monday",
  start_time: "09:00",
  end_time: "11:00",  // 2 heures = 4 créneaux
  task_type: "lecture"
}
```

**Résultat attendu:**
- Session occupe 4 créneaux de 30 min
- Hauteur visuelle = 4 × 3rem

### Test 2: Disponibilités Multiples
**Objectif:** Vérifier l'affichage de plusieurs disponibilités

**Données:**
```javascript
[
  { day_of_week: "Monday", start_time: "08:00", end_time: "12:00" },
  { day_of_week: "Monday", start_time: "14:00", end_time: "18:00" }
]
```

**Résultat attendu:**
- Deux zones vertes distinctes le lundi
- Pas de chevauchement visuel

### Test 3: Contrainte Forbidden Slot
**Objectif:** Vérifier l'affichage des créneaux interdits

**Données:**
```javascript
{
  constraint_type: "forbidden_slot",
  is_active: true,
  parameters: {
    day_of_week: "Wednesday",
    start_time: "12:00",
    end_time: "13:00"
  }
}
```

**Résultat attendu:**
- Zone rouge le mercredi de 12h à 13h
- Aucune session ne devrait être dans cette zone

### Test 4: Matières Multiples
**Objectif:** Vérifier les couleurs distinctes

**Données:**
- 5 matières différentes
- Sessions pour chaque matière

**Résultat attendu:**
- Chaque matière a une couleur unique
- Couleurs cohérentes pour la même matière

### Test 5: État Vide
**Objectif:** Vérifier l'affichage sans sessions

**Données:**
- Aucune session

**Résultat attendu:**
- Message "Aucune session planifiée"
- Icône de calendrier
- Texte explicatif

## 🐛 Problèmes Connus et Solutions

### Problème: Le calendrier ne s'affiche pas
**Causes possibles:**
- Backend non démarré
- Token d'authentification manquant
- CORS non configuré

**Solution:**
```bash
# Vérifier le backend
curl http://localhost:8000/api/docs

# Vérifier le token dans localStorage
console.log(localStorage.getItem('access_token'))
```

### Problème: Sessions ne se sauvegardent pas
**Causes possibles:**
- Validation échouée
- Permissions insuffisantes
- Plan non actif

**Solution:**
- Vérifier la console pour les erreurs
- Vérifier que studyPlan.id existe
- Vérifier les validations de formulaire

### Problème: Couleurs incorrectes
**Causes possibles:**
- subject_id manquant
- Map de couleurs non initialisée

**Solution:**
- Vérifier que chaque session a subject_id
- Vérifier useMemo pour subjectColors

## 📊 Couverture de Test Attendue

### Objectifs de Couverture
- **Statements:** > 80%
- **Branches:** > 75%
- **Functions:** > 80%
- **Lines:** > 80%

### Zones Critiques à Tester
1. ✅ Rendu du calendrier
2. ✅ Calcul des créneaux horaires
3. ✅ Gestion des sessions multi-créneaux
4. ✅ Navigation entre semaines
5. ✅ Callbacks d'événements
6. ⚠️ Validation de formulaire (SessionEditor)
7. ⚠️ Appels API (PlannerPage)
8. ⚠️ Gestion des erreurs

## 🔄 Tests d'Intégration

### Test E2E Complet
1. Créer un utilisateur
2. Configurer le profil
3. Ajouter des matières
4. Définir des disponibilités
5. Générer un plan
6. Modifier une session
7. Ajouter une session
8. Supprimer une session
9. Naviguer entre semaines
10. Vérifier les statistiques

## 📝 Checklist de Test

Avant de considérer la fonctionnalité complète :

- [ ] Tous les tests unitaires passent
- [ ] Couverture > 80%
- [ ] Test manuel de génération réussi
- [ ] Test manuel d'édition réussi
- [ ] Test manuel d'ajout réussi
- [ ] Test manuel de suppression réussi
- [ ] Navigation fonctionnelle
- [ ] Responsive vérifié
- [ ] Accessibilité vérifiée
- [ ] Performance acceptable (<2s)
- [ ] Pas d'erreurs console
- [ ] Pas de warnings React

## 🎓 Ressources

### Documentation
- [Vitest](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- [Jest DOM Matchers](https://github.com/testing-library/jest-dom)

### Exemples de Tests
Voir `src/components/WeeklyCalendarView.test.jsx` pour des exemples complets.

## 🚀 Prochaines Étapes

Après validation de la Tâche 15 :
1. Implémenter les tests pour SessionEditor
2. Implémenter les tests pour PlannerPage
3. Ajouter des tests d'intégration
4. Configurer CI/CD pour tests automatiques
