# 🏗️ OpportunityDetection - Architecture Overview

## 🎯 System Architecture Summary

The OpportunityDetection platform is built with a **React frontend** and **FastAPI backend** using **MCP (Model Context Protocol)** for AI agent orchestration.

### **Technology Stack Overview**

#### **Frontend (React 18 + Vite)**
- **Framework**: React 18.3.1 with functional components and hooks
- **Build Tool**: Vite 5.4.2 for fast development and building
- **Styling**: Tailwind CSS 3.4.1 for responsive design
- **Visualization**: Chart.js 4.5.0 & Recharts 3.1.2 for data charts
- **Maps**: React-Leaflet 5.0.0 for interactive geographic analysis
- **Animation**: Framer Motion 12.23.12 for smooth interactions
- **HTTP Client**: Axios 1.11.0 for API communication

#### **Backend (FastAPI + MCP)**
- **Framework**: FastAPI with Python 3.13.2
- **AI Orchestration**: MCP (Model Context Protocol) with 18 AI agents
- **AI Provider**: Google Generative AI (Gemini 1.5 Pro)
- **Database**: MongoDB for flexible data storage
- **Caching**: Redis for performance optimization
- **Server**: Uvicorn ASGI server

---

## 📊 High-Level System Architecture

```mermaid
graph TB
    subgraph "🖥️ Frontend (React + Vite)"
        UI[React Components]
        STATE[State Management]
        API_CLIENT[Axios API Client]
        CHARTS[Chart.js & Recharts]
        MAPS[React-Leaflet Maps]
    end
    
    subgraph "🌐 API Gateway"
        CORS[CORS Middleware]
        RATE[Rate Limiting]
        VALIDATOR[Request Validation]
    end
    
    subgraph "🚀 Backend (FastAPI)"
        FASTAPI[FastAPI Server]
        ROUTES[API Routes]
        STREAMING[WebSocket Streaming]
    end
    
    subgraph "🤖 AI System (MCP)"
        MCP[MCP Framework]
        ORCHESTRATOR[Agent Orchestrator]
        AGENTS[18 AI Agents]
        GEMINI[Google Gemini AI]
    end
    
    subgraph "💾 Data Layer"
        MONGO[(MongoDB)]
        REDIS[(Redis Cache)]
        FILES[File Storage]
    end
    
    subgraph "🌍 External APIs"
        LINKEDIN[LinkedIn API]
        NEWS[News APIs]
        MARKET[Market Data]
    end
    
    UI --> API_CLIENT
    API_CLIENT --> CORS
    CORS --> FASTAPI
    FASTAPI --> ROUTES
    ROUTES --> MCP
    MCP --> ORCHESTRATOR
    ORCHESTRATOR --> AGENTS
    AGENTS --> GEMINI
    AGENTS --> LINKEDIN
    AGENTS --> NEWS
    AGENTS --> MARKET
    FASTAPI --> MONGO
    FASTAPI --> REDIS
    STREAMING --> UI
```

---

## 🎭 Core Use Cases

```mermaid
graph LR
    subgraph "👥 Users"
        BU[Business User]
        ANALYST[Market Analyst]
        ADMIN[System Admin]
    end
    
    subgraph "📈 Business Use Cases"
        UC1[Analyze Market Opportunities]
        UC2[Generate Competitor Intelligence]
        UC3[Create Market Reports]
        UC4[Monitor Business Trends]
        UC5[Upload Business Data]
        UC6[View Interactive Dashboard]
    end
    
    subgraph "⚙️ System Use Cases"
        UC7[Process Real-time Data]
        UC8[Orchestrate AI Agents]
        UC9[Manage Data Storage]
        UC10[Handle Rate Limiting]
    end
    
    BU --> UC1
    BU --> UC5
    BU --> UC6
    
    ANALYST --> UC1
    ANALYST --> UC2
    ANALYST --> UC3
    ANALYST --> UC4
    
    ADMIN --> UC9
    
    UC1 --> UC8
    UC2 --> UC8
    UC3 --> UC7
    UC4 --> UC7
    UC8 --> UC10
```

