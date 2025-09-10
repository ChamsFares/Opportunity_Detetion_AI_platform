import {
    ArcElement,
    BarElement,
    CategoryScale,
    Chart as ChartJS,
    Tooltip as ChartTooltip,
    Filler,
    Legend,
    LinearScale,
    LineElement,
    PointElement,
    RadialLinearScale,
    Title,
} from 'chart.js';
import { motion } from "framer-motion";
import {
    AlertTriangle,
    BarChart3,
    Bot,
    Clock,
    FileText,
    Filter,
    PieChart,
    Send,
    Shield,
    Target,
    TrendingUp,
    User,
} from "lucide-react";
import React, { useState } from "react";
import { Bar as ChartJSBar, Doughnut, Line, Pie, PolarArea, Radar, Scatter } from 'react-chartjs-2';
import apiService from '../services/api';

// Chart data interface for frontend components
interface ChartDataFromBackend {
    title: string;
    type: 'line' | 'bar' | 'pie' | 'doughnut' | 'area' | 'scatter' | 'horizontalBar' | 'polarArea' | 'radar';
    labels: string[];
    data: number[];
    description?: string;
    backgroundColor?: string | string[];
    borderColor?: string | string[];
    insights?: string[];
    id?: string;
    createdAt?: number;
    updatedAt?: number;
}

// Register Chart.js components
ChartJS.register(
    CategoryScale,
    LinearScale,
    RadialLinearScale,
    PointElement,
    LineElement,
    BarElement,
    ArcElement,
    Title,
    ChartTooltip,
    Legend,
    Filler
);

interface Opportunity {
    opportunity_description: string;
    opportunity_type: string;
    urgency: string;
    market_size_potential: string;
    competitive_advantage: string;
}

interface Gap {
    gap_description: string;
    impact_level: string;
    gap_category: string;
    evidence: string;
}

interface TrendAnalysis {
    trend_based_opportunities: string[];
    emerging_trends: string[];
    trend_implications: string[];
}

interface CompetitiveInsights {
    competitive_weaknesses: string[];
    competitive_strengths: string[];
    market_positioning: string;
    differentiation_opportunities: string[];
}

interface Risk {
    risk_description: string;
    risk_type: string;
    mitigation_strategy: string;
    probability: string;
}

interface Recommendation {
    recommendation: string;
    priority: string;
    implementation_complexity: string;
    expected_impact: string;
}

