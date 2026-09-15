"""
Curriculum Topics and Pedagogical Note Enrichment Service

Provides domain-specific learning objectives, syllabus concepts, and practical exercises
for subjects to replace vague synthetic placeholders (e.g., 'Solve problems 7.3-8.16')
with precise, actionable academic guidance.
"""
import re
from typing import Dict, Any, List, Optional

# Knowledge base of curriculum topics by subject or topic keywords
CURRICULUM_DATABASE: Dict[str, Dict[str, Any]] = {
    "calculus and analysis": {
        "keywords": ["calculus", "analysis", "analyse", "math", "maths", "integration", "derivatives"],
        "lecture_review": [
            "Propriétés des fonctions réelles, limites et développements limités de Taylor",
            "Calcul différentiel à plusieurs variables : dérivées partielles, gradient et matrice hessienne",
            "Intégrales multiples, théorème de Fubini et formules de changement de variables",
            "Séries numériques, critères de convergence et séries entières",
            "Équations différentielles linéaires d'ordre 1 et 2 avec second membre",
        ],
        "exercise_practice": [
            "Exercices d'application : Calcul de dérivées partielles d'ordre 2 et optimisation sous contraintes",
            "Problèmes d'intégration : Calcul d'intégrales doubles et triples sur des domaines réguliers",
            "Entraînement : Étude de convergence de suites et séries à termes positifs et alternées",
            "Résolution guidée d'équations différentielles et recherche de solutions particulières",
        ],
        "project_work": [
            "Modélisation analytique : Résolution numérique d'équations différentielles sous Python/NumPy",
            "Approximation de fonctions : Tracé et comparaison de séries de Fourier et polynômes d'interpolation",
        ],
        "reading": [
            "Lecture approfondie : Chapitre sur les espaces vectoriels normés et la topologie de ℝⁿ",
            "Démonstrations clés : Théorème des accroissements finis et formule de Taylor-Lagrange",
        ],
        "exam_preparation": [
            "Annales d'examen : Épreuve de synthèse d'Analyse (intégration, séries et extrema locaux)",
            "Simulation chronométrée : Résolution complète d'un problème type partiel de calcul intégral",
        ],
    },
    "model deployment and serving": {
        "keywords": ["model deployment", "deployment", "serving", "mlops", "production", "fastapi", "docker"],
        "lecture_review": [
            "Architecture des systèmes de serving ML (TorchServe, Triton Inference Server et FastAPI)",
            "Conteneurisation Docker, images multi-stage et bonnes pratiques pour modèles d'inférence",
            "Stratégies de déploiement : Canary releases, Blue/Green et A/B testing de modèles ML",
            "Monitoring en production : Détection du data drift, concept drift et métriques de latence p95/p99",
            "Optimisation de modèles pour l'inférence : Quantification INT8, pruning et ONNX Runtime",
        ],
        "exercise_practice": [
            "Exercice pratique : Création d'une API REST FastAPI avec validation Pydantic pour prédictions en temps réel",
            "Atelier conteneurisation : Rédaction du Dockerfile optimisé et construction d'une image d'inférence légère",
            "Benchmarking d'inférence : Mesure du débit (RPS) et de la latence avec Locust ou Apache Benchmark",
            "Configuration d'un pipeline de monitoring de drift avec Evidently AI ou Prometheus",
        ],
        "project_work": [
            "Projet déploiement : Mise en conteneur Docker de l'API de scoring et déploiement local ou cloud",
            "Mise en place d'un pipeline CI/CD automatisé pour le versioning de modèles avec DVC et GitHub Actions",
        ],
        "reading": [
            "Lecture technique : Documentation officielle ONNX Runtime et formats de sérialisation de modèles",
            "Étude d'architecture : Bonnes pratiques de conception MLOps pour charges d'inférence à grande échelle",
        ],
        "exam_preparation": [
            "Annales et études de cas : Conception d'une architecture de déploiement haute disponibilité pour modèle NLP",
            "Revue des questions types d'examen : Trade-offs latence vs précision et stratégies de rollback",
        ],
    },
    "text preprocessing": {
        "keywords": ["text preprocessing", "preprocessing", "nlp", "texte", "tokenization", "linguistic"],
        "lecture_review": [
            "Fondamentaux du TALN : Normalisation de texte, expressions régulières et gestion des encodages UTF-8",
            "Algorithmes de tokenisation : Word-level, Subword tokenization (Byte-Pair Encoding, WordPiece, SentencePiece)",
            "Techniques morphologiques : Stemming (Porter, Snowball) vs Lemmatisation basée sur dictionnaires (SpaCy)",
            "Nettoyage et filtrage : Stopwords, ponctuation, suppression d'entités sensibles et gestion du bruit",
            "Représentations vectorielles : Sac de mots (Bag of Words), matrices TF-IDF et n-grammes de caractères",
        ],
        "exercise_practice": [
            "Exercice pratique : Développement d'un pipeline complet de nettoyage avec SpaCy et NLTK",
            "Implémentation : Algorithme Byte-Pair Encoding (BPE) pas à pas sur un mini-corpus textuel",
            "Atelier vectorisation : Calcul manuel et avec Scikit-Learn d'une matrice TF-IDF sur des documents réels",
            "Traitement des cas limites : Gestion des émojis, fautes de frappe et variations linguistiques",
        ],
        "project_work": [
            "Projet NLP : Préparation et nettoyage d'un jeu de données textuelles de 10 000 avis clients pour classification",
            "Construction d'un vocabulaire optimisé et benchmarking de l'impact du preprocessing sur un classifieur",
        ],
        "reading": [
            "Lecture d'article scientifique : 'Neural Machine Translation of Rare Words with Subword Units' (BPE)",
            "Guide de référence : Bonnes pratiques de tokenisation moderne pour Large Language Models",
        ],
        "exam_preparation": [
            "Synthèse pour partiel : Comparatif détaillé des méthodes de tokenisation et extraction de features textuelles",
            "Résolution d'épreuves précédentes : QCM d'analyse syntaxique et exercices de vectorisation TF-IDF",
        ],
    },
    "statistics fundamentals": {
        "keywords": ["statistics", "statistique", "probabilite", "probability", "inference", "stats"],
        "lecture_review": [
            "Statistique descriptive : Mesures de tendance centrale, dispersion, asymétrie et kurtosis",
            "Lois de probabilité fondamentales : Normale, Binomiale, Poisson, Student et Chi-deux",
            "Théorème Central Limite et distributions d'échantillonnage de la moyenne",
            "Théorie de l'estimation : Estimateurs sans biais, méthode du maximum de vraisemblance et intervalles de confiance",
            "Principes des tests d'hypothèses : Risque de première espèce (alpha), puissance (1-beta) et p-value",
        ],
        "exercise_practice": [
            "Exercices d'application : Calcul d'intervalles de confiance à 95% et 99% pour moyennes et proportions",
            "Problèmes de tests statistiques : Test de Student à deux échantillons et test du Chi-deux d'indépendance",
            "Analyse de régression : Ajustement d'une régression linéaire simple et interprétation du coefficient R²",
            "Calculs de probabilités : Application de la loi normale centrée réduite et lecture des tables statistiques",
        ],
        "project_work": [
            "Étude statistique sur jeu de données : Tests d'hypothèses et analyses de corrélations avec SciPy et Pandas",
            "Rapport d'analyse exploratoire : Visualisations des distributions et vérification des hypothèses de normalité",
        ],
        "reading": [
            "Lecture de référence : Principes fondateurs de l'inférence statistique et pièges des p-values",
            "Fiche synthèse : Formulaire complet des lois de probabilité et tables de valeurs critiques",
        ],
        "exam_preparation": [
            "Annales d'examen : Traitement complet de 3 exercices d'inférence statistique et formulation des conclusions de tests",
            "Révision intensive : Arbre de décision pour choisir le bon test statistique selon le type de données",
        ],
    },
    "neural network fundamentals": {
        "keywords": ["neural network", "deep learning", "perceptron", "backpropagation", "reseaux de neurones"],
        "lecture_review": [
            "Architecture du Perceptron Multicouche (MLP) : Couches denses, biais et fonctions d'activation (ReLU, Sigmoid)",
            "Rétropropagation du gradient : Règle de dérivation en chaîne et calcul des gradients matriciels",
            "Algorithmes d'optimisation : SGD, Momentum, RMSprop et Adam",
            "Techniques de régularisation : Dropout, régularisation L1/L2 (Weight Decay) et Batch Normalization",
        ],
        "exercise_practice": [
            "Exercice pratique : Implémentation manuelle du forward pass et backpropagation en NumPy pur",
            "Atelier PyTorch : Construction d'un réseau de neurones complet pour la classification MNIST",
            "Expérimentation : Impact des fonctions d'activation et du learning rate sur la convergence du modèle",
        ],
        "project_work": [
            "Projet Deep Learning : Entraînement et réglage des hyperparamètres d'un classifieur de données tabulaires",
        ],
        "reading": [
            "Lecture de référence : 'Deep Learning' (Goodfellow, Bengio) — Chapitre sur l'optimisation pour l'entraînement",
        ],
        "exam_preparation": [
            "Synthèse d'examen : Dérivations mathématiques des gradients et analyse des causes d'explosion/disparition du gradient",
        ],
    },
    "transformer models": {
        "keywords": ["transformer", "attention", "bert", "gpt", "llm", "transformers"],
        "lecture_review": [
            "Mécanisme d'attention : Scaled Dot-Product Attention et Multi-Head Attention",
            "Architecture Encodeur-Décodeur du Transformer : Positional Encoding, LayerNorm et Feed-Forward networks",
            "Modèles pré-entraînés : BERT (auto-encodeur masqué) vs GPT (auto-régressif causal)",
        ],
        "exercise_practice": [
            "Exercice pratique : Implémentation du mécanisme de self-attention multi-têtes en PyTorch",
            "Fine-tuning : Adaptation d'un modèle Hugging Face pour une tâche de classification de texte",
        ],
        "project_work": [
            "Mini-projet : Pipeline de Question-Answering ou classification avec Transformers et Hugging Face",
        ],
        "reading": [
            "Lecture d'article fondamental : 'Attention Is All You Need' (Vaswani et al.)",
        ],
        "exam_preparation": [
            "Annales d'examen : Calcul des complexités temporelles et spatiales de l'attention et schémas d'architectures",
        ],
    },
    "python for data science": {
        "keywords": ["python", "data science", "pandas", "numpy", "matplotlib", "seaborn"],
        "lecture_review": [
            "Manipulation avancée de tableaux NumPy : Indexation booléenne, broadcasting et opérations vectorisées",
            "Nettoyage de données avec Pandas : Groupby, fusions (merge/concat) et gestion des valeurs manquantes",
            "Visualisation de données : Conception de graphiques d'analyse exploratoire avec Seaborn et Matplotlib",
        ],
        "exercise_practice": [
            "Exercices d'entraînement Pandas : Requêtes complexes, agrégations et transformations de séries temporelles",
            "Atelier pratique NumPy : Traitement matriciel sans boucles for pour optimiser les performances",
        ],
        "project_work": [
            "Projet EDA : Analyse exploratoire complète d'un dataset public avec visualisations et insights",
        ],
        "reading": [
            "Documentation Pandas : Bonnes pratiques d'optimisation mémoire et types catégoriels",
        ],
        "exam_preparation": [
            "Épreuve chronométrée de coding : Manipulation de DataFrames et résolution de problèmes en temps limité",
        ],
    },
    "sentiment and text classification": {
        "keywords": ["sentiment", "classification", "classification de texte", "text classification"],
        "lecture_review": [
            "Modélisation supervisée pour le texte : Naive Bayes, Régression Logistique et Support Vector Machines",
            "Métriques d'évaluation en classification : Précision, Rappel, F1-Score macro/micro et matrice de confusion",
        ],
        "exercise_practice": [
            "Atelier pratique : Entraînement d'un classifieur de sentiment sur des commentaires avec Scikit-Learn",
            "Analyse d'erreurs : Inspection des faux positifs/négatifs et optimisation du seuil de décision",
        ],
        "project_work": [
            "Projet de bout en bout : Du scraping ou chargement de données au modèle de prédiction de sentiment",
        ],
        "reading": [
            "Étude de cas : Comparaison des performances modèles linéaires vs Deep Learning sur l'analyse de sentiment",
        ],
        "exam_preparation": [
            "Synthèse de révision : Pipeline complet de classification et calcul des métriques d'évaluation",
        ],
    },
    "editorial standards and policies": {
        "keywords": ["editorial", "journalism", "journalisme", "ethics", "deontologie", "presse"],
        "lecture_review": [
            "Déontologie journalistique : Charte de Munich, devoir d'exactitude et protection des sources",
            "Cadre juridique de la presse : Diffamation, droit de réponse et respect de la vie privée",
            "Processus de vérification éditoriale : Fact-checking, recoupement d'informations et transparence",
        ],
        "exercise_practice": [
            "Étude de cas éthique : Analyse d'un dilemme éditorial et rédaction d'une note de cadrage déontologique",
            "Exercice de relecture critique : Détection de biais d'information et correction d'un article avant publication",
        ],
        "project_work": [
            "Projet éditorial : Rédaction d'une charte de modération et politique de correction des erreurs pour un média en ligne",
        ],
        "reading": [
            "Lecture des textes fondateurs : Charte internationale des journalistes et jurisprudence sur la liberté d'expression",
        ],
        "exam_preparation": [
            "Annales d'examen : Dissertation sur la responsabilité éditoriale à l'ère des réseaux sociaux et de l'IA",
        ],
    },
    "commodity markets": {
        "keywords": ["commodity", "markets", "trading", "matieres premieres", "finance", "derivatives"],
        "lecture_review": [
            "Structure des marchés de matières premières : Marchés spot, contrats à terme (Futures) et options",
            "Mécanismes de fixation des prix : Offre, demande physique, contraintes logistiques et stockage",
            "Gestion du risque de prix : Stratégies de couverture (hedging) par les producteurs et industriels",
        ],
        "exercise_practice": [
            "Exercices de pricing : Calcul du basis (base cash-futures), contango et backwardation sur des contrats réels",
            "Simulation de couverture : Mise en place d'une stratégie de hedge sur matières premières agricoles ou énergie",
        ],
        "project_work": [
            "Étude de marché : Analyse fondamentale des facteurs d'influence du cours d'une matière première clé",
        ],
        "reading": [
            "Lecture économique : Rapports périodiques d'organisations internationales sur l'évolution des matières premières",
        ],
        "exam_preparation": [
            "Cas pratiques d'examen : Calculs de marges, appels de marge et arbitrage sur les marchés dérivés",
        ],
    },
    "automated news writing": {
        "keywords": ["automated news", "automated news writing", "nlg", "robot journalism", "redaction automatisee"],
        "lecture_review": [
            "Fondements du journalisme automatisé : NLG (Natural Language Generation) et pipelines de données",
            "Génération de texte basée sur des gabarits structurés (sports, finances, météo)",
            "Éthique et transparence : Déclaration des contenus générés et supervision humaine (human-in-the-loop)",
            "Évaluation de la qualité textuelle : Cohérence, exactitude factuelle et style journalistique",
        ],
        "exercise_practice": [
            "Atelier pratique : Création d'un générateur automatisé de brèves financières à partir de données CSV/JSON",
            "Exercice de contrôle qualité : Audit d'articles générés et détection d'erreurs de formulation ou de chiffres",
            "Implémentation d'un pipeline de validation avant publication assistée par IA",
        ],
        "project_work": [
            "Projet de rédaction automatisée : Système complet de génération et mise en page d'alertes d'actualité",
        ],
        "reading": [
            "Lecture de recherche : 'Automated Journalism: Ethics, AI and the Future of Media' (Columbia Journalism Review)",
        ],
        "exam_preparation": [
            "Cas d'étude d'examen : Conception d'un workflow de génération automatique pour un desk de dépêches en direct",
        ],
    },
    "ai verification tools": {
        "keywords": ["ai verification", "verification tools", "fact-checking", "source verification", "osint"],
        "lecture_review": [
            "Méthodologie du fact-checking numérique et protocoles de vérification des sources en ligne",
            "Outils IA d'analyse d'authenticité textuelle et détection de contenus synthétiques",
            "Vérification des métadonnées, analyse forensique d'images (InVID / WeVerify) et recherche inversée",
            "Cartographie de la désinformation : Réseaux de bots, astroturfing et campagnes coordonnées",
        ],
        "exercise_practice": [
            "Cas pratique de vérification : Analyse forensique d'une image suspecte virale avec InVID et FotoForensics",
            "Atelier fact-checking : Recoupement de sources primaires et rédaction d'un billet de vérification rigoureux",
            "Utilisation d'outils d'investigation OSINT pour géolocaliser une vidéo partagée sur les réseaux sociaux",
        ],
        "project_work": [
            "Dossier d'investigation : Enquête complète de fact-checking sur un sujet d'actualité avec rapport de vérification",
        ],
        "reading": [
            "Guide pratique : Manuel de vérification du European Journalism Centre pour le journalisme d'investigation",
        ],
        "exam_preparation": [
            "Épreuve pratique chronométrée : Vérification complète de 3 sources d'information sous contrainte de temps",
        ],
    },
    "deepfake detection": {
        "keywords": ["deepfake", "deepfake detection", "synthetic media", "manipulation video", "detection"],
        "lecture_review": [
            "Technologies de génération de deepfakes : GANs, Auto-encodeurs variationnels et synthèse vocale clonée",
            "Artéfacts visuels et acoustiques révélateurs : Clignotement des yeux, distorsions faciales et spectrogrammes audio",
            "Cadre juridique et éditorial : Responsabilité des plateformes et protection des personnalités visées",
            "Limites des détecteurs automatiques : Faux positifs, attaques adversariales et compression vidéo",
        ],
        "exercise_practice": [
            "Atelier détection visuelle : Analyse trame par trame d'extraits vidéo pour identifier les artefacts de fusion",
            "Atelier détection audio : Analyse fréquentielle et identification de clonage vocal par spectrogramme",
            "Benchmark : Évaluation comparée de deux outils de détection de deepfakes sur un échantillon de test",
        ],
        "project_work": [
            "Projet média : Guide méthodologique interne pour une rédaction sur la détection des manipulations audiovisuelles",
        ],
        "reading": [
            "Étude technique : 'Deepfakes and Synthetic Media: Verification in the Age of Generative AI'",
        ],
        "exam_preparation": [
            "Synthèse d'examen : Grille d'analyse éditoriale pour valider ou rejeter une vidéo présumée authentique",
        ],
    },
    "newsroom management": {
        "keywords": ["newsroom", "newsroom management", "redaction", "management des redactions", "desk"],
        "lecture_review": [
            "Organisation moderne des rédactions : Pôles d'édition, desks web, print et audiovisuel",
            "Management de projets éditoriaux et collaboration journalistes-ingénieurs-data scientists",
            "Modèles économiques des médias numériques : Paywalls, abonnements, syndication et monétisation",
            "Gestion des flux d'urgence : Couverture d'événements majeurs (breaking news) et gestion du stress",
        ],
        "exercise_practice": [
            "Simulation de conférence de rédaction : Arbitrage des sujets, hiérarchisation de l'information et planning de publication",
            "Exercice de gestion de crise : Réaction rapide et communication transparente suite à une fausse information publiée",
            "Élaboration d'un budget prévisionnel de production pour une série de reportages d'investigation",
        ],
        "project_work": [
            "Projet éditorial : Plan stratégique de transformation numérique pour une rédaction régionale",
        ],
        "reading": [
            "Rapport Reuters Institute : 'Journalism, Media, and Technology Trends and Predictions'",
        ],
        "exam_preparation": [
            "Étude de cas managériale : Restructuration d'un desk d'information en continu et optimisation du workflow",
        ],
    },
    "leadership in journalism": {
        "keywords": ["leadership", "leadership in journalism", "management des medias", "strategie editoriale"],
        "lecture_review": [
            "Vision et leadership éditorial : Maintenir la confiance du public et l'indépendance journalistique",
            "Pilotage de l'innovation dans les médias : Nouveaux formats (podcasts, newsletters, verticales vidéo)",
            "Développement et fidélisation d'audience : Métriques d'engagement éthiques vs course au clic",
        ],
        "exercise_practice": [
            "Atelier stratégie éditoriale : Conception du positionnement et de la proposition de valeur d'un nouveau média",
            "Analyse de tableaux de bord d'audience : Prise de décision éditoriale basée sur les données d'engagement",
        ],
        "project_work": [
            "Projet de fin d'études : Pitch complet d'un média numérique innovant (ligne éditoriale, gouvernance, modèle économique)",
        ],
        "reading": [
            "Ouvrage de référence : 'The Elements of Journalism' (Kovach & Rosenstiel)",
        ],
        "exam_preparation": [
            "Grand oral de leadership : Soutenance d'une stratégie éditoriale face à un jury de professionnels",
        ],
    },
}

