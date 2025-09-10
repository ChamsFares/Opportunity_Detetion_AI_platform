// API Service for OpporTuna Backend Integration

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

/**
 * Extract or confirm business information from prompt and optional files
 * @param {string} prompt - The user's prompt/message
 * @param {File[]} files - Optional array of files to upload
 * @param {string} sessionId - Optional session ID for tracking
 * @param {boolean} isConfirmation - Whether this is a confirmation request
 * @returns {Promise<Object>} API response
 */
export const extractOrConfirmInfo = async (prompt, files = null, sessionId = null, isConfirmation = false) => {
    try {
        const formData = new FormData();

        // Add prompt
        formData.append('prompt', prompt);

        // Add files if provided
        if (files && files.length > 0) {
            files.forEach((file) => {
                formData.append('files', file);
            });
        }

        // Add confirmation flag
        formData.append('is_confirmation', isConfirmation.toString());

        // Prepare headers
        const headers = {
            // Don't set Content-Type header - let axios set it with boundary for FormData
        };

        // Add session ID if provided
        if (sessionId) {
            headers['session_id'] = sessionId;
        }

        const response = await axios.post(`${API_BASE_URL}/extract-info`, formData, {
            headers,
        });

        return response.data;

    } catch (error) {
        console.error('Error in extractOrConfirmInfo:', error);

        // Handle axios errors
        if (error.response) {
            if (error.response.status === 403) {
                const errorData = error.response.data;
                throw new Error(errorData?.detail || 'Access forbidden');
            }
            throw new Error(`HTTP error! status: ${error.response.status}`);
        }

        throw error;
    }
};

/**
 * Generate a unique session ID
 * @returns {string} Unique session ID
 */