---

## 🔄 Market Analysis Workflow

```mermaid
sequenceDiagram
    participant 👤 as User
    participant 🖥️ as React UI
    participant 🚀 as FastAPI
    participant 🤖 as MCP System
    participant 🧠 as AI Agents
    participant 🔮 as Gemini AI
    participant 💾 as MongoDB
    
    👤->>🖥️: Submit business analysis
    🖥️->>🚀: POST /api/v1/analysis
    🚀->>🤖: Initialize workflow
    
    🤖->>🧠: Activate Business Trends Agent
    🧠->>🔮: Analyze market trends
    🔮-->>🧠: Market insights
    🧠->>💾: Store trends data
    
    🤖->>🧠: Activate Competitor Agent
    🧠->>🔮: Analyze competitors
    🔮-->>🧠: Competitor intelligence
    🧠->>💾: Store competitor data
    
    🤖->>🧠: Activate News Processor
    🧠->>📡: Fetch market news
    📡-->>🧠: News data
    🧠->>🔮: Process relevance
    
    🤖->>🚀: Compile results
    🚀->>💾: Store final analysis
    🚀-->>🖥️: Return results
    🖥️-->>👤: Display insights
    
    Note over 👤,💾: Real-time streaming available
    🚀->>🖥️: Stream updates via WebSocket
```

---

## 🏛️ Core System Classes

### **Backend Architecture**

```mermaid
classDiagram
    class FastAPIApp {
        +app: FastAPI
        +setup_cors()
        +setup_routes()
        +startup_event()
    }
    
    class MCPFramework {
        +agent_registry: AgentRegistry
        +orchestrator: Orchestrator
        +discover_agents()
        +execute_workflow()
    }
    
    class BaseAgent {
        <<abstract>>
        +name: string
        +capabilities: List
        +execute(input: Dict)
        +validate_input()
    }
    
    class BusinessTrendsAgent {
        +gemini_client: GenerativeModel
        +analyze_trends()
        +identify_opportunities()
    }
    
    class CompetitorAgent {
        +web_scraper: WebScraper
        +analyze_competitors()
        +score_relevance()
    }
    
    class NewsProcessor {
        +news_apis: List[API]
        +fetch_news()
        +process_articles()
    }
    
    class DatabaseManager {
        +mongo_client: MongoClient
        +store_analysis()
        +retrieve_results()
    }
    
    FastAPIApp --> MCPFramework
    MCPFramework --> BaseAgent
    BaseAgent <|-- BusinessTrendsAgent
    BaseAgent <|-- CompetitorAgent
    BaseAgent <|-- NewsProcessor
    FastAPIApp --> DatabaseManager
```

### **Frontend Architecture**

```mermaid
classDiagram
    class App {
        +router: Router
        +globalState: State
        +apiClient: ApiClient
        +render()
    }
    
    class ApiClient {
        +baseURL: string
        +get(url: string)
        +post(url: string, data: object)
        +streamAnalysis(id: string)
    }
    
    class AnalysisPage {
        +formData: BusinessForm
        +analysisResult: AnalysisResult
        +handleSubmit()
        +connectWebSocket()
    }
    
    class BusinessForm {
        +sector: string
        +services: string[]
        +validate()
        +serialize()
    }
    
    class DashboardPage {
        +analytics: Analytics
        +recentAnalyses: AnalysisResult[]
        +loadDashboard()
    }
    
    class MapComponent {
        +mapInstance: LeafletMap
        +markers: Marker[]
        +initializeMap()
        +addMarkers()
    }
    
    class ChartComponent {
        +chartType: string
        +data: ChartData
        +renderChart()
    }
    
    App --> ApiClient
    App --> AnalysisPage
    AnalysisPage --> BusinessForm
    App --> DashboardPage
    DashboardPage --> MapComponent
    DashboardPage --> ChartComponent
```

---

## 🔧 Component Architecture

### **React Component Hierarchy**

