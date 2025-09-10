// API Service for OpporTuna Backend Integration

import axios, { AxiosError } from "axios";
import { ProgressTracker, ProgressUpdate, ANALYSIS_PHASES } from './progressTracker';

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

export interface ExtractedInfo {
  company_name?: string;
  business_domain?: string;
  region_or_market?: string;
  target_audience?: string;
  unique_value_proposition?: string;
  distribution_channels?: string;
  revenue_model?: string;
  key_partners?: string;
  urls?: string[];
  website_crawled_info?:
    | Array<Record<string, unknown>>
    | Record<string, unknown>;
  crawled_info?: Array<Record<string, unknown>>;
  [key: string]:
    | string
    | string[]
    | Array<Record<string, unknown>>
    | Record<string, unknown>
    | undefined;
}

export interface ReportRequest {
  company: string;
  sector: string;
  service: string;
}

export interface ReportResponse {
  status: string;
  pdf_path: string;
}

export interface StreamProgressEvent {
  step: string;
  message: string;
  progress: number;
  phase: string;
  eta_seconds?: number;
  eta_formatted?: string;
  execution_time?: string;
  details?: string;
  velocity?: number;
  phase_factor?: number;
  timestamp?: string;
  elapsed_time?: string;
  performance?: {
    update_frequency: number;
    phase_progress: string;
  };
  heartbeat?: boolean;
}

export interface StreamConnectedEvent {
  message: string;
  timestamp: string;
  session_id: string;
  company: string;
  sector: string;
  service: string;
  streaming_mode: string;
  features: string[];
}

export interface StreamHeartbeatEvent {
  message: string;
  progress: number;
  phase: string;
  step: string;
  timestamp: string;
  elapsed_time: string;
  heartbeat: boolean;
  eta_seconds?: number;
  eta_formatted?: string;
}

export interface MarketOpportunity {
  opportunity_type: string;
  opportunity_description: string;
  urgency: string;
  market_size_potential: string;
  competitive_advantage: string;
}

export interface MarketGap {
  gap_category: string;
  gap_description: string;
  impact_level: string;
  evidence: string;
}

export interface CompetitiveInsights {
  market_positioning: string;
  competitive_strengths: string[];
  competitive_weaknesses: string[];
  differentiation_opportunities: string[];
}

export interface StrategicRecommendation {
  recommendation: string;
  priority: string;
  implementation_complexity: string;
  expected_impact: string;
}

export interface RiskAssessment {
  risk_type: string;
  risk_description: string;
  probability: string;
  mitigation_strategy: string;
}

export interface TrendAnalysis {
  emerging_trends: string[];
  trend_implications: string[];
  trend_based_opportunities: string[];
}

export interface ReportData {
  market_opportunities: MarketOpportunity[];
  market_gaps: MarketGap[];
  competitive_insights: CompetitiveInsights;
  strategic_recommendations: StrategicRecommendation[];
  risk_assessment: RiskAssessment[];
  trend_analysis: TrendAnalysis;
}

export interface StreamResultEvent {
  status: string;
  message: string;
  pdf_path: string;
  company: string;
  sector: string;
  service: string;
  session_id?: string;
  execution_time?: string;
  timestamp: string;
  report_data?: ReportData;
  report_markdown?: string;
  data_charts?: Array<{
    title: string;
    type: "line" | "bar" | "pie" | "doughnut" | "area" | "scatter";
    labels: string[];
    data: number[];
    description?: string;
    backgroundColor?: string | string[];
    borderColor?: string | string[];
    insights?: string[];
  }>;
  dashboard_data?: {
    kpiData: Array<{
      title: string;
      value: string;
      change: string;
      icon: string;
      color: string;
      description: string;
    }>;
    revenueData: Array<{
      name: string;
      value: number;
      fill: string;
    }>;
    profitabilityData: Array<{
      month: string;
      profit: number;
    }>;
    roiActions: Array<{
      action: string;
      roi: number;
      complexity: string;
      impact: string;
    }>;
  };
  analytics?: {
    execution_time: string;
    processing_speed: string;
    report_quality: string;
    data_sources: string[];
    ai_models_used: string[];
    analysis_quality?: string;
    performance_metrics?: {
      total_time: string;
      average_velocity: string;
      report_size: string;
      quality_score: string;
      processing_time: number;
    };
  };
}

