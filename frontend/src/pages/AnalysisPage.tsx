import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Users, Database, TrendingUp, Target, CheckCircle } from "lucide-react";

const AnalysisPage: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);
  const navigate = useNavigate();

  const steps = [
    {
      id: 1,
      title: "Identifying competitors",
      description: "Analyzing the competitive landscape",
      icon: Users,
      duration: 3000,
    },
    {
      id: 2,
      title: "Collecting data",
      description: "Extracting market data",
      icon: Database,
      duration: 4000,
    },
    {
      id: 3,
      title: "Gap analysis",
      description: "Identifying growth opportunities",
      icon: TrendingUp,
      duration: 3500,
    },
    {
      id: 4,
      title: "Generating recommendations",
      description: "Creating the strategic report",
      icon: Target,
      duration: 2500,
    },
  ];

  useEffect(() => {
    let progressInterval: NodeJS.Timeout;
    let stepTimeout: NodeJS.Timeout;

    const startStep = (stepIndex: number) => {
      if (stepIndex >= steps.length) {
        // Analysis complete, navigate to dashboard
        setTimeout(() => navigate("/dashboard"), 1000);
        return;
      }

      const step = steps[stepIndex];
      const stepDuration = step.duration;
      let stepProgress = 0;

      progressInterval = setInterval(() => {
        stepProgress += 100 / (stepDuration / 50);
        const totalProgress = (stepIndex * 100 + stepProgress) / steps.length;
        setProgress(Math.min(totalProgress, 100));

        if (stepProgress >= 100) {
          clearInterval(progressInterval);
          setCurrentStep(stepIndex + 1);
          stepTimeout = setTimeout(() => startStep(stepIndex + 1), 500);
        }
      }, 50);
    };

    startStep(currentStep);

    return () => {
      clearInterval(progressInterval);
      clearTimeout(stepTimeout);
    };
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="min-h-[calc(100vh-4rem)] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8"
    >
      <div className="max-w-2xl w-full">
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="text-center mb-12"
        >
          <div className="w-20 h-20 bg-gradient-to-r from-blue-600 to-emerald-600 rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg shadow-blue-500/25">
            <div className="w-12 h-12 border-4 border-white border-t-transparent rounded-full animate-spin"></div>
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-4">
            Analysis in progress
          </h1>
          <p className="text-lg text-slate-600 mb-8">
            Our AI is analyzing your market and identifying growth opportunities
          </p>

          {/* Progress Bar */}
          <div className="mb-8">
            <div className="flex items-center justify-between text-sm text-slate-600 mb-2">
              <span>Progress</span>
              <span>{Math.round(progress)}%</span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-2">
              <motion.div
                className="bg-gradient-to-r from-blue-600 to-emerald-600 h-2 rounded-full"
                style={{ width: `${progress}%` }}
                transition={{ ease: "easeOut" }}
              />
            </div>
          </div>
        </motion.div>

        {/* Steps */}
        <div className="space-y-4">
          {steps.map((step, index) => {
            const Icon = step.icon;
            const isActive = index === currentStep;
            const isCompleted = index < currentStep;
            const isPending = index > currentStep;

            return (
              <motion.div
                key={step.id}
                initial={{ x: -20, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                transition={{ delay: index * 0.1 }}
                className={`flex items-center p-6 rounded-xl border transition-all duration-500 ${
                  isActive
                    ? "bg-gradient-to-r from-blue-50 to-emerald-50 border-blue-200 shadow-md"
                    : isCompleted
                    ? "bg-green-50 border-green-200"
                    : "bg-white border-slate-200"
                }`}
              >
                <div
                  className={`w-12 h-12 rounded-full flex items-center justify-center mr-4 transition-all duration-500 ${
                    isActive
                      ? "bg-gradient-to-r from-blue-600 to-emerald-600 text-white animate-pulse"
                      : isCompleted
                      ? "bg-green-500 text-white"
                      : "bg-slate-200 text-slate-400"
                  }`}
                >
                  {isCompleted ? (
                    <CheckCircle className="w-6 h-6" />
                  ) : (
                    <Icon className="w-6 h-6" />
                  )}
                </div>
                <div className="flex-1">
                  <h3
                    className={`font-semibold text-lg transition-colors duration-500 ${
                      isActive
                        ? "text-blue-900"
                        : isCompleted
                        ? "text-green-900"
                        : "text-slate-600"
                    }`}
                  >
                    {step.title}
                  </h3>
                  <p
                    className={`text-sm transition-colors duration-500 ${
                      isActive
                        ? "text-blue-700"
                        : isCompleted
                        ? "text-green-700"
                        : "text-slate-500"
                    }`}
                  >
                    {step.description}
                  </p>
                </div>
                {isActive && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"
                  />
                )}
              </motion.div>
            );
          })}
        </div>

        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="text-center mt-8"
        >
          <p className="text-sm text-slate-500">
            The analysis usually takes between 2 to 5 minutes
          </p>
        </motion.div>
      </div>
    </motion.div>
  );
};

export default AnalysisPage;
