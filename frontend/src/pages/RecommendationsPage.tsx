import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Lightbulb,
  AlertTriangle,
  TrendingUp,
  Clock,
  DollarSign,
  Users,
  Target,
  ChevronRight,
  Star,
  Shield,
  Zap,
} from "lucide-react";

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

interface AnalysisData {
  strategic_recommendations: StrategicRecommendation[];
  risk_assessment: RiskAssessment[];
}

const RecommendationsPage: React.FC = () => {
  const [data, setData] = useState<AnalysisData | null>(null);
  const [selectedPriority, setSelectedPriority] = useState("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/analysed_data.json")
      .then((res) => res.json())
      .then((json) => {
        setData(json);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error loading data:", err);
        setLoading(false);
      });
  }, []);

  // Transform JSON data to match component structure
  const transformRecommendations = (
    recommendations: StrategicRecommendation[]
  ) => {
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

  const transformRisks = (risks: RiskAssessment[]) => {
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

  const recommendations = data
    ? transformRecommendations(data.strategic_recommendations)
    : [];
  const risks = data ? transformRisks(data.risk_assessment) : [];

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

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-slate-600">Loading recommendations...</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <AlertTriangle className="w-12 h-12 text-orange-500 mx-auto mb-4" />
          <p className="text-slate-600">Error loading data</p>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="py-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto"
    >
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold text-slate-900 mb-2">
          Strategic Recommendations
        </h1>
        <p className="text-slate-600">
          Priority actions to optimize your growth
        </p>
      </motion.div>

      {/* Performance Indicators */}
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
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
              selectedPriority === priority.id
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
          <h2 className="text-2xl font-bold text-slate-900 flex items-center">
            <Lightbulb className="w-6 h-6 text-yellow-500 mr-2" />
            Priority Recommendations
          </h2>

          {filteredRecommendations.map((rec, index) => (
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
                    <h3 className="text-lg font-semibold text-slate-900">
                      {rec.title}
                    </h3>
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

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
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
          ))}
        </div>

        {/* Risk Assessment */}
        <div className="space-y-6">
          <h2 className="text-2xl font-bold text-slate-900 flex items-center">
            <AlertTriangle className="w-6 h-6 text-orange-500 mr-2" />
            Risk Assessment
          </h2>

          {risks.map((risk, index) => (
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
                    <h3 className="text-lg font-semibold text-slate-900">
                      {risk.type}
                    </h3>
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
                    className={`h-2 rounded-full ${
                      risk.probability >= 70
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
                <h4 className="font-semibold text-slate-900 mb-2 flex items-center">
                  <Shield className="w-4 h-4 text-blue-600 mr-1" />
                  Mitigation Strategy
                </h4>
                <p className="text-sm text-slate-700">{risk.mitigation}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </motion.div>
  );
};

export default RecommendationsPage;