export interface StreamErrorEvent {
  error: string;
  error_code: string;
  status_code: number;
  details?: string;
}

export interface ApiResponse {
  status: "processed" | "confirmed" | "confirmation_required";
  message: string;
  extracted_info?: ExtractedInfo;
  confirmed_info?: ExtractedInfo;
  missing_info?: string[];
  newly_provided?: string[];
  website_crawled_info?: Record<string, unknown>;
}

export interface ValidationResult {
  isValid: boolean;
  missingFields: string[];
  requiredFields: string[];
}

export interface ApiConfig {
  BASE_URL: string;
  ENDPOINTS: {
    EXTRACT_INFO: string;
    GENERATE_REPORT: string;
    GENERATE_REPORT_STREAM: string;
  };
}

/**
 * Extract or confirm business information from prompt and optional files
 * @param prompt - The user's prompt/message
 * @param files - Optional array of files to upload
 * @param sessionId - Optional session ID for tracking
 * @param isConfirmation - Whether this is a confirmation request
 * @returns API response
 */
export const extractOrConfirmInfo = async (
  prompt: string,
  files: File[] | null = null,
  sessionId: string | null = null,
  isConfirmation: boolean = false
): Promise<ApiResponse> => {
  try {
    const formData = new FormData();

    // Add prompt
    formData.append("prompt", prompt);

    // Add files if provided
    if (files && files.length > 0) {
      files.forEach((file) => {
        formData.append("files", file);
      });
    }

    // Add confirmation flag
    formData.append("is_confirmation", isConfirmation.toString());

    // Prepare headers
    const headers: Record<string, string> = {
      // Don't set Content-Type header - let axios set it with boundary for FormData
    };

    // Add session ID if provided
    if (sessionId) {
      headers["session_id"] = sessionId;
    }

    const response = await axios.post(
      `${API_BASE_URL}/extract-info`,
      formData,
      {
        headers,
      }
    );

    return response.data;
  } catch (error) {
    console.error("Error in extractOrConfirmInfo:", error);

    // Handle axios errors
    if (error instanceof AxiosError) {
      if (error.response?.status === 403) {
        const errorData = error.response.data;
        throw new ApiError(errorData?.detail || "Access forbidden", 403);
      }
      throw new ApiError(
        `HTTP error! status: ${error.response?.status || "Unknown"}`,
        error.response?.status || 500
      );
    }

    throw error;
  }
};

/**
 * Generate a unique session ID
 * @returns Unique session ID
 */
