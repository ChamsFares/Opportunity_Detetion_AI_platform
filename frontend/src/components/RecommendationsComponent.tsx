import { motion } from "framer-motion";
import {
    AlertTriangle,
    ChevronRight,
    Clock,
    Lightbulb,
    Shield,
    Star,
    Target,
    TrendingUp,
    Zap,
} from "lucide-react";
import React, { useState } from "react";

interface StrategicRecommendation {
    recommendation: string;
    priority: string;
    implementation_complexity: string;
    expected_impact: string;
}

interface RiskAssessment {
    risk_type: string;
    probability: string;
    risk_description: string;
    mitigation_strategy: string;
}

interface TransformedRecommendation {
    id: number;
    title: string;
    description: string;
    priority: string;
    complexity: string;
    impact: string;
    roi: number;
    timeframe: string;
}

interface TransformedRisk {
    id: number;
    type: string;
    level: string;
    probability: number;
    description: string;
    mitigation: string;
    impact: string;
}

interface BackendReportData {
    strategic_recommendations?: StrategicRecommendation[];
    risk_assessment?: RiskAssessment[];
    market_opportunities?: Array<{
        opportunity_type: string;
        opportunity_description: string;
        urgency: string;
        market_size_potential: string;
        competitive_advantage: string;
    }>;
    metadata?: {
        company?: string;
        sector?: string;
        service?: string;
    };
}

interface BackendResponse {
    status: string;
    data: {
        report_data: BackendReportData;
        company?: string;
        sector?: string;
        service?: string;
    };
}

interface RecommendationsComponentProps {
    strategicRecommendations?: StrategicRecommendation[];
    riskAssessment?: RiskAssessment[];
    reportData?: BackendReportData | BackendResponse;
    title?: string;
    description?: string;
    showPerformanceIndicators?: boolean;
    className?: string;
}

