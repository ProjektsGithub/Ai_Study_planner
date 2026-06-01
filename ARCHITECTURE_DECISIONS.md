# Décisions d'Architecture - AI Study Planner

## 📅 Historique des Décisions

### **[2026-05-17] Choix du Modèle AI : Llama + LoRA sur Google Colab**

#### **Décision**
Utiliser **Llama 3.2 + LoRA** hébergé sur **Google Colab** au lieu de Phi-3 Mini local via Ollama.

#### **Contexte**
- Client souhaite une solution IA personnalisable et performante
- Budget initial limité pour infrastructure dédiée
- Besoin de flexibilité pour tester et itérer rapidement

#### **Options Considérées**

| Option | Avantages | Inconvénients | Coût |
|--------|-----------|---------------|------|
| **Phi-3 Mini (Ollama local)** | Simple, gratuit | Performance limitée, pas de LoRA | 0€ |
| **Llama + LoRA (VPS dédié)** | Performance max, contrôle total | Coût élevé, maintenance | 200-500€/mois |
| **Llama + LoRA (Google Colab)** ✅ | Bon compromis, GPU gratuit/abordable | Sessions limitées | 0-50€/mois |

#### **Choix Final : Google Colab Pro**
- **Coût** : 10€/mois (Colab Pro)
- **GPU** : NVIDIA T4/A100
- **RAM** : 32 GB
- **Durée session** : 24h max
- **Setup** : Immédiat

#### **Implications Techniques**

1. **Backend (FastAPI)**
   - Connexion via API REST au notebook Colab
   - Utilisation de ngrok pour exposer Colab
   - Gestion des timeouts et reconnexions
   - Fallback sur modèle local si Colab indisponible

2. **Configuration**
   ```env
   # .env
   AI_SERVICE_TYPE=colab  # ou "ollama" pour fallback
   COLAB_API_URL=https://xxxx.ngrok.io
   COLAB_API_KEY=your-secret-key
   OLLAMA_BASE_URL=http://127.0.0.1:11434  # fallback
   ```

3. **Notebooks à créer**
   - `notebooks/train_lora_study_planner.ipynb` - Entraînement LoRA
   - `notebooks/llama_lora_inference_server.ipynb` - Serveur d'inférence

4. **Adaptateurs LoRA prévus**
   - `study-planning-general-v1` - Adaptateur général
   - `study-planning-cs-v1` - Informatique
   - `study-planning-med-v1` - Médecine
   - `study-planning-law-v1` - Droit

#### **Plan de Migration Future**

**Phase 1 (Mois 1-3) : Google Colab**
- Développement et tests
- Collecte de données pour LoRA
- Validation du concept

**Phase 2 (Mois 4-6) : Évaluation**
- Si < 50 utilisateurs : Rester sur Colab
- Si > 50 utilisateurs : Migrer vers VPS dédié

**Phase 3 (Mois 6+) : Production**
- VPS dédié si volume justifie
- Ou Colab Pro+ (50€/mois) si suffisant

#### **Risques Identifiés**

| Risque | Impact | Mitigation |
|--------|--------|------------|
| Session Colab expire | Moyen | Auto-reconnexion + fallback Ollama |
| Limite GPU gratuite | Faible | Colab Pro (10€/mois) |
| Latence réseau | Faible | Cache + optimisation prompts |
| Dépendance externe | Moyen | Fallback sur Ollama local |

#### **Métriques de Succès**

- ✅ Temps de génération < 5 secondes
- ✅ Disponibilité > 95%
- ✅ Coût < 50€/mois
- ✅ Qualité plannings > 80% satisfaction

#### **Références**
- [LLAMA_LORA_PROPOSAL.md](./LLAMA_LORA_PROPOSAL.md) - Analyse détaillée
- [GOOGLE_COLAB_SETUP.md](./GOOGLE_COLAB_SETUP.md) - Guide de configuration

---

## 📝 Autres Décisions Importantes

### **[2026-05-17] Base de Données : PostgreSQL**
- ✅ PostgreSQL 17 via Laragon
- ✅ Utilisateur : `user` (sans mot de passe en dev)
- ✅ Driver : psycopg3 (meilleur support Windows)

### **[2026-05-17] Authentification : JWT**
- ✅ Access token : 15 minutes
- ✅ Refresh token : 7 jours
- ✅ Algorithme : HS256
- ✅ Sécurité : bcrypt pour mots de passe

### **[2026-05-17] Serveur Backend**
- ✅ FastAPI sur http://localhost:8000
- ✅ Mode reload activé pour développement
- ✅ CORS configuré pour frontend

---

## 🔄 Prochaines Décisions à Prendre

- [ ] Choix du framework frontend (React confirmé ?)
- [ ] Stratégie de déploiement production
- [ ] Système de monitoring et logs
- [ ] Stratégie de backup base de données
- [ ] Gestion des versions LoRA

---

**Dernière mise à jour** : 17 Mai 2026  
**Maintenu par** : Équipe de développement