export const generateSessionId = (): string => {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * Validate if all required fields are present and valid
 * @param data - The extracted data object
 * @returns Validation result with missing fields
 */
export const validateRequiredFields = (
  data: ExtractedInfo
): ValidationResult => {
  const requiredFields = [
    "company_name",
    "business_domain",
    "region_or_market",
    "target_audience",
    "unique_value_proposition",
    "distribution_channels",
    "revenue_model",
    "key_partners",
  ];

  const isInvalid = (
    value:
      | string
      | string[]
      | Array<Record<string, unknown>>
      | Record<string, unknown>
      | undefined
  ): boolean => {
    return (
      value === null ||
      value === undefined ||
      (typeof value === "string" &&
        (!value.trim() || value.trim().toUpperCase() === "N/A")) ||
      (Array.isArray(value) && value.length === 0) ||
      (typeof value === "object" &&
        value !== null &&
        !Array.isArray(value) &&
        Object.keys(value).length === 0)
    );
  };

  const missingFields = requiredFields.filter((field) =>
    isInvalid(data[field as keyof ExtractedInfo])
  );

  return {
    isValid: missingFields.length === 0,
    missingFields,
    requiredFields,
  };
};

/**
 * Process chatbot conversation and extract business information
 * @param messages - Array of conversation messages
 * @param files - Optional files to include
 * @param sessionId - Session ID for tracking
 * @returns Processed information
 */
export const processChatbotConversation = async (
  messages: Array<{ text: string; isBot: boolean }>,
  files: File[] | null = null,
  sessionId: string | null = null
): Promise<ApiResponse> => {
  try {
    // Combine all user messages into a single prompt
    const userMessages = messages
      .filter((message) => !message.isBot)
      .map((message) => message.text)
      .join("\n\n");

    if (!userMessages.trim()) {
      throw new Error("No user messages found to process");
    }

    const result = await extractOrConfirmInfo(
      userMessages,
      files,
      sessionId,
      false
    );
    return result;
  } catch (error) {
    console.error("Error processing chatbot conversation:", error);
    throw error;
  }
};

/**
 * Generate market analysis report
 * @param company - Company name
 * @param sector - Business sector
 * @param service - Main product or service
 * @param sessionId - Optional session ID for tracking
 * @returns Report generation response
 */
export const generateReport = async (
  company: string,
  sector: string,
  service: string,
  sessionId: string | null = null
): Promise<ReportResponse> => {
  try {
    const requestData: ReportRequest = {
      company: company.trim(),
      sector: sector.trim(),
      service: service.trim(),
    };

    // Prepare headers
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    // Add session ID if provided
    if (sessionId) {
      headers["session_id"] = sessionId;
    }

    const response = await axios.post(
      `${API_BASE_URL}/optigap/report`,
      requestData,
      {
        headers,
      }
    );

    return response.data;
  } catch (error) {
    console.error("Error in generateReport:", error);

    // Handle axios errors
    if (error instanceof AxiosError) {
      if (error.response?.status === 422) {
        const errorData = error.response.data;
        throw new ApiError(errorData?.detail || "Validation error", 422);
      }
      if (error.response?.status === 403) {
        const errorData = error.response.data;
        throw new ApiError(errorData?.detail || "Access forbidden", 403);
      }
      if (error.response?.status === 500) {
        const errorData = error.response.data;
        throw new ApiError(errorData?.detail || "Internal server error", 500);
      }
      throw new ApiError(
        `HTTP error! status: ${error.response?.status || "Unknown"}`,
        error.response?.status || 500
      );
    }

    throw error;
  }
};

/**
 * Generate market analysis report with streaming progress updates
 * @param company - Company name
 * @param sector - Business sector
 * @param service - Main product or service
 * @param sessionId - Optional session ID for tracking
 * @param onProgress - Callback for progress updates
 * @param onComplete - Callback for completion
 * @param onError - Callback for errors
 * @returns Promise that resolves when streaming starts
 */
/**
 * Generate market analysis report with simulated streaming progress
 * @param company - Company name
 * @param sector - Business sector
 * @param service - Main product or service
 * @param sessionId - Optional session ID for tracking
 * @param onProgress - Progress callback function
 * @param onComplete - Completion callback function
 * @param onError - Error callback function
 * @returns Promise that resolves when complete
 */
export const generateReportStream = async (
  company: string,
  sector: string,
  service: string,
  sessionId: string | null = null,
  onProgress?: (event: StreamProgressEvent) => void,
  onComplete?: (event: StreamResultEvent) => void,
  onError?: (event: StreamErrorEvent) => void
): Promise<void> => {
  const startTime = Date.now();
  let currentProgress = 0;

  // Simulate progress updates
  const simulateProgress = () => {
    const phases = [
      {
        key: "initialization",
        label: "Initializing analysis pipeline",
        duration: 1000,
        progress: 15,
      },
      {
        key: "competitor_analysis",
        label: "AI-powered competitor identification",
        duration: 2000,
        progress: 35,
      },
      {
        key: "parallel_processing",
        label: "Deep AI relevance scoring with Gemini Pro",
        duration: 3000,
        progress: 70,
      },
      {
        key: "trend_analysis",
        label: "Multi-dimensional trend analysis",
        duration: 1500,
        progress: 85,
      },
      {
        key: "final_analysis",
        label: "AI orchestrating comprehensive market gap analysis",
        duration: 1000,
        progress: 95,
      },
      {
        key: "report_generation",
        label: "Generating professional PDF report",
        duration: 500,
        progress: 100,
      },
    ];

    let phaseIndex = 0;
    let phaseStartTime = Date.now();

    const updateProgress = () => {
      if (phaseIndex >= phases.length) return;

      const currentPhase = phases[phaseIndex];
      const phaseElapsed = Date.now() - phaseStartTime;
      const phaseProgress = Math.min(phaseElapsed / currentPhase.duration, 1);

      // Calculate overall progress
      const previousProgress =
        phaseIndex > 0 ? phases[phaseIndex - 1].progress : 0;
      const progressInPhase =
        (currentPhase.progress - previousProgress) * phaseProgress;
      currentProgress = previousProgress + progressInPhase;

      // Calculate ETA
      const totalElapsed = (Date.now() - startTime) / 1000;
      const velocity = currentProgress / totalElapsed;
      const remainingProgress = 100 - currentProgress;
      const etaSeconds = velocity > 0 ? remainingProgress / velocity : null;

      const formatETA = (seconds: number | null): string => {
        if (!seconds) return "Calculating...";
        if (seconds < 10) return `${seconds.toFixed(1)}s`;
        if (seconds < 60) return `${Math.round(seconds)}s`;
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.round(seconds % 60);
        return `${minutes}m ${remainingSeconds}s`;
      };

      if (onProgress) {
        onProgress({
          step: currentPhase.key,
          message: currentPhase.label,
          progress: Math.round(currentProgress),
          phase: currentPhase.key,
          eta_seconds: etaSeconds ? Math.round(etaSeconds) : undefined,
          eta_formatted: formatETA(etaSeconds),
          velocity: Math.round(velocity * 10) / 10,
          elapsed_time: `${totalElapsed.toFixed(1)}s`,
          timestamp: new Date().toISOString(),
          details: `Processing ${currentPhase.label.toLowerCase()}...`,
          performance: {
            update_frequency: 10,
            phase_progress: `${Math.round(currentProgress)}% in ${
              currentPhase.key
            }`,
          },
        });
      }

      // Move to next phase if current is complete
      if (phaseProgress >= 1 && phaseIndex < phases.length - 1) {
        phaseIndex++;
        phaseStartTime = Date.now();
      }
    };

    return setInterval(updateProgress, 100); // Update every 100ms
  };

  try {
    // Start progress simulation
    if (onProgress) {
      onProgress({
        step: "connected",
        message: "🚀 Connected to OptiGap Analysis Engine",
        progress: 0,
        phase: "initialization",
        eta_formatted: "Starting...",
        timestamp: new Date().toISOString(),
      });
    }

    const progressInterval = simulateProgress();

    // Make the actual API call
    const requestData: ReportRequest = {
      company: company.trim(),
      sector: sector.trim(),
      service: service.trim(),
    };

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    if (sessionId) {
      headers["session_id"] = sessionId;
    }

    const response = await fetch(`${API_BASE_URL}/optigap/report-stream`, {
      method: "POST",
      headers,
      body: JSON.stringify(requestData),
    });

    // Clear progress simulation
    clearInterval(progressInterval);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));

      if (onError) {
        onError({
          error:
            errorData.detail?.error || `HTTP error! status: ${response.status}`,
          error_code: errorData.detail?.error_code || "HTTP_ERROR",
          status_code: response.status,
          details: errorData.detail?.details || "Request failed",
        });
      }
      return;
    }

    const result = await response.json();

    // Send final progress update
    if (onProgress) {
      onProgress({
        step: "complete",
        message: "✅ Market analysis report generated successfully!",
        progress: 100,
        phase: "completed",
        eta_formatted: "Complete ✓",
        timestamp: new Date().toISOString(),
      });
    }

    // Send completion event
    if (onComplete) {
      onComplete({
        status: result.status,
        message: result.message,
        pdf_path: result.data.pdf_path,
        company: result.data.company,
        sector: result.data.sector,
        service: result.data.service,
        session_id: result.data.session_id,
        timestamp: result.metadata.timestamp,
        report_data: result.data.report_data,
        report_markdown: result.data.report_markdown,
        data_charts: result.data.data_charts,
        dashboard_data: result.data.dashboard_data,
        analytics: result.analytics,
      });
    }
  } catch (error) {
    console.error("Error in generateReportStream:", error);

    // Handle connection or network errors
    if (
      error instanceof TypeError &&
      error.message.includes("Failed to fetch")
    ) {
      console.log(
        "Network error detected, attempting fallback to regular report generation"
      );

      if (onProgress) {
        onProgress({
          step: "fallback",
          message: "Connection issue detected, using alternative method...",
          progress: 25,
          phase: "fallback",
          eta_formatted: "Retrying...",
        });
      }

      try {
        const fallbackResult = await generateReport(
          company,
          sector,
          service,
          sessionId
        );

        if (onProgress) {
          onProgress({
            step: "complete",
            message: "Report generated successfully",
            progress: 100,
            phase: "completed",
            eta_formatted: "Complete",
          });
        }

        if (onComplete) {
          onComplete({
            status: fallbackResult.status,
            message: "Report generated successfully (fallback mode)",
            pdf_path: fallbackResult.pdf_path,
            company,
            sector,
            service,
            session_id: sessionId || undefined,
            timestamp: new Date().toISOString(),
          });
        }
        return;
      } catch (fallbackError) {
        console.error(
          "Fallback to regular report generation failed:",
          fallbackError
        );
        if (onError) {
          onError({
            error: "Unable to connect to report generation service",
            error_code: "CONNECTION_FAILED",
            status_code: 503,
            details:
              "Please check that the backend server is running on the correct port",
          });
        }
        return;
      }
    }

    // Handle other errors
    if (onError) {
      onError({
        error: "An unexpected error occurred during report generation",
        error_code: "UNEXPECTED_ERROR",
        status_code: 500,
        details: error instanceof Error ? error.message : String(error),
      });
    }
  }
};