```mermaid
graph TD
    subgraph "🏠 App Layer"
        APP[App.tsx]
        ROUTER[React Router]
        STATE[Global State]
    end
    
    subgraph "📄 Pages"
        HOME[HomePage]
        ANALYSIS[AnalysisPage]
        DASHBOARD[DashboardPage]
        REPORTS[ReportPage]
        RECOMMENDATIONS[RecommendationsPage]
    end
    
    subgraph "🎯 Feature Components"
        BUSINESS_FORM[BusinessForm]
        CHATBOT[Chatbot]
        MAP[MapComponent]
        CHARTS[ChartComponent]
        REPORT_VIEWER[ReportViewer]
    end
    
    subgraph "🎨 UI Components"
        BUTTON[Button]
        INPUT[Input]
        MODAL[Modal]
        LOADING[Loading]
        ERROR[ErrorBoundary]
    end
    
    subgraph "🔧 Utilities"
        API[ApiClient]
        HOOKS[Custom Hooks]
        UTILS[Utility Functions]
        TYPES[TypeScript Types]
    end
    
    APP --> ROUTER
    ROUTER --> HOME
    ROUTER --> ANALYSIS
    ROUTER --> DASHBOARD
    ROUTER --> REPORTS
    ROUTER --> RECOMMENDATIONS
    
    ANALYSIS --> BUSINESS_FORM
    ANALYSIS --> CHATBOT
    DASHBOARD --> CHARTS
    REPORTS --> MAP
    REPORTS --> REPORT_VIEWER
    
    BUSINESS_FORM --> BUTTON
    BUSINESS_FORM --> INPUT
    CHATBOT --> MODAL
    MAP --> LOADING
    CHARTS --> ERROR
    
    ALL_COMPONENTS -.-> API
    ALL_COMPONENTS -.-> HOOKS
    ALL_COMPONENTS -.-> UTILS
    ALL_COMPONENTS -.-> TYPES
```

### **Backend Service Structure**

```mermaid
graph TD
    subgraph "🌐 API Layer"
        FASTAPI[FastAPI App]
        ROUTES[Route Handlers]
        MIDDLEWARE[Middleware]
    end
    
    subgraph "📊 Business Logic"
        ANALYSIS_SVC[Analysis Service]
        REPORT_SVC[Report Service]
        DATA_SVC[Data Service]
        STREAM_SVC[Streaming Service]
    end
    
    subgraph "🤖 MCP Framework"
        MCP_SERVER[MCP Server]
        TOOL_REGISTRY[Tool Registry]
        AGENT_MGR[Agent Manager]
    end
    
    subgraph "🧠 AI Agents (18 total)"
        BUSINESS[Business Trends]
        COMPETITOR[Competitor Analysis]
        NEWS[News Processing]
        CHART[Chart Analysis]
        PDF[PDF Generation]
        MORE[... 13 more agents]
    end
    
    subgraph "💾 Data Access"
        MONGO[MongoDB Service]
        CACHE[Redis Cache]
        FILES[File Storage]
    end
    
    subgraph "🌍 External APIs"
        GEMINI[Google Gemini AI]
        LINKEDIN[LinkedIn API]
        NEWS_API[News APIs]
        SCRAPER[Web Scraper]
    end
    
    FASTAPI --> ROUTES
    ROUTES --> ANALYSIS_SVC
    ROUTES --> REPORT_SVC
    ROUTES --> DATA_SVC
    ROUTES --> STREAM_SVC
    
    ANALYSIS_SVC --> MCP_SERVER
    MCP_SERVER --> TOOL_REGISTRY
    TOOL_REGISTRY --> AGENT_MGR
    
    AGENT_MGR --> BUSINESS
    AGENT_MGR --> COMPETITOR
    AGENT_MGR --> NEWS
    AGENT_MGR --> CHART
    AGENT_MGR --> PDF
    AGENT_MGR --> MORE
    
    BUSINESS --> GEMINI
    COMPETITOR --> SCRAPER
    NEWS --> NEWS_API
    CHART --> GEMINI
    
    ALL_SERVICES --> MONGO
    ALL_SERVICES --> CACHE
    ALL_SERVICES --> FILES
```