export const generateSessionId = () => {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * Validate if all required fields are present and valid
 * @param {Object} data - The extracted data object
 * @returns {Object} Validation result with missing fields
 */
export const validateRequiredFields = (data) => {
    const requiredFields = [
        'company_name',
        'business_domain',
        'region_or_market',
        'target_audience',
        'unique_value_proposition',
        'distribution_channels',
        'revenue_model',
        'key_partners',
    ];

    const isInvalid = (value) => {
        return value === null ||
            value === undefined ||
            (typeof value === 'string' && (!value.trim() || value.trim().toUpperCase() === 'N/A'));
    };

    const missingFields = requiredFields.filter(field => isInvalid(data[field]));

    return {
        isValid: missingFields.length === 0,
        missingFields,
        requiredFields,
    };
};

/**
 * Process chatbot conversation and extract business information
 * @param {Array} messages - Array of conversation messages
 * @param {File[]} files - Optional files to include
 * @param {string} sessionId - Session ID for tracking
 * @returns {Promise<Object>} Processed information
 */
export const processChatbotConversation = async (messages, files = null, sessionId = null) => {
    try {
        // Combine all user messages into a single prompt
        const userMessages = messages
            .filter(message => !message.isBot)
            .map(message => message.text)
            .join('\n\n');

        if (!userMessages.trim()) {
            throw new Error('No user messages found to process');
        }

        const result = await extractOrConfirmInfo(userMessages, files, sessionId, false);
        return result;

    } catch (error) {
        console.error('Error processing chatbot conversation:', error);
        throw error;
    }
};

/**
 * Confirm business information with additional details
 * @param {string} confirmationPrompt - Additional confirmation details
 * @param {Object} previousInfo - Previously extracted information
 * @param {File[]} files - Optional additional files
 * @param {string} sessionId - Session ID for tracking
 * @returns {Promise<Object>} Confirmation result
 */
export const confirmBusinessInfo = async (confirmationPrompt, previousInfo, files = null, sessionId = null) => {
    try {
        // Combine previous info context with new confirmation prompt
        const contextPrompt = `
Previous information:
${JSON.stringify(previousInfo, null, 2)}

Additional confirmation details:
${confirmationPrompt}
    `.trim();

        const result = await extractOrConfirmInfo(contextPrompt, files, sessionId, true);
        console.log(result);

        return result;

    } catch (error) {
        console.error('Error confirming business info:', error);
        throw error;
    }
};

// Export API configuration for external use
export const API_CONFIG = {
    BASE_URL: API_BASE_URL,
    ENDPOINTS: {
        EXTRACT_INFO: '/extract-info',
        DYNAMIC_CHART: '/optigap/dynamic-chart',
    },
};

/**
 * Helper function to convert backend ChartData to frontend ChartDataFromBackend
 * @param {Object} backendChart - Chart data from backend
 * @returns {Object} Converted chart data for frontend
 */
export const convertChartData = (backendChart) => {
    const chartData = backendChart.data || {};
    const datasets = chartData.datasets || [];
    const firstDataset = datasets[0] || {};

    return {
        title: backendChart.title,
        type: backendChart.type,
        labels: chartData.labels || [],
        data: firstDataset.data || chartData.data || [],
        description: chartData.description,
        backgroundColor: firstDataset.backgroundColor,
        borderColor: firstDataset.borderColor,
        insights: chartData.insights,
    };
};

/**
 * Helper function to detect if a prompt is requesting charts
 * @param {string} prompt - User prompt to analyze
 * @returns {boolean} Whether the prompt is requesting charts
 */
export const isChartRequest = (prompt) => {
    const chartKeywords = [
        "chart", "graph", "plot", "visualiz", "show", "generate", "create", "display",
        "pie", "bar", "line", "scatter", "doughnut", "area", "radar", "polar",
        "dashboard", "report", "metrics", "data", "statistics", "analytics",
    ];

    const lowerPrompt = prompt.toLowerCase();
    return chartKeywords.some((keyword) => lowerPrompt.includes(keyword));
};

/**
 * Call the dynamic chart API to generate charts based on user prompts
 * @param {string} userPrompt - User's natural language request
 * @param {string} sessionId - Session identifier
 * @param {Array} existingCharts - Previously generated charts (optional)
 * @param {Object} previousAnalysisData - Previous analysis data (optional)
 * @returns {Promise<Object>} API response with generated charts
 */
export const callDynamicChartAPI = async (
    userPrompt,
    sessionId,
    existingCharts = null,
    previousAnalysisData = null
) => {
    console.log(`🔄 API Call - Existing charts received:`, {
        count: existingCharts?.length || 0,
        charts: existingCharts?.map(chart => ({
            title: chart.title,
            type: chart.type,
            dataLength: chart.data?.length || 0
        })) || []
    });

    // Convert frontend charts to backend format if needed
    const convertedExistingCharts = existingCharts?.map((chart) => ({
        id: chart.id || `chart-${Date.now()}`,
        type: chart.type,
        title: chart.title,
        data: {
            labels: chart.labels || [],
            datasets: [
                {
                    data: chart.data || [],
                    backgroundColor: chart.backgroundColor,
                    borderColor: chart.borderColor,
                },
            ],
        },
        description: chart.description || '',
        insights: chart.insights || [],
        // Include additional metadata that might be useful for the backend
        createdAt: chart.createdAt,
        updatedAt: chart.updatedAt,
        // Add chart metadata for better context
        metadata: {
            source: chart.source || 'ai_generated',
            categories: chart.categories || [],
            dataPoints: chart.data?.length || 0
        }
    }));

    const requestBody = {
        user_prompt: userPrompt,
        session_id: sessionId,
        existing_charts: convertedExistingCharts,
        previous_analysis_data: previousAnalysisData,
    };

    console.log("📊 Sending dynamic chart request:", {
        prompt: userPrompt.substring(0, 100) + "...",
        sessionId,
        chartsCount: convertedExistingCharts?.length || 0,
        hasAnalysisData: !!previousAnalysisData,
        chartDetails: convertedExistingCharts?.map(chart => ({
            id: chart.id,
            title: chart.title,
            type: chart.type,
            labels: chart.data?.labels?.length || 0,
            dataPoints: chart.data?.datasets?.[0]?.data?.length || 0
        })) || []
    });

    // Add detailed request body logging to verify format matches expected structure
    console.log("🔍 Full request body structure:", {
        user_prompt: `"${userPrompt.substring(0, 50)}..."`,
        session_id: sessionId,
        existing_charts: `Array[${convertedExistingCharts?.length || 0}]`,
        previous_analysis_data: previousAnalysisData ? "Object" : null,
        sample_chart: convertedExistingCharts?.[0] ? {
            id: convertedExistingCharts[0].id,
            type: convertedExistingCharts[0].type,
            title: convertedExistingCharts[0].title,
            dataStructure: {
                labels: `Array[${convertedExistingCharts[0].data?.labels?.length || 0}]`,
                datasets: `Array[1]`
            }
        } : "No charts available"
    });

    console.log("📋 Complete request body:", JSON.stringify(requestBody, null, 2));
    console.log("🔗 Target URL:", `${API_BASE_URL}${API_CONFIG.ENDPOINTS.DYNAMIC_CHART}`);

    // Log example of expected request format for debugging
    if (convertedExistingCharts?.length > 0) {
        console.log("📋 Request Format Example:", {
            "user_prompt": "Generate a bar chart showing competitor revenue comparison",
            "session_id": "session_12345",
            "existing_charts": [
                {
                    "id": "chart-example",
                    "type": "bar",
                    "title": "Sample Chart",
                    "data": {
                        "labels": ["Q1", "Q2", "Q3"],
                        "datasets": [{ "data": [100, 200, 300] }]
                    },
                    "description": "Sample description",
                    "insights": ["insight1", "insight2"]
                }
            ],
            "previous_analysis_data": {
                "market_opportunities": [],
                "competitive_insights": {}
            }
        });
    }

    try {
        const response = await axios.post(
            `${API_BASE_URL}${API_CONFIG.ENDPOINTS.DYNAMIC_CHART}`,
            requestBody,
            {
                headers: {
                    "Content-Type": "application/json",
                },
                timeout: 120000, // Increased to 2 minutes for complex chart generation
            }
        );

        console.log("✅ Dynamic chart API response:", {
            status: response.data.status,
            chartsGenerated: response.data.data?.charts?.length || 0,
            requestType: response.data.analytics?.request_type,
        });

        return response.data;
    } catch (error) {
        console.error("🚨 Error calling dynamic chart API:", error);

        // If we get a 404, try the fallback URL (without /api prefix)
        if (error.response?.status === 404) {
            console.log("🔄 Trying fallback URL without /api prefix...");
            try {
                const fallbackResponse = await axios.post(
                    `${API_BASE_URL}/dynamic-chart`,
                    requestBody,
                    {
                        headers: {
                            "Content-Type": "application/json",
                        },
                        timeout: 120000, // Increased to 2 minutes for fallback requests
                    }
                );

                console.log("✅ Fallback API call successful!");
                return fallbackResponse.data;
            } catch (fallbackError) {
                console.error("🚨 Fallback API call also failed:", fallbackError);
            }
        }

        // Handle axios errors
        if (error.response) {
            const status = error.response.status;
            const message = error.response.data?.detail?.error || error.message;
            throw new Error(`API Error (${status}): ${message}`);
        }

        throw error;
    }
};

/**
 * Sample request patterns for dynamic charts documentation
 */
export const SAMPLE_CHART_REQUESTS = {
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

/**
 * Generate smart responses based on report data and user prompts
 * @param {string} prompt - User's message/prompt
 * @param {Object} reportData - Report data to analyze
 * @returns {string} Smart response based on the prompt and data
 */
export const generateSmartResponse = (prompt, reportData) => {
    if (!reportData) {
        return "I'd be happy to help you understand your report. Could you please generate an analysis first?";
    }

    const lowerPrompt = prompt.toLowerCase();

    if (lowerPrompt.includes('opportunit')) {
        const count = reportData.market_opportunities?.length || 0;
        return `Based on your analysis, ${count} major opportunities have been identified in your sector. ${count > 0 ? `The top opportunity is ${reportData.market_opportunities?.[0]?.opportunity_type} with ${reportData.market_opportunities?.[0]?.urgency} urgency.` : ''}`;
    }

    if (lowerPrompt.includes('gap') || lowerPrompt.includes('weakness')) {
        const count = reportData.market_gaps?.length || 0;
        return `The analysis shows ${count} strategic gaps to address. ${count > 0 ? `The most critical gap is in ${reportData.market_gaps?.[0]?.gap_category} with ${reportData.market_gaps?.[0]?.impact_level} impact.` : ''}`;
    }

    if (lowerPrompt.includes('compet') || lowerPrompt.includes('strength')) {
        const strengths = reportData.competitive_insights?.competitive_strengths?.length || 0;
        const weaknesses = reportData.competitive_insights?.competitive_weaknesses?.length || 0;
        return `Your competitive positioning reveals ${strengths} main strengths and ${weaknesses} areas for improvement. ${reportData.competitive_insights?.market_positioning || ''}`;
    }

    if (lowerPrompt.includes('trend')) {
        const trends = reportData.trend_analysis?.emerging_trends?.length || 0;
        return `The trend analysis identifies ${trends} emerging trends to monitor. ${trends > 0 ? `Key trend: ${reportData.trend_analysis?.emerging_trends?.[0]}` : ''}`;
    }

    if (lowerPrompt.includes('risk')) {
        const risks = reportData.risk_assessment?.length || 0;
        return `${risks} potential risks have been identified in your business analysis. ${risks > 0 ? `Primary risk: ${reportData.risk_assessment?.[0]?.risk_type} with ${reportData.risk_assessment?.[0]?.probability} probability.` : ''}`;
    }

    if (lowerPrompt.includes('recommend')) {
        const recommendations = reportData.strategic_recommendations?.length || 0;
        return `I've found ${recommendations} strategic recommendations for your business. ${recommendations > 0 ? `Top priority: ${reportData.strategic_recommendations?.[0]?.recommendation}` : ''}`;
    }

    // Default response
    return "I can help you explore opportunities, gaps, competitive insights, trends, risks, and recommendations from your report. You can also ask me to create charts and visualizations by saying things like 'show me a chart' or 'create a graph'.";
};

/**
 * Process chatbot message and determine the appropriate response
 * @param {string} prompt - User's message
 * @param {string} sessionId - Session identifier
 * @param {Array} existingCharts - Current charts in the conversation
 * @param {Object} reportData - Report data for context
 * @returns {Promise<Object>} Response object with message and optional charts
 */
export const processChatbotMessage = async (prompt, sessionId, existingCharts = [], reportData = null) => {
    try {
        // Check if the user is requesting charts
        const isChartRequestFlag = isChartRequest(prompt);

        if (isChartRequestFlag) {
            // Call the dynamic chart API
            const response = await callDynamicChartAPI(
                prompt,
                sessionId,
                existingCharts,
                reportData
            );

            if (response.status === 'success') {
                const backendCharts = response.data.charts || [];
                const newCharts = backendCharts.map(convertChartData);

                return {
                    type: 'chart_response',
                    success: true,
                    message: response.message || `I've generated ${newCharts.length} chart(s) based on your request. ${response.data.type === 'chart_generation' ? 'The visualizations show your data insights.' : 'Here\'s the data you requested with visualizations.'}`,
                    charts: newCharts,
                    data: response.data,
                };
            } else {
                throw new Error('Failed to generate charts');
            }
        } else {
            // Generate smart response based on report data
            const smartResponse = generateSmartResponse(prompt, reportData);

            return {
                type: 'text_response',
                success: true,
                message: smartResponse,
                charts: null,
                data: null,
            };
        }
    } catch (error) {
        console.error('Error processing chatbot message:', error);

        // Fallback to smart response if API fails
        const fallbackResponse = generateSmartResponse(prompt, reportData);

        return {
            type: 'fallback_response',
            success: false,
            message: `${fallbackResponse} (Note: Chart generation is currently unavailable)`,
            charts: null,
            data: null,
            error: error.message,
        };
    }
};

/**
 * Generate a unique chat session ID
 * @returns {string} Unique session ID for chat
 */
export const generateChatSessionId = () => {
    return `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * Format chat message object
 * @param {string} id - Message ID
 * @param {string} text - Message text
 * @param {boolean} isBot - Whether message is from bot
 * @param {Array} charts - Optional charts array
 * @returns {Object} Formatted message object
 */
export const formatChatMessage = (id, text, isBot, charts = null) => {
    return {
        id,
        text,
        isBot,
        timestamp: new Date(),
        charts: charts && charts.length > 0 ? charts : undefined,
    };
};

export default {
    extractOrConfirmInfo,
    generateSessionId,
    validateRequiredFields,
    processChatbotConversation,
    confirmBusinessInfo,
    callDynamicChartAPI,
    convertChartData,
    isChartRequest,
    generateSmartResponse,
    processChatbotMessage,
    generateChatSessionId,
    formatChatMessage,
    API_CONFIG,
    SAMPLE_CHART_REQUESTS,
};
