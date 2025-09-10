# 🚀 OpportunityDetection Platform

## Overview

The OpportunityDetection platform is a modern web application that helps businesses identify market opportunities through AI-powered analysis. The platform consists of a Next.js frontend and a FastAPI backend with MCP (Model Context Protocol) architecture.

## 🏗️ Architecture

- **Frontend**: React 18, TypeScript
- **Backend**: FastAPI with MCP-based agent system
- **Database**: MongoDB for data persistence
- **AI Integration**: Ollama with llama3:8b for local intelligent analysis
- **Deployment**: Production-ready with comprehensive dependency management

## 📋 Prerequisites

Before setting up the project, ensure you have the following installed:

- **Python 3.13.2** (recommended)
- **Node.js 18+** and **npm/yarn**
- **MongoDB** (local or cloud instance)
- **Git** for version control

### Required API Keys

1. **Ollama Local LLM**
   - Install Ollama from [ollama.ai](https://ollama.ai)
   - Pull the llama3:8b model: `ollama pull llama3:8b`
   - Create a new API key
   - Keep it secure for environment configuration

2. **MongoDB Connection String**
   - Local MongoDB: `mongodb://localhost:27017/opportunity_detection`
   - Or use MongoDB Atlas for cloud deployment

## 🛠️ Setup Instructions

### 1. Clone and Setup Project Structure

```bash
# Clone the repository (if using git)
git clone <your-repository-url>
cd <project-directory>

# Or navigate to your existing project directory
cd /path/to/your/project
```

### 2. Backend Setup (FastAPI + MCP)

#### Step 2.1: Navigate to Backend Directory
```bash
cd OpportunityDetection\backend
```

#### Step 2.2: Create and Activate Virtual Environment
```bash
# Create virtual environment
python -m venv ../opportunityDetection

# Activate virtual environment (Windows)
../opportunityDtection/Scripts/Activate.ps1

# On macOS/Linux:
source ../opportunityDtection/bin/activate
```

#### Step 2.3: Install Dependencies
```bash
# Install all required packages using UV (recommended)
uv pip install -r requirements.txt

# Alternative: Use pip if UV is not available
pip install -r requirements.txt
```

#### Step 2.4: Environment Configuration
Create a `.env` file in the backend directory:

```bash
# Create .env file
touch .env
# On Windows: 
New-Item -Path ".env" -ItemType File
```

Add the following configuration to `.env`:

```env
# API Keys
# Ollama Configuration (no API key needed for local deployment)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL llama3:8b

# Database Configuration
MONGODB_URL=mongodb://localhost:27017/opportunity_detection
DATABASE_NAME=opportunity_detection

# Server Configuration
HOST=localhost
PORT=8000
DEBUG=True

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"]
ALLOW_CREDENTIALS=False

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Logging
LOG_LEVEL=INFO
```

#### Step 2.5: Database Setup
Ensure MongoDB is running:

```bash
# If using local MongoDB, start the service
# Windows (if MongoDB is installed as service):
net start MongoDB

# macOS (using brew):
brew services start mongodb/brew/mongodb-community

# Linux (systemd):
sudo systemctl start mongod
```

#### Step 2.6: Start Backend Server
```bash
# Start the FastAPI server
python main.py

# Alternative: Use uvicorn directly
uvicorn main:app --host localhost --port 8000 --reload
```

The backend will be available at: **http://localhost:8000**

### 3. Frontend Setup (React.js)

#### Using frontend (Vite + React)

```bash
# Navigate to Talan frontend
cd ../OpportunityDetection/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at: **http://localhost:5173**

Add to `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_ENV=development
```

```bash
# Start development server
npm run dev
```

Frontend will be available at: **http://localhost:3000**

## 🔧 Development Workflow

### Starting Both Services

1. **Terminal 1 - Backend**:
```bash
cd OpportunityDetection/backend
../opportunityDtection/Scripts/Activate.ps1  # Windows
# source ../opportunityDtection/bin/activate   # macOS/Linux
python main.py
```

2. **Terminal 2 - Frontend** (choose one):
```bash
# For Talan-Front-main (Vite + React)
cd OpportunityDetection/Talan-Front-main
npm run dev

# OR for opportuna-nextjs (Next.js 14)
cd OpportunityDetection/opportuna-nextjs
npm run dev
```

### Accessing the Application

- **Frontend (Talan)**: http://localhost:5173
- **Frontend (React.js)**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Interactive API Explorer**: http://localhost:8000/redoc

## 📚 Key Features

### Backend Features (FastAPI + MCP)

- **18 AI Agents**: Converted to MCP tools for modular analysis
- **Multi-Agent Orchestration**: Coordinated market analysis workflows
- **Local AI Integration**: Advanced AI capabilities with Ollama (Qwen2.5:3b)
- **MongoDB Integration**: Robust data persistence and retrieval
- **Rate Limiting**: API quota management and optimization
- **Real-time Streaming**: WebSocket support for live updates
- **Comprehensive Error Handling**: Robust error recovery and logging

### Frontend Features

#### Talan-Front-main (Vite + React)
- **React 18** with modern hooks and context
- **Vite** for fast development and building
- **Tailwind CSS** for responsive design
- **Chart.js & Recharts** for data visualization
- **Leaflet Maps** for geographic analysis

#### opportuna-nextjs (Next.js 14)
- **Next.js 14** with App Router
- **Server-Side Rendering (SSR)** and Static Site Generation (SSG)
- **Advanced SEO** with metadata and sitemap generation
- **Enhanced Performance** with optimizations
- **Modern TypeScript** with strict type checking

## 🔍 API Endpoints

### Core Endpoints
- `GET /api/v1/health` - Health check
- `POST /api/v1/analysis` - Start market analysis
- `GET /api/v1/opportunities` - List opportunities
- `GET /api/v1/competitors` - Competitor analysis
- `POST /api/v1/upload` - File upload for analysis

### Streaming Endpoints
- `GET /api/v1/stream/analysis/{id}` - Real-time analysis updates
- `GET /api/v1/stream/report/{id}` - Streaming report generation

### Agent Tools (MCP)
- Business Trends Analysis
- Competitor Intelligence
- Market Research
- News Processing
- PDF Generation
- Chart Analysis
- LinkedIn Scraping
- And 11 more specialized tools
