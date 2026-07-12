# Configuration Google Colab pour Llama + LoRA

## 🎯 Architecture avec Google Colab

```
┌─────────────────┐      API REST      ┌──────────────────┐
│   Frontend      │ ◄─────────────────► │   Backend        │
│   (React)       │                     │   (FastAPI)      │
└─────────────────┘                     └──────────────────┘
                                               │
                                               │ HTTPS/ngrok
                                               ▼
                                        ┌──────────────────┐
                                        │  Google Colab    │
                                        │  Flask API       │
                                        │  Llama + LoRA    │
                                        │  (GPU T4/A100)   │
                                        └──────────────────┘
```

---

## 💰 Avantages de Google Colab

| Critère | Colab Free | Colab Pro | Colab Pro+ | VPS |
|---------|------------|-----------|------------|-----|
| **Prix** | 0€ | 10€/mois | 50€/mois | 200-500€/mois |
| **GPU** | T4 (limité) | T4/A100 | A100 prioritaire | Dédié |
| **RAM** | 12 GB | 32 GB | 52 GB | 16-128 GB |
| **Durée session** | 12h max | 24h max | 24h max | Illimité |
| **Setup** | Immédiat | Immédiat | Immédiat | 1-2 jours |
| **Maintenance** | 0 | 0 | 0 | Élevée |

**Recommandation : Colab Pro (10€/mois) pour démarrer**

---

## 📦 Structure des fichiers

```
AIplaning/
├── notebooks/
│   ├── colab_inference_server.ipynb   # Serveur d'inférence (à exécuter dans Colab)
│   └── train_lora_study_planner.ipynb # Entraînement LoRA (futur)
├── backend/
│   ├── test_colab_connection.py       # Script de test de connexion
│   └── .env                            # Configuration (COLAB_API_URL, COLAB_API_KEY)
└── GOOGLE_COLAB_SETUP.md              # Ce fichier
```

---

## 🚀 Guide d'Installation Rapide

### **Étape 1 : Créer le dossier notebooks**



Le dossier `notebooks/` existe déjà dans votre projet. Passez à l'étape suivante.

### **Étape 2 : Ouvrir Google Colab**

