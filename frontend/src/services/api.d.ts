// Type definitions for API service

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number);
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
  };
}

export declare function extractOrConfirmInfo(
  prompt: string,
  files?: File[] | null,
  sessionId?: string | null,
  isConfirmation?: boolean
): Promise<ApiResponse>;

export declare function generateSessionId(): string;

export declare function validateRequiredFields(
  data: ExtractedInfo
): ValidationResult;

export declare function processChatbotConversation(
  messages: Array<{ text: string; isBot: boolean }>,
  files?: File[] | null,
  sessionId?: string | null
): Promise<ApiResponse>;

export declare function confirmBusinessInfo(
  confirmationPrompt: string,
  previousInfo: ExtractedInfo,
  files?: File[] | null,
  sessionId?: string | null
): Promise<ApiResponse>;

export declare function callDynamicChartAPI(
  prompt: string,
  sessionId: string,
  existingCharts?: any[],
  reportData?: any
): Promise<any>;

export declare function processChatbotMessage(
  prompt: string,
  sessionId: string,
  existingCharts?: any[],
  reportData?: any
): Promise<any>;

export declare function formatChatMessage(
  id: string,
  text: string,
  isBot: boolean,
  charts?: any[]
): any;

export declare function isChartRequest(prompt: string): boolean;

export declare function generateChatSessionId(): string;

export declare const API_CONFIG: ApiConfig;

declare const api: {
  extractOrConfirmInfo: typeof extractOrConfirmInfo;
  generateSessionId: typeof generateSessionId;
  validateRequiredFields: typeof validateRequiredFields;
  processChatbotConversation: typeof processChatbotConversation;
  confirmBusinessInfo: typeof confirmBusinessInfo;
  callDynamicChartAPI: typeof callDynamicChartAPI;
  processChatbotMessage: typeof processChatbotMessage;
  formatChatMessage: typeof formatChatMessage;
  isChartRequest: typeof isChartRequest;
  generateChatSessionId: typeof generateChatSessionId;
  API_CONFIG: ApiConfig;
};

export default api;
