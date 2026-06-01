# Configuration Google Colab pour Llama + LoRA

## 🎯 Architecture avec Google Colab

```
┌─────────────────┐      API REST      ┌──────────────────┐
│   Frontend      │ ◄─────────────────► │   Backend        │
│   (React)       │                     │   (FastAPI)      │
└─────────────────┘                     └──────────────────┘
                                               │
                                               │ HTTP/ngrok
                                               ▼
                                        ┌──────────────────┐
                                        │  Google Colab    │
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

## 📦 Notebooks Colab à Créer

### **1. Notebook : Entraînement LoRA**
`notebooks/train_lora_study_planner.ipynb`

### **2. Notebook : Serveur d'Inférence**
`notebooks/llama_lora_inference_server.ipynb`

---

## 🚀 Étape 1 : Créer le Notebook d'Entraînement LoRA

