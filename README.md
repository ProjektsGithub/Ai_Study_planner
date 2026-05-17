# 📚 AI Study Planner

> Intelligent web application for generating personalized weekly study schedules for university students

## 🎯 Overview

AI Study Planner is a full-stack web application that automatically generates personalized weekly study plans using a hybrid architecture combining a deterministic planning engine with local lightweight AI (Ollama + Phi-3 Mini).

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
| **AI Service** | Ollama + Phi-3 Mini |
| **Reverse Proxy** | Nginx |
| **Containerization** | Docker + Docker Compose |

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
- Ollama (for AI features)

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

### Ollama Setup (AI Service)

1. **Install Ollama**
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```

2. **Pull Phi-3 Mini model**
   ```bash
   ollama pull phi3
   ```

3. **Start Ollama service**
   ```bash
   ollama serve
   ```

   Ollama API will be available at: http://127.0.0.1:11434

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