---

## 📈 Data Flow Architecture

```mermaid
graph LR
    subgraph "📥 Input"
        USER[User Input]
        FILES[File Upload]
        API[API Requests]
    end
    
    subgraph "✅ Validation"
        VALIDATE[Input Validation]
        SCHEMA[Schema Validation]
        RULES[Business Rules]
    end
    
    subgraph "⚙️ Processing"
        MCP[MCP Orchestrator]
        AGENTS[AI Agent Pool]
        AI[AI Processing]
    end
    
    subgraph "🧠 Intelligence"
        GEMINI[Gemini AI]
        TRENDS[Trend Analysis]
        INTEL[Competitor Intel]
        NEWS_PROC[News Processing]
    end
    
    subgraph "💾 Storage"
        MONGO[MongoDB]
        REDIS[Redis Cache]
        FILE_STORE[File Storage]
    end
    
    subgraph "📤 Output"
        RESPONSE[API Response]
        STREAM[Real-time Stream]
        REPORTS[PDF Reports]
    end
    
    USER --> VALIDATE
    FILES --> SCHEMA
    API --> RULES
    
    VALIDATE --> MCP
    SCHEMA --> MCP
    RULES --> MCP
    
    MCP --> AGENTS
    AGENTS --> AI
    
    AI --> GEMINI
    AI --> TRENDS
    AI --> INTEL
    AI --> NEWS_PROC
    
    GEMINI --> MONGO
    TRENDS --> REDIS
    INTEL --> FILE_STORE
    
    MONGO --> RESPONSE
    REDIS --> STREAM
    FILE_STORE --> REPORTS
```

---

## 🔄 Real-time Streaming Architecture

```mermaid
sequenceDiagram
    participant 🖥️ as React Client
    participant 🔌 as WebSocket
    participant 🚀 as FastAPI
    participant 📡 as Stream Manager
    participant 🤖 as AI Agents
    
    🖥️->>🚀: Request analysis with streaming
    🚀->>📡: Initialize stream session
    🚀->>🔌: Establish WebSocket
    🔌-->>🖥️: Connection confirmed
    
    🚀->>🤖: Start analysis with callbacks
    
    loop Analysis Progress
        🤖->>📡: Progress update (20%, 40%, 60%...)
        📡->>🔌: Stream progress data
        🔌-->>🖥️: Real-time update
        🖥️->>🖥️: Update progress bar
    end
    
    🤖->>📡: Partial results available
    📡->>🔌: Stream partial insights
    🔌-->>🖥️: Incremental results
    
    🤖->>📡: Analysis complete
    📡->>🔌: Final comprehensive results
    🔌-->>🖥️: Complete analysis
    🖥️->>🖥️: Display final dashboard
    
    🔌->>🔌: Close connection
```

---

## 🚀 Deployment Architecture

```mermaid
graph TD
    subgraph "👥 Users"
        BROWSER[Web Browsers]
        MOBILE[Mobile Devices]
    end
    
    subgraph "🌐 Edge & CDN"
        CDN[Content Delivery Network]
        LOAD_BALANCER[Load Balancer]
    end
    
    subgraph "🏗️ Application Layer"
        REACT[React App (Vite)]
        NGINX[Nginx Reverse Proxy]
        FASTAPI_CLUSTER[FastAPI Cluster]
    end
    
    subgraph "🤖 AI Services"
        MCP_SERVICES[MCP Services]
        AGENT_POOL[AI Agent Pool]
        GEMINI_API[Google Gemini API]
    end
    
    subgraph "💾 Data Layer"
        MONGODB_CLUSTER[MongoDB Cluster]
        REDIS_CLUSTER[Redis Cluster]
        OBJECT_STORAGE[Object Storage]
    end
    
    subgraph "📊 Monitoring"
        LOGS[Centralized Logging]
        METRICS[Performance Metrics]
        ALERTS[Alert System]
    end
    
    BROWSER --> CDN
    MOBILE --> CDN
    CDN --> LOAD_BALANCER
    LOAD_BALANCER --> NGINX
    NGINX --> REACT
    NGINX --> FASTAPI_CLUSTER
    
    FASTAPI_CLUSTER --> MCP_SERVICES
    MCP_SERVICES --> AGENT_POOL
    AGENT_POOL --> GEMINI_API
    
    FASTAPI_CLUSTER --> MONGODB_CLUSTER
    FASTAPI_CLUSTER --> REDIS_CLUSTER
    FASTAPI_CLUSTER --> OBJECT_STORAGE
    
    ALL_SERVICES --> LOGS
    ALL_SERVICES --> METRICS
    METRICS --> ALERTS
```

