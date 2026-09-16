# 📊 Structure Complète du Fichier Excel d'Import

## 📁 Onglets Requis (Tabs/Sheets)

Le fichier Excel doit contenir **10 onglets** avec ces noms EXACTS :

1. **Universities**
2. **Campuses**
3. **Programs**
4. **University_Programs**
5. **Tracks**
6. **Semesters**
7. **TeachingUnits**
8. **Courses**
9. **Prerequisites**
10. **ClassSchedules**

---

## 📋 Structure Détaillée de Chaque Onglet

### 1. Universities (Universités)

**Colonnes obligatoires:**
```
| name | country | description | name_de | description_de |
```

**Exemple:**
```excel
name                    | country | description                          | name_de              | description_de
TU Berlin               | Germany | Technical University of Berlin       | TU Berlin            | Technische Universität Berlin
University of Douala    | Cameroon| Leading university in Cameroon       | Universität Douala   | Führende Universität in Kamerun
```

**Règles:**
- ✅ `name` doit être **unique**
- ✅ `country` recommandé (défaut: "Germany")
- ⚠️ Colonnes allemandes (`_de`) optionnelles

---

### 2. Campuses

**Colonnes obligatoires:**
```
| university_name | name | location | description | name_de | description_de |
```

**Exemple:**
```excel
university_name      | name           | location        | description              | name_de        | description_de
TU Berlin            | Main Campus    | Berlin-Mitte    | Main campus downtown     | Hauptcampus    | Hauptcampus Innenstadt
University of Douala | Akwa Campus    | Douala, Akwa    | Business school campus   | Akwa Campus    | Wirtschaftscampus
```

**Règles:**
- ✅ `university_name` doit correspondre EXACTEMENT au nom dans l'onglet **Universities**
- ✅ `name` doit être unique par université

---

### 3. Programs (Programmes d'études)

**Colonnes obligatoires:**
```
| name | code | description | name_de | description_de |
```

**Exemple:**
```excel
name                          | code    | description                      | name_de                | description_de
Computer Science              | CS      | Bachelor of Computer Science     | Informatik             | Bachelor Informatik
Business Administration       | BA      | Master of Business Admin         | Betriebswirtschaft     | Master BWL
```

**Règles:**
- ✅ `name` doit être **unique**
- ✅ `code` doit être **unique** (ex: "CS", "BA", "ME")
- ⚠️ Si `code` est vide, le système génère automatiquement

---

### 4. University_Programs (Liens Université ↔ Programme)

**Colonnes obligatoires:**
```
| university_name | program_name |
```

**Exemple:**
```excel
university_name      | program_name
TU Berlin            | Computer Science
TU Berlin            | Business Administration
University of Douala | Business Administration
```

**Règles:**
- ✅ `university_name` doit exister dans **Universities**
- ✅ `program_name` doit exister dans **Programs**
- ⚠️ Une université peut avoir plusieurs programmes
- ⚠️ Un programme peut être dans plusieurs universités

---

### 5. Tracks (Filières/Parcours)

**Colonnes obligatoires:**
```
| program_name | name | level | total_ects_required | description | name_de | description_de | graduation_conditions |
```

**Exemple:**
```excel
program_name     | name                  | level    | total_ects_required | description              | name_de           | description_de
Computer Science | Bachelor CS           | Bachelor | 180                 | 3-year bachelor program  | Bachelor Info     | 3-jähriger Bachelor
Computer Science | Master CS             | Master   | 120                 | 2-year master program    | Master Info       | 2-jähriger Master
```

**Règles:**
- ✅ `program_name` doit exister dans **Programs**
- ✅ `name` doit être **unique**
- ✅ `level` doit être: **"Bachelor"**, **"Master"**, ou **"Doctorate"**
- ✅ `total_ects_required` : nombre (ex: 180 pour licence, 120 pour master)

---

### 6. Semesters (Semestres)

