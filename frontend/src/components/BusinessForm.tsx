import { motion } from "framer-motion";
import { AlertCircle, ArrowRight, BarChart3, Building2, Clock, Cpu, FileText, Globe, Lightbulb, Package, Shield, Target, TrendingUp, Zap } from "lucide-react";
import React, { useState } from "react";
import {
  generateSessionId,
  ReportData,
  StreamErrorEvent,
  StreamProgressEvent,
  StreamResultEvent
} from "../services/api.ts";
import { generateReportStreamWithProgress } from "../services/reportGenerator.ts";

interface BusinessFormProps {
  onSubmit: (reportData?: {
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
  }) => void;
}

const BusinessForm: React.FC<BusinessFormProps> = ({ onSubmit }) => {
  const [formData, setFormData] = useState({
    companyName: "",
    product: "",
    sector: "",
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId] = useState(() => generateSessionId());

  // Streaming progress state
  const [progressData, setProgressData] = useState<StreamProgressEvent | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isFallbackMode, setIsFallbackMode] = useState(false);
  const [completionAnalytics, setCompletionAnalytics] = useState<{
    execution_time: string;
    processing_speed: string;
    report_quality: string;
    data_sources: string[];
    ai_models_used: string[];
  } | null>(null);
  const [reportData, setReportData] = useState<ReportData | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.companyName || !formData.product || !formData.sector) return;

    setIsSubmitting(true);
    setIsStreaming(true);
    setIsFallbackMode(false);
    setError(null);
    setProgressData(null);
    setCompletionAnalytics(null);
    setReportData(null);

    try {
      // Use streaming API for real-time progress updates
      await generateReportStreamWithProgress(
        formData.companyName,
        formData.sector,
        formData.product,
        sessionId,
        // Progress callback
        (progressEvent: StreamProgressEvent) => {
          setProgressData(progressEvent);
          // Check if we're in fallback mode
          if (progressEvent.message?.includes('Falling back') || progressEvent.message?.includes('fallback')) {
            setIsFallbackMode(true);
            setIsStreaming(false); // No more streaming updates expected
          }
        },
        // Complete callback
        (resultEvent: StreamResultEvent) => {
          setProgressData(null);
          setIsStreaming(false);
          setIsFallbackMode(false);
          setIsSubmitting(false);

          // Store analytics and report data if available
          if (resultEvent.analytics) {
            setCompletionAnalytics(resultEvent.analytics);
          }
          if (resultEvent.report_data) {
            setReportData(resultEvent.report_data);
          }

          // Pass the result to the parent component
          onSubmit({
            status: resultEvent.status,
            pdf_path: resultEvent.pdf_path,
            report_data: resultEvent.report_data,
            data_charts: resultEvent.data_charts,
            dashboard_data: resultEvent.dashboard_data,
            analytics: resultEvent.analytics,
          });
        },
        // Error callback
        (errorEvent: StreamErrorEvent) => {
          setIsStreaming(false);
          setIsSubmitting(false);
          setProgressData(null);

          // Handle API errors based on error codes
          switch (errorEvent.error_code) {
            case "CONNECTION_FAILED":
              setIsFallbackMode(true);
              setError("Connection to streaming server failed. Falling back to standard processing...");
              break;
            case "FALLBACK_FAILED":
              setIsFallbackMode(false);
              setError("Both streaming and standard processing failed. Please try again later.");
              break;
            case "INVALID_COMPANY":
            case "INVALID_SECTOR":
            case "INVALID_SERVICE":
              setError("Please check your input. All fields must be filled correctly.");
              break;
            case "AGENT_PROCESSING_ERROR":
              setError("Analysis engine error. Please try again in a few minutes.");
              break;
            case "INTERNAL_ERROR":
              setError("Server error. Please try again later.");
              break;
            default:
              setError(`Error: ${errorEvent.error}`);
          }
        }
      );
    } catch (err) {
      console.error("Error during streaming:", err);
      setIsStreaming(false);
      setIsFallbackMode(false);
      setIsSubmitting(false);
      setProgressData(null);
      setError("An unexpected error occurred. Please try again.");
    }
  }; const isValid = formData.companyName && formData.product && formData.sector;

  return (
    <motion.div
      initial={{ y: 20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="bg-white rounded-2xl shadow-xl shadow-slate-200/50 border border-slate-200/50 overflow-hidden"
    >
      <div className="bg-gradient-to-r from-blue-50 to-emerald-50 px-8 py-6">
        <h2 className="text-2xl font-bold text-slate-900 mb-2">
          Let's analyze your business
        </h2>
        <p className="text-slate-600">
          A few details to personalize your analysis
        </p>
      </div>

      <form onSubmit={handleSubmit} className="p-8 space-y-6">
        {/* Error Message */}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center space-x-3"
          >
            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
            <p className="text-red-700 text-sm">{error}</p>
          </motion.div>
        )}

        {/* Enhanced Streaming Progress Indicator */}
        {(isStreaming || isFallbackMode) && progressData && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className={`border rounded-xl p-6 space-y-4 ${isFallbackMode
              ? "bg-amber-50 border-amber-200"
              : "bg-gradient-to-br from-blue-50 to-emerald-50 border-blue-200"
              }`}
          >
            {/* Main Progress Header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center shadow-lg ${isFallbackMode
                  ? "bg-gradient-to-r from-amber-500 to-orange-500"
                  : "bg-gradient-to-r from-blue-600 to-emerald-600"
                  }`}>
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                  >
                    {progressData.heartbeat ? (
                      <Clock className="w-5 h-5 text-white" />
                    ) : progressData.phase === "competitor_analysis" ? (
                      <Globe className="w-5 h-5 text-white" />
                    ) : progressData.phase === "parallel_processing" ? (
                      <Cpu className="w-5 h-5 text-white" />
                    ) : progressData.phase === "trend_analysis" ? (
                      <TrendingUp className="w-5 h-5 text-white" />
                    ) : progressData.phase === "initialization" ? (
                      <Zap className="w-5 h-5 text-white" />
                    ) : (
                      <Clock className="w-5 h-5 text-white" />
                    )}
                  </motion.div>
                </div>
                <div className="flex-1">
                  <h4 className="font-bold text-slate-900 text-sm">
                    {isFallbackMode ? "Standard Processing Mode" :
                      progressData.phase?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) || "Processing"}
                  </h4>
                  <p className="text-slate-700 text-sm font-medium">{progressData.message}</p>
                  {progressData.details && (
                    <p className="text-slate-500 text-xs mt-1">{progressData.details}</p>
                  )}
                  {progressData.heartbeat && (
                    <div className="flex items-center space-x-1 mt-1">
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                      <span className="text-xs text-blue-600 font-medium">Live connection active</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Progress Stats */}
              <div className="text-right space-y-1">
                {!isFallbackMode && (
                  <>
                    <div className={`text-2xl font-bold ${isFallbackMode ? "text-amber-600" : "text-blue-600"
                      }`}>{progressData.progress}%</div>
                    
                    {/* Enhanced Time Information */}
                    <div className="space-y-1">
                      {progressData.eta_formatted && (
                        <div className="flex items-center justify-end space-x-2">
                          <Clock className="w-3 h-3 text-slate-400" />
                          <span className="text-xs text-slate-600 font-medium">
                            ETA: <span className="text-blue-600 font-semibold">{progressData.eta_formatted}</span>
                          </span>
                        </div>
                      )}
                      
                      {progressData.elapsed_time && (
                        <div className="flex items-center justify-end space-x-2">
                          <Target className="w-3 h-3 text-slate-400" />
                          <span className="text-xs text-slate-500 font-medium">
                            Elapsed: <span className="text-emerald-600 font-semibold">{progressData.elapsed_time}</span>
                          </span>
                        </div>
                      )}
                      
                      {progressData.velocity && progressData.velocity > 0 && (
                        <div className="flex items-center justify-end space-x-2">
                          <TrendingUp className="w-3 h-3 text-slate-400" />
                          <span className="text-xs text-emerald-600 font-medium">
                            {progressData.velocity.toFixed(1)}%/s
                          </span>
                        </div>
                      )}
                      
                      {progressData.phase_factor && (
                        <div className="flex items-center justify-end space-x-2">
                          <BarChart3 className="w-3 h-3 text-slate-400" />
                          <span className="text-xs text-purple-600 font-medium">
                            Phase {Math.round(progressData.phase_factor * 100)}%
                          </span>
                        </div>
                      )}
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Enhanced Progress Bar */}
            {!isFallbackMode && (
              <div className="space-y-2">
                <div className="w-full bg-slate-200 rounded-full h-4 overflow-hidden shadow-inner">
                  <motion.div
                    className="bg-gradient-to-r from-blue-600 via-cyan-500 to-emerald-600 h-full rounded-full shadow-sm relative overflow-hidden"
                    initial={{ width: 0 }}
                    animate={{ width: `${progressData.progress}%` }}
                    transition={{ duration: 0.8, ease: "easeOut" }}
                  >
                    {/* Animated shine effect */}
                    <motion.div
                      className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent"
                      initial={{ x: "-100%" }}
                      animate={{ x: "100%" }}
                      transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                    />
                  </motion.div>
                </div>

                {/* Performance Metrics */}
                {progressData.performance && (
                  <div className="flex justify-between text-xs text-slate-600">
                    <span>Update: {progressData.performance.update_frequency}Hz</span>
                    <span>{progressData.elapsed_time}</span>
                  </div>
                )}
              </div>
            )}

            {/* Fallback Mode Indicator */}
            {isFallbackMode && (
              <div className="bg-amber-100 border border-amber-300 rounded-xl p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <div className="w-6 h-6 bg-amber-500 rounded-full flex items-center justify-center">
                    <Clock className="w-3 h-3 text-white" />
                  </div>
                  <p className="text-amber-800 text-sm font-bold">
                    Standard Processing Mode Active
                  </p>
                </div>
                <p className="text-amber-700 text-xs">
                  Real-time streaming unavailable. Using reliable standard processing method.
                </p>
              </div>
            )}

            {/* Enhanced Progress Steps - only show in streaming mode */}
            {!isFallbackMode && (
              <div className="grid grid-cols-4 gap-3 text-xs">
                {[
                  { key: 'initialization', label: 'Initialization', icon: '⚡' },
                  { key: 'competitor_analysis', label: 'Competitor Detection', icon: '🔍' },
                  { key: 'parallel_processing', label: 'AI Deep Analysis', icon: '🧠' },
                  { key: 'trend_analysis', label: 'Trend Analysis', icon: '📈' },
                  { key: 'final_analysis', label: 'Final Report', icon: '📊' },
                  { key: 'report_generation', label: 'Chart Generation', icon: '�' }
                ].map((phase, index) => {
                  const isActive = progressData.phase === phase.key;
                  const isCompleted = progressData.progress > ((index + 1) * 100) / 6;
                  const isUpcoming = progressData.progress <= (index * 100) / 6;

                  return (
                    <motion.div
                      key={phase.key}
                      className={`text-center p-3 rounded-lg border transition-all duration-300 ${isActive
                        ? 'bg-blue-100 border-blue-300 text-blue-800 font-bold shadow-sm'
                        : isCompleted
                          ? 'bg-emerald-100 border-emerald-300 text-emerald-800 font-medium'
                          : 'bg-slate-50 border-slate-200 text-slate-500'
                        }`}
                      initial={{ scale: 0.95, opacity: 0.7 }}
                      animate={{
                        scale: isActive ? 1.05 : 1,
                        opacity: isActive ? 1 : isUpcoming ? 0.6 : 1
                      }}
                      transition={{ duration: 0.3 }}
                    >
                      <div className="text-lg mb-1">
                        {isCompleted ? '✅' : isActive ? phase.icon : '⏳'}
                      </div>
                      <div className="font-medium text-xs leading-tight">
                        {phase.label}
                      </div>
                      {isActive && (
                        <motion.div
                          className="w-full h-1 bg-blue-500 rounded-full mt-2"
                          initial={{ scaleX: 0 }}
                          animate={{ scaleX: 1 }}
                          transition={{ duration: 0.5, repeat: Infinity, repeatType: "reverse" }}
                        />
                      )}
                    </motion.div>
                  );
                })}
              </div>
            )}

            {/* Real-time Analytics */}
            {!isFallbackMode && progressData.timestamp && (
              <div className="bg-slate-50 rounded-lg p-3 border border-slate-200">
                <div className="flex items-center justify-between text-xs text-slate-600">
                  <div className="flex items-center space-x-4">
                    <span className="font-medium">Stream Status:</span>
                    <div className="flex items-center space-x-1">
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                      <span className="text-green-600 font-medium">Live</span>
                    </div>
                  </div>
                  <div className="text-slate-500">
                    Last update: {new Date(progressData.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            )}
          </motion.div>
        )}

        {/* Completion Analytics Display */}
        {completionAnalytics && !isSubmitting && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gradient-to-r from-emerald-50 to-blue-50 border border-emerald-200 rounded-xl p-6"
          >
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-8 h-8 bg-gradient-to-r from-emerald-600 to-blue-600 rounded-full flex items-center justify-center">
                <TrendingUp className="w-4 h-4 text-white" />
              </div>
              <div>
                <h4 className="font-bold text-slate-900 text-sm">Report Generation Complete</h4>
                <p className="text-slate-600 text-xs">Performance analytics and quality metrics</p>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-white/70 rounded-lg p-3 text-center">
                <div className="text-lg font-bold text-emerald-600">{completionAnalytics.execution_time}</div>
                <div className="text-xs text-slate-600 font-medium">Execution Time</div>
              </div>
              <div className="bg-white/70 rounded-lg p-3 text-center">
                <div className="text-lg font-bold text-blue-600">{completionAnalytics.processing_speed}</div>
                <div className="text-xs text-slate-600 font-medium">Processing Speed</div>
              </div>
              <div className="bg-white/70 rounded-lg p-3 text-center">
                <div className="text-lg font-bold text-purple-600">{completionAnalytics.report_quality}</div>
                <div className="text-xs text-slate-600 font-medium">Quality Grade</div>
              </div>
              <div className="bg-white/70 rounded-lg p-3 text-center">
                <div className="text-lg font-bold text-orange-600">{completionAnalytics.data_sources.length}</div>
                <div className="text-xs text-slate-600 font-medium">Data Sources</div>
              </div>
            </div>

            <div className="mt-4 text-xs text-slate-600">
              <span className="font-medium">AI Models Used:</span> {completionAnalytics.ai_models_used.join(", ")}
            </div>
          </motion.div>
        )}

        {/* Enhanced Report Data Display */}
        {reportData && !isSubmitting && (
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="space-y-6"
          >
            {/* Market Opportunities */}
            {reportData.market_opportunities && reportData.market_opportunities.length > 0 && (
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className="bg-gradient-to-r from-emerald-50 to-green-50 border border-emerald-200 rounded-xl p-6"
              >
                <div className="flex items-center space-x-3 mb-4">
                  <div className="w-8 h-8 bg-gradient-to-r from-emerald-600 to-green-600 rounded-full flex items-center justify-center">
                    <Lightbulb className="w-4 h-4 text-white" />
                  </div>
                  <div>
                    <h4 className="font-bold text-slate-900 text-sm">Market Opportunities</h4>
                    <p className="text-slate-600 text-xs">Identified growth potential and strategic advantages</p>
                  </div>
                </div>
                <div className="grid gap-4">
                  {reportData.market_opportunities.map((opportunity, index) => (
                    <div key={index} className="bg-white/70 rounded-lg p-4 border border-emerald-100">
                      <div className="flex justify-between items-start mb-2">
                        <h5 className="font-semibold text-emerald-800 text-sm">{opportunity.opportunity_type}</h5>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${opportunity.urgency === 'High' ? 'bg-red-100 text-red-700' :
                          opportunity.urgency === 'Medium' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-green-100 text-green-700'
                          }`}>
                          {opportunity.urgency} Priority
                        </span>
                      </div>
                      <p className="text-slate-700 text-sm mb-3">{opportunity.opportunity_description}</p>
                      <div className="grid grid-cols-2 gap-3 text-xs">
                        <div>
                          <span className="font-medium text-slate-600">Market Size:</span>
                          <span className="ml-1 text-slate-800">{opportunity.market_size_potential}</span>
                        </div>
                        <div>
                          <span className="font-medium text-slate-600">Advantage:</span>
                          <span className="ml-1 text-slate-800">{opportunity.competitive_advantage}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}

            {/* Market Gaps */}
            {reportData.market_gaps && reportData.market_gaps.length > 0 && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="bg-gradient-to-r from-orange-50 to-amber-50 border border-orange-200 rounded-xl p-6"
              >
                <div className="flex items-center space-x-3 mb-4">
                  <div className="w-8 h-8 bg-gradient-to-r from-orange-600 to-amber-600 rounded-full flex items-center justify-center">
                    <BarChart3 className="w-4 h-4 text-white" />
                  </div>
                  <div>
                    <h4 className="font-bold text-slate-900 text-sm">Market Gaps</h4>
                    <p className="text-slate-600 text-xs">Areas with insufficient market coverage</p>
                  </div>
                </div>
                <div className="grid gap-4">
                  {reportData.market_gaps.map((gap, index) => (
                    <div key={index} className="bg-white/70 rounded-lg p-4 border border-orange-100">
                      <div className="flex justify-between items-start mb-2">
                        <h5 className="font-semibold text-orange-800 text-sm">{gap.gap_category}</h5>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${gap.impact_level === 'High' ? 'bg-red-100 text-red-700' :
                          gap.impact_level === 'Medium' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-green-100 text-green-700'
                          }`}>
                          {gap.impact_level} Impact
                        </span>
                      </div>
                      <p className="text-slate-700 text-sm mb-2">{gap.gap_description}</p>
                      <div className="text-xs text-slate-600">
                        <span className="font-medium">Evidence:</span>
                        <span className="ml-1">{gap.evidence}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}

            {/* Strategic Recommendations */}
            {reportData.strategic_recommendations && reportData.strategic_recommendations.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-6"
              >
                <div className="flex items-center space-x-3 mb-4">
                  <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full flex items-center justify-center">
                    <FileText className="w-4 h-4 text-white" />
                  </div>
                  <div>
                    <h4 className="font-bold text-slate-900 text-sm">Strategic Recommendations</h4>
                    <p className="text-slate-600 text-xs">Actionable insights for business growth</p>
                  </div>
                </div>
                <div className="grid gap-4">
                  {reportData.strategic_recommendations.map((recommendation, index) => (
                    <div key={index} className="bg-white/70 rounded-lg p-4 border border-blue-100">
                      <div className="flex justify-between items-start mb-2">
                        <h5 className="font-semibold text-blue-800 text-sm">{recommendation.recommendation}</h5>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${recommendation.priority === 'High' ? 'bg-red-100 text-red-700' :
                          recommendation.priority === 'Medium' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-green-100 text-green-700'
                          }`}>
                          {recommendation.priority} Priority
                        </span>
                      </div>
                      <p className="text-slate-700 text-sm mb-3">{recommendation.expected_impact}</p>
                      <div className="text-xs text-slate-600">
                        <span className="font-medium">Complexity:</span>
                        <span className="ml-1">{recommendation.implementation_complexity}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}

            {/* Risk Assessment */}
            {reportData.risk_assessment && reportData.risk_assessment.length > 0 && (
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className="bg-gradient-to-r from-red-50 to-pink-50 border border-red-200 rounded-xl p-6"
              >
                <div className="flex items-center space-x-3 mb-4">
                  <div className="w-8 h-8 bg-gradient-to-r from-red-600 to-pink-600 rounded-full flex items-center justify-center">
                    <Shield className="w-4 h-4 text-white" />
                  </div>
                  <div>
                    <h4 className="font-bold text-slate-900 text-sm">Risk Assessment</h4>
                    <p className="text-slate-600 text-xs">Potential challenges and mitigation strategies</p>
                  </div>
                </div>
                <div className="grid gap-4">
                  {reportData.risk_assessment.map((risk, index) => (
                    <div key={index} className="bg-white/70 rounded-lg p-4 border border-red-100">
                      <div className="flex justify-between items-start mb-2">
                        <h5 className="font-semibold text-red-800 text-sm">{risk.risk_type}</h5>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${risk.probability === 'High' ? 'bg-red-100 text-red-700' :
                          risk.probability === 'Medium' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-green-100 text-green-700'
                          }`}>
                          {risk.probability} Probability
                        </span>
                      </div>
                      <p className="text-slate-700 text-sm mb-3">{risk.risk_description}</p>
                      <div className="text-xs text-slate-600">
                        <span className="font-medium">Mitigation:</span>
                        <span className="ml-1">{risk.mitigation_strategy}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </motion.div>
        )}

        <div>
          <label className="flex items-center space-x-2 text-sm font-medium text-slate-700 mb-3">
            <Building2 className="w-4 h-4" />
            <span>Company name</span>
          </label>
          <input
            type="text"
            value={formData.companyName}
            onChange={(e) =>
              setFormData({ ...formData, companyName: e.target.value })
            }
            placeholder="e.g. TechCorp Solutions"
            className="w-full px-4 py-3 rounded-lg border border-slate-200 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 placeholder-slate-400"
            required
          />
        </div>

        <div>
          <label className="flex items-center space-x-2 text-sm font-medium text-slate-700 mb-3">
            <Package className="w-4 h-4" />
            <span>Main product or service</span>
          </label>
          <input
            type="text"
            value={formData.product}
            onChange={(e) =>
              setFormData({ ...formData, product: e.target.value })
            }
            placeholder="e.g. CRM management platform"
            className="w-full px-4 py-3 rounded-lg border border-slate-200 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 placeholder-slate-400"
            required
          />
        </div>

        <div>
          <label className="flex items-center space-x-2 text-sm font-medium text-slate-700 mb-3">
            <Target className="w-4 h-4" />
            <span>Industry sector</span>
          </label>
          <input
            type="text"
            value={formData.sector}
            onChange={(e) =>
              setFormData({ ...formData, sector: e.target.value })
            }
            placeholder="e.g. Banking & Finance sector"
            className="w-full px-4 py-3 rounded-lg border border-slate-200 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 placeholder-slate-400"
            required
          />
        </div>

        <motion.button
          type="submit"
          disabled={!isValid || isSubmitting}
          whileHover={isValid ? { scale: 1.02 } : {}}
          whileTap={isValid ? { scale: 0.98 } : {}}
          className={`w-full py-4 rounded-lg font-medium text-white transition-all duration-200 flex items-center justify-center space-x-2 ${isValid && !isSubmitting
            ? "bg-gradient-to-r from-blue-600 to-emerald-600 hover:from-blue-700 hover:to-emerald-700 shadow-lg shadow-blue-500/25"
            : "bg-slate-300 cursor-not-allowed"
            }`}
        >
          {isSubmitting ? (
            isStreaming ? (
              <>
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  className="w-5 h-5 border-2 border-white border-t-transparent rounded-full"
                />
                <span>Real-time Analysis in Progress...</span>
              </>
            ) : isFallbackMode ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Standard Processing...</span>
              </>
            ) : (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Connecting...</span>
              </>
            )
          ) : (
            <>
              <span>Generate Report</span>
              <ArrowRight className="w-5 h-5" />
            </>
          )}
        </motion.button>
      </form>
    </motion.div>
  );
};

export default BusinessForm;
