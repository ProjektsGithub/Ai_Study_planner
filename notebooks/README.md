# 📓 Notebooks Google Colab

Ce dossier contient les notebooks Jupyter pour utiliser Google Colab avec le projet AI Study Planner.

---

## 📂 Fichiers

### **`colab_inference_server.ipynb`** ⭐
Serveur d'inférence pour Llama 3.2 avec API REST.

**Fonctionnalités :**
- ✅ Chargement automatique de Llama 3.2 (3B ou 8B)
- ✅ API REST Flask avec authentification
- ✅ Exposition via ngrok (tunnel HTTPS)
- ✅ Génération de clé API sécurisée
- ✅ Monitoring en temps réel
- ✅ Support GPU (T4, A100)

**Comment l'utiliser :**
1. Ouvrez le notebook dans Google Colab
2. Runtime → Change runtime type → T4 GPU
3. Runtime → Run all
4. Copiez l'URL ngrok et la clé API
5. Configurez votre backend local (.env)

**Temps d'exécution :** ~3-5 minutes

---

### **`train_lora_study_planner.ipynb`** (À venir)
Notebook pour entraîner un adaptateur LoRA spécialisé dans la génération de plans d'étude.

**Fonctionnalités prévues :**
- 🔄 Fine-tuning avec LoRA (Low-Rank Adaptation)
- 🔄 Dataset personnalisé de plans d'étude
- 🔄 Optimisation pour la génération JSON
- 🔄 Export de l'adaptateur LoRA

---

## 🚀 Démarrage Rapide

### **Option 1 : Depuis Google Drive (Recommandé)**

1. Ouvrez [Google Drive](https://drive.google.com/)
2. Créez un dossier `AI_Study_Planner`
3. Uploadez `colab_inference_server.ipynb`
4. Clic droit → Open with → Google Colaboratory
5. Suivez les instructions du notebook

### **Option 2 : Upload direct**

1. Allez sur [colab.research.google.com](https://colab.research.google.com/)
2. File → Upload notebook
3. Sélectionnez `colab_inference_server.ipynb`
4. Suivez les instructions du notebook

---

## 📊 Performances

### **Colab Free (GPU T4)**
- Temps de chargement : ~2-3 min
- Génération (100 tokens) : ~3-5s
- Durée de session : ~12h
- **Prix : 0€**

### **Colab Pro (GPU T4/A100)**
- Temps de chargement : ~1-2 min
- Génération (100 tokens) : ~1-3s
- Durée de session : ~24h
- **Prix : 10€/mois**

### **Colab Pro+ (GPU A100)**
- Temps de chargement : ~1 min
- Génération (100 tokens) : ~0.5-1s
- Durée de session : ~24h
- **Prix : 50€/mois**

---

## 🔧 Configuration

### **Variables d'environnement (backend/.env)**

Après avoir exécuté le notebook, configurez votre backend :

```bash
# Mode Colab activé
AI_SERVICE_TYPE=colab

# URL ngrok (copiée depuis le notebook)
COLAB_API_URL=https://xxxx-xx-xx-xx-xx.ngrok-free.app

# Clé API (copiée depuis le notebook)
COLAB_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### **Test de connexion**

```bash
cd backend
python test_colab_connection.py
```

---

## 📚 Documentation

- [Guide de Démarrage Rapide](../QUICK_START_COLAB.md) - 10 minutes pour tout configurer
- [Documentation Complète](../GOOGLE_COLAB_SETUP.md) - Tous les détails techniques
- [AI Service](../backend/app/services/ai_service.py) - Code source du client

---

## 🔒 Sécurité

### **Clés API**
- Générées automatiquement par le notebook
- Format : `sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` (48 caractères)
- **Ne jamais commit dans Git !** (déjà dans `.gitignore`)

### **Ngrok**
- Tunnel HTTPS sécurisé (SSL/TLS)
- URL aléatoire générée à chaque session
- Gratuit pour usage basique (40 requêtes/minute)
- Pour production : Compte ngrok payant recommandé

---

## 🆘 Dépannage

### **"Runtime disconnected"**
→ Session Colab expirée. Relancez le notebook (Runtime → Run all)

### **"No GPU available"**
→ Runtime → Change runtime type → T4 GPU → Save

### **"ngrok tunnel not created"**
→ Attendez 30 secondes. Le tunnel prend du temps à démarrer.

### **"Model download failed"**
→ Vérifiez votre connexion Internet. Le modèle fait ~3-6 GB.

### **"Out of memory"**
→ Utilisez un modèle plus petit (Llama 3.2 3B au lieu de 8B)

---

## 🎯 Roadmap

- [x] Serveur d'inférence de base
- [ ] Support LoRA
- [ ] Dataset d'entraînement
- [ ] Notebook d'entraînement LoRA
- [ ] Optimisation des prompts
- [ ] Batch processing
- [ ] Cache de génération

---

## 💡 Conseils

### **Garder la session active**
Colab peut se déconnecter si inactif. Consultez le notebook régulièrement.

### **Optimiser la vitesse**
- Utilisez `Llama 3.2 3B` pour Colab Free (2x plus rapide)
- Utilisez `Llama 3.1 8B` pour Colab Pro (meilleure qualité)
- Limitez `max_tokens` à 512 pour les réponses courtes

### **Monitoring**
Le notebook affiche en temps réel :
- Nombre de requêtes
- Temps de génération moyen
- Utilisation GPU/RAM

### **Backup**
Sauvegardez vos notebooks sur Google Drive pour ne pas les perdre.

---

## 📞 Support

Consultez la documentation complète dans [GOOGLE_COLAB_SETUP.md](../GOOGLE_COLAB_SETUP.md)
