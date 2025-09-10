# Updated Components - Backend Integration Guide

The MapComponent and RecommendationsComponent have been updated to dynamically display data from the backend API. Here's how to use them:

## MapComponent Updates

### New Features
- **Dynamic Region Generation**: Automatically creates regions based on market opportunities from backend data
- **Opportunity-based Scoring**: Calculates region scores based on urgency levels and market potential
- **Backend Data Integration**: Accepts both custom regions and backend report data

### Usage Example

```tsx
import MapComponent from './components/MapComponent';

// With backend response data
const backendResponse = {
  "status": "success",
  "data": {
    "report_data": {
      "market_opportunities": [
        {
          "opportunity_type": "Regulatory & Ethical Compliance",
          "opportunity_description": "Growing concerns and emerging regulations around AI ethics...",
          "urgency": "immediate",
          "market_size_potential": "large",
          "competitive_advantage": "Ability to combine technical AI knowledge with legal frameworks"
        }
      ],
      "market_gaps": [...],
      "metadata": {
        "company": "Talan",
        "sector": "AI"
      }
    }
  }
};

// Component usage
<MapComponent 
  reportData={backendResponse}
  title="AI Market Opportunities Map"
  description="Regional analysis based on AI consulting opportunities"
/>
```

### Dynamic Region Features
- Regions are automatically generated from market opportunities
- Urgency levels map to opportunity scores:
  - "immediate" → 95 points (Very High)
  - "short_term" → 80 points (High)  
  - default → 65 points (Medium)
- Market potential determines region size estimates
- Recommendations are generated from opportunity descriptions

## RecommendationsComponent Updates

### New Features
- **Backend Data Integration**: Processes strategic recommendations and risk assessments from backend
- **Automatic Recommendation Generation**: Creates recommendations from market opportunities if none provided
- **Dynamic ROI Calculation**: Calculates ROI based on priority and complexity
- **Enhanced Risk Visualization**: Maps probability levels to visual indicators

### Usage Example

```tsx
import RecommendationsComponent from './components/RecommendationsComponent';

// With backend data
<RecommendationsComponent 
  reportData={backendResponse}
  title="AI Strategy Recommendations"
  description="Strategic actions based on market analysis"
  showPerformanceIndicators={true}
/>

// With direct props (legacy support)
<RecommendationsComponent 
  strategicRecommendations={[
    {
      recommendation: "Develop AI ethics consulting services",
      priority: "high",
      implementation_complexity: "medium",
      expected_impact: "Establish market leadership in compliance"
    }
  ]}
  riskAssessment={[
    {
      risk_type: "Technological",
      probability: "high", 
      risk_description: "Rapid AI evolution may obsolete expertise",
      mitigation_strategy: "Continuous learning and R&D investment"
    }
  ]}
/>
```

### Backend Data Processing
- **Priority Mapping**: high/medium/low priorities with color coding
- **ROI Calculation**: Automatic calculation based on priority + complexity
- **Timeframe Generation**: Dynamic timeframes based on priority levels
- **Risk Probability**: Maps high/medium/low to percentage values (75%/50%/25%)

## DashboardPage Updates

### New Props Interface
```tsx
interface DashboardPageProps {
  backendData?: BackendResponse | BackendReportData;
}

// Usage
<DashboardPage backendData={analysisResponse} />
```

### Data Flow
1. **Extract Backend Data**: Automatically detects and extracts report_data from backend responses
2. **Pass to Components**: All three components (Map, Recommendations, Report) receive backend data
3. **Fallback to Sample Data**: Uses sample data when backend data is unavailable
4. **Dynamic Updates**: Components automatically update when new backend data is provided

## Backend Data Structure Expected

```json
{
  "status": "success", 
  "data": {
    "report_data": {
      "market_opportunities": [
        {
          "opportunity_type": "string",
          "opportunity_description": "string", 
          "urgency": "immediate|short_term|medium",
          "market_size_potential": "large|medium|small",
          "competitive_advantage": "string"
        }
      ],
      "strategic_recommendations": [
        {
          "recommendation": "string",
          "priority": "high|medium|low",
          "implementation_complexity": "high|medium|low", 
          "expected_impact": "string"
        }
      ],
      "risk_assessment": [
        {
          "risk_type": "string",
          "probability": "high|medium|low",
          "risk_description": "string",
          "mitigation_strategy": "string"
        }
      ],
      "market_gaps": [...],
      "competitive_insights": {...},
      "metadata": {
        "company": "string",
        "sector": "string",
        "analysis_timestamp": "ISO date"
      }
    }
  }
}
```

## Error Handling

All components gracefully handle:
- Missing or null backend data
- Empty arrays in backend responses  
- Malformed data structures
- Missing required fields

Fallback behaviors:
- **MapComponent**: Uses default sample regions
- **RecommendationsComponent**: Shows "no recommendations" message
- **ReportComponent**: Shows "no data available" state

## Backward Compatibility

All components maintain full backward compatibility:
- Can still accept custom props directly
- Sample data is preserved as fallback
- Existing prop interfaces remain unchanged
- Legacy usage patterns continue to work

## Integration Examples

### Full Backend Integration
```tsx
// Fetch analysis from your backend
const analysisData = await fetchBusinessAnalysis(companyId);

// Pass to dashboard
<DashboardPage backendData={analysisData} />
```

### Mixed Data Sources
```tsx
// Use backend for some components, custom for others
<RecommendationsComponent 
  reportData={backendData}
  showPerformanceIndicators={false}
/>

<MapComponent 
  regions={customRegions}  // Use custom regions instead of backend
  title="Custom Regional Analysis"
/>
```

### Real-time Updates
```tsx
const [backendData, setBackendData] = useState(null);

// Update data from API
useEffect(() => {
  const interval = setInterval(async () => {
    const newData = await fetchLatestAnalysis();
    setBackendData(newData);
  }, 30000); // Update every 30 seconds
  
  return () => clearInterval(interval);
}, []);

return <DashboardPage backendData={backendData} />;
```

This update enables seamless integration with your backend analysis API while maintaining all existing functionality.