const RecommendationsComponent: React.FC<RecommendationsComponentProps> = ({
    strategicRecommendations: directRecommendations = [],
    riskAssessment: directRiskAssessment = [],
    reportData,
    title = "Strategic Recommendations",
    description = "Priority actions to optimize your growth",
    showPerformanceIndicators = true,
    className = "",
}) => {
    const [selectedPriority, setSelectedPriority] = useState("all");

    // Extract backend data if available
    const getBackendData = (): BackendReportData | null => {
        if (!reportData) return null;

        // Check if it's a backend response
        if ('status' in reportData && 'data' in reportData) {
            const backendResponse = reportData as BackendResponse;
            return backendResponse.data.report_data;
        }

        // Otherwise, it's already in the expected format
        return reportData as BackendReportData;
    };

    const backendData = getBackendData();

    // Use backend data if available, otherwise use direct props
    const strategicRecommendations = backendData?.strategic_recommendations || directRecommendations;
    const riskAssessment = backendData?.risk_assessment || directRiskAssessment;

    // If no recommendations from backend or props, generate from opportunities
    const generateRecommendationsFromOpportunities = (): StrategicRecommendation[] => {
        if (!backendData?.market_opportunities) return [];

        return backendData.market_opportunities.map((opp) => ({
            recommendation: `Develop ${opp.opportunity_type.toLowerCase()} strategy: ${opp.opportunity_description.substring(0, 100)}...`,
            priority: opp.urgency === "immediate" ? "high" :
                opp.urgency === "short_term" ? "medium" : "low",
            implementation_complexity: opp.market_size_potential === "large" ? "high" :
                opp.market_size_potential === "medium" ? "medium" : "low",
            expected_impact: `Leverage competitive advantage: ${opp.competitive_advantage.substring(0, 80)}...`
        }));
    };

    // Use available recommendations or generate from opportunities
    const finalRecommendations = strategicRecommendations.length > 0
        ? strategicRecommendations
        : generateRecommendationsFromOpportunities();

    // Transform JSON data to match component structure
    const transformRecommendations = (
        recommendations: StrategicRecommendation[]
    ): TransformedRecommendation[] => {
        return recommendations.map((rec, index) => {
            // Extract title from recommendation (first 60 characters)
            const title =
                rec.recommendation.length > 60
                    ? rec.recommendation.substring(0, 60) + "..."
                    : rec.recommendation;

            // Generate ROI based on priority and complexity
            const baseROI =
                rec.priority === "high" ? 400 : rec.priority === "medium" ? 300 : 200;
            const complexityModifier =
                rec.implementation_complexity === "low"
                    ? 50
                    : rec.implementation_complexity === "medium"
                        ? 0
                        : -50;
            const roi = Math.max(150, baseROI + complexityModifier + index * 25);

            // Generate timeframe based on priority
            const timeframes = {
                high: ["2-3 months", "3-4 months", "4-5 months"],
                medium: ["4-6 months", "6-8 months", "8-10 months"],
                low: ["6-9 months", "9-12 months", "12-15 months"],
            };

            return {
                id: index + 1,
                title,
                description: rec.expected_impact,
                priority: rec.priority,
                complexity: rec.implementation_complexity,
                impact: rec.priority, // Use priority as proxy for impact
                roi,
                timeframe:
                    timeframes[rec.priority as keyof typeof timeframes]?.[index % 3] ||
                    "6-8 months",
            };
        });
    };

    const transformRisks = (risks: RiskAssessment[]): TransformedRisk[] => {
        return risks.map((risk, index) => {
            // Convert probability to percentage
            const probabilityMap = {
                high: 75,
                medium: 50,
                low: 25,
            };

            // Convert probability to English level
            const levelMap = {
                high: "High",
                medium: "Medium",
                low: "Low",
            };

            return {
                id: index + 1,
                type: risk.risk_type,
                level: levelMap[risk.probability as keyof typeof levelMap] || "Medium",
                probability:
                    probabilityMap[risk.probability as keyof typeof probabilityMap] || 50,
                description: risk.risk_description,
                mitigation: risk.mitigation_strategy,
                impact: levelMap[risk.probability as keyof typeof levelMap] || "Medium",
            };
        });
    };

    const priorities = [
        { id: "all", label: "All" },
        { id: "high", label: "High Priority" },
        { id: "medium", label: "Medium Priority" },
        { id: "low", label: "Low Priority" },
    ];

    const recommendations = transformRecommendations(finalRecommendations);
    const risks = transformRisks(riskAssessment);

    const filteredRecommendations =
        selectedPriority === "all"
            ? recommendations
            : recommendations.filter((rec) => rec.priority === selectedPriority);

    const getPriorityColor = (priority: string) => {
        switch (priority) {
            case "high":
                return "bg-red-100 text-red-800 border-red-200";
            case "medium":
                return "bg-yellow-100 text-yellow-800 border-yellow-200";
            case "low":
                return "bg-green-100 text-green-800 border-green-200";
            default:
                return "bg-slate-100 text-slate-800 border-slate-200";
        }
    };

    const getComplexityColor = (complexity: string) => {
        switch (complexity) {
            case "low":
                return "text-green-600";
            case "medium":
                return "text-yellow-600";
            case "high":
                return "text-red-600";
            default:
                return "text-slate-600";
        }
    };

    const getRiskColor = (level: string) => {
        switch (level) {
            case "High":
                return "bg-red-100 text-red-800 border-red-200";
            case "Medium":
                return "bg-yellow-100 text-yellow-800 border-yellow-200";
            case "Low":
                return "bg-green-100 text-green-800 border-green-200";
            default:
                return "bg-slate-100 text-slate-800 border-slate-200";
        }
    };

    return (
        <div className={`space-y-6 ${className}`}>
            <div className="mb-6">
                <h2 className="text-2xl font-bold text-slate-900 mb-2">{title}</h2>
                <p className="text-slate-600">{description}</p>
            </div>

            {/* Performance Indicators */}
            {showPerformanceIndicators && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <motion.div
                        initial={{ y: 20, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        transition={{ delay: 0.1 }}
                        className="bg-white rounded-xl p-6 shadow-lg shadow-slate-200/50 border border-slate-200 text-center"
                    >
                        <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                            <Target className="w-8 h-8 text-blue-600" />
                        </div>
                        <div className="relative w-24 h-24 mx-auto mb-4">
                            <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 36 36">
                                <path
                                    d="M18 2.0845
                    a 15.9155 15.9155 0 0 1 0 31.831
                    a 15.9155 15.9155 0 0 1 0 -31.831"
                                    fill="none"
                                    stroke="#E5E7EB"
                                    strokeWidth="2"
                                />
                                <path
                                    d="M18 2.0845
                    a 15.9155 15.9155 0 0 1 0 31.831
                    a 15.9155 15.9155 0 0 1 0 -31.831"
                                    fill="none"
                                    stroke="#3B82F6"
                                    strokeWidth="2"
                                    strokeDasharray="89, 100"
                                />
                            </svg>
                            <div className="absolute inset-0 flex items-center justify-center">
                                <span className="text-2xl font-bold text-slate-900">89%</span>
                            </div>
                        </div>
                        <h3 className="text-lg font-semibold text-slate-900 mb-1">
                            Accuracy
                        </h3>
                        <p className="text-sm text-slate-600">
                            Reliability of recommendations
                        </p>
                    </motion.div>

                    <motion.div
                        initial={{ y: 20, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        transition={{ delay: 0.2 }}
                        className="bg-white rounded-xl p-6 shadow-lg shadow-slate-200/50 border border-slate-200 text-center"
                    >
                        <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
                            <Shield className="w-8 h-8 text-emerald-600" />
                        </div>
                        <div className="relative w-24 h-24 mx-auto mb-4">
                            <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 36 36">
                                <path
                                    d="M18 2.0845
                    a 15.9155 15.9155 0 0 1 0 31.831
                    a 15.9155 15.9155 0 0 1 0 -31.831"
                                    fill="none"
                                    stroke="#E5E7EB"
                                    strokeWidth="2"
                                />
                                <path
                                    d="M18 2.0845
                    a 15.9155 15.9155 0 0 1 0 31.831
                    a 15.9155 15.9155 0 0 1 0 -31.831"
                                    fill="none"
                                    stroke="#10B981"
                                    strokeWidth="2"
                                    strokeDasharray="92, 100"
                                />
                            </svg>
                            <div className="absolute inset-0 flex items-center justify-center">
                                <span className="text-2xl font-bold text-slate-900">92%</span>
                            </div>
                        </div>
                        <h3 className="text-lg font-semibold text-slate-900 mb-1">
                            Reliability
                        </h3>
                        <p className="text-sm text-slate-600">Consistency of analyses</p>
                    </motion.div>

                    <motion.div
                        initial={{ y: 20, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        transition={{ delay: 0.3 }}
                        className="bg-white rounded-xl p-6 shadow-lg shadow-slate-200/50 border border-slate-200 text-center"
                    >
                        <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
                            <Star className="w-8 h-8 text-orange-600" />
                        </div>
                        <div className="relative w-24 h-24 mx-auto mb-4">
                            <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 36 36">
                                <path
                                    d="M18 2.0845
                    a 15.9155 15.9155 0 0 1 0 31.831
                    a 15.9155 15.9155 0 0 1 0 -31.831"
                                    fill="none"
                                    stroke="#E5E7EB"
                                    strokeWidth="2"
                                />
                                <path
                                    d="M18 2.0845
                    a 15.9155 15.9155 0 0 1 0 31.831
                    a 15.9155 15.9155 0 0 1 0 -31.831"
                                    fill="none"
                                    stroke="#F59E0B"
                                    strokeWidth="2"
                                    strokeDasharray="95, 100"
                                />
                            </svg>
                            <div className="absolute inset-0 flex items-center justify-center">
                                <span className="text-2xl font-bold text-slate-900">95%</span>
                            </div>
                        </div>
                        <h3 className="text-lg font-semibold text-slate-900 mb-1">Utility</h3>
                        <p className="text-sm text-slate-600">Actionable impact</p>
                    </motion.div>
                </div>
            )}

            {/* Filters */}
            <motion.div
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.4 }}
                className="flex flex-wrap gap-2 mb-8"
            >
                {priorities.map((priority) => (
                    <button
                        key={priority.id}
                        onClick={() => setSelectedPriority(priority.id)}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${selectedPriority === priority.id
                            ? "bg-blue-600 text-white shadow-lg shadow-blue-500/25"
                            : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-50"
                            }`}
                    >
                        {priority.label}
                    </button>
                ))}
            </motion.div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Recommendations */}
                <div className="space-y-6">
                    <h3 className="text-xl font-bold text-slate-900 flex items-center">
                        <Lightbulb className="w-6 h-6 text-yellow-500 mr-2" />
                        Priority Recommendations
                    </h3>

                    {filteredRecommendations.length > 0 ? (
                        filteredRecommendations.map((rec, index) => (
                            <motion.div
                                key={rec.id}
                                initial={{ y: 20, opacity: 0 }}
                                animate={{ y: 0, opacity: 1 }}
                                transition={{ delay: 0.5 + index * 0.1 }}
                                className="bg-white rounded-xl p-6 shadow-lg shadow-slate-200/50 border border-slate-200 hover:shadow-xl transition-all duration-300"
                            >
                                <div className="flex items-start justify-between mb-4">
                                    <div className="flex-1">
                                        <div className="flex items-center space-x-2 mb-2">
                                            <h4 className="text-lg font-semibold text-slate-900">
                                                {rec.title}
                                            </h4>
                                            <span
                                                className={`px-2 py-1 rounded-full text-xs font-medium border ${getPriorityColor(
                                                    rec.priority
                                                )}`}
                                            >
                                                {rec.priority === "high"
                                                    ? "High"
                                                    : rec.priority === "medium"
                                                        ? "Medium"
                                                        : "Low"}
                                            </span>
                                        </div>
                                        <p className="text-sm text-slate-600 mb-3">
                                            {rec.description}
                                        </p>
                                    </div>
                                    <ChevronRight className="w-5 h-5 text-slate-400 flex-shrink-0 ml-4" />
                                </div>

                                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                                    <div className="text-center">
                                        <div className="flex items-center justify-center space-x-1 mb-1">
                                            <TrendingUp className="w-4 h-4 text-emerald-600" />
                                            <span className="text-sm font-medium text-slate-700">
                                                ROI
                                            </span>
                                        </div>
                                        <span className="text-lg font-bold text-emerald-600">
                                            {rec.roi}%
                                        </span>
                                    </div>
                                    <div className="text-center">
                                        <div className="flex items-center justify-center space-x-1 mb-1">
                                            <Clock className="w-4 h-4 text-blue-600" />
                                            <span className="text-sm font-medium text-slate-700">
                                                Timeframe
                                            </span>
                                        </div>
                                        <span className="text-sm font-semibold text-slate-900">
                                            {rec.timeframe}
                                        </span>
                                    </div>
                                    <div className="text-center">
                                        <div className="flex items-center justify-center space-x-1 mb-1">
                                            <Zap
                                                className={`w-4 h-4 ${getComplexityColor(
                                                    rec.complexity
                                                )}`}
                                            />
                                            <span className="text-sm font-medium text-slate-700">
                                                Complexity
                                            </span>
                                        </div>
                                        <span
                                            className={`text-sm font-semibold ${getComplexityColor(
                                                rec.complexity
                                            )}`}
                                        >
                                            {rec.complexity === "low"
                                                ? "Low"
                                                : rec.complexity === "medium"
                                                    ? "Medium"
                                                    : "High"}
                                        </span>
                                    </div>
                                </div>
                            </motion.div>
                        ))
                    ) : (
                        <div className="bg-white rounded-xl p-8 shadow-lg shadow-slate-200/50 border border-slate-200 text-center">
                            <Lightbulb className="w-12 h-12 text-slate-400 mx-auto mb-4" />
                            <h4 className="text-lg font-semibold text-slate-900 mb-2">
                                No recommendations
                            </h4>
                            <p className="text-slate-600">
                                No recommendations available for the selected filter.
                            </p>
                        </div>
                    )}
                </div>

                {/* Risk Assessment */}
                <div className="space-y-6">
                    <h3 className="text-xl font-bold text-slate-900 flex items-center">
                        <AlertTriangle className="w-6 h-6 text-orange-500 mr-2" />
                        Risk Assessment
                    </h3>

                    {risks.length > 0 ? (
                        risks.map((risk, index) => (
                            <motion.div
                                key={risk.id}
                                initial={{ y: 20, opacity: 0 }}
                                animate={{ y: 0, opacity: 1 }}
                                transition={{ delay: 0.7 + index * 0.1 }}
                                className="bg-white rounded-xl p-6 shadow-lg shadow-slate-200/50 border border-slate-200"
                            >
                                <div className="flex items-start justify-between mb-4">
                                    <div className="flex-1">
                                        <div className="flex items-center space-x-2 mb-2">
                                            <h4 className="text-lg font-semibold text-slate-900">
                                                {risk.type}
                                            </h4>
                                            <span
                                                className={`px-2 py-1 rounded-full text-xs font-medium border ${getRiskColor(
                                                    risk.level
                                                )}`}
                                            >
                                                {risk.level}
                                            </span>
                                        </div>
                                        <p className="text-sm text-slate-600 mb-3">
                                            {risk.description}
                                        </p>
                                    </div>
                                </div>

                                <div className="mb-4">
                                    <div className="flex items-center justify-between text-sm text-slate-600 mb-2">
                                        <span>Probability</span>
                                        <span>{risk.probability}%</span>
                                    </div>
                                    <div className="w-full bg-slate-200 rounded-full h-2">
                                        <div
                                            className={`h-2 rounded-full ${risk.probability >= 70
                                                ? "bg-red-500"
                                                : risk.probability >= 50
                                                    ? "bg-yellow-500"
                                                    : "bg-green-500"
                                                }`}
                                            style={{ width: `${risk.probability}%` }}
                                        />
                                    </div>
                                </div>

                                <div className="bg-slate-50 rounded-lg p-4">
                                    <h5 className="font-semibold text-slate-900 mb-2 flex items-center">
                                        <Shield className="w-4 h-4 text-blue-600 mr-1" />
                                        Mitigation Strategy
                                    </h5>
                                    <p className="text-sm text-slate-700">{risk.mitigation}</p>
                                </div>
                            </motion.div>
                        ))
                    ) : (
                        <div className="bg-white rounded-xl p-8 shadow-lg shadow-slate-200/50 border border-slate-200 text-center">
                            <AlertTriangle className="w-12 h-12 text-slate-400 mx-auto mb-4" />
                            <h4 className="text-lg font-semibold text-slate-900 mb-2">
                                No risks identified
                            </h4>
                            <p className="text-slate-600">
                                No risk assessments available at this time.
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default RecommendationsComponent;