---

## 🔧 Key Technical Features

### **Frontend Capabilities**
- ⚡ **Fast Development**: Vite for instant hot reload and fast builds
- 🎨 **Modern UI**: Tailwind CSS with responsive design principles
- 📊 **Rich Visualizations**: Interactive charts with Chart.js and Recharts
- 🗺️ **Geographic Analysis**: Leaflet maps with custom markers and clusters
- 🌊 **Smooth Animations**: Framer Motion for engaging user interactions
- 📱 **Mobile Responsive**: Works seamlessly across all device sizes

### **Backend Capabilities**
- 🚀 **High Performance**: FastAPI with async/await for concurrent processing
- 🤖 **AI Orchestration**: MCP framework managing 18 specialized AI agents
- 🧠 **Advanced AI**: Google Gemini 1.5 Pro for sophisticated analysis
- 💾 **Flexible Storage**: MongoDB for complex data structures
- ⚡ **Fast Caching**: Redis for sub-millisecond data access
- 📡 **Real-time Streaming**: WebSocket support for live updates

### **AI Agent Capabilities**
1. **Business Trends Agent** - Market trend identification and analysis
2. **Competitor Agent** - Comprehensive competitor intelligence
3. **News Processor** - Real-time news analysis and sentiment
4. **Chart Analysis Agent** - Automated chart generation and insights
5. **LinkedIn Scraper** - Professional network data extraction
6. **Market Analyzer** - Comprehensive market assessment
7. **PDF Generator** - Professional report creation
8. **Summarization Agent** - Content summarization and key insights
9. **Trend Identification** - Pattern recognition in market data
10. **Working Space Manager** - Workflow and task coordination
11. **Info Extractor** - Data extraction from various sources
12. **Keywording Agent** - SEO and keyword analysis
13. **Top Competitors** - Competitive landscape mapping
14. **Dynamic Chart Generator** - Interactive visualization creation
15. **CSV Reader** - Data processing and analysis
16. **Gemini API Manager** - AI model interaction optimization
17. **Analyze Data Agent** - Statistical analysis and insights
18. **Multi-Agent Coordinator** - Agent workflow orchestration

---

## 📊 Performance Metrics

### **Response Time Targets**
- **API Endpoints**: < 200ms average response time
- **Analysis Processing**: 30-120 seconds for complete market analysis
- **Real-time Updates**: < 100ms WebSocket latency
- **Database Queries**: < 50ms average query execution
- **File Uploads**: Support up to 100MB with progress tracking

### **Scalability Targets**
- **Concurrent Users**: 1,000+ simultaneous active users
- **Daily Analyses**: 10,000+ market analyses per day
- **Data Processing**: 1TB+ of market data processed monthly
- **API Requests**: 1M+ API requests per day
- **Storage Growth**: Scalable to petabytes of historical data

### **Availability Targets**
- **Uptime**: 99.9% availability (8.77 hours downtime/year)
- **Error Rate**: < 0.1% error rate for API requests
- **Recovery Time**: < 5 minutes for service restoration
- **Backup Recovery**: < 1 hour for complete data restoration

---

This architecture overview provides a comprehensive yet accessible view of the OpportunityDetection platform's technical foundation, emphasizing the React frontend and FastAPI backend with MCP-based AI agent orchestration.
