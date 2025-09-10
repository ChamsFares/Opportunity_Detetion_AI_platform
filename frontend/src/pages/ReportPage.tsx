import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  FileText,
  MessageSquare,
  Send,
  Bot,
  User,
  Filter,
  ChevronDown,
  TrendingUp,
  AlertTriangle,
  Target,
  Zap,
} from "lucide-react";

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

interface ReportData {
  market_opportunities: Opportunity[];
  market_gaps: Gap[];
  trend_analysis: {
    trend_based_opportunities: string[];
    emerging_trends: string[];
    trend_implications: string[];
  };
  competitive_insights: {
    competitive_weaknesses: string[];
    competitive_strengths: string[];
    market_positioning: string;
    differentiation_opportunities: string[];
  };
}

interface ChatMessage {
  id: string;
  text: string;
  isBot: boolean;
  timestamp: Date;
}

const ReportPage: React.FC = () => {
  const [data, setData] = useState<ReportData | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "1",
      text: "Hello! I'm here to help you understand your analysis report. What would you like to know?",
      isBot: true,
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [activeFilter, setActiveFilter] = useState("all");

  useEffect(() => {
    fetch("/analysed_data.json")
      .then((res) => res.json())
      .then((json) => setData(json))
      .catch((err) => console.error("Error loading data:", err));
  }, []);

  const filters = [
    { id: "all", label: "Show All" },
    { id: "opportunities", label: "Opportunities" },
    { id: "gaps", label: "Gaps" },
    { id: "trends", label: "Trends" },
    { id: "competitive", label: "Competitive" },
  ];

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      text: inputValue,
      isBot: false,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsTyping(true);

    // Simulate AI response based on data
    await new Promise((resolve) => setTimeout(resolve, 1500));

    const botResponses = [
      `Based on your analysis, ${
        data?.market_opportunities?.length || 0
      } major opportunities have been identified in your sector.`,
      `The data shows ${
        data?.market_gaps?.length || 0
      } strategic gaps to address to optimize your performance.`,
      `Your competitive positioning reveals ${
        data?.competitive_insights?.competitive_strengths?.length || 0
      } main strengths and ${
        data?.competitive_insights?.competitive_weaknesses?.length || 0
      } areas for improvement.`,
      `The trend analysis identifies ${
        data?.trend_analysis?.emerging_trends?.length || 0
      } emerging trends to monitor.`,
    ];

    const randomResponse =
      botResponses[Math.floor(Math.random() * botResponses.length)];

    const botMessage: ChatMessage = {
      id: (Date.now() + 1).toString(),
      text: randomResponse,
      isBot: true,
      timestamp: new Date(),
    };

    setIsTyping(false);
    setMessages((prev) => [...prev, botMessage]);
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
      case "elevated": // Translated from "élevée"
        return "text-red-600";
      case "medium":
      case "moderate": // Translated from "moyenne"
        return "text-orange-600";
      case "low":
      case "weak": // Translated from "faible"
        return "text-green-600";
      default:
        return "text-slate-600";
    }
  };

  const getImpactColor = (impact: string) => {
    switch (impact?.toLowerCase()) {
      case "high":
      case "elevated": // Translated from "élevé"
        return "bg-red-50 border-red-200 text-red-900";
      case "medium":
      case "moderate": // Translated from "moyen"
        return "bg-orange-50 border-orange-200 text-orange-900";
      case "low":
      case "weak": // Translated from "faible"
        return "bg-green-50 border-green-200 text-green-900";
      default:
        return "bg-slate-50 border-slate-200 text-slate-900";
    }
  };

  if (!data) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-slate-600">Loading data...</p>
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
          Comprehensive Report
        </h1>
        <p className="text-slate-600">
          Detailed analysis with integrated AI assistant
        </p>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Report Content */}
        <div className="lg:col-span-2 space-y-8">
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
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                  activeFilter === filter.id
                    ? "bg-blue-600 text-white shadow-lg shadow-blue-500/25"
                    : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-50"
                }`}
              >
                <Filter className="w-4 h-4" />
                <span>{filter.label}</span>
              </button>
            ))}
          </motion.div>

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
                <h2 className="text-2xl font-bold text-slate-900">Summary</h2>
              </div>
              <div className="prose prose-slate max-w-none">
                <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center">
                  <TrendingUp className="w-5 h-5 text-emerald-600 mr-2" />
                  Identified Opportunities (
                  {data.market_opportunities?.length || 0})
                </h3>
                <ul className="space-y-3 mb-6">
                  {data.market_opportunities
                    ?.slice(0, 3)
                    .map((opportunity, i) => (
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

                <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center">
                  <AlertTriangle className="w-5 h-5 text-orange-600 mr-2" />
                  Strategic Gaps ({data.market_gaps?.length || 0})
                </h3>
                <ul className="space-y-3 mb-6">
                  {data.market_gaps?.slice(0, 3).map((gap, i) => (
                    <li key={i} className="flex items-start space-x-3">
                      <div className="w-2 h-2 bg-orange-500 rounded-full mt-2 flex-shrink-0"></div>
                      <span>
                        <strong>{gap.gap_category}:</strong>{" "}
                        {gap.gap_description}
                        <span className="ml-2 text-sm text-orange-600">
                          (Impact: {gap.impact_level})
                        </span>
                      </span>
                    </li>
                  ))}
                </ul>

                <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center">
                  <Target className="w-5 h-5 text-blue-600 mr-2" />
                  Competitive Positioning
                </h3>
                <div className="bg-slate-50 rounded-lg p-6">
                  <p className="text-slate-700 mb-4">
                    {data.competitive_insights?.market_positioning}
                  </p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-semibold text-slate-900 mb-2">
                        Identified Strengths
                      </h4>
                      <div className="w-full bg-slate-200 rounded-full h-2 mb-2">
                        <div
                          className="bg-emerald-500 h-2 rounded-full"
                          style={{
                            width: `${Math.min(
                              (data.competitive_insights?.competitive_strengths
                                ?.length || 0) * 20,
                              100
                            )}%`,
                          }}
                        ></div>
                      </div>
                      <span className="text-sm text-slate-600">
                        {data.competitive_insights?.competitive_strengths
                          ?.length || 0}{" "}
                        strengths identified
                      </span>
                    </div>
                    <div>
                      <h4 className="font-semibold text-slate-900 mb-2">
                        Areas for Improvement
                      </h4>
                      <div className="w-full bg-slate-200 rounded-full h-2 mb-2">
                        <div
                          className="bg-orange-500 h-2 rounded-full"
                          style={{
                            width: `${Math.min(
                              (data.competitive_insights?.competitive_weaknesses
                                ?.length || 0) * 20,
                              100
                            )}%`,
                          }}
                        ></div>
                      </div>
                      <span className="text-sm text-slate-600">
                        {data.competitive_insights?.competitive_weaknesses
                          ?.length || 0}{" "}
                        weaknesses to address
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* Opportunities Section */}
          {(activeFilter === "all" || activeFilter === "opportunities") && (
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.3 }}
              className="bg-white rounded-xl p-8 shadow-lg shadow-slate-200/50 border border-slate-200"
            >
              <div className="flex items-center space-x-2 mb-6">
                <TrendingUp className="w-6 h-6 text-emerald-600" />
                <h2 className="text-2xl font-bold text-slate-900">
                  Market Opportunities
                </h2>
              </div>
              <div className="space-y-4">
                {data.market_opportunities?.map((opportunity, i) => (
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
          {(activeFilter === "all" || activeFilter === "gaps") && (
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.4 }}
              className="bg-white rounded-xl p-8 shadow-lg shadow-slate-200/50 border border-slate-200"
            >
              <div className="flex items-center space-x-2 mb-6">
                <Target className="w-6 h-6 text-blue-600" />
                <h2 className="text-2xl font-bold text-slate-900">
                  Strategic Gaps
                </h2>
              </div>
              <div className="space-y-4">
                {data.market_gaps?.map((gap, i) => (
                  <div
                    key={i}
                    className={`border rounded-lg p-6 ${getImpactColor(
                      gap.impact_level
                    )}`}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <h4 className="font-semibold text-lg">
                        {gap.gap_category}
                      </h4>
                      <span className="px-3 py-1 rounded-full text-xs font-medium bg-white text-slate-700">
                        Impact: {gap.impact_level}
                      </span>
                    </div>
                    <p className="mb-3">{gap.gap_description}</p>
                    <div>
                      <span className="text-sm font-medium">Evidence:</span>
                      <p className="text-sm opacity-80">{gap.evidence}</p>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Trends Section */}
          {(activeFilter === "all" || activeFilter === "trends") && (
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.5 }}
              className="bg-white rounded-xl p-8 shadow-lg shadow-slate-200/50 border border-slate-200"
            >
              <div className="flex items-center space-x-2 mb-6">
                <Zap className="w-6 h-6 text-indigo-600" />
                <h2 className="text-2xl font-bold text-slate-900">
                  Trend Analysis
                </h2>
              </div>
              <div className="space-y-6">
                <div>
                  <h4 className="font-semibold mb-3 text-slate-800 flex items-center">
                    <TrendingUp className="w-4 h-4 mr-2 text-emerald-600" />
                    Trend-Based Opportunities
                  </h4>
                  <ul className="space-y-2">
                    {data.trend_analysis?.trend_based_opportunities?.map(
                      (trend, i) => (
                        <li
                          key={i}
                          className="flex items-start space-x-3 p-3 bg-emerald-50 rounded-lg"
                        >
                          <div className="w-2 h-2 bg-emerald-500 rounded-full mt-2 flex-shrink-0"></div>
                          <span className="text-slate-700">{trend}</span>
                        </li>
                      )
                    )}
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold mb-3 text-slate-800 flex items-center">
                    <Zap className="w-4 h-4 mr-2 text-indigo-600" />
                    Emerging Trends
                  </h4>
                  <ul className="space-y-2">
                    {data.trend_analysis?.emerging_trends?.map((trend, i) => (
                      <li
                        key={i}
                        className="flex items-start space-x-3 p-3 bg-indigo-50 rounded-lg"
                      >
                        <div className="w-2 h-2 bg-indigo-500 rounded-full mt-2 flex-shrink-0"></div>
                        <span className="text-slate-700">{trend}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold mb-3 text-slate-800 flex items-center">
                    <Target className="w-4 h-4 mr-2 text-blue-600" />
                    Strategic Implications
                  </h4>
                  <ul className="space-y-2">
                    {data.trend_analysis?.trend_implications?.map(
                      (implication, i) => (
                        <li
                          key={i}
                          className="flex items-start space-x-3 p-3 bg-blue-50 rounded-lg"
                        >
                          <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                          <span className="text-slate-700">{implication}</span>
                        </li>
                      )
                    )}
                  </ul>
                </div>
              </div>
            </motion.div>
          )}

          {/* Competitive Analysis Section */}
          {(activeFilter === "all" || activeFilter === "competitive") && (
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.6 }}
              className="bg-white rounded-xl p-8 shadow-lg shadow-slate-200/50 border border-slate-200"
            >
              <div className="flex items-center space-x-2 mb-6">
                <FileText className="w-6 h-6 text-purple-600" />
                <h2 className="text-2xl font-bold text-slate-900">
                  Competitive Analysis
                </h2>
              </div>
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-semibold text-slate-900 mb-3 flex items-center">
                      <TrendingUp className="w-4 h-4 mr-2 text-emerald-600" />
                      Competitive Strengths
                    </h4>
                    <ul className="space-y-2">
                      {data.competitive_insights?.competitive_strengths?.map(
                        (strength, i) => (
                          <li
                            key={i}
                            className="flex items-start space-x-3 p-3 bg-emerald-50 rounded-lg"
                          >
                            <div className="w-2 h-2 bg-emerald-500 rounded-full mt-2 flex-shrink-0"></div>
                            <span className="text-slate-700">{strength}</span>
                          </li>
                        )
                      )}
                    </ul>
                  </div>
                  <div>
                    <h4 className="font-semibold text-slate-900 mb-3 flex items-center">
                      <AlertTriangle className="w-4 h-4 mr-2 text-orange-600" />
                      Weaknesses to Address
                    </h4>
                    <ul className="space-y-2">
                      {data.competitive_insights?.competitive_weaknesses?.map(
                        (weakness, i) => (
                          <li
                            key={i}
                            className="flex items-start space-x-3 p-3 bg-orange-50 rounded-lg"
                          >
                            <div className="w-2 h-2 bg-orange-500 rounded-full mt-2 flex-shrink-0"></div>
                            <span className="text-slate-700">{weakness}</span>
                          </li>
                        )
                      )}
                    </ul>
                  </div>
                </div>
                <div>
                  <h4 className="font-semibold text-slate-900 mb-3">
                    Market Positioning
                  </h4>
                  <div className="bg-slate-50 rounded-lg p-4">
                    <p className="text-slate-700">
                      {data.competitive_insights?.market_positioning}
                    </p>
                  </div>
                </div>
                <div>
                  <h4 className="font-semibold text-slate-900 mb-3 flex items-center">
                    <Target className="w-4 h-4 mr-2 text-blue-600" />
                    Differentiation Opportunities
                  </h4>
                  <ul className="space-y-2">
                    {data.competitive_insights?.differentiation_opportunities?.map(
                      (opportunity, i) => (
                        <li
                          key={i}
                          className="flex items-start space-x-3 p-3 bg-blue-50 rounded-lg"
                        >
                          <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                          <span className="text-slate-700">{opportunity}</span>
                        </li>
                      )
                    )}
                  </ul>
                </div>
              </div>
            </motion.div>
          )}
        </div>

        {/* AI Chat Assistant */}
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
                  <h3 className="font-semibold text-slate-900">AI Assistant</h3>
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
                  className={`flex ${
                    message.isBot ? "justify-start" : "justify-end"
                  }`}
                >
                  <div
                    className={`flex items-start space-x-2 max-w-[85%] ${
                      message.isBot
                        ? "flex-row"
                        : "flex-row-reverse space-x-reverse"
                    }`}
                  >
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                        message.isBot
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
                      className={`rounded-2xl px-4 py-3 ${
                        message.isBot
                          ? "bg-slate-100 text-slate-900"
                          : "bg-gradient-to-r from-blue-600 to-emerald-600 text-white"
                      }`}
                    >
                      <p className="text-sm leading-relaxed">{message.text}</p>
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
                  placeholder="Ask your question..."
                  disabled={isTyping}
                  className="flex-1 px-4 py-3 rounded-lg border border-slate-200 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 placeholder-slate-400 text-sm disabled:bg-slate-50 disabled:text-slate-400"
                />
                <button
                  onClick={handleSendMessage}
                  disabled={!inputValue.trim() || isTyping}
                  className={`px-4 py-3 rounded-lg transition-all duration-200 ${
                    inputValue.trim() && !isTyping
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
      </div>
    </motion.div>
  );
};

export default ReportPage;
