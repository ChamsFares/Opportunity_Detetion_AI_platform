import { motion } from "framer-motion";
import { ArrowRight, Building2, MessageSquare, Sparkles } from "lucide-react";
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import BusinessForm from "../components/BusinessForm";
import Chatbot from "../components/Chatbot";

// Define the report data interface
interface ReportData {
  market_opportunities?: Array<{
    opportunity_type: string;
    opportunity_description: string;
    urgency: string;
    market_size_potential: string;
    competitive_advantage: string;
  }>;
  market_gaps?: Array<{
    gap_category: string;
    gap_description: string;
    impact_level: string;
    evidence: string;
  }>;
  trend_analysis?: {
    emerging_trends: string[];
    trend_implications: string[];
    trend_based_opportunities: string[];
  };
  competitive_insights?: {
    market_positioning: string;
    competitive_strengths: string[];
    competitive_weaknesses: string[];
    differentiation_opportunities: string[];
  };
  strategic_recommendations?: Array<{
    recommendation: string;
    priority: string;
    implementation_complexity: string;
    expected_impact: string;
  }>;
  risk_assessment?: Array<{
    risk_type: string;
    probability: string;
    risk_description: string;
    mitigation_strategy: string;
  }>;
  metadata?: {
    company?: string;
    sector?: string;
    service?: string;
    analysis_timestamp?: string;
    data_sources?: {
      trends_analyzed?: number;
      news_articles?: number;
      competitor_pages?: number;
    };
  };
  dashboard_data?: unknown;
}

const HomePage: React.FC = () => {
  const [mode, setMode] = useState<"form" | "chat">("form");
  const navigate = useNavigate();

  const handleAnalysisStart = () => {
    navigate("/analysis");
  };

  const handleFormSubmit = (reportData?: {
    status: string;
    pdf_path: string;
    report_data?: ReportData;
    data_charts?: Array<{
      title: string;
      type: 'line' | 'bar' | 'pie' | 'doughnut' | 'area' | 'scatter';
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
    };
  }) => {
    if (reportData && reportData.status === 'success') {
      // Navigate to dashboard with the response data
      navigate("/dashboard", {
        state: {
          backendData: {
            status: reportData.status,
            data: {
              report_data: reportData.report_data,
              data_charts: reportData.data_charts,
              dashboard_data: reportData.dashboard_data,
              company: reportData.report_data?.metadata?.company,
              sector: reportData.report_data?.metadata?.sector,
              service: reportData.report_data?.metadata?.service,
            },
            analytics: reportData.analytics
          }
        }
      });
    } else {
      // Fallback to analysis page if no data or error
      navigate("/analysis");
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="min-h-[calc(100vh-4rem)] flex flex-col"
    >
      {/* Hero Section */}
      <div className="flex-1 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl w-full">
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="text-center mb-12"
          >
            <div className="flex items-center justify-center mb-6">
              <div className="w-16 h-16 bg-gradient-to-r from-blue-600 to-emerald-600 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-500/25">
                <Sparkles className="w-8 h-8 text-white" />
              </div>
            </div>
            <h1 className="text-4xl sm:text-6xl font-bold mb-6">
              <span className="bg-gradient-to-r from-blue-600 to-emerald-600 bg-clip-text text-transparent">
                OPPORTUNA
              </span>
            </h1>
            <p className="text-xl sm:text-2xl text-slate-600 mb-4 max-w-3xl mx-auto leading-relaxed">
              Identify your growth opportunities and close performance gaps
            </p>
            <p className="text-base text-slate-500 max-w-2xl mx-auto">
              Our intelligent assistant analyzes your market, identifies your
              competition, and generates tailored strategic recommendations
            </p>
          </motion.div>

          {/* Mode Selector - Enhanced Visual */}
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="mb-8"
          >
            <div className="flex justify-center">
              <div className="bg-white rounded-2xl p-2 shadow-xl border border-slate-200/50 inline-flex">
                <motion.button
                  onClick={() => setMode("form")}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className={`flex items-center space-x-3 px-8 py-4 rounded-xl text-sm font-medium transition-all duration-300 min-w-[200px] ${
                    mode === "form"
                      ? "bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-lg shadow-blue-500/25 transform scale-105"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
                  }`}
                >
                  <Building2 className="w-5 h-5" />
                  <div className="text-left">
                    <div className="font-semibold">My business already exists</div>
                    <div className="text-xs opacity-80">Quick analysis setup</div>
                  </div>
                  {mode === "form" && (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      className="w-2 h-2 bg-white rounded-full ml-auto"
                    />
                  )}
                </motion.button>
                <motion.button
                  onClick={() => setMode("chat")}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className={`flex items-center space-x-3 px-8 py-4 rounded-xl text-sm font-medium transition-all duration-300 min-w-[200px] ${
                    mode === "chat"
                      ? "bg-gradient-to-r from-emerald-600 to-emerald-700 text-white shadow-lg shadow-emerald-500/25 transform scale-105"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
                  }`}
                >
                  <MessageSquare className="w-5 h-5" />
                  <div className="text-left">
                    <div className="font-semibold">Project in creation</div>
                    <div className="text-xs opacity-80">Interactive guidance</div>
                  </div>
                  {mode === "chat" && (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      className="w-2 h-2 bg-white rounded-full ml-auto"
                    />
                  )}
                </motion.button>
              </div>
            </div>
            
            {/* Mode Description */}
            <motion.div
              key={mode}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center mt-4"
            >
              <p className="text-sm text-slate-500">
                {mode === "form" 
                  ? "Perfect for existing businesses looking to optimize and identify new opportunities"
                  : "Ideal for entrepreneurs developing new business ideas with step-by-step guidance"
                }
              </p>
            </motion.div>
          </motion.div>

          {/* Content */}
          <motion.div
            key={mode}
            initial={{ x: mode === "form" ? -20 : 20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ duration: 0.3 }}
            className="max-w-2xl mx-auto"
          >
            {mode === "form" ? (
              <BusinessForm onSubmit={handleFormSubmit} />
            ) : (
              <Chatbot onComplete={handleAnalysisStart} />
            )}
          </motion.div>
        </div>
      </div>

      {/* Features Preview */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.6 }}
        className="border-t border-slate-200/50 bg-white/50 py-8 px-4"
      >
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <ArrowRight className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="font-semibold text-slate-900 mb-1">
                Automatic Analysis
              </h3>
              <p className="text-sm text-slate-600">
                Competitor identification and real-time market analysis
              </p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-emerald-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <Sparkles className="w-6 h-6 text-emerald-600" />
              </div>
              <h3 className="font-semibold text-slate-900 mb-1">
                Strategic AI
              </h3>
              <p className="text-sm text-slate-600">
                Personalized recommendations based on your business data
              </p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <Building2 className="w-6 h-6 text-orange-600" />
              </div>
              <h3 className="font-semibold text-slate-900 mb-1">360° Vision</h3>
              <p className="text-sm text-slate-600">
                Complete mapping of regional opportunities
              </p>
            </div>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default HomePage;