/**
 * Confirm business information with additional details
 * @param confirmationPrompt - Additional confirmation details
 * @param previousInfo - Previously extracted information
 * @param files - Optional additional files
 * @param sessionId - Session ID for tracking
 * @returns Confirmation result
 */
export const confirmBusinessInfo = async (
  confirmationPrompt: string,
  previousInfo: ExtractedInfo,
  files: File[] | null = null,
  sessionId: string | null = null
): Promise<ApiResponse> => {
  try {
    // Combine previous info context with new confirmation prompt
    const contextPrompt = `
Previous information:
${JSON.stringify(previousInfo, null, 2)}

Additional confirmation details:
${confirmationPrompt}
    `.trim();

    const result = await extractOrConfirmInfo(
      contextPrompt,
      files,
      sessionId,
      true
    );
    return result;
  } catch (error) {
    console.error("Error confirming business info:", error);
    throw error;
  }
};

// Export API configuration for external use
export const API_CONFIG: ApiConfig = {
  BASE_URL: API_BASE_URL,
  ENDPOINTS: {
    EXTRACT_INFO: "/extract-info",
    GENERATE_REPORT: "/optigap/report",
    GENERATE_REPORT_STREAM: "/optigap/report-stream",
  },
};

export default {
  extractOrConfirmInfo,
  generateSessionId,
  validateRequiredFields,
  processChatbotConversation,
  confirmBusinessInfo,
  generateReport,
  generateReportStream,
  API_CONFIG,
};