1. Allez sur [https://colab.research.google.com/](https://colab.research.google.com/)
2. Connectez-vous avec votre compte Google
3. Créez un nouveau notebook : **File → New notebook**
4. Renommez-le : **`colab_inference_server`**

### **Étape 1 : Configurer le GPU dans Colab**

1. Dans Colab : **Runtime → Change runtime type**
2. Sélectionnez : 
   - **Hardware accelerator : L4 GPU** (recommandé pour Llama 3.1-8B) ⭐
   - **Hardware accelerator : A100 GPU** (Colab Pro - performances maximales) 🚀
   - **Hardware accelerator : T4 GPU** (Colab Free - utilisera Llama 3.2-3B auto) ⚡
3. Cliquez sur **Save**

**Recommandations GPU pour Llama 3.1-8B :**

| GPU | VRAM | Modèle optimal | Tokens/sec | Latence | Disponibilité |
|-----|------|----------------|------------|---------|---------------|
| **L4** | 24 GB | Llama 3.1-8B | 40-60 | 5-8s | Colab Standard/Pro |
| **A100** | 40 GB | Llama 3.1-8B | 80-120 | 3-5s | Colab Pro |
| **T4** | 16 GB | Llama 3.2-3B (auto) | 30-40 | 8-12s | Colab Free |

💡 **Meilleur rapport qualité/prix : L4 avec Llama 3.1-8B**

### **Étape 2 : Obtenir un token ngrok GRATUIT**

Ngrok permet d'exposer votre notebook sur Internet.

1. Allez sur [https://dashboard.ngrok.com/signup](https://dashboard.ngrok.com/signup)
2. Créez un compte gratuit (Google/GitHub disponible)
3. Copiez votre **authtoken** depuis [cette page](https://dashboard.ngrok.com/get-started/your-authtoken)
4. **Gardez-le sous la main** pour l'étape 4

### **Étape 3 : Exécuter le notebook**

1. Exécutez toutes les cellules : **Runtime → Run all**
2. **Cellule 1** : Installation des dépendances (~1 min)
3. **Cellule 2** : Configuration - Copiez la **clé API** affichée
4. **Cellule 3** : Chargement du modèle Unsloth (~2-3 min première fois, puis ~30s)
5. **Cellule 4** : Création du serveur Flask
6. **Cellule 5** : 
   - **Collez votre token ngrok** quand demandé
   - Attendez l'URL ngrok (~10-20 secondes)
7. **Cellule 6** : Test automatique du serveur

**Résultat attendu après la cellule 5 :**

Éditez `backend/.env` :

```bash
# Passer en mode Colab
AI_SERVICE_TYPE=colab

# URL ngrok de votre notebook Colab
COLAB_API_URL=https://xxxx-xx-xx-xx-xx.ngrok-free.app

# Clé API générée par le notebook
COLAB_API_KEY=sk-xxxxxxxxxxxxxx
```

### **Étape 7 : Tester la connexion**

```bash
cd backend
python test_colab_connection.py
```

Vous devriez voir :
```
✅ Connexion au serveur Colab réussie!
✅ Génération de texte fonctionnelle!
Réponse: [texte généré par Llama]
```

---

## 📝 Fichiers créés automatiquement

### **1. `notebooks/colab_inference_server.ipynb`**
Notebook Colab prêt à l'emploi avec :
- Installation automatique des dépendances
- Serveur Flask avec authentification
- Tunnel ngrok
- Endpoint `/generate` compatible avec votre backend

### **2. `backend/test_colab_connection.py`**
Script Python pour tester la connexion et la génération.

---

## 🔒 Sécurité

### **Clé API**
- Générée automatiquement par le notebook (format : `sk-xxxxxxxxxxxxxxxx`)
- À copier dans `backend/.env` → `COLAB_API_KEY`
- **Ne jamais commit cette clé dans Git !**

### **Ngrok**
- Tunnel HTTPS sécurisé (SSL/TLS)
- URL aléatoire générée à chaque session
- Gratuit pour usage basique (limite : 40 requêtes/minute)

---

## ⚡ Performances attendues

### **GPU L4 (24 GB) - RECOMMANDÉ** ⭐
- Modèle : Llama 3.1-8B-Instruct
- Temps de chargement : ~2 min
- Génération (plan complet ~200 tokens) : ~5-8 secondes
- Tokens/seconde : 40-60 tok/s
- VRAM utilisée : ~6-8 GB
- **Meilleur compromis qualité/prix**

### **GPU A100 (40 GB) - PERFORMANCES MAXIMALES** 🚀
- Modèle : Llama 3.1-8B-Instruct
- Temps de chargement : ~1.5 min
- Génération (plan complet ~200 tokens) : ~3-5 secondes
- Tokens/seconde : 80-120 tok/s
- VRAM utilisée : ~6-8 GB
- Limite : ~24h de session continue

### **GPU T4 (16 GB) - GRATUIT** ⚡
- Modèle : Llama 3.2-3B-Instruct (auto-switch)
- Temps de chargement : ~2 min
- Génération (plan complet ~200 tokens) : ~8-12 secondes
- Tokens/seconde : 30-40 tok/s
- VRAM utilisée : ~3-4 GB
- Limite : ~12h de session continue

### **Qualité des réponses**
- **Llama 3.1-8B** (L4/A100) : Excellente compréhension, planning optimisé, respect des contraintes complexes
- **Llama 3.2-3B** (T4) : Bonne qualité, convient pour la plupart des cas d'usage

---

## 🛠️ Dépannage

### **Erreur : "No GPU available"**
→ Vérifiez : **Runtime → Change runtime type → T4 GPU**

### **Erreur : "ngrok not working"**
→ Le tunnel ngrok peut prendre 30 secondes à démarrer. Attendez.

### **Erreur : "Connection timeout"**
→ Vérifiez que l'URL ngrok est à jour dans `.env` (elle change à chaque redémarrage du notebook)

### **Erreur : "401 Unauthorized"**
→ Vérifiez que `COLAB_API_KEY` dans `.env` correspond à celle affichée par le notebook

### **Session Colab expirée**
→ Redémarrez le notebook et mettez à jour `COLAB_API_URL` dans `.env`

---

## 📊 Monitoring

Le notebook affiche en temps réel :
- Nombre de requêtes reçues
- Temps de génération moyen
- Erreurs éventuelles

---

## 🔄 Workflow de développement

### **Mode développement (Ollama local)**
```bash
AI_SERVICE_TYPE=ollama
```
- Pas besoin de GPU externe
- Plus rapide pour tester
- Pas de coûts

### **Mode production (Colab)**
```bash
AI_SERVICE_TYPE=colab
COLAB_API_URL=https://xxxx.ngrok-free.app
COLAB_API_KEY=sk-xxxxxx
```
- GPU puissant
- Meilleure qualité de génération
- Coûts : 0€ (Free) ou 10€/mois (Pro)

---

## 🎯 Prochaines étapes

1. ✅ **Configurer le serveur d'inférence de base** (ce guide)
2. ⏳ **Créer un dataset d'entraînement** pour LoRA
3. ⏳ **Entraîner un adaptateur LoRA** spécialisé dans la génération de plans d'étude
4. ⏳ **Déployer LoRA sur Colab** pour améliorer la qualité

---

## 📚 Ressources

- [Google Colab](https://colab.research.google.com/)
- [ngrok Documentation](https://ngrok.com/docs)
- [Hugging Face Transformers](https://huggingface.co/docs/transformers/)
- [Llama Models](https://huggingface.co/meta-llama)

---

## 💡 Astuces

### **Garder la session active**
Colab peut se déconnecter si vous n'interagissez pas. Ajoutez ce code dans une cellule :

```python
# Keep-alive (optional)
import time
while True:
    time.sleep(300)  # Ping every 5 minutes
```

### **Optimiser la vitesse**
- Utilisez `torch.float16` pour les poids (2x plus rapide)
- Limitez `max_new_tokens` à 512 pour la génération
- Utilisez `do_sample=False` pour la génération déterministe

### **Sauvegarder les logs**
Le notebook sauvegarde automatiquement les logs dans `/content/inference_logs.json`



**Résultat attendu :**

```
======================================================================
🎉 SERVEUR PRÊT !
======================================================================

📋 CONFIGURATION À COPIER dans votre backend/.env :

AI_SERVICE_TYPE=colab
COLAB_API_URL=https://1234-56-78-90-12.ngrok-free.app
COLAB_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

======================================================================
```

### **Étape 4 : Configurer votre backend local**

Éditez `backend/.env` et ajoutez/modifiez ces lignes :

```bash
# Passer en mode Colab
AI_SERVICE_TYPE=colab

# URL ngrok de votre notebook Colab (CHANGEZ avec votre URL)
COLAB_API_URL=https://1234-56-78-90-12.ngrok-free.app

# Clé API générée par le notebook (CHANGEZ avec votre clé)
COLAB_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### **Étape 5 : Tester la connexion**

**Windows :**
```bash
cd backend
python test_colab_connection.py
```

**Ou double-cliquez sur :**
```
test_colab.bat
```

**Résultat attendu :**
```
✅ Connexion au serveur Colab réussie!
📊 Informations du serveur :
   Status: healthy
   Modèle: unsloth/Meta-Llama-3.1-8B-Instruct
   Device: cuda
   GPU: Tesla A100-SXM4-40GB

✅ Génération de texte fonctionnelle!
⏱️  Temps de génération : 0.87s
🔢 Tokens générés: 142
```

---

## 🚀 **Amélioration : Unsloth**

Le notebook utilise maintenant **Unsloth** au lieu de Transformers standard.

### **Avantages Unsloth :**

| Aspect | Transformers | Unsloth | Gain |
|--------|--------------|---------|------|
| **Vitesse** | 3-5s | 1-2s | **2-3x plus rapide** |
| **RAM GPU** | 12-16 GB | 4-6 GB | **75% économisée** |
| **Setup** | ~50 lignes | ~10 lignes | **5x moins de code** |
| **Fine-tuning** | Complexe | Simple | **Natif LoRA** |

### **GPU Recommandé :**

- **L4 (24 GB)** : `unsloth/Meta-Llama-3.1-8B-Instruct` (recommandé) ⭐
- **A100 (40 GB)** : `unsloth/Meta-Llama-3.1-8B-Instruct` (performances max) 🚀
- **T4 (16 GB)** : `unsloth/Llama-3.2-3B-Instruct` (auto-détecté) ⚡

Voir [UNSLOTH_BENEFITS.md](./UNSLOTH_BENEFITS.md) pour les détails complets.

---

## 📝 Configuration ngrok

**Première utilisation :**
1. Créez un compte sur [ngrok.com](https://dashboard.ngrok.com/signup)
2. Copiez votre authtoken
3. Collez-le dans la cellule 5 du notebook

**Sessions suivantes :**
- Le token est sauvegardé dans Colab
- Pas besoin de le resaisir (sauf si vous redémarrez le runtime)

**Limite gratuite :**
- 1 tunnel simultané
- 40 connexions/minute
- Suffisant pour 5-20 utilisateurs

**Upgrade ngrok (optionnel) :**
- Pro ($10/mois) : 3 tunnels, 120 conn/min
- Recommandé si > 20 utilisateurs

