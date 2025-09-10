import axios from "axios";

// Dynamic Chart API interfaces
export interface DynamicChartRequest {
  user_prompt: string;
  session_id: string;
  existing_charts?: Record<string, unknown>[];
  previous_analysis_data?: ReportData;
}

export interface DynamicChartResponse {
  status: string;
  message: string;
  data: {
    type: string;
    charts: ChartData[];
    data: Record<string, unknown>;
    user_request: string;
    session_id?: string;
  };
  analytics: {
    execution_time: string;
    request_type: string;
    charts_generated: number;
    data_categories: number;
    processing_mode: string;
  };
  metadata: {
    timestamp: string;
    api_version: string;
    agent_type: string;
    processed_at: string;
  };
}

export interface ChartData {
  type: string;
  title: string;
  data: Record<string, unknown>;
  options?: Record<string, unknown>;
}

// Additional interfaces based on backend models
export interface IntentAnalysis {
  type: string;
  chart_type?: string;
  data_categories: string[];
  metrics: string[];
  confidence: number;
  original_prompt: string;
}

export interface DataFetchResult {
  success: boolean;
  type: string;
  data: Record<string, unknown>;
  categories: string[];
  metrics: string[];
  user_request: string;
  fetched_at: string;
  error?: string;
}

export interface ChartGenerationResult {
  success: boolean;
  type: string;
  charts: ChartData[];
  data_used: Record<string, unknown>;
  user_request: string;
  generated_at: string;
  fallback?: boolean;
  error?: string;
}

export interface HybridResult {
  success: boolean;
  type: string;
  data: Record<string, unknown>;
  charts: ChartData[];
  user_request: string;
  processed_at: string;
  error?: string;
}

export interface ChartDataFromBackend {
  title: string;
  type:
    | "line"
    | "bar"
    | "pie"
    | "doughnut"
    | "area"
    | "scatter"
    | "horizontalBar"
    | "polarArea"
    | "radar";
  labels: string[];
  data: number[];
  description?: string;
  backgroundColor?: string | string[];
  borderColor?: string | string[];
  insights?: string[];
}

export interface ReportData {
  market_opportunities?: Array<{
    opportunity_description: string;
    opportunity_type: string;
    urgency: string;
    market_size_potential: string;
    competitive_advantage: string;
  }>;
  market_gaps?: Array<{
    gap_description: string;
    impact_level: string;
    gap_category: string;
    evidence: string;
  }>;
  trend_analysis?: {
    trend_based_opportunities: string[];
    emerging_trends: string[];
    trend_implications: string[];
  };
  competitive_insights?: {
    competitive_weaknesses: string[];
    competitive_strengths: string[];
    market_positioning: string;
    differentiation_opportunities: string[];
  };
  risk_assessment?: Array<{
    risk_description: string;
    risk_type: string;
    mitigation_strategy: string;
    probability: string;
  }>;
  strategic_recommendations?: Array<{
    recommendation: string;
    priority: string;
    implementation_complexity: string;
    expected_impact: string;
  }>;
  metadata?: {
    analysis_timestamp?: string;
    company?: string;
    sector?: string;
    service?: string;
    data_sources?: {
      trends_analyzed?: number;
      news_articles?: number;
      competitor_pages?: number;
    };
    analysis_successful?: boolean;
  };
}

// API Configuration
const API_BASE_URL = "http://localhost:8000/api";
const FALLBACK_API_BASE_URL = "http://localhost:8000";

// Helper function to convert backend ChartData to frontend ChartDataFromBackend
export const convertChartData = (
  backendChart: ChartData
): ChartDataFromBackend => {
  const chartData = backendChart.data as Record<string, unknown>;
  const datasets = chartData.datasets as Record<string, unknown>[] | undefined;
  const firstDataset = datasets?.[0] as Record<string, unknown> | undefined;

  return {
    title: backendChart.title,
    type: backendChart.type as ChartDataFromBackend["type"],
    labels: (chartData.labels as string[]) || [],
    data:
      (firstDataset?.data as number[]) || (chartData.data as number[]) || [],
    description: chartData.description as string | undefined,
    backgroundColor: firstDataset?.backgroundColor as
      | string
      | string[]
      | undefined,
    borderColor: firstDataset?.borderColor as string | string[] | undefined,
    insights: chartData.insights as string[] | undefined,
  };
};