# Regex pattern matching vague / synthetic placeholder notes
VAGUE_NOTE_PATTERNS = [
    re.compile(r"solve\s+problems?\s+[\d\.\-\s,]+", re.IGNORECASE),
    re.compile(r"review\s+(chapters?|modules?|lectures?)\s+[\d\.\-\s,]+", re.IGNORECASE),
    re.compile(r"read\s+(textbook\s+)?pages?\s+[\d\.\-\s,]+", re.IGNORECASE),
    re.compile(r"work\s+on\s+project\s+milestone\s+\d+", re.IGNORECASE),
    re.compile(r"^mock\s+exam\s+practice(\s+and\s+review\s+weak\s+areas)?$", re.IGNORECASE),
    re.compile(r"^review\s+notes?$", re.IGNORECASE),
    re.compile(r"^study\s+session$", re.IGNORECASE),
]


def find_matching_curriculum(subject_name: str) -> Optional[Dict[str, Any]]:
    """Find curriculum database entry matching the given subject name."""
    clean_name = subject_name.lower().strip()
    
    # Exact match first
    if clean_name in CURRICULUM_DATABASE:
        return CURRICULUM_DATABASE[clean_name]
    
    # Keyword match
    for key, data in CURRICULUM_DATABASE.items():
        if key in clean_name or clean_name in key:
            return data
        for kw in data.get("keywords", []):
            if kw in clean_name:
                return data
                
    return None