**Colonnes obligatoires:**
```
| track_name | name | semester_number | ects_required | description | name_de | description_de |
```

**Exemple:**
```excel
track_name    | name        | semester_number | ects_required | description       | name_de       | description_de
Bachelor CS   | Semester 1  | 1               | 30            | First semester    | Semester 1    | Erstes Semester
Bachelor CS   | Semester 2  | 2               | 30            | Second semester   | Semester 2    | Zweites Semester
Bachelor CS   | Semester 3  | 3               | 30            | Third semester    | Semester 3    | Drittes Semester
```

**Règles:**
- ✅ `track_name` doit exister dans **Tracks**
- ✅ `name` doit être **unique**
- ✅ `semester_number` : 1, 2, 3, 4, 5, 6...
- ✅ `ects_required` : généralement 30 par semestre

---

### 7. TeachingUnits (Unités d'Enseignement)

**Colonnes obligatoires:**
```
| semester_name | name | code | ects_required | description | name_de | description_de |
```

**Exemple:**
```excel
semester_name | name                      | code  | ects_required | description              | name_de
Semester 1    | Fundamental Programming   | UE-01 | 12            | Core programming skills  | Grundlagen Programmierung
Semester 1    | Mathematics I             | UE-02 | 10            | Calculus and algebra     | Mathematik I
```

**Règles:**
- ✅ `semester_name` doit exister dans **Semesters**
- ✅ `name` doit être **unique**
- ✅ `code` doit être **unique** (ou vide)

---

### 8. Courses (Cours) ⚠️ ATTENTION AUX DOUBLONS

**Colonnes obligatoires:**
```
| semester_name | teaching_unit_name | name | code | ects_credits | coefficient | difficulty_level | description | name_de | description_de |
```

**Exemple:**
```excel
semester_name | teaching_unit_name      | name              | code      | ects_credits | coefficient | difficulty_level | description
Semester 1    | Fundamental Programming | Intro to Python   | CS-101    | 6            | 2           | 2                | Python basics
Semester 1    | Fundamental Programming | Algorithms I      | CS-102    | 6            | 2           | 3                | Data structures
Semester 1    | Mathematics I           | Calculus          | MATH-101  | 5            | 2           | 3                | Differential calculus
```

**Règles CRITIQUES:**
- ✅ `semester_name` doit exister dans **Semesters**
- ✅ `teaching_unit_name` doit exister dans **TeachingUnits** (ou vide)
- ⚠️ **`code` DOIT ÊTRE UNIQUE DANS TOUT LE FICHIER !**
- ⚠️ **PAS DE DOUBLONS DE CODE !** (ex: deux cours "CS-101")
- ✅ `ects_credits` : nombre de crédits (ex: 3, 5, 6)
- ✅ `coefficient` : poids du cours (défaut: 1)
- ✅ `difficulty_level` : 1-5 (1=facile, 5=très difficile)

**❌ ERREUR COMMUNE:**
```excel
# MAUVAIS - DOUBLON!
CS-101 | Intro to Python  | Semester 1
CS-101 | Python Advanced  | Semester 2  ← ❌ DOUBLON!

# BON
CS-101 | Intro to Python  | Semester 1
CS-201 | Python Advanced  | Semester 2  ← ✅ Code unique
```

---

### 9. Prerequisites (Prérequis)

**Colonnes obligatoires:**
```
| course_name | prerequisite_name |
```

**Exemple:**
```excel
course_name       | prerequisite_name
Algorithms II     | Algorithms I
Data Structures   | Intro to Python
Web Development   | JavaScript Basics
```

**Règles:**
- ✅ `course_name` doit exister dans **Courses**
- ✅ `prerequisite_name` doit exister dans **Courses**
- ⚠️ Un cours peut avoir plusieurs prérequis (plusieurs lignes)

---

### 10. ClassSchedules (Emplois du Temps)

