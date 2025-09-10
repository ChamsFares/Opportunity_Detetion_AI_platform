# OpporTuna - Frontend Application

🎨 **Frontend** for the OpporTuna AI-powered market opportunity detection platform. Built with React, TypeScript, and Vite for a modern, responsive user experience.

## 🎯 Overview

The frontend provides an intuitive interface for:

- **Interactive Dashboard**: Real-time market analysis visualization
- **Market Analysis Forms**: Easy-to-use forms for business input
- **Dynamic Charts**: Interactive data visualization with Chart.js
- **Real-time Chat**: AI-powered chatbot for insights
- **Report Viewer**: PDF and interactive report viewing
- **Responsive Design**: Mobile-first design approach

## 🏗️ Project Structure

```
src/
├── components/              # Reusable React components
│   ├── ApiDebug.tsx        # API debugging component
│   ├── BusinessForm.tsx    # Business information form
│   ├── Chatbot.tsx         # AI chatbot interface
│   ├── Header.tsx          # Application header
│   ├── MapComponent.tsx    # Interactive map visualization
│   ├── RecommendationsComponent.tsx  # Strategic recommendations
│   └── ...
├── pages/                  # Page components
│   ├── DashboardPage.tsx   # Main dashboard
│   ├── AnalysisPage.tsx    # Analysis results page
│   └── ...
├── api/                    # API client functions
│   ├── dynamicChart.ts     # Chart API integration
│   └── ...
├── services/               # Frontend services
│   └── ...
├── styles/                 # CSS and styling
├── utils/                  # Utility functions
└── types/                  # TypeScript type definitions
```

## 🚀 Quick Start

### Prerequisites

- **Node.js 16+**
- **npm** or **yarn**

### Installation

1. **Navigate to frontend directory**
   ```bash
   cd Talan-Front-main
   ```

2. **Install dependencies**
   ```bash
   npm install
   # or
   yarn install
   ```

3. **Environment Configuration**
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your configuration
   ```

4. **Start development server**
   ```bash
   npm run dev
   # or
   yarn dev
   ```

The application will be available at `http://localhost:5173`

## 🔑 Environment Variables

Create a `.env.local` file with the following configuration:

```env
# Backend API Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_API_TIMEOUT=30000

# Application Configuration
VITE_APP_NAME=OpporTuna
VITE_APP_VERSION=1.0.0
VITE_DEBUG=true

# Optional Services
VITE_MAP_API_KEY=your_map_api_key_here
VITE_ANALYTICS_ID=your_analytics_id_here
```

## 🧩 Key Components

### 1. Dashboard (`DashboardPage.tsx`)
- **Purpose**: Main application dashboard with overview metrics
- **Features**: Real-time updates, interactive charts, key insights
- **Data Sources**: Market analysis results, trend data, competitor insights

### 2. Business Form (`BusinessForm.tsx`)
- **Purpose**: Input form for business information and analysis parameters
- **Features**: Form validation, dynamic fields, progress tracking
- **Integration**: Connects to backend market analysis API

### 3. Chatbot (`Chatbot.tsx`)
- **Purpose**: AI-powered conversational interface
- **Features**: Natural language queries, contextual responses, session management
- **Backend**: Real-time communication with AI agents

### 4. Dynamic Charts (Chart Components)
- **Purpose**: Interactive data visualization
- **Features**: Multiple chart types, responsive design, real-time updates
- **Library**: Chart.js with React integration

### 5. Map Component (`MapComponent.tsx`)
- **Purpose**: Geographic data visualization
- **Features**: Interactive maps, custom markers, data overlays
- **Library**: Leaflet with React integration

### 6. Recommendations (`RecommendationsComponent.tsx`)
- **Purpose**: Display strategic recommendations and insights
- **Features**: Prioritized recommendations, implementation guides, impact metrics
- **Data**: AI-generated strategic insights

## 🎨 Styling & Design

### Tailwind CSS
- **Utility-first CSS framework**
- **Responsive design out of the box**
- **Custom color palette and components**
- **Dark mode support**

### Design System
- **Consistent spacing and typography**
- **Reusable component patterns**
- **Accessible design principles**
- **Mobile-first approach**

## 📡 API Integration