interface ReportData {
    market_opportunities?: Opportunity[];
    market_gaps?: Gap[];
    trend_analysis?: TrendAnalysis;
    competitive_insights?: CompetitiveInsights;
    risk_assessment?: Risk[];
    strategic_recommendations?: Recommendation[];
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

interface BackendResponse {
    status: string;
    message?: string;
    data: {
        report_data: ReportData;
        report_markdown?: string;
        company?: string;
        sector?: string;
        service?: string;
    };
    analytics?: {
        execution_time: string;
        processing_speed: string;
        report_quality: string;
        data_sources?: string[];
    };
}

interface ChatMessage {
    id: string;
    text: string;
    isBot: boolean;
    timestamp: Date;
}

// Chart rendering component for backend generated charts
const BackendChart = ({ chart }: { chart: ChartDataFromBackend }) => {
    const { title, type, labels, data, description, backgroundColor, borderColor, insights } = chart;

    // Define vibrant color palettes for different chart types
    const getChartColors = () => {
        const colorPalettes = {
            pie: {
                background: [
                    'rgba(236, 72, 153, 0.8)',    // Pink
                    'rgba(59, 130, 246, 0.8)',    // Blue
                    'rgba(16, 185, 129, 0.8)',    // Emerald
                    'rgba(245, 158, 11, 0.8)',    // Amber
                    'rgba(139, 92, 246, 0.8)',    // Violet
                    'rgba(239, 68, 68, 0.8)',     // Red
                    'rgba(34, 197, 94, 0.8)',     // Green
                    'rgba(168, 85, 247, 0.8)',    // Purple
                    'rgba(6, 182, 212, 0.8)',     // Cyan
                    'rgba(251, 146, 60, 0.8)',    // Orange
                ],
                border: [
                    'rgba(236, 72, 153, 1)',
                    'rgba(59, 130, 246, 1)',
                    'rgba(16, 185, 129, 1)',
                    'rgba(245, 158, 11, 1)',
                    'rgba(139, 92, 246, 1)',
                    'rgba(239, 68, 68, 1)',
                    'rgba(34, 197, 94, 1)',
                    'rgba(168, 85, 247, 1)',
                    'rgba(6, 182, 212, 1)',
                    'rgba(251, 146, 60, 1)',
                ]
            },
            doughnut: {
                background: [
                    'rgba(99, 102, 241, 0.8)',    // Indigo
                    'rgba(244, 63, 94, 0.8)',     // Rose
                    'rgba(14, 165, 233, 0.8)',    // Sky
                    'rgba(101, 163, 13, 0.8)',    // Lime
                    'rgba(217, 70, 239, 0.8)',    // Fuchsia
                    'rgba(220, 38, 127, 0.8)',    // Pink
                    'rgba(5, 150, 105, 0.8)',     // Emerald
                    'rgba(202, 138, 4, 0.8)',     // Yellow
                    'rgba(147, 51, 234, 0.8)',    // Purple
                    'rgba(249, 115, 22, 0.8)',    // Orange
                ],
                border: [
                    'rgba(99, 102, 241, 1)',
                    'rgba(244, 63, 94, 1)',
                    'rgba(14, 165, 233, 1)',
                    'rgba(101, 163, 13, 1)',
                    'rgba(217, 70, 239, 1)',
                    'rgba(220, 38, 127, 1)',
                    'rgba(5, 150, 105, 1)',
                    'rgba(202, 138, 4, 1)',
                    'rgba(147, 51, 234, 1)',
                    'rgba(249, 115, 22, 1)',
                ]
            },
            line: {
                background: 'rgba(59, 130, 246, 0.2)',
                border: 'rgba(59, 130, 246, 1)'
            },
            area: {
                background: 'rgba(16, 185, 129, 0.3)',
                border: 'rgba(16, 185, 129, 1)'
            },
            bar: {
                background: 'rgba(245, 158, 11, 0.8)',
                border: 'rgba(245, 158, 11, 1)'
            },
            horizontalBar: {
                background: 'rgba(139, 92, 246, 0.8)',
                border: 'rgba(139, 92, 246, 1)'
            },
            scatter: {
                background: 'rgba(236, 72, 153, 0.7)',
                border: 'rgba(236, 72, 153, 1)'
            },
            polarArea: {
                background: [
                    'rgba(255, 99, 132, 0.7)',
                    'rgba(54, 162, 235, 0.7)',
                    'rgba(255, 205, 86, 0.7)',
                    'rgba(75, 192, 192, 0.7)',
                    'rgba(153, 102, 255, 0.7)',
                    'rgba(255, 159, 64, 0.7)',
                ],
                border: [
                    'rgba(255, 99, 132, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 205, 86, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(153, 102, 255, 1)',
                    'rgba(255, 159, 64, 1)',
                ]
            },
            radar: {
                background: 'rgba(99, 102, 241, 0.3)',
                border: 'rgba(99, 102, 241, 1)'
            }
        };

        const palette = colorPalettes[type] || colorPalettes.bar;
        return {
            backgroundColor: backgroundColor || palette.background,
            borderColor: borderColor || palette.border
        };
    };

    const colors = getChartColors();

    // Create chart data object
    const chartData = {
        labels: type === 'scatter' ? undefined : labels,
        datasets: [
            {
                label: title,
                data: type === 'scatter'
                    ? data.map((value, index) => ({ x: index + 1, y: value }))
                    : data,
                backgroundColor: colors.backgroundColor,
                borderColor: colors.borderColor,
                borderWidth: type === 'line' || type === 'area' ? 3 : 2,
                fill: type === 'area' ? true : type === 'line' ? false : undefined,
                tension: type === 'line' || type === 'area' ? 0.4 : undefined,
                pointRadius: type === 'scatter' ? 8 : type === 'line' ? 6 : undefined,
                pointHoverRadius: type === 'scatter' ? 12 : type === 'line' ? 8 : undefined,
                pointBackgroundColor: type === 'line' ? colors.borderColor : undefined,
                pointBorderColor: type === 'line' ? '#ffffff' : undefined,
                pointBorderWidth: type === 'line' ? 2 : undefined,
            },
        ],
    };

    // Configure chart options based on type
    const getChartOptions = () => {
        const baseOptions = {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index' as const,
            },
            animations: {
                tension: {
                    duration: 1000,
                    easing: 'linear' as const,
                    from: 1,
                    to: 0,
                    loop: false
                }
            },
            plugins: {
                legend: {
                    position: 'top' as const,
                    labels: {
                        usePointStyle: true,
                        pointStyle: 'circle',
                        padding: 20,
                        font: {
                            size: 12,
                            weight: 'bold' as const,
                        },
                        color: '#475569',
                    }
                },
                title: {
                    display: true,
                    text: title,
                    font: {
                        size: 18,
                        weight: 'bold' as const,
                    },
                    color: '#1e293b',
                    padding: {
                        top: 10,
                        bottom: 30
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                    titleColor: '#f8fafc',
                    bodyColor: '#e2e8f0',
                    borderColor: '#334155',
                    borderWidth: 1,
                    cornerRadius: 8,
                    displayColors: true,
                    padding: 12,
                }
            },
        };

        // For charts that don't need scales (or have custom scales)
        if (type === 'pie' || type === 'doughnut' || type === 'polarArea' || type === 'radar') {
            return baseOptions;
        }

        // For charts that need scales
        return {
            ...baseOptions,
            indexAxis: type === 'horizontalBar' ? 'y' as const : undefined,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(148, 163, 184, 0.2)',
                        drawBorder: false,
                    },
                    ticks: {
                        color: '#64748b',
                        font: {
                            size: 12,
                        },
                        padding: 8,
                    },
                    title: {
                        display: false,
                    }
                },
                x: type === 'scatter'
                    ? {
                        type: 'linear' as const,
                        position: 'bottom' as const,
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(148, 163, 184, 0.2)',
                            drawBorder: false,
                        },
                        ticks: {
                            color: '#64748b',
                            font: {
                                size: 12,
                            },
                            padding: 8,
                        },
                    }
                    : {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(148, 163, 184, 0.2)',
                            drawBorder: false,
                        },
                        ticks: {
                            color: '#64748b',
                            font: {
                                size: 12,
                            },
                            padding: 8,
                        },
                    },
            },
        };
    };

    const options = getChartOptions();

    // Select the appropriate chart component based on type
    const renderChart = () => {
        switch (type) {
            case 'line':
                return <Line data={chartData} options={options} />;
            case 'bar':
                return <ChartJSBar data={chartData} options={options} />;
            case 'horizontalBar':
                // Horizontal bar chart is just a bar chart with indexAxis: 'y'
                return <ChartJSBar data={chartData} options={options} />;
            case 'pie':
                return <Pie data={chartData} options={getChartOptions()} />;
            case 'doughnut':
                return <Doughnut data={chartData} options={getChartOptions()} />;
            case 'polarArea':
                // PolarArea charts use radial scales, so we need different options
                return <PolarArea data={chartData} options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top' as const,
                        },
                        title: {
                            display: true,
                            text: title,
                            font: {
                                size: 16,
                                weight: 'bold' as const,
                            },
                        },
                    },
                }} />;
            case 'area':
                // Area chart is essentially a line chart with fill
                return <Line data={chartData} options={options} />;
            case 'scatter':
                return <Scatter data={chartData} options={options} />;
            case 'radar':
                return <Radar data={chartData} options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top' as const,
                            labels: {
                                color: '#374151',
                                font: {
                                    size: 12,
                                    weight: 'normal' as const,
                                },
                                padding: 20,
                                usePointStyle: true,
                            }
                        },
                        title: {
                            display: true,
                            text: title,
                            font: {
                                size: 18,
                                weight: 'bold' as const,
                            },
                            color: '#1e293b',
                            padding: {
                                top: 10,
                                bottom: 30
                            }
                        },
                    },
                    scales: {
                        r: {
                            beginAtZero: true,
                            grid: {
                                color: 'rgba(148, 163, 184, 0.2)',
                            },
                            pointLabels: {
                                color: '#64748b',
                                font: {
                                    size: 11,
                                },
                            },
                            ticks: {
                                color: '#64748b',
                                font: {
                                    size: 10,
                                },
                                backdropColor: 'rgba(255, 255, 255, 0.8)',
                            },
                        }
                    },
                }} />;
            default:
                return (
                    <div className="flex items-center justify-center h-64 bg-slate-100 rounded-lg">
                        <p className="text-slate-500">Unsupported chart type: {type}</p>
                    </div>
                );
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gradient-to-br from-white to-slate-50 rounded-xl shadow-lg shadow-slate-200/50 border border-slate-200 p-6 hover:shadow-xl hover:shadow-slate-200/70 transition-all duration-300"
        >
            <div className="h-80 mb-4 p-2">
                {renderChart()}
            </div>
            {description && (
                <div className="text-sm text-slate-700 italic pt-4 mb-4 bg-slate-50 rounded-lg p-3 border border-slate-200">
                    {description}
                </div>
            )}
            {insights && insights.length > 0 && (
                <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4">
                    <h5 className="font-semibold text-blue-900 mb-3 flex items-center">
                        <TrendingUp className="w-4 h-4 mr-2" />
                        Key Insights
                    </h5>
                    <div className="space-y-2">
                        {insights.map((insight, index) => (
                            <div key={index} className="flex items-start space-x-3 p-2 bg-white/70 rounded-lg">
                                <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                                <span className="text-sm text-blue-800 leading-relaxed">{insight}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </motion.div>
    );
};

interface ChatMessage {
    id: string;
    text: string;
    isBot: boolean;
    timestamp: Date;
    // Charts are no longer part of chat messages - they only appear in the Generated Charts Section
}

interface ReportComponentProps {
    reportData?: ReportData | BackendResponse;
    dataCharts?: ChartDataFromBackend[];
    title?: string;
    description?: string;
    showChat?: boolean;
    className?: string;
}

const ReportComponent: React.FC<ReportComponentProps> = ({
    reportData: rawReportData,
    dataCharts,
    title = "Comprehensive Report",
    description = "Detailed analysis with integrated AI assistant",
    showChat = true,
    className = "",
}) => {
    // Transform backend response to expected format
    const getReportData = (): ReportData | null => {
        if (!rawReportData) return null;

        // Check if it's a backend response
        if ('status' in rawReportData && 'data' in rawReportData) {
            const backendResponse = rawReportData as BackendResponse;
            return backendResponse.data.report_data;
        }

        // Otherwise, it's already in the expected format
        return rawReportData as ReportData;
    };

    const reportData = getReportData();

    // Generate session ID using centralized function
    const [sessionId] = useState<string>(() => apiService.generateSessionId());

    // State for dynamic charts from AI
    const [dynamicCharts, setDynamicCharts] = useState<ChartDataFromBackend[]>([]);
    const [lastChartOperation, setLastChartOperation] = useState<{ type: 'update' | 'add', count: number } | null>(null);

    const [messages, setMessages] = useState<ChatMessage[]>([
        {
            id: "1",
            text: "Hello! I'm here to help you understand your analysis report. I can also generate custom charts and visualizations based on your questions. What would you like to know?",
            isBot: true,
            timestamp: new Date(),
        },
    ]);
    const [inputValue, setInputValue] = useState("");
    const [isTyping, setIsTyping] = useState(false);
    const [activeFilter, setActiveFilter] = useState("all");

    const filters = [
        { id: "all", label: "Show All" },
        { id: "charts", label: "Charts & Visualizations" },
        { id: "opportunities", label: "Opportunities" },
        { id: "gaps", label: "Gaps" },
        { id: "trends", label: "Trends" },
        { id: "competitive", label: "Competitive" },
        { id: "risks", label: "Risks" },
        { id: "recommendations", label: "Recommendations" },
    ];

    // Helper function to create chat messages
    const formatChatMessage = (id: string, text: string, isBot: boolean): ChatMessage => ({
        id,
        text,
        isBot,
        timestamp: new Date(),
    });

    const handleSendMessage = async () => {
        if (!inputValue.trim()) return;

        const userMessage: ChatMessage = formatChatMessage(
            Date.now().toString(),
            inputValue,
            false
        );

        setMessages((prev) => [...prev, userMessage]);
        const currentPrompt = inputValue;
        setInputValue("");
        setIsTyping(true);

        // Check if this is a chart request for extended loading feedback
        const isChartRequest = currentPrompt.toLowerCase().includes('chart') ||
            currentPrompt.toLowerCase().includes('graph') ||
            currentPrompt.toLowerCase().includes('visualiz');

        // Show extended loading message for chart requests after 15 seconds
        let extendedLoadingTimeout: number | null = null;
        if (isChartRequest) {
            extendedLoadingTimeout = setTimeout(() => {
                if (isTyping) {
                    // Add a temporary message about extended processing
                    const extendedLoadingMessage: ChatMessage = formatChatMessage(
                        `temp-loading-${Date.now()}`,
                        "🔄 Generating complex charts takes time... Please wait while I create your visualization.",
                        true
                    );
                    setMessages((prev) => [...prev, extendedLoadingMessage]);
                }
            }, 15000);
        }

        try {
            // Use centralized chatbot processing - collect all available charts
            const allCharts = [...(dataCharts || []), ...dynamicCharts];

            // Ensure all charts have the required properties for the API
            const normalizedCharts = allCharts.map((chart, index) => ({
                id: chart.id || `chart-${index}`,
                title: chart.title || `Chart ${index + 1}`,
                type: chart.type || 'bar',
                labels: chart.labels || [],
                data: chart.data || [],
                backgroundColor: chart.backgroundColor,
                borderColor: chart.borderColor,
                description: chart.description,
                insights: chart.insights,
                createdAt: chart.createdAt,
                updatedAt: chart.updatedAt
            }));

            // Enhanced logging for debugging
            console.log(`📊 Sending ${normalizedCharts.length} charts to API:`, {
                dataCharts: dataCharts?.length || 0,
                dynamicCharts: dynamicCharts.length,
                totalCharts: normalizedCharts.length,
                chartTitles: normalizedCharts.map(chart => chart.title)
            });

            // Use default export with all functions
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const response = await (apiService as any).processChatbotMessage(
                currentPrompt,
                sessionId,
                normalizedCharts,
                reportData || undefined
            );

            // Comprehensive response logging for debugging
            console.log('🔍 Full API response structure:', {
                success: response.success,
                type: response.type,
                hasMessage: !!response.message,
                message: response.message?.substring(0, 100) + '...',
                hasCharts: !!response.charts,
                chartsCount: response.charts?.length || 0,
                hasData: !!response.data,
                dataStructure: response.data ? {
                    hasCharts: !!response.data.charts,
                    chartsInData: response.data.charts?.length || 0,
                    hasAnalytics: !!response.data.analytics,
                    dataKeys: Object.keys(response.data),
                    // Enhanced analytics logging
                    analytics: response.data.analytics ? {
                        execution_time: response.data.analytics.execution_time,
                        request_type: response.data.analytics.request_type,
                        regeneration_scope: response.data.analytics.regeneration_scope,
                        processing_description: response.data.analytics.processing_description,
                        charts_generated: response.data.analytics.charts_generated,
                        data_categories: response.data.analytics.data_categories,
                        processing_mode: response.data.analytics.processing_mode,
                        user_intent_detected: response.data.analytics.user_intent_detected,
                        preferences_applied: response.data.analytics.preferences_applied,
                        performance: response.data.analytics.performance
                    } : null,
                    // Enhanced metadata logging
                    metadata: response.data.metadata ? {
                        agent_type: response.data.metadata.agent_type,
                        agent_features: response.data.metadata.agent_features,
                        api_version: response.data.metadata.api_version,
                        timestamp: response.data.metadata.timestamp
                    } : null
                } : null
            });

            if (response.success) {
                console.log('✅ Successful response received:', {
                    type: response.type,
                    hasCharts: !!response.charts,
                    chartsCount: response.charts?.length || 0,
                    // eslint-disable-next-line @typescript-eslint/no-explicit-any
                    chartTitles: response.charts?.map((chart: any) => chart.title) || [],
                    hasData: !!response.data,
                    dataKeys: response.data ? Object.keys(response.data) : []
                });

                // Handle chart responses
                if (response.type === 'chart_response' && response.charts && response.charts.length > 0) {
                    let chartsUpdated = 0;
                    let chartsAdded = 0;

                    // Update dynamic charts state with new or updated charts
                    setDynamicCharts(prev => {
                        const updatedCharts = [...prev];

                        response.charts.forEach((newChart: ChartDataFromBackend) => {
                            // Enhanced matching logic for chart replacement with unique ID generation
                            const chartId = `${newChart.title}-${newChart.type}`.toLowerCase().replace(/\s+/g, '-');

                            const existingIndex = updatedCharts.findIndex(chart => {
                                const existingId = `${chart.title}-${chart.type}`.toLowerCase().replace(/\s+/g, '-');

                                // Match by generated ID first
                                if (existingId === chartId) {
                                    return true;
                                }

                                // Match by title (exact match - case insensitive)
                                if (chart.title.toLowerCase() === newChart.title.toLowerCase()) {
                                    return true;
                                }

                                // Match by type and similar data structure for regeneration
                                if (chart.type === newChart.type) {
                                    // For regeneration, check if labels are similar or data length matches
                                    const labelsMatch = JSON.stringify(chart.labels) === JSON.stringify(newChart.labels);
                                    const similarDataLength = chart.data.length === newChart.data.length;

                                    // If it's a regeneration request, match charts with similar structure
                                    if (labelsMatch || similarDataLength) {
                                        return true;
                                    }
                                }

                                return false;
                            });

                            if (existingIndex >= 0) {
                                // Replace existing chart (regeneration)
                                updatedCharts[existingIndex] = {
                                    ...newChart,
                                    // Add a timestamp to help with React re-rendering
                                    id: chartId,
                                    updatedAt: Date.now()
                                };
                                chartsUpdated++;
                            } else {
                                // Add new chart
                                updatedCharts.push({
                                    ...newChart,
                                    id: chartId,
                                    createdAt: Date.now()
                                });
                                chartsAdded++;
                            }
                        });

                        return updatedCharts;
                    });

                    // Track the operation for UI feedback
                    setLastChartOperation({
                        type: chartsUpdated > 0 ? 'update' : 'add',
                        count: chartsUpdated + chartsAdded
                    });                    // Create enhanced message based on operation type
                    let chatMessage = "";

                    if (chartsUpdated > 0 && chartsAdded === 0) {
                        // Only regenerated charts
                        chatMessage = `✅ Successfully regenerated ${chartsUpdated} chart(s)! Check the Charts & Visualizations section above to see the updated charts.`;
                    } else if (chartsAdded > 0 && chartsUpdated === 0) {
                        // Only new charts
                        chatMessage = `✅ Successfully generated ${chartsAdded} new chart(s)! Check the Charts & Visualizations section above to see your new charts.`;
                    } else if (chartsUpdated > 0 && chartsAdded > 0) {
                        // Both regenerated and new
                        chatMessage = `✅ Successfully regenerated ${chartsUpdated} chart(s) and generated ${chartsAdded} new chart(s)! Check the Charts & Visualizations section above to see all your charts.`;
                    } else {
                        // Fallback message
                        chatMessage = `✅ Charts generated successfully! Check the Charts & Visualizations section above to view them.`;
                    }

                    // Add comprehensive analytics information if available
                    if (response.data && response.data.analytics) {
                        const analytics = response.data.analytics;
                        console.log('📊 Chart generation analytics:', analytics);

                        // Core performance metrics
                        if (analytics.execution_time) {
                            chatMessage += ` ⚡ Generated in ${analytics.execution_time}.`;
                        }
                        if (analytics.regeneration_scope) {
                            chatMessage += ` 🎯 Scope: ${analytics.regeneration_scope}.`;
                        }
                        if (analytics.charts_generated) {
                            chatMessage += ` 📈 Created ${analytics.charts_generated} visualizations.`;
                        }

                        // Enhanced analytics from backend
                        if (analytics.processing_description) {
                            chatMessage += ` ${analytics.processing_description}.`;
                        }
                        if (analytics.performance?.speed && analytics.performance.speed !== 'instant') {
                            chatMessage += ` 🏃‍♂️ Speed: ${analytics.performance.speed}.`;
                        }
                        if (analytics.performance?.efficiency) {
                            chatMessage += ` 🎯 Mode: ${analytics.performance.efficiency}.`;
                        }

                        // Data processing metrics
                        if (analytics.data_categories && analytics.data_categories > 0) {
                            chatMessage += ` 📊 Processed ${analytics.data_categories} data categories.`;
                        }
                        if (analytics.existing_charts_processed && analytics.existing_charts_processed > 0) {
                            chatMessage += ` 🔄 Updated from ${analytics.existing_charts_processed} existing charts.`;
                        }

                        // User experience features
                        if (analytics.preferences_applied) {
                            chatMessage += ` 🎨 Applied your preferences.`;
                        }
                        if (analytics.user_intent_detected) {
                            chatMessage += ` 🧠 Smart intent detection used.`;
                        }
                    }

                    // Create bot message WITHOUT charts (charts will be displayed in the main section only)
                    const botMessage: ChatMessage = formatChatMessage(
                        (Date.now() + 1).toString(),
                        chatMessage,
                        true
                        // Remove charts parameter - they will only be displayed in the Generated Charts Section
                    );

                    setMessages((prev) => [...prev, botMessage]);
                } else if (response.success && response.data?.charts && response.data.charts.length > 0) {
                    // Handle case where charts are directly in response.data.charts (backup)
                    console.log('📊 Found charts in response.data.charts:', response.data.charts.length);
                    const chartsFromData = response.data.charts;

                    setDynamicCharts(prev => {
                        const updatedCharts = [...prev];
                        chartsFromData.forEach((newChart: ChartDataFromBackend) => {
                            const chartId = `${newChart.title}-${newChart.type}`.toLowerCase().replace(/\s+/g, '-');
                            updatedCharts.push({
                                ...newChart,
                                id: chartId,
                                createdAt: Date.now()
                            });
                        });
                        return updatedCharts;
                    });

                    const botMessage: ChatMessage = formatChatMessage(
                        (Date.now() + 1).toString(),
                        `✅ Successfully generated ${chartsFromData.length} chart(s)! Check the Charts & Visualizations section above to see your new charts.`,
                        true
                    );
                    setMessages((prev) => [...prev, botMessage]);
                } else {
                    // Handle text/data responses - show the actual response content
                    const botMessage: ChatMessage = formatChatMessage(
                        (Date.now() + 1).toString(),
                        response.message,
                        true
                    );

                    setMessages((prev) => [...prev, botMessage]);
                }
            } else {
                // Handle failed responses with enhanced backend error information
                console.log('❌ Failed response received:', {
                    success: response.success,
                    type: response.type,
                    error: response.error,
                    message: response.message,
                    // Check for backend's detailed error structure
                    hasDetailedError: !!response.detail,
                    detail: response.detail
                });

                let errorMessage;

                // Check if backend provided detailed error information
                if (response.detail && typeof response.detail === 'object') {
                    const detail = response.detail;

                    // Use backend's helpful message if available
                    if (detail.helpful_message) {
                        errorMessage = `❌ ${detail.error || 'Request failed'}\n\n${detail.helpful_message}`;

                        // Add troubleshooting suggestions if available
                        if (detail.troubleshooting?.suggestions?.length > 0) {
                            errorMessage += `\n\n💡 Suggestions:\n• ${detail.troubleshooting.suggestions.slice(0, 2).join('\n• ')}`;
                        }
                    } else {
                        // Fallback to detail.error or standard message
                        errorMessage = `❌ ${detail.error || 'Failed to process request'}`;
                    }
                } else {
                    // Standard error handling
                    errorMessage = response.type === 'chart_response' || response.type === 'fallback_response'
                        ? `❌ Failed to generate charts. ${response.error ? `Error: ${response.error}` : 'Please try again.'}`
                        : response.message || "❌ I encountered an issue processing your request. Please try again.";
                }

                const botMessage: ChatMessage = formatChatMessage(
                    (Date.now() + 1).toString(),
                    errorMessage,
                    true
                );

                setMessages((prev) => [...prev, botMessage]);
            }
        } catch (error: unknown) {
            console.error('Error processing message:', error);

            // Determine if this was a chart request that failed
            const isChartRequestCheck = currentPrompt.toLowerCase().includes('chart') ||
                currentPrompt.toLowerCase().includes('graph') ||
                currentPrompt.toLowerCase().includes('visualiz');

            let errorMessage;

            // Enhanced error handling for backend HTTP exceptions
            const errorObj = error as {
                code?: string;
                message?: string;
                response?: {
                    status?: number;
                    data?: {
                        detail?: {
                            error?: string;
                            helpful_message?: string;
                            troubleshooting?: {
                                suggestions?: string[];
                            };
                        };
                    };
                }
            };

            // Check if it's a backend HTTP error with detailed information
            if (errorObj.response?.data?.detail) {
                const detail = errorObj.response.data.detail;

                if (detail.helpful_message) {
                    errorMessage = `❌ ${detail.error || 'Request failed'}\n\n${detail.helpful_message}`;

                    if (detail.troubleshooting?.suggestions?.length > 0) {
                        errorMessage += `\n\n💡 Try:\n• ${detail.troubleshooting.suggestions.slice(0, 2).join('\n• ')}`;
                    }
                } else {
                    errorMessage = `❌ ${detail.error || 'Server error occurred'}`;
                }
            }
            // Check if it's a timeout error
            else if (errorObj.code === 'ECONNABORTED' || errorObj.message?.includes('timeout')) {
                errorMessage = isChartRequestCheck
                    ? `⏳ Chart generation is taking longer than expected. This usually happens with complex visualizations. Please wait a moment and try again, or try a simpler chart request.`
                    : `⏳ Request timed out. Please try again with a simpler query.`;
            }
            // Check for server errors
            else if (errorObj.response?.status && errorObj.response.status >= 500) {
                errorMessage = isChartRequestCheck
                    ? `🔧 Server is currently processing heavy workloads. Chart generation may take longer than usual. Please try again in a moment.`
                    : `🔧 Server error occurred. Please try again.`;
            }
            // Check for client errors (400-499)
            else if (errorObj.response?.status && errorObj.response.status >= 400 && errorObj.response.status < 500) {
                errorMessage = isChartRequestCheck
                    ? `⚠️ Invalid chart request format. Please check your request and try again with clearer chart specifications.`
                    : `⚠️ Request format issue. Please rephrase your question and try again.`;
            }
            // Generic fallback
            else {
                errorMessage = isChartRequestCheck
                    ? `❌ Failed to generate charts. Please check your connection and try again.`
                    : `❌ I'm sorry, I encountered an error while processing your request. Please try again.`;
            }

            const botMessage: ChatMessage = formatChatMessage(
                (Date.now() + 1).toString(),
                errorMessage,
                true
            );

            setMessages((prev) => [...prev, botMessage]);
        } finally {
            setIsTyping(false);
            // Clean up the extended loading timeout
            if (extendedLoadingTimeout) {
                clearTimeout(extendedLoadingTimeout);
            }
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    const getUrgencyColor = (urgency: string) => {
        switch (urgency?.toLowerCase()) {
            case "high":
            case "elevated":
            case "immediate":
                return "text-red-600";
            case "medium":
            case "moderate":
            case "short_term":
                return "text-orange-600";
            case "low":
            case "weak":
                return "text-green-600";
            default:
                return "text-slate-600";
        }
    };

    const getPriorityColor = (priority: string) => {
        switch (priority?.toLowerCase()) {
            case "high":
                return "text-red-600 bg-red-50 border-red-200";
            case "medium":
                return "text-orange-600 bg-orange-50 border-orange-200";
            case "low":
                return "text-green-600 bg-green-50 border-green-200";
            default:
                return "text-slate-600 bg-slate-50 border-slate-200";
        }
    };

    const getComplexityColor = (complexity: string) => {
        switch (complexity?.toLowerCase()) {
            case "high":
            case "élevé":
                return "text-red-600";
            case "medium":
            case "moyen":
                return "text-orange-600";
            case "low":
            case "faible":
                return "text-green-600";
            default:
                return "text-slate-600";
        }
    };

    const getProbabilityColor = (probability: string) => {
        switch (probability?.toLowerCase()) {
            case "high":
                return "text-red-600";
            case "medium":
                return "text-orange-600";
            case "low":
                return "text-green-600";
            default:
                return "text-slate-600";
        }
    };

    if (!reportData) {
        return (
            <div className={`space-y-6 ${className}`}>
                <div className="bg-white rounded-xl p-8 shadow-lg shadow-slate-200/50 border border-slate-200 text-center">
                    <FileText className="w-16 h-16 text-slate-400 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-slate-900 mb-2">
                        No Report Data Available
                    </h3>
                    <p className="text-slate-600">
                        Generate a report to view detailed analysis here.
                    </p>
                </div>
            </div>
        );
    }

    const chatSection = showChat && (
        <div className="lg:col-span-1">
            <motion.div
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.4 }}
                className="bg-white rounded-xl shadow-lg shadow-slate-200/50 border border-slate-200 min-h-[calc(100vh-7rem)] flex flex-col sticky top-24"
            >
                <div className="bg-gradient-to-r from-blue-50 to-emerald-50 px-6 py-4 border-b border-slate-200 rounded-t-xl">
                    <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-emerald-600 rounded-full flex items-center justify-center">
                            <Bot className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h4 className="font-semibold text-slate-900">AI Assistant</h4>
                            <p className="text-sm text-slate-600">
                                Ask questions about the report
                            </p>
                        </div>
                    </div>
                </div>
                <div className="flex-1 overflow-y-auto p-6 space-y-4">
                    {messages.map((message) => (
                        <div
                            key={message.id}
                            className={`flex ${message.isBot ? "justify-start" : "justify-end"
                                }`}
                        >
                            <div
                                className={`flex items-start space-x-2 max-w-[85%] ${message.isBot
                                    ? "flex-row"
                                    : "flex-row-reverse space-x-reverse"
                                    }`}
                            >
                                <div
                                    className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${message.isBot
                                        ? "bg-gradient-to-r from-blue-600 to-emerald-600"
                                        : "bg-slate-600"
                                        }`}
                                >
                                    {message.isBot ? (
                                        <Bot className="w-4 h-4 text-white" />
                                    ) : (
                                        <User className="w-4 h-4 text-white" />
                                    )}
                                </div>
                                <div
                                    className={`rounded-2xl px-4 py-3 ${message.isBot
                                        ? "bg-slate-100 text-slate-900"
                                        : "bg-gradient-to-r from-blue-600 to-emerald-600 text-white"
                                        }`}
                                >
                                    <p className="text-sm leading-relaxed">{message.text}</p>
                                    {/* Charts are no longer displayed in chat - only in the Generated Charts Section */}
                                </div>
                            </div>
                        </div>
                    ))}
                    {isTyping && (
                        <div className="flex justify-start">
                            <div className="flex items-start space-x-2">
                                <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-600 to-emerald-600 flex items-center justify-center">
                                    <Bot className="w-4 h-4 text-white" />
                                </div>
                                <div className="bg-slate-100 rounded-2xl px-4 py-3">
                                    <div className="flex space-x-1">
                                        <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></div>
                                        <div
                                            className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"
                                            style={{ animationDelay: "0.1s" }}
                                        ></div>
                                        <div
                                            className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"
                                            style={{ animationDelay: "0.2s" }}
                                        ></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
                <div className="p-6 border-t border-slate-200">
                    <div className="flex space-x-2">
                        <input
                            type="text"
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            onKeyPress={handleKeyPress}
                            placeholder="Ask questions or request charts (e.g., 'create a pie chart of opportunities')..."
                            disabled={isTyping}
                            className="flex-1 px-4 py-3 rounded-lg border border-slate-200 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 placeholder-slate-400 text-sm disabled:bg-slate-50 disabled:text-slate-400"
                        />
                        <button
                            onClick={handleSendMessage}
                            disabled={!inputValue.trim() || isTyping}
                            className={`px-4 py-3 rounded-lg transition-all duration-200 ${inputValue.trim() && !isTyping
                                ? "bg-gradient-to-r from-blue-600 to-emerald-600 text-white shadow-lg shadow-blue-500/25 hover:from-blue-700 hover:to-emerald-700"
                                : "bg-slate-200 text-slate-400 cursor-not-allowed"
                                }`}
                        >
                            <Send className="w-5 h-5" />
                        </button>
                    </div>
                </div>
            </motion.div>
        </div>
    );

    return (
        <div className={`space-y-6 ${className}`}>
            <div className="mb-6">
                <h2 className="text-2xl font-bold text-slate-900 mb-2">{title}</h2>
                <p className="text-slate-600">{description}</p>
            </div>

            <div className={`grid grid-cols-1 ${showChat ? "lg:grid-cols-3" : ""} gap-8`}>
                {/* Main Report Content */}
                <div className={`${showChat ? "lg:col-span-2" : ""} space-y-8`}>
                    {/* Filters */}
                    <motion.div
                        initial={{ y: 20, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        transition={{ delay: 0.1 }}
                        className="flex flex-wrap gap-2"
                    >
                        {filters.map((filter) => (
                            <button
                                key={filter.id}
                                onClick={() => setActiveFilter(filter.id)}
                                className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${activeFilter === filter.id
                                    ? "bg-blue-600 text-white shadow-lg shadow-blue-500/25"
                                    : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-50"
                                    }`}
                            >
                                <Filter className="w-4 h-4" />
                                <span>{filter.label}</span>
                            </button>
                        ))}
                    </motion.div>

                    {/* Generated Charts Section */}
                    {(activeFilter === "all" || activeFilter === "charts") && ((dataCharts && dataCharts.length > 0) || dynamicCharts.length > 0) && (
                        <motion.div
                            initial={{ y: 20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            transition={{ delay: 0.15 }}
                            className="bg-white rounded-xl p-8 shadow-lg shadow-slate-200/50 border border-slate-200"
                        >
                            <div className="flex items-center space-x-2 mb-6">
                                <PieChart className="w-6 h-6 text-purple-600" />
                                <h3 className="text-xl font-bold text-slate-900">
                                    AI-Generated Data Visualizations
                                </h3>
                                <span className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-xs font-medium">
                                    {(dataCharts?.length || 0) + dynamicCharts.length} Charts
                                </span>
                                {lastChartOperation && (
                                    <span className={`px-2 py-1 rounded-full text-xs font-medium ml-2 ${lastChartOperation.type === 'update'
                                        ? 'bg-blue-100 text-blue-700'
                                        : 'bg-green-100 text-green-700'
                                        }`}>
                                        {lastChartOperation.type === 'update' ? '🔄 Updated' : '✨ New'}
                                    </span>
                                )}
                            </div>
                            <p className="text-slate-600 mb-6">
                                Interactive charts and visualizations generated from your business analysis data and chat requests.
                            </p>

                            {/* Original charts from analysis */}
                            {dataCharts && dataCharts.length > 0 && (
                                <div className="mb-8">
                                    <h4 className="text-lg font-semibold text-slate-900 mb-4 flex items-center">
                                        <BarChart3 className="w-5 h-5 text-blue-600 mr-2" />
                                        Analysis Charts ({dataCharts.length})
                                    </h4>
                                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                        {dataCharts.map((chart, index) => (
                                            <BackendChart key={`original-${index}`} chart={chart} />
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Dynamic charts from chat */}
                            {dynamicCharts.length > 0 && (
                                <div>
                                    <h4 className="text-lg font-semibold text-slate-900 mb-4 flex items-center">
                                        <Bot className="w-5 h-5 text-emerald-600 mr-2" />
                                        AI Assistant Charts ({dynamicCharts.length})
                                        <span className="ml-2 px-2 py-1 bg-emerald-100 text-emerald-700 rounded-full text-xs">
                                            Live Updates
                                        </span>
                                    </h4>
                                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                        {dynamicCharts.map((chart, index) => (
                                            <motion.div
                                                key={chart.id || `dynamic-${chart.title}-${chart.type}-${index}`}
                                                initial={{ scale: 0.95, opacity: 0 }}
                                                animate={{ scale: 1, opacity: 1 }}
                                                transition={{ duration: 0.3, delay: index * 0.1 }}
                                                layout
                                            >
                                                <BackendChart chart={chart} />
                                            </motion.div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </motion.div>
                    )}

                    {/* Executive Summary */}
                    {activeFilter === "all" && (
                        <motion.div
                            initial={{ y: 20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            transition={{ delay: 0.2 }}
                            className="bg-white rounded-xl p-8 shadow-lg shadow-slate-200/50 border border-slate-200"
                        >
                            <div className="flex items-center space-x-2 mb-6">
                                <FileText className="w-6 h-6 text-blue-600" />
                                <h3 className="text-xl font-bold text-slate-900">Summary</h3>
                            </div>
                            <div className="prose prose-slate max-w-none">
                                <h4 className="text-lg font-semibold text-slate-900 mb-4 flex items-center">
                                    <TrendingUp className="w-5 h-5 text-emerald-600 mr-2" />
                                    Identified Opportunities ({reportData.market_opportunities?.length || 0})
                                </h4>
                                <ul className="space-y-3 mb-6">
                                    {reportData.market_opportunities?.slice(0, 3).map((opportunity, i) => (
                                        <li key={i} className="flex items-start space-x-3">
                                            <div className="w-2 h-2 bg-emerald-500 rounded-full mt-2 flex-shrink-0"></div>
                                            <span>
                                                <strong>{opportunity.opportunity_type}:</strong>{" "}
                                                {opportunity.opportunity_description}
                                                <span
                                                    className={`ml-2 text-sm ${getUrgencyColor(
                                                        opportunity.urgency
                                                    )}`}
                                                >
                                                    (Urgency: {opportunity.urgency})
                                                </span>
                                            </span>
                                        </li>
                                    ))}
                                </ul>

                                <h4 className="text-lg font-semibold text-slate-900 mb-4 flex items-center">
                                    <AlertTriangle className="w-5 h-5 text-orange-600 mr-2" />
                                    Strategic Gaps ({reportData.market_gaps?.length || 0})
                                </h4>
                                <ul className="space-y-3 mb-6">
                                    {reportData.market_gaps?.slice(0, 3).map((gap, i) => (
                                        <li key={i} className="flex items-start space-x-3">
                                            <div className="w-2 h-2 bg-orange-500 rounded-full mt-2 flex-shrink-0"></div>
                                            <span>
                                                <strong>{gap.gap_category}:</strong> {gap.gap_description}
                                                <span className="ml-2 text-sm text-orange-600">
                                                    (Impact: {gap.impact_level})
                                                </span>
                                            </span>
                                        </li>
                                    ))}
                                </ul>

                                <h4 className="text-lg font-semibold text-slate-900 mb-4 flex items-center">
                                    <Target className="w-5 h-5 text-blue-600 mr-2" />
                                    Competitive Positioning
                                </h4>
                                <div className="bg-slate-50 rounded-lg p-6">
                                    <p className="text-slate-700 mb-4">
                                        {reportData.competitive_insights?.market_positioning}
                                    </p>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        <div>
                                            <h5 className="font-semibold text-slate-900 mb-2">
                                                Identified Strengths
                                            </h5>
                                            <div className="w-full bg-slate-200 rounded-full h-2 mb-2">
                                                <div
                                                    className="bg-emerald-500 h-2 rounded-full"
                                                    style={{
                                                        width: `${Math.min(
                                                            (reportData.competitive_insights?.competitive_strengths?.length || 0) * 20,
                                                            100
                                                        )}%`,
                                                    }}
                                                ></div>
                                            </div>
                                            <span className="text-sm text-slate-600">
                                                {reportData.competitive_insights?.competitive_strengths?.length || 0}{" "}
                                                strengths identified
                                            </span>
                                        </div>
                                        <div>
                                            <h5 className="font-semibold text-slate-900 mb-2">
                                                Areas for Improvement
                                            </h5>
                                            <div className="w-full bg-slate-200 rounded-full h-2 mb-2">
                                                <div
                                                    className="bg-orange-500 h-2 rounded-full"
                                                    style={{
                                                        width: `${Math.min(
                                                            (reportData.competitive_insights?.competitive_weaknesses?.length || 0) * 20,
                                                            100
                                                        )}%`,
                                                    }}
                                                ></div>
                                            </div>
                                            <span className="text-sm text-slate-600">
                                                {reportData.competitive_insights?.competitive_weaknesses?.length || 0}{" "}
                                                weaknesses to address
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    )}

                    {/* Opportunities Section */}
                    {(activeFilter === "all" || activeFilter === "opportunities") && reportData.market_opportunities && (
                        <motion.div
                            initial={{ y: 20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            transition={{ delay: 0.3 }}
                            className="bg-white rounded-xl p-8 shadow-lg shadow-slate-200/50 border border-slate-200"
                        >
                            <div className="flex items-center space-x-2 mb-6">
                                <TrendingUp className="w-6 h-6 text-emerald-600" />
                                <h3 className="text-xl font-bold text-slate-900">
                                    Market Opportunities
                                </h3>
                            </div>
                            <div className="space-y-4">
                                {reportData.market_opportunities.map((opportunity, i) => (
                                    <div
                                        key={i}
                                        className="bg-emerald-50 border border-emerald-200 rounded-lg p-6"
                                    >
                                        <div className="flex items-start justify-between mb-3">
                                            <h4 className="font-semibold text-emerald-900 text-lg">
                                                {opportunity.opportunity_type}
                                            </h4>
                                            <span
                                                className={`px-3 py-1 rounded-full text-xs font-medium ${getUrgencyColor(
                                                    opportunity.urgency
                                                )} bg-white`}
                                            >
                                                {opportunity.urgency}
                                            </span>
                                        </div>
                                        <p className="text-slate-700 mb-3">
                                            {opportunity.opportunity_description}
                                        </p>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            <div>
                                                <span className="text-sm font-medium text-emerald-800">
                                                    Competitive Advantage:
                                                </span>
                                                <p className="text-sm text-emerald-700">
                                                    {opportunity.competitive_advantage}
                                                </p>
                                            </div>
                                            <div>
                                                <span className="text-sm font-medium text-emerald-800">
                                                    Market Potential:
                                                </span>
                                                <p className="text-sm text-emerald-700">
                                                    {opportunity.market_size_potential}
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </motion.div>
                    )}

                    {/* Gaps Section */}
                    {(activeFilter === "all" || activeFilter === "gaps") && reportData.market_gaps && (
                        <motion.div
                            initial={{ y: 20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            transition={{ delay: 0.4 }}
                            className="bg-white rounded-xl p-8 shadow-lg shadow-slate-200/50 border border-slate-200"
                        >
                            <div className="flex items-center space-x-2 mb-6">
                                <AlertTriangle className="w-6 h-6 text-orange-600" />
                                <h3 className="text-xl font-bold text-slate-900">
                                    Market Gaps
                                </h3>
                            </div>
                            <div className="space-y-4">
                                {reportData.market_gaps.map((gap, i) => (
                                    <div
                                        key={i}
                                        className="bg-orange-50 border border-orange-200 rounded-lg p-6"
                                    >
                                        <div className="flex items-start justify-between mb-3">
                                            <h4 className="font-semibold text-orange-900 text-lg">
                                                {gap.gap_category}
                                            </h4>
                                            <span
                                                className={`px-3 py-1 rounded-full text-xs font-medium ${getUrgencyColor(
                                                    gap.impact_level
                                                )} bg-white`}
                                            >
                                                {gap.impact_level}
                                            </span>
                                        </div>
                                        <p className="text-slate-700 mb-3">
                                            {gap.gap_description}
                                        </p>
                                        <div>
                                            <span className="text-sm font-medium text-orange-800">
                                                Evidence:
                                            </span>
                                            <p className="text-sm text-orange-700">
                                                {gap.evidence}
                                            </p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </motion.div>
                    )}

                    {/* Trends Section */}
                    {(activeFilter === "all" || activeFilter === "trends") && reportData.trend_analysis && (
                        <motion.div
                            initial={{ y: 20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            transition={{ delay: 0.5 }}
                            className="bg-white rounded-xl p-8 shadow-lg shadow-slate-200/50 border border-slate-200"
                        >
                            <div className="flex items-center space-x-2 mb-6">
                                <BarChart3 className="w-6 h-6 text-blue-600" />
                                <h3 className="text-xl font-bold text-slate-900">
                                    Trend Analysis
                                </h3>
                            </div>
                            <div className="space-y-6">
                                <div>
                                    <h4 className="text-lg font-semibold text-slate-900 mb-4">
                                        Emerging Trends
                                    </h4>
                                    <div className="space-y-2">
                                        {reportData.trend_analysis.emerging_trends?.map((trend, i) => (
                                            <div key={i} className="flex items-start space-x-3">
                                                <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                                                <span className="text-slate-700">{trend}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                <div>
                                    <h4 className="text-lg font-semibold text-slate-900 mb-4">
                                        Trend Implications
                                    </h4>
                                    <div className="space-y-2">
                                        {reportData.trend_analysis.trend_implications?.map((implication, i) => (
                                            <div key={i} className="flex items-start space-x-3">
                                                <div className="w-2 h-2 bg-emerald-500 rounded-full mt-2 flex-shrink-0"></div>
                                                <span className="text-slate-700">{implication}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                <div>
                                    <h4 className="text-lg font-semibold text-slate-900 mb-4">
                                        Trend-Based Opportunities
                                    </h4>
                                    <div className="space-y-2">
                                        {reportData.trend_analysis.trend_based_opportunities?.map((opportunity, i) => (
                                            <div key={i} className="flex items-start space-x-3">
                                                <div className="w-2 h-2 bg-purple-500 rounded-full mt-2 flex-shrink-0"></div>
                                                <span className="text-slate-700">{opportunity}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    )}

                    {/* Competitive Insights Section */}
                    {(activeFilter === "all" || activeFilter === "competitive") && reportData.competitive_insights && (
                        <motion.div
                            initial={{ y: 20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            transition={{ delay: 0.6 }}
                            className="bg-white rounded-xl p-8 shadow-lg shadow-slate-200/50 border border-slate-200"
                        >
                            <div className="flex items-center space-x-2 mb-6">
                                <Target className="w-6 h-6 text-indigo-600" />
                                <h3 className="text-xl font-bold text-slate-900">
                                    Competitive Analysis
                                </h3>
                            </div>
                            <div className="space-y-6">
                                <div className="bg-indigo-50 rounded-lg p-6">
                                    <h4 className="text-lg font-semibold text-indigo-900 mb-3">
                                        Market Positioning
                                    </h4>
                                    <p className="text-indigo-800">
                                        {reportData.competitive_insights.market_positioning}
                                    </p>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div>
                                        <h4 className="text-lg font-semibold text-slate-900 mb-4">
                                            Competitive Strengths
                                        </h4>
                                        <div className="space-y-2">
                                            {reportData.competitive_insights.competitive_strengths?.map((strength, i) => (
                                                <div key={i} className="flex items-start space-x-3">
                                                    <div className="w-2 h-2 bg-emerald-500 rounded-full mt-2 flex-shrink-0"></div>
                                                    <span className="text-slate-700">{strength}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    <div>
                                        <h4 className="text-lg font-semibold text-slate-900 mb-4">
                                            Areas for Improvement
                                        </h4>
                                        <div className="space-y-2">
                                            {reportData.competitive_insights.competitive_weaknesses?.map((weakness, i) => (
                                                <div key={i} className="flex items-start space-x-3">
                                                    <div className="w-2 h-2 bg-orange-500 rounded-full mt-2 flex-shrink-0"></div>
                                                    <span className="text-slate-700">{weakness}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>

                                <div>
                                    <h4 className="text-lg font-semibold text-slate-900 mb-4">
                                        Differentiation Opportunities
                                    </h4>
                                    <div className="space-y-2">
                                        {reportData.competitive_insights.differentiation_opportunities?.map((opportunity, i) => (
                                            <div key={i} className="flex items-start space-x-3">
                                                <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                                                <span className="text-slate-700">{opportunity}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    )}

                    {/* Strategic Recommendations Section */}
                    {(activeFilter === "all" || activeFilter === "recommendations") && reportData.strategic_recommendations && (
                        <motion.div
                            initial={{ y: 20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            transition={{ delay: 0.7 }}
                            className="bg-white rounded-xl p-8 shadow-lg shadow-slate-200/50 border border-slate-200"
                        >
                            <div className="flex items-center space-x-2 mb-6">
                                <Target className="w-6 h-6 text-purple-600" />
                                <h3 className="text-xl font-bold text-slate-900">
                                    Strategic Recommendations
                                </h3>
                            </div>
                            <div className="space-y-4">
                                {reportData.strategic_recommendations.map((recommendation, i) => (
                                    <div
                                        key={i}
                                        className="bg-purple-50 border border-purple-200 rounded-lg p-6"
                                    >
                                        <div className="flex items-start justify-between mb-3">
                                            <h4 className="font-semibold text-purple-900 text-lg flex-1 mr-4">
                                                {recommendation.recommendation}
                                            </h4>
                                            <span
                                                className={`px-3 py-1 rounded-full text-xs font-medium ${getPriorityColor(
                                                    recommendation.priority
                                                )}`}
                                            >
                                                {recommendation.priority}
                                            </span>
                                        </div>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                                            <div>
                                                <span className="text-sm font-medium text-purple-800">
                                                    Implementation Complexity:
                                                </span>
                                                <p className={`text-sm ${getComplexityColor(recommendation.implementation_complexity)}`}>
                                                    {recommendation.implementation_complexity}
                                                </p>
                                            </div>
                                            <div>
                                                <span className="text-sm font-medium text-purple-800">
                                                    Expected Impact:
                                                </span>
                                                <p className="text-sm text-purple-700">
                                                    {recommendation.expected_impact}
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </motion.div>
                    )}

                    {/* Risk Assessment Section */}
                    {(activeFilter === "all" || activeFilter === "risks") && reportData.risk_assessment && (
                        <motion.div
                            initial={{ y: 20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            transition={{ delay: 0.8 }}
                            className="bg-white rounded-xl p-8 shadow-lg shadow-slate-200/50 border border-slate-200"
                        >
                            <div className="flex items-center space-x-2 mb-6">
                                <Shield className="w-6 h-6 text-red-600" />
                                <h3 className="text-xl font-bold text-slate-900">
                                    Risk Assessment
                                </h3>
                            </div>
                            <div className="space-y-4">
                                {reportData.risk_assessment.map((risk, i) => (
                                    <div
                                        key={i}
                                        className="bg-red-50 border border-red-200 rounded-lg p-6"
                                    >
                                        <div className="flex items-start justify-between mb-3">
                                            <div className="flex-1">
                                                <h4 className="font-semibold text-red-900 text-lg mb-2">
                                                    {risk.risk_type}
                                                </h4>
                                                <p className="text-slate-700 mb-3">
                                                    {risk.risk_description}
                                                </p>
                                            </div>
                                            <span
                                                className={`px-3 py-1 rounded-full text-xs font-medium ${getProbabilityColor(
                                                    risk.probability
                                                )} bg-white ml-4`}
                                            >
                                                {risk.probability} probability
                                            </span>
                                        </div>
                                        <div className="bg-white rounded-lg p-4 border border-red-100">
                                            <span className="text-sm font-medium text-red-800">
                                                Mitigation Strategy:
                                            </span>
                                            <p className="text-sm text-red-700 mt-1">
                                                {risk.mitigation_strategy}
                                            </p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </motion.div>
                    )}

                    {/* Company Metadata */}
                    {reportData.metadata && (
                        <motion.div
                            initial={{ y: 20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            transition={{ delay: 0.9 }}
                            className="bg-slate-50 rounded-xl p-6 border border-slate-200"
                        >
                            <div className="flex items-center space-x-2 mb-4">
                                <Clock className="w-5 h-5 text-slate-600" />
                                <h4 className="font-semibold text-slate-900">Analysis Details</h4>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                                {reportData.metadata.company && (
                                    <div>
                                        <span className="font-medium text-slate-700">Company:</span>
                                        <p className="text-slate-600">{reportData.metadata.company}</p>
                                    </div>
                                )}
                                {reportData.metadata.sector && (
                                    <div>
                                        <span className="font-medium text-slate-700">Sector:</span>
                                        <p className="text-slate-600">{reportData.metadata.sector}</p>
                                    </div>
                                )}
                                {reportData.metadata.analysis_timestamp && (
                                    <div>
                                        <span className="font-medium text-slate-700">Generated:</span>
                                        <p className="text-slate-600">
                                            {new Date(reportData.metadata.analysis_timestamp).toLocaleDateString()}
                                        </p>
                                    </div>
                                )}
                            </div>
                            {reportData.metadata.data_sources && (
                                <div className="mt-4 pt-4 border-t border-slate-200">
                                    <span className="font-medium text-slate-700">Data Sources:</span>
                                    <div className="flex flex-wrap gap-2 mt-2">
                                        <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                                            {reportData.metadata.data_sources.trends_analyzed || 0} trends analyzed
                                        </span>
                                        <span className="text-xs bg-emerald-100 text-emerald-800 px-2 py-1 rounded">
                                            {reportData.metadata.data_sources.news_articles || 0} news articles
                                        </span>
                                        <span className="text-xs bg-orange-100 text-orange-800 px-2 py-1 rounded">
                                            {reportData.metadata.data_sources.competitor_pages || 0} competitor pages
                                        </span>
                                    </div>
                                </div>
                            )}
                        </motion.div>
                    )}

                    {/* Add other sections as needed based on activeFilter */}
                </div>

                {/* AI Chat Assistant */}
                {chatSection}
            </div>
        </div>
    );
};

export default ReportComponent;