**Colonnes obligatoires:**
```
| program_name | track_name | semester_number | course_name | course_code | day_of_week | start_time | end_time | session_type | group_name | room_location | is_fixed |
```

**Exemple:**
```excel
program_name     | track_name  | semester_number | course_name      | course_code | day_of_week | start_time | end_time | session_type | group_name | room_location | is_fixed
Computer Science | Bachelor CS | 1               | Intro to Python  | CS-101      | Monday      | 08:00      | 10:00    | CM           | Promo      | Room A101     | true
Computer Science | Bachelor CS | 1               | Intro to Python  | CS-101      | Wednesday   | 14:00      | 16:00    | TD           | Groupe 1   | Lab B203      | false
Computer Science | Bachelor CS | 1               | Calculus         | MATH-101    | Tuesday     | 10:00      | 12:00    | CM           | Promo      | Amphi C       | true
```

**Règles:**
- ✅ `program_name` doit exister dans **Programs**
- ✅ `track_name` doit exister dans **Tracks** (optionnel)
- ✅ `semester_number` doit exister dans **Semesters**
- ✅ `course_name` ou `course_code` doit correspondre à un cours existant
- ✅ `day_of_week` : Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday
- ✅ `start_time` / `end_time` : format 08:00, 14:30, 16:45
- ✅ `session_type` : **CM** (cours magistral), **TD** (travaux dirigés), **TP** (travaux pratiques)
- ✅ `group_name` : nom du groupe (ex: "Promo", "Groupe 1", "Groupe A")
- ✅ `is_fixed` : true/false (true = cours fixe pour tous)

---

## ⚠️ VÉRIFICATIONS AVANT IMPORT

### Checklist de Validation

#### 1. Codes Uniques (CRITIQUE)
```bash
# Dans l'onglet Courses, vérifier qu'aucun code n'apparaît 2 fois
- Tri alphabétique par colonne "code"
- Chercher visuellement les doublons
- Utiliser la fonction Excel: =COUNTIF($D:$D, D2) > 1
```

#### 2. Noms Exacts
```
✅ Les noms doivent correspondre EXACTEMENT (majuscules/minuscules/espaces)
- "Bachelor CS" ≠ "Bachelor cs" ≠ "Bachelor  CS" (deux espaces)
```

#### 3. Références Croisées
```
✅ Vérifier que tous les noms référencés existent :
- University_Programs.university_name → Universities.name
- Tracks.program_name → Programs.name
- Semesters.track_name → Tracks.name
- Courses.semester_name → Semesters.name
- Prerequisites.course_name → Courses.name
- ClassSchedules.program_name → Programs.name
```

---

## 🔧 Script de Détection de Doublons dans Excel

**Formule Excel à ajouter dans Courses (colonne vide):**
```excel
# Colonne K (par exemple)
=SI(NB.SI($D:$D;D2)>1;"❌ DOUBLON";"✅ OK")
```

Cela affichera "❌ DOUBLON" si le code apparaît plusieurs fois.

---

## 📥 Exemple de Fichier Excel Minimal

```
Universities:
- TU Berlin | Germany | Technical University

Programs:
- Computer Science | CS | Bachelor program

Tracks:
- Bachelor CS | Bachelor | 180 ECTS

Semesters:
- Semester 1 | 1 | 30 ECTS

TeachingUnits:
- Programming Basics | UE-01 | 12 ECTS

Courses:
- Intro to Python | CS-101 | 6 ECTS  ← Code unique!
- Algorithms I    | CS-102 | 6 ECTS  ← Code unique!

Prerequisites:
- (vide si aucun prérequis)

ClassSchedules:
- Intro to Python | Monday | 08:00-10:00 | CM
```

---

## 🆘 Si l'Import Échoue Encore

**Envoie-moi une capture d'écran de:**
1. L'onglet **Courses** (toutes les lignes)
2. La colonne **code** en particulier
3. Le message d'erreur exact

Je pourrai identifier précisément quel code est dupliqué ! 🔍
