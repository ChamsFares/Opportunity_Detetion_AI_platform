# ReportComponent - Updated for Backend Integration

The ReportComponent has been updated to handle dynamic data from the backend API. It now supports both the original data format and the new backend response format.

## Usage

### With Backend Response Data

```tsx
import ReportComponent from './components/ReportComponent';

// Example backend response
const backendResponse = {
  "status": "success",
  "message": "🎉 Comprehensive market analysis completed successfully!",
  "data": {
    "report_data": {
      "market_opportunities": [...],
      "market_gaps": [...],
      "trend_analysis": {...},
      "competitive_insights": {...},
      "risk_assessment": [...],
      "strategic_recommendations": [...],
      "metadata": {...}
    }
  }
};

// Use the component
<ReportComponent 
  reportData={backendResponse}
  title="Strategic Analysis Report"
  description="Comprehensive business intelligence report"
  showChat={true}
/>
```

### With Direct Report Data

```tsx
// Direct report data (legacy format)
const reportData = {
  market_opportunities: [...],
  market_gaps: [...],
  trend_analysis: {...},
  competitive_insights: {...}
};

<ReportComponent 
  reportData={reportData}
  title="Market Analysis"
  showChat={false}
/>
```

## New Features

### 1. Dynamic Data Transformation
- Automatically detects backend response format vs direct data
- Extracts `report_data` from backend responses
- Maintains backward compatibility

### 2. Enhanced Filtering
- **All**: Shows complete executive summary
- **Opportunities**: Market opportunities with urgency indicators
- **Gaps**: Market gaps with impact levels
- **Trends**: Emerging trends, implications, and opportunities
- **Competitive**: Competitive analysis with strengths/weaknesses
- **Risks**: Risk assessment with mitigation strategies
- **Recommendations**: Strategic recommendations with priority levels

### 3. Rich Data Visualization

#### Market Opportunities
- Opportunity type and description
- Urgency indicators (immediate, short_term, etc.)
- Market size potential
- Competitive advantages

#### Market Gaps
- Gap categories (Implementation & Adoption, etc.)
- Impact levels (high, medium, low)
- Supporting evidence

#### Trend Analysis
- Emerging trends list
- Trend implications
- Trend-based opportunities

#### Competitive Insights
- Market positioning statement
- Competitive strengths and weaknesses
- Differentiation opportunities

#### Risk Assessment
- Risk types (Technological, Operational, Competitive)
- Risk descriptions and probability levels
- Detailed mitigation strategies

#### Strategic Recommendations
- Recommendation descriptions
- Priority levels (high, medium, low)
- Implementation complexity
- Expected impact statements

### 4. Metadata Display
- Company information
- Analysis timestamp
- Data source statistics
- Quality indicators

### 5. AI Chat Integration
- Interactive chat with contextual responses
- Analysis-specific responses based on data
- Typing indicators and message history

## Color Coding System

### Urgency/Priority Levels
- **High/Immediate**: Red indicators
- **Medium/Short-term**: Orange indicators  
- **Low**: Green indicators

### Impact/Complexity
- **High**: Red text
- **Medium**: Orange text
- **Low**: Green text

### Risk Probability
- **High**: Red indicators
- **Medium**: Orange indicators
- **Low**: Green indicators

## Props Interface

```tsx
interface ReportComponentProps {
  reportData?: ReportData | BackendResponse;  // Supports both formats
  title?: string;                             // Default: "Comprehensive Report"
  description?: string;                       // Default: "Detailed analysis..."
  showChat?: boolean;                         // Default: true
  className?: string;                         // Additional CSS classes
}
```

## Backend Data Structure

The component expects this data structure from the backend:

```json
{
  "status": "success",
  "data": {
    "report_data": {
      "market_opportunities": [
        {
          "opportunity_type": "Regulatory & Ethical Compliance",
          "opportunity_description": "Description text...",
          "urgency": "immediate",
          "market_size_potential": "large",
          "competitive_advantage": "Advantage description..."
        }
      ],
      "market_gaps": [
        {
          "gap_category": "Implementation & Adoption",
          "gap_description": "Description text...",
          "impact_level": "high",
          "evidence": "Evidence text..."
        }
      ],
      "trend_analysis": {
        "emerging_trends": ["Trend 1", "Trend 2"],
        "trend_implications": ["Implication 1", "Implication 2"],
        "trend_based_opportunities": ["Opportunity 1", "Opportunity 2"]
      },
      "competitive_insights": {
        "market_positioning": "Positioning statement...",
        "competitive_strengths": ["Strength 1", "Strength 2"],
        "competitive_weaknesses": ["Weakness 1", "Weakness 2"],
        "differentiation_opportunities": ["Opportunity 1", "Opportunity 2"]
      },
      "risk_assessment": [
        {
          "risk_type": "Technological",
          "risk_description": "Risk description...",
          "probability": "high",
          "mitigation_strategy": "Mitigation strategy..."
        }
      ],
      "strategic_recommendations": [
        {
          "recommendation": "Recommendation text...",
          "priority": "high",
          "implementation_complexity": "medium",
          "expected_impact": "Impact description..."
        }
      ],
      "metadata": {
        "analysis_timestamp": "2025-08-10T11:04:46.131661",
        "company": "Company Name",
        "sector": "Industry Sector",
        "data_sources": {
          "trends_analyzed": 5,
          "news_articles": 12,
          "competitor_pages": 8
        }
      }
    }
  }
}
```

## Error Handling

- Gracefully handles missing or null data
- Shows "No Report Data Available" message when no data is provided
- Conditionally renders sections based on available data
- Filters are automatically hidden if related data is missing

## Responsive Design

- Mobile-friendly layout with responsive grids
- Sticky chat panel on larger screens
- Collapsible sections for better mobile experience
- Optimized typography and spacing for all screen sizes