def is_note_vague(note: Optional[str]) -> bool:
    """Check if a session note contains vague placeholder text."""
    if not note or len(note.strip()) < 10:
        return True
    
    clean_note = note.strip()
    for pattern in VAGUE_NOTE_PATTERNS:
        if pattern.search(clean_note):
            return True
            
    return False


def enrich_session_note(
    subject_name: str,
    task_type: str,
    current_note: Optional[str] = None,
    session_index: int = 0,
    language: str = "fr"
) -> str:
    """
    Enrich or replace a vague session note with a concrete, educational learning objective.
    
    If the current note is already concrete and informative (not matching vague templates),
    it is preserved. Otherwise, a tailored objective is generated from the curriculum database.
    """
    if current_note and not is_note_vague(current_note):
        return current_note
    
    lang = (language or "fr").lower()[:2]
    curriculum = find_matching_curriculum(subject_name)
    
    if curriculum and lang == "fr":
        topics_list = curriculum.get(task_type) or curriculum.get("lecture_review") or []
        if topics_list:
            selected_topic = topics_list[session_index % len(topics_list)]
            return f"{subject_name} : {selected_topic}"
    
    # Generic domain fallback (or localized template for non-FR languages)
    clean_subj = subject_name.strip()

    if lang == "en":
        if task_type == "exercise_practice":
            return f"{clean_subj}: Practical exercises and methodological problem-solving"
        elif task_type == "lecture_review":
            return f"{clean_subj}: In-depth review of key lecture concepts and theoretical summary"
        elif task_type == "exam_preparation":
            return f"{clean_subj}: Practice on past exam papers and targeted review of complex topics"
        elif task_type == "project_work":
            return f"{clean_subj}: Practical lab work, implementation, and project milestones"
        elif task_type == "reading":
            return f"{clean_subj}: Critical reading and documentation on syllabus topics"
        else:
            return f"{clean_subj}: Study session on core concepts"
    elif lang == "de":
        if task_type == "exercise_practice":
            return f"{clean_subj}: Praktische Anwendungsübungen und methodische Problemlösung"
        elif task_type == "lecture_review":
            return f"{clean_subj}: Vertiefte Wiederholung der Kernkonzepte der Vorlesung und Theoriezusammenfassung"
        elif task_type == "exam_preparation":
            return f"{clean_subj}: Prüfungsvorbereitung anhand von Altklausuren und gezielte Wiederholung"
        elif task_type == "project_work":
            return f"{clean_subj}: Praktische Laborarbeiten, Implementierung und Projektfortschritt"
        elif task_type == "reading":
            return f"{clean_subj}: Fachliteraturstudium und Dokumentation zu den Schwerpunktthemen"
        else:
            return f"{clean_subj}: Lerneinheit zu den Schlüsselkonzepten"
    else:
        if task_type == "exercise_practice":
            return f"{clean_subj} : Exercices d'application pratique et résolution de problèmes méthodologiques"
        elif task_type == "lecture_review":
            return f"{clean_subj} : Révision approfondie des concepts clés du cours et synthèse théorique"
        elif task_type == "exam_preparation":
            return f"{clean_subj} : Entraînement sur annales d'examen et révision ciblée des points complexes"
        elif task_type == "project_work":
            return f"{clean_subj} : Travaux pratiques, implémentation et avancement des livrables du projet"
        elif task_type == "reading":
            return f"{clean_subj} : Lecture critique et documentation sur les thématiques du programme"
        else:
            return f"{clean_subj} : Session d'approfondissement des notions clés"


def get_subject_prompt_context(subject_name: str) -> str:
    """
    Returns a concise string of key syllabus concepts for prompt injection.
    Helps the AI generate real, precise notes instead of inventing placeholders.
    """
    curriculum = find_matching_curriculum(subject_name)
    if not curriculum:
        return ""
    
    lectures = curriculum.get("lecture_review", [])[:2]
    exercises = curriculum.get("exercise_practice", [])[:2]
    
    concepts = []
    for l in lectures:
        # shorten
        concepts.append(l.split(":")[0] if ":" in l else l)
    for e in exercises:
        concepts.append(e.split(":")[0] if ":" in e else e)
        
    return f"  Key concepts: {'; '.join(concepts[:3])}"