### HTTP Client Configuration
```typescript
// api/client.ts
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: parseInt(import.meta.env.VITE_API_TIMEOUT) || 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});
```

### API Endpoints Integration

#### Market Analysis
```typescript
// api/analysis.ts
export const analyzeMarket = async (data: MarketAnalysisInput) => {
  const response = await apiClient.post('/analyze-market', data);
  return response.data;
};
```

#### Dynamic Charts
```typescript
// api/dynamicChart.ts
export const generateChart = async (prompt: string, sessionId: string) => {
  const response = await apiClient.post('/dynamic-chart', {
    prompt,
    session_id: sessionId
  });
  return response.data;
};
```

#### Real-time Updates
```typescript
// services/websocket.ts
const wsUrl = API_BASE_URL.replace('http', 'ws') + '/ws';
const socket = new WebSocket(wsUrl);

socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Handle real-time updates
};
```

## 🔧 Development Tools

### Build System
- **Vite**: Fast build tool and dev server
- **TypeScript**: Type safety and enhanced development experience
- **ESLint**: Code linting and style enforcement
- **Prettier**: Code formatting

### Testing
```bash
# Run unit tests
npm run test

# Run tests with coverage
npm run test:coverage

# Run e2e tests
npm run test:e2e
```

### Build & Deployment
```bash
# Build for production
npm run build

# Preview production build
npm run preview

# Type checking
npm run type-check

# Linting
npm run lint
```

## 📱 Responsive Design

### Breakpoints
- **sm**: 640px and up (mobile)
- **md**: 768px and up (tablet)
- **lg**: 1024px and up (desktop)
- **xl**: 1280px and up (large desktop)

### Mobile Optimization
- Touch-friendly interface elements
- Optimized images and assets
- Progressive loading for better performance
- Offline capabilities where applicable

## 🔒 Security

### Input Validation
- Client-side validation for all forms
- XSS protection through React's built-in escaping
- CSRF protection for API calls

### Environment Security
- No sensitive data in client-side code
- Environment variables for configuration
- Secure API communication (HTTPS in production)

## 🚀 Performance Optimization

### Code Splitting
```typescript
// Lazy loading components
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const AnalysisPage = lazy(() => import('./pages/AnalysisPage'));
```

### Asset Optimization
- Image optimization and lazy loading
- Tree shaking for unused code elimination
- Bundle size monitoring
- CDN integration for static assets

### Caching Strategy
- Browser caching for static assets
- API response caching where appropriate
- Service worker for offline functionality

## 🧪 Testing Strategy

### Unit Testing
- Component testing with React Testing Library
- Service function testing
- Custom hook testing

### Integration Testing
- API integration testing
- User workflow testing
- Cross-browser compatibility testing

### E2E Testing
- Critical user journey testing
- Performance testing
- Accessibility testing

## 📊 Analytics & Monitoring

### Performance Monitoring
- Core Web Vitals tracking
- Bundle size monitoring
- Error tracking and reporting

### User Analytics
- User interaction tracking
- Feature usage analytics
- Performance metrics

## 🛠️ Development Guidelines

### Code Style
- Use TypeScript for type safety
- Follow React best practices
- Implement proper error boundaries
- Use custom hooks for reusable logic

### Component Design
- Keep components small and focused
- Use composition over inheritance
- Implement proper prop validation
- Follow accessibility guidelines

### State Management
- Use React hooks for local state
- Context API for global state
- Consider Redux for complex state needs

## 📚 Dependencies

### Core Dependencies
- **React 18**: UI framework
- **TypeScript**: Type safety
- **Vite**: Build tool
- **Tailwind CSS**: Styling framework

### UI Components
- **Chart.js**: Data visualization
- **Leaflet**: Interactive maps
- **React Router**: Client-side routing
- **Axios**: HTTP client

### Development Dependencies
- **ESLint**: Code linting
- **Prettier**: Code formatting
- **Vitest**: Testing framework
- **TypeScript**: Type checking

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Follow the coding standards and guidelines
4. Write tests for new functionality
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is proprietary. Please contact the team for licensing information.

## 📞 Support

For technical support or questions:
- Create an issue in the repository
- Contact the frontend development team
- Check the component documentation
