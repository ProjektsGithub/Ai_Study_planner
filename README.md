# 📚 AI Study Planner

> Intelligent web application for generating personalized weekly study schedules for university students

## 🎯 Overview

AI Study Planner is a full-stack web application that automatically generates personalized weekly study plans using a hybrid architecture combining a deterministic planning engine with AI (Llama 3.2 + LoRA fine-tuning).

### Key Features

- **Automated Planning**: Generate balanced weekly study schedules based on your academic profile
- **Smart Prioritization**: AI-powered scheduling considering exam dates, subject difficulty, and priorities
- **Manual Editing**: Modify generated plans to fit your personal preferences
- **Plan History**: Track and restore previous planning versions
- **PDF Export**: Download printable versions of your study plans
- **Notifications**: Receive reminders for upcoming study sessions

## 🏗️ Architecture

### Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React + TailwindCSS + Axios |
| **Backend** | FastAPI + Python 3.11+ |
| **Database** | PostgreSQL 15+ |
| **AI Service** | Llama 3.2 + LoRA (Google Colab) / Ollama (local fallback) |
| **Reverse Proxy** | Nginx |
| **Containerization** | Docker + Docker Compose |

### AI Architecture

The application uses a **hybrid AI approach** for optimal cost-effectiveness:

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Deterministic Planning Engine                │  │
│  │  • Constructs valid time slots                       │  │
│  │  • Calculates subject priorities                     │  │
│  │  • Validates constraints                             │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              AI Service (Adaptive)                   │  │
│  │                                                       │  │
│  │  Primary: Google Colab (Llama 3.2 + LoRA)          │  │
│  │  • Cost: 0-50€/month                                │  │
│  │  • Fine-tuned for study planning                    │  │
│  │  • Accessible via ngrok tunnel                      │  │
│  │                                                       │  │
│  │  Fallback: Local Ollama (Llama 3.2)                │  │
│  │  • Used when Colab unavailable                      │  │
│  │  • Development environment                          │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            Validation Service                        │  │
│  │  • Schema validation                                 │  │
│  │  • Constraint checking                               │  │
│  │  • Auto-correction                                   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Why Llama 3.2 + LoRA on Google Colab?**
- **Cost-effective**: 0-50€/month vs 200-500€/month for VPS
- **Scalable**: Handles up to ~50 users before needing migration
- **Fine-tunable**: LoRA adapters for domain-specific optimization
- **Flexible**: Easy migration to VPS when user base grows

See [ARCHITECTURE_DECISIONS.md](./ARCHITECTURE_DECISIONS.md) and [GOOGLE_COLAB_SETUP.md](./GOOGLE_COLAB_SETUP.md) for details.

### Project Structure

```
AIplaning/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/v1/         # API endpoints
│   │   ├── core/           # Core configuration
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   ├── tests/          # Test suite
│   │   └── main.py         # Application entry point
│   ├── requirements.txt    # Python dependencies
│   └── .env.example        # Environment variables template
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── api/            # API client
│   │   └── main.jsx        # Application entry point
│   ├── package.json        # Node dependencies
│   └── .env.example        # Environment variables template
└── README.md               # This file
```

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Google Colab account (for AI features) OR Ollama (local fallback)

### Backend Setup

1. **Create virtual environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

5. **Start development server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   Backend will be available at: http://localhost:8000
   API documentation: http://localhost:8000/api/docs

### Frontend Setup

1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

   Frontend will be available at: http://localhost:5173

### AI Service Setup

The application supports two AI service configurations:

#### Option 1: Google Colab + Llama 3.2 + LoRA (Recommended for Production)

This is the cost-effective production solution (0-50€/month).

1. **Set up Google Colab notebook**
   - See [GOOGLE_COLAB_SETUP.md](./GOOGLE_COLAB_SETUP.md) for detailed instructions
   - Configure Llama 3.2 with LoRA adapter
   - Set up ngrok tunnel for external access

2. **Configure backend**
   ```bash
   # In backend/.env
   AI_SERVICE_TYPE=colab
   AI_SERVICE_URL=https://your-ngrok-url.ngrok.io
   AI_MODEL_NAME=llama3.2
   AI_LORA_ADAPTER=study-planning-v1
   ```

3. **Start Colab notebook**
   - Run all cells in the notebook
   - Copy the ngrok URL to your `.env` file
   - Keep the notebook running while using the application

**Cost Estimate:**
- Free tier: Limited GPU hours
- Colab Pro: ~10€/month for extended GPU access
- Scales to ~50 users before needing VPS migration

#### Option 2: Local Ollama (Development/Fallback)

For local development or as a fallback when Colab is unavailable.

1. **Install Ollama**
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```

2. **Pull Llama 3.2 model**
   ```bash
   ollama pull llama3.2
   ```

3. **Start Ollama service**
   ```bash
   ollama serve
   ```

4. **Configure backend**
   ```bash
   # In backend/.env
   AI_SERVICE_TYPE=ollama
   AI_SERVICE_URL=http://127.0.0.1:11434
   AI_MODEL_NAME=llama3.2
   ```

   Ollama API will be available at: http://127.0.0.1:11434

**Note:** The backend automatically falls back to Ollama if the Colab service is unavailable.

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest
```

### Frontend Tests

```bash
cd frontend
npm test
```

## 🔧 Development

### Code Formatting

**Backend (Python)**
```bash
cd backend
black app/
isort app/
flake8 app/
```

**Frontend (JavaScript)**
```bash
cd frontend
npm run lint
npm run format
```

### Database Migrations

**Create new migration**
```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
```

**Apply migrations**
```bash
alembic upgrade head
```

**Rollback migration**
```bash
alembic downgrade -1
```

## 📦 Deployment

### Docker Deployment

1. **Build and start services**
   ```bash
   docker-compose up -d
   ```

2. **View logs**
   ```bash
   docker-compose logs -f
   ```

3. **Stop services**
   ```bash
   docker-compose down
   ```

### Production Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed production deployment instructions.

## 📝 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is part of an academic Bachelor/Master program.

## 👥 Team

- Backend Development: Python/FastAPI
- Frontend Development: React/TypeScript
- DevOps: Docker/Nginx

## 📞 Support

For questions or issues, please open an issue on GitHub.

---

**Version**: 1.0.0  
**Last Updated**: May 2026