// API function for dynamic chart requests
export const callDynamicChartAPI = async (
  userPrompt: string,
  sessionId: string,
  existingCharts?: ChartDataFromBackend[],
  previousAnalysisData?: ReportData
): Promise<DynamicChartResponse> => {
  // Convert frontend charts to backend format if needed
  const convertedExistingCharts = existingCharts?.map((chart) => ({
    type: chart.type,
    title: chart.title,
    data: {
      labels: chart.labels,
      datasets: [
        {
          data: chart.data,
          backgroundColor: chart.backgroundColor,
          borderColor: chart.borderColor,
        },
      ],
      description: chart.description,
      insights: chart.insights,
    },
  })) as Record<string, unknown>[] | undefined;

  const requestBody: DynamicChartRequest = {
    user_prompt: userPrompt,
    session_id: sessionId,
    existing_charts: convertedExistingCharts,
    previous_analysis_data: previousAnalysisData,
  };

  console.log("📊 Sending dynamic chart request:", {
    prompt: userPrompt.substring(0, 100) + "...",
    sessionId,
    chartsCount: existingCharts?.length || 0,
    hasAnalysisData: !!previousAnalysisData,
  });

  // Add detailed request body logging
  console.log("🔍 Full request body:", JSON.stringify(requestBody, null, 2));
  console.log("🔗 Target URL:", `${API_BASE_URL}/dynamic-chart`);

  try {
    const response = await axios.post(
      `${API_BASE_URL}/dynamic-chart`,
      requestBody,
      {
        headers: {
          "Content-Type": "application/json",
        },
        timeout: 30000, // 30 second timeout
      }
    );

    console.log("✅ Dynamic chart API response:", {
      status: response.data.status,
      chartsGenerated: response.data.data?.charts?.length || 0,
      requestType: response.data.analytics?.request_type,
    });

    return response.data as DynamicChartResponse;
  } catch (error) {
    console.error("🚨 Error calling dynamic chart API:", error);

    // If we get a 404, try the fallback URL (without /api prefix)
    if (axios.isAxiosError(error) && error.response?.status === 404) {
      console.log("🔄 Trying fallback URL without /api prefix...");
      try {
        const fallbackResponse = await axios.post(
          `${FALLBACK_API_BASE_URL}/dynamic-chart`,
          requestBody,
          {
            headers: {
              "Content-Type": "application/json",
            },
            timeout: 30000,
          }
        );

        console.log("✅ Fallback API call successful!");
        return fallbackResponse.data as DynamicChartResponse;
      } catch (fallbackError) {
        console.error("🚨 Fallback API call also failed:", fallbackError);
      }
    }

    if (axios.isAxiosError(error)) {
      const status = error.response?.status;
      const message = error.response?.data?.detail?.error || error.message;

      throw new Error(`API Error (${status}): ${message}`);
    }

    throw error;
  }
};

// Helper function to detect chart requests
export const isChartRequest = (prompt: string): boolean => {
  const chartKeywords = [
    "chart",
    "graph",
    "plot",
    "visualiz",
    "show",
    "generate",
    "create",
    "display",
    "pie",
    "bar",
    "line",
    "scatter",
    "doughnut",
    "area",
    "radar",
    "polar",
    "dashboard",
    "report",
    "metrics",
    "data",
    "statistics",
    "analytics",
  ];

  const lowerPrompt = prompt.toLowerCase();
  return chartKeywords.some((keyword) => lowerPrompt.includes(keyword));
};

// Sample request patterns for documentation
export const SAMPLE_REQUESTS = {
  chartGeneration: [
    "Generate a pie chart showing market opportunities",
    "Create a bar chart of competitive strengths vs weaknesses",
    "Show a line chart of trend analysis over time",
    "Plot the risk assessment data in a scatter chart",
    "Visualize strategic recommendations as a doughnut chart",
    "Create a radar chart showing AI service mentions",
    "Generate a radar chart for competitive analysis",
  ],
  dataFetch: [
    "Get all market opportunities data",
    "Fetch competitive insights information",
    "Retrieve trend analysis results",
    "Show me risk assessment details",
  ],
  hybrid: [
    "Get market gaps data and create a visualization",
    "Fetch opportunity data and generate charts",
    "Show competitive data with bar charts",
    "Analyze trends and create visualizations",
    "Create radar charts for AI services analysis",
  ],
};
