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
  Clock,
  Database,
  DollarSign,
  PieChart,
  RefreshCw,
  Target,
  TrendingUp
} from "lucide-react";
import React, { useState } from "react";
import { Bar as ChartJSBar, Doughnut, Line, Pie, Scatter } from 'react-chartjs-2';
import { useLocation } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie as RechartsPie,
  PieChart as RechartsPieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

// Import our custom components
import MapComponent from "../components/MapComponent";
import RecommendationsComponent from "../components/RecommendationsComponent";
import ReportComponent from "../components/ReportComponent";

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

// Types for chart data
interface ChartData {
  title: string;
  type: 'line' | 'bar' | 'pie' | 'doughnut' | 'area' | 'scatter';
  labels: string[];
  data: number[];
  description?: string;
}

// Types for API data
interface KpiData {
  title: string;
  value: string;
  change: string;
  icon: string;
  color: string;
  description: string;
}

interface ProcessedKpiData extends Omit<KpiData, 'icon'> {
  icon: React.ComponentType<{ className?: string }>;
}

interface RevenueData {
  name: string;
  value: number;
  fill: string;
}

interface ProfitabilityData {
  month: string;
  profit: number;
}

interface RoiAction {
  action: string;
  roi: number;
  complexity: string;
  impact: string;
}

interface DashboardApiData {
  kpiData?: KpiData[];
  revenueData?: RevenueData[];
  profitabilityData?: ProfitabilityData[];
  roiActions?: RoiAction[];
}

// Chart rendering component for analyzed data
const AnalyzedChart = ({ chart }: { chart: ChartData }) => {
  const { title, type, labels, data, description } = chart;

  // Create chart data object
  const chartData = {
    labels: type === 'scatter' ? undefined : labels,
    datasets: [
      {
        label: title,
        data: type === 'scatter'
          ? data.map((value, index) => ({ x: index + 1, y: value }))
          : data,
        backgroundColor:
          type === 'pie' || type === 'doughnut'
            ? [
              'rgba(255, 99, 132, 0.8)',
              'rgba(54, 162, 235, 0.8)',
              'rgba(255, 205, 86, 0.8)',
              'rgba(75, 192, 192, 0.8)',
              'rgba(153, 102, 255, 0.8)',
              'rgba(255, 159, 64, 0.8)',
              'rgba(255, 193, 7, 0.8)',
              'rgba(156, 39, 176, 0.8)',
            ]
            : type === 'line'
              ? 'rgba(75, 192, 192, 0.6)'
              : type === 'area'
                ? 'rgba(75, 192, 192, 0.4)'
                : type === 'scatter'
                  ? 'rgba(255, 99, 132, 0.6)'
                  : 'rgba(54, 162, 235, 0.8)',
        borderColor:
          type === 'pie' || type === 'doughnut'
            ? [
              'rgba(255, 99, 132, 1)',
              'rgba(54, 162, 235, 1)',
              'rgba(255, 205, 86, 1)',
              'rgba(75, 192, 192, 1)',
              'rgba(153, 102, 255, 1)',
              'rgba(255, 159, 64, 1)',
              'rgba(255, 193, 7, 1)',
              'rgba(156, 39, 176, 1)',
            ]
            : type === 'line'
              ? 'rgba(75, 192, 192, 1)'
              : type === 'area'
                ? 'rgba(75, 192, 192, 1)'
                : type === 'scatter'
                  ? 'rgba(255, 99, 132, 1)'
                  : 'rgba(54, 162, 235, 1)',
        borderWidth: 2,
        fill: type === 'area' ? true : type === 'line' ? false : undefined,
        tension: type === 'line' || type === 'area' ? 0.1 : undefined,
        pointRadius: type === 'scatter' ? 6 : undefined,
        pointHoverRadius: type === 'scatter' ? 8 : undefined,
      },
    ],
  };

  // Chart options
  const options = {
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
    scales: type !== 'pie' && type !== 'doughnut' ? {
      y: {
        beginAtZero: true,
      },
      x: type === 'scatter' ? {
        type: 'linear' as const,
        position: 'bottom' as const,
        beginAtZero: true,
      } : {
        beginAtZero: true,
      }
    } : undefined,
  };

  // Select the appropriate chart component based on type
  const renderChart = () => {
    switch (type) {
      case 'line':
        return <Line data={chartData} options={options} />;
      case 'bar':
        return <ChartJSBar data={chartData} options={options} />;
      case 'pie':
        return <Pie data={chartData} options={options} />;
      case 'doughnut':
        return <Doughnut data={chartData} options={options} />;
      case 'area':
        // Area chart is essentially a line chart with fill
        return <Line data={chartData} options={options} />;
      case 'scatter':
        return <Scatter data={chartData} options={options} />;
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
      className="bg-white rounded-xl shadow-lg shadow-slate-200/50 border border-slate-200 p-6"
    >
      <div className="h-64 mb-4">
        {renderChart()}
      </div>
      {description && (
        <div className="text-sm text-slate-600 italic border-t border-slate-100 pt-4">
          {description}
        </div>
      )}
    </motion.div>
  );
};

// Interface for backend response
interface BackendReportData {
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
}

interface ChartDataFromBackend {
  title: string;
  type: 'line' | 'bar' | 'pie' | 'doughnut' | 'area' | 'scatter';
  labels: string[];
  data: number[];
  description?: string;
  backgroundColor?: string | string[];
  borderColor?: string | string[];
  insights?: string[];
}

interface BackendResponse {
  status: string;
  data: {
    report_data: BackendReportData;
    dashboard_data?: DashboardApiData;
    data_charts?: ChartDataFromBackend[];
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

interface DashboardPageProps {
  backendData?: BackendResponse | BackendReportData;
}

// Interface for location state
interface LocationState {
  backendData?: BackendResponse;
}

const DashboardPage: React.FC<DashboardPageProps> = ({ backendData }) => {
  const location = useLocation() as { state?: LocationState };
  const [jsonInput, setJsonInput] = useState('');
  const [analyzedCharts, setAnalyzedCharts] = useState<ChartData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAnalyzer, setShowAnalyzer] = useState(false);
  const [jsonValid, setJsonValid] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  // Dashboard data state
  const [dashboardData, setDashboardData] = useState<DashboardApiData | null>(null);

  // Get backend data from props or navigation state
  const getBackendData = (): BackendResponse | BackendReportData | null => {
    // First check if data is passed via navigation state (from form submission)
    if (location.state && location.state.backendData) {
      return location.state.backendData;
    }
    // Fallback to props
    return backendData || null;
  };

  const currentBackendData = getBackendData();

  // Extract backend data if available
  const getBackendReportData = (): BackendReportData | null => {
    const dataSource = currentBackendData;
    if (!dataSource) return null;

    // Check if it's a backend response
    if ('status' in dataSource && 'data' in dataSource) {
      const backendResponse = dataSource as BackendResponse;
      return backendResponse.data.report_data;
    }

    // Otherwise, it's already in the expected format
    return dataSource as BackendReportData;
  };

  const reportData = getBackendReportData();

  // Check if we have fresh data from form submission
  const hasNewData = location.state && location.state.backendData;

  // Load API data (this would typically come from props or context)
  React.useEffect(() => {
    // Check if we have fresh backend data from form submission
    if (hasNewData && currentBackendData) {
      // Extract dashboard data if available
      if ('data' in currentBackendData && currentBackendData.data.dashboard_data) {
        setDashboardData(currentBackendData.data.dashboard_data);
      }

      // Show success notification
      console.log('Successfully loaded fresh analysis data!');

      // If we have new data, switch to the report tab to show the fresh analysis
      setActiveTab('report');

      return; // Don't load sample data if we have real data
    }

    // Fallback to sample data if no backend data
    // You can set this from props, context, or API call
    const sampleApiData = {
      "dashboard_data": {
        "kpiData": [
          {
            "title": "Potentiel de revenus",
            "value": "1.0M€",
            "change": "+18%",
            "icon": "TrendingUp",
            "color": "blue",
            "description": "Revenus supplémentaires identifiés"
          },
          {
            "title": "ROI moyen",
            "value": "399%",
            "change": "+9%",
            "icon": "Target",
            "color": "emerald",
            "description": "Retour sur investissement prévu"
          },
          {
            "title": "Économies identifiées",
            "value": "593K€",
            "change": "+23%",
            "icon": "DollarSign",
            "color": "orange",
            "description": "Coûts optimisables détectés"
          },
          {
            "title": "Temps de retour",
            "value": "10 mois",
            "change": "-3 mois",
            "icon": "Clock",
            "color": "purple",
            "description": "Délai de rentabilité estimé"
          }
        ],
        "revenueData": [
          {
            "name": "Services core",
            "value": 350000,
            "fill": "#3B82F6"
          },
          {
            "name": "Services B2B",
            "value": 250000,
            "fill": "#10B981"
          },
          {
            "name": "Consulting",
            "value": 200000,
            "fill": "#F59E0B"
          },
          {
            "name": "Formation",
            "value": 120000,
            "fill": "#8B5CF6"
          },
          {
            "name": "Partenariats",
            "value": 80000,
            "fill": "#EF4444"
          }
        ],
        "profitabilityData": [
          {
            "month": "Jan",
            "profit": 14175
          },
          {
            "month": "Fév",
            "profit": 12508
          },
          {
            "month": "Mar",
            "profit": 15389
          },
          {
            "month": "Avr",
            "profit": 14514
          },
          {
            "month": "Mai",
            "profit": 18073
          },
          {
            "month": "Juin",
            "profit": 16830
          },
          {
            "month": "Juil",
            "profit": 18845
          },
          {
            "month": "Août",
            "profit": 21293
          },
          {
            "month": "Sep",
            "profit": 19588
          },
          {
            "month": "Oct",
            "profit": 21136
          },
          {
            "month": "Nov",
            "profit": 20308
          },
          {
            "month": "Déc",
            "profit": 26700
          }
        ],
        "roiActions": [
          {
            "action": "Optimisation SEO",
            "roi": 416,
            "complexity": "Faible",
            "impact": "Fort"
          },
          {
            "action": "Automatisation marketing",
            "roi": 422,
            "complexity": "Moyen",
            "impact": "Fort"
          },
          {
            "action": "Expansion géographique",
            "roi": 332,
            "complexity": "Élevé",
            "impact": "Fort"
          },
          {
            "action": "Diversification produit",
            "roi": 281,
            "complexity": "Élevé",
            "impact": "Moyen"
          },
          {
            "action": "Partenariats stratégiques",
            "roi": 226,
            "complexity": "Moyen",
            "impact": "Moyen"
          }
        ]
      }
    };

    setDashboardData(sampleApiData.dashboard_data);
  }, [hasNewData, currentBackendData]);

  // Sample data for components
  const sampleReportData = {
    market_opportunities: [
      {
        opportunity_description: "Expansion into AI-powered consulting services for SMEs",
        opportunity_type: "Market Expansion",
        urgency: "high",
        market_size_potential: "€1.2M potential revenue",
        competitive_advantage: "First-mover advantage in AI consulting for SMEs"
      },
      {
        opportunity_description: "Development of automated business intelligence platform",
        opportunity_type: "Product Innovation",
        urgency: "medium",
        market_size_potential: "€800K potential revenue",
        competitive_advantage: "Proprietary algorithms and local market expertise"
      }
    ],
    market_gaps: [
      {
        gap_description: "Limited digital transformation support for traditional industries",
        impact_level: "high",
        gap_category: "Service Gap",
        evidence: "82% of local businesses lack comprehensive digital strategy"
      },
      {
        gap_description: "Absence of specialized AI training programs",
        impact_level: "medium",
        gap_category: "Education Gap",
        evidence: "Growing demand for AI skills with no local providers"
      }
    ],
    trend_analysis: {
      trend_based_opportunities: [
        "Rising demand for AI integration in business processes",
        "Increased focus on data-driven decision making",
        "Growing need for cybersecurity consulting"
      ],
      emerging_trends: [
        "Sustainable business practices adoption",
        "Remote work optimization solutions",
        "Cloud-first infrastructure migration"
      ],
      trend_implications: [
        "Position as AI transformation leader",
        "Develop sustainable consulting offerings",
        "Expand cloud migration services"
      ]
    },
    competitive_insights: {
      competitive_weaknesses: [
        "Limited presence in emerging tech sectors",
        "Lack of specialized AI expertise",
        "Insufficient digital marketing presence"
      ],
      competitive_strengths: [
        "Strong local network and relationships",
        "Proven track record in traditional consulting",
        "Excellent client retention rates"
      ],
      market_positioning: "Well-established in traditional consulting with opportunity to lead in AI transformation",
      differentiation_opportunities: [
        "Become the go-to AI transformation partner",
        "Develop industry-specific AI solutions",
        "Create educational content and thought leadership"
      ]
    }
  };

  const sampleStrategicRecommendations = [
    {
      recommendation: "Develop comprehensive AI consulting practice with specialized team and training programs",
      priority: "high",
      implementation_complexity: "medium",
      expected_impact: "Expected to capture 30% of local AI consulting market within 18 months"
    },
    {
      recommendation: "Launch digital transformation assessment tool for SMEs",
      priority: "high",
      implementation_complexity: "low",
      expected_impact: "Generate 200+ qualified leads per quarter"
    },
    {
      recommendation: "Create strategic partnerships with technology vendors",
      priority: "medium",
      implementation_complexity: "low",
      expected_impact: "Reduce implementation costs by 25% and expand service offerings"
    }
  ];

  const sampleRiskAssessment = [
    {
      risk_type: "Market Competition",
      probability: "high",
      risk_description: "Large consulting firms entering the local AI market",
      mitigation_strategy: "Establish first-mover advantage and build strong client relationships"
    },
    {
      risk_type: "Technology Evolution",
      probability: "medium",
      risk_description: "Rapid changes in AI technology making current solutions obsolete",
      mitigation_strategy: "Continuous learning and partnership with technology leaders"
    }
  ];

  // Icon mapping function
  const getIconComponent = (iconName: string) => {
    const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
      TrendingUp,
      Target,
      DollarSign,
      Clock,
    };
    return iconMap[iconName] || TrendingUp;
  };

  // Generate KPI data from backend report data
  const generateKpiFromBackend = (): ProcessedKpiData[] => {
    if (!reportData) return getDefaultKpiData();

    const kpis: ProcessedKpiData[] = [];

    // Calculate revenue potential from market opportunities
    if (reportData.market_opportunities && reportData.market_opportunities.length > 0) {
      const totalOpportunities = reportData.market_opportunities.length;
      const highUrgencyCount = reportData.market_opportunities.filter(
        op => op.urgency.toLowerCase() === 'high'
      ).length;

      // Extract market size potential values and calculate total
      const marketSizes = reportData.market_opportunities
        .map(op => {
          const match = op.market_size_potential.match(/[\d,]+/);
          return match ? parseInt(match[0].replace(/,/g, '')) : 500000;
        });
      const totalRevenuePotential = marketSizes.reduce((sum, val) => sum + val, 0);

      kpis.push({
        title: "Revenue Potential",
        value: `€${(totalRevenuePotential / 1000000).toFixed(1)}M`,
        change: `+${totalOpportunities * 5}%`,
        icon: TrendingUp,
        color: "blue",
        description: `${totalOpportunities} market opportunities identified`,
      });

      kpis.push({
        title: "High Priority Actions",
        value: `${highUrgencyCount}`,
        change: `${Math.round((highUrgencyCount / totalOpportunities) * 100)}%`,
        icon: Target,
        color: "emerald",
        description: "Urgent opportunities requiring immediate action",
      });
    }

    // Calculate risk and gap metrics
    if (reportData.market_gaps && reportData.market_gaps.length > 0) {
      const highImpactGaps = reportData.market_gaps.filter(
        gap => gap.impact_level.toLowerCase() === 'high'
      ).length;

      kpis.push({
        title: "Market Gaps",
        value: `${reportData.market_gaps.length}`,
        change: `-${highImpactGaps * 10}%`,
        icon: DollarSign,
        color: "orange",
        description: `${highImpactGaps} high-impact gaps identified`,
      });
    }

    // Calculate implementation timeline
    if (reportData.strategic_recommendations && reportData.strategic_recommendations.length > 0) {
      const avgComplexity = reportData.strategic_recommendations.reduce((acc, rec) => {
        const complexity = rec.implementation_complexity.toLowerCase();
        return acc + (complexity === 'low' ? 3 : complexity === 'medium' ? 6 : 12);
      }, 0) / reportData.strategic_recommendations.length;

      kpis.push({
        title: "Implementation Time",
        value: `${Math.round(avgComplexity)} months`,
        change: "-2 months",
        icon: Clock,
        color: "purple",
        description: "Average implementation timeline",
      });
    }

    // Fill with default data if not enough KPIs generated
    while (kpis.length < 4) {
      const defaultKpis = getDefaultKpiData();
      kpis.push(defaultKpis[kpis.length]);
    }

    return kpis.slice(0, 4);
  };

  // Generate revenue data from backend
  const generateRevenueFromBackend = (): RevenueData[] => {
    if (!reportData?.market_opportunities) return getDefaultRevenueData();

    const revenueCategories: { [key: string]: number } = {};
    const colors = ["#3B82F6", "#10B981", "#F59E0B", "#8B5CF6", "#EF4444"];

    reportData.market_opportunities.forEach((opportunity, index) => {
      const category = opportunity.opportunity_type || `Opportunity ${index + 1}`;
      const sizeMatch = opportunity.market_size_potential.match(/[\d,]+/);
      const value = sizeMatch ? parseInt(sizeMatch[0].replace(/,/g, '')) : 100000;

      if (revenueCategories[category]) {
        revenueCategories[category] += value;
      } else {
        revenueCategories[category] = value;
      }
    });

    return Object.entries(revenueCategories)
      .map(([name, value], index) => ({
        name: name.slice(0, 20) + (name.length > 20 ? '...' : ''),
        value,
        fill: colors[index % colors.length]
      }))
      .slice(0, 5);
  };

  // Generate profitability projection from trends
  const generateProfitabilityFromBackend = (): ProfitabilityData[] => {
    if (!reportData?.trend_analysis?.emerging_trends) return getDefaultProfitabilityData();

    const months = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sep", "Oct", "Nov", "Déc"];
    const trendCount = reportData.trend_analysis.emerging_trends.length;
    const baseProfit = 15000;

    return months.map((month, index) => ({
      month,
      profit: Math.round(baseProfit + (trendCount * 1000 * (1 + index * 0.1)) + (Math.random() * 3000))
    }));
  };

  // Generate ROI actions from strategic recommendations
  const generateRoiFromBackend = (): RoiAction[] => {
    if (!reportData?.strategic_recommendations) return getDefaultRoiActions();

    return reportData.strategic_recommendations.map((rec) => {
      const complexity = rec.implementation_complexity.toLowerCase();
      const priority = rec.priority.toLowerCase();

      // Calculate ROI based on priority and complexity
      let roi = 200 + (priority === 'high' ? 150 : priority === 'medium' ? 100 : 50);
      roi += (complexity === 'low' ? 100 : complexity === 'medium' ? 50 : 0);
      roi += Math.random() * 100;

      return {
        action: rec.recommendation.slice(0, 50) + (rec.recommendation.length > 50 ? '...' : ''),
        roi: Math.round(roi),
        complexity: complexity === 'low' ? 'Faible' : complexity === 'medium' ? 'Moyen' : 'Élevé',
        impact: priority === 'high' ? 'Fort' : 'Moyen'
      };
    }).slice(0, 5);
  };

  // Default data functions
  const getDefaultKpiData = (): ProcessedKpiData[] => [
    {
      title: "Potentiel de revenus",
      value: "1.0M€",
      change: "+18%",
      icon: TrendingUp,
      color: "blue",
      description: "Revenus supplémentaires identifiés",
    },
    {
      title: "ROI moyen",
      value: "399%",
      change: "+9%",
      icon: Target,
      color: "emerald",
      description: "Retour sur investissement prévu",
    },
    {
      title: "Économies identifiées",
      value: "593K€",
      change: "+23%",
      icon: DollarSign,
      color: "orange",
      description: "Coûts optimisables détectés",
    },
    {
      title: "Temps de retour",
      value: "10 mois",
      change: "-3 mois",
      icon: Clock,
      color: "purple",
      description: "Délai de rentabilité estimé",
    },
  ];

  const getDefaultRevenueData = (): RevenueData[] => [
    { name: "Services core", value: 350000, fill: "#3B82F6" },
    { name: "Services B2B", value: 250000, fill: "#10B981" },
    { name: "Consulting", value: 200000, fill: "#F59E0B" },
    { name: "Formation", value: 120000, fill: "#8B5CF6" },
    { name: "Partenariats", value: 80000, fill: "#EF4444" },
  ];

  const getDefaultProfitabilityData = (): ProfitabilityData[] => [
    { month: "Jan", profit: 14175 },
    { month: "Fév", profit: 12508 },
    { month: "Mar", profit: 15389 },
    { month: "Avr", profit: 14514 },
    { month: "Mai", profit: 18073 },
    { month: "Juin", profit: 16830 },
    { month: "Juil", profit: 18845 },
    { month: "Août", profit: 21293 },
    { month: "Sep", profit: 19588 },
    { month: "Oct", profit: 21136 },
    { month: "Nov", profit: 20308 },
    { month: "Déc", profit: 26700 },
  ];

  const getDefaultRoiActions = (): RoiAction[] => [
    {
      action: "Optimisation SEO",
      roi: 416,
      complexity: "Faible",
      impact: "Fort",
    },
    {
      action: "Automatisation marketing",
      roi: 422,
      complexity: "Moyen",
      impact: "Fort",
    },
    {
      action: "Expansion géographique",
      roi: 332,
      complexity: "Élevé",
      impact: "Fort",
    },
    {
      action: "Diversification produit",
      roi: 281,
      complexity: "Élevé",
      impact: "Moyen",
    },
    {
      action: "Partenariats stratégiques",
      roi: 226,
      complexity: "Moyen",
      impact: "Moyen",
    },
  ];

  // Use API data or generate from backend data
  const kpiData = dashboardData?.kpiData?.map((kpi: KpiData) => ({
    ...kpi,
    icon: getIconComponent(kpi.icon)
  })) || generateKpiFromBackend();

  const revenueData = dashboardData?.revenueData || generateRevenueFromBackend();

  const profitabilityData = dashboardData?.profitabilityData || generateProfitabilityFromBackend();

  const roiActions = dashboardData?.roiActions || generateRoiFromBackend();

  // Validate JSON input
  const validateJson = (input: string) => {
    try {
      JSON.parse(input);
      setJsonValid(true);
      setError(null);
    } catch {
      setJsonValid(false);
      setError('Invalid JSON format');
    }
  };

  // Analyze data and generate charts
  const analyzeData = async () => {
    if (!jsonInput.trim() || !jsonValid) {
      setError('Please enter valid JSON data');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Simulate API call to analyze data
      const data = JSON.parse(jsonInput);

      // Simple data analysis to generate chart suggestions
      const charts = generateChartSuggestions(data);
      setAnalyzedCharts(charts);
    } catch {
      setError('Failed to analyze data');
    } finally {
      setLoading(false);
    }
  };

  // Generate chart suggestions based on data structure
  const generateChartSuggestions = (data: unknown): ChartData[] => {
    const charts: ChartData[] = [];

    // If data is an array of objects
    if (Array.isArray(data) && data.length > 0 && typeof data[0] === 'object' && data[0] !== null) {
      const keys = Object.keys(data[0] as Record<string, unknown>);

      // Find numerical columns
      const numericKeys = keys.filter(key =>
        data.every((item: unknown) => {
          const obj = item as Record<string, unknown>;
          return typeof obj[key] === 'number' || !isNaN(Number(obj[key]));
        })
      );

      // Find categorical columns
      const categoricalKeys = keys.filter(key => {
        const firstItem = data[0] as Record<string, unknown>;
        return !numericKeys.includes(key) && typeof firstItem[key] === 'string';
      });

      if (categoricalKeys.length > 0 && numericKeys.length > 0) {
        const categoryKey = categoricalKeys[0];
        const valueKey = numericKeys[0];

        // Generate bar chart
        charts.push({
          title: `${valueKey} by ${categoryKey}`,
          type: 'bar',
          labels: data.map((item: unknown) => String((item as Record<string, unknown>)[categoryKey])),
          data: data.map((item: unknown) => Number((item as Record<string, unknown>)[valueKey])),
          description: `A bar chart showing the distribution of ${valueKey} across different ${categoryKey} categories.`
        });

        // Generate pie chart if data length is reasonable
        if (data.length <= 10) {
          charts.push({
            title: `${valueKey} Distribution`,
            type: 'pie',
            labels: data.map((item: unknown) => String((item as Record<string, unknown>)[categoryKey])),
            data: data.map((item: unknown) => Number((item as Record<string, unknown>)[valueKey])),
            description: `A pie chart showing the proportional distribution of ${valueKey}.`
          });
        }

        // Generate line chart if data appears to be time-series
        if (data.length > 2) {
          charts.push({
            title: `${valueKey} Trend`,
            type: 'line',
            labels: data.map((item: unknown, index: number) => {
              const obj = item as Record<string, unknown>;
              return String(obj[categoryKey]) || `Point ${index + 1}`;
            }),
            data: data.map((item: unknown) => Number((item as Record<string, unknown>)[valueKey])),
            description: `A line chart showing the trend of ${valueKey} over time or sequence.`
          });
        }

        // Generate doughnut chart as an alternative to pie chart
        if (data.length <= 8) {
          charts.push({
            title: `${valueKey} Breakdown`,
            type: 'doughnut',
            labels: data.map((item: unknown) => String((item as Record<string, unknown>)[categoryKey])),
            data: data.map((item: unknown) => Number((item as Record<string, unknown>)[valueKey])),
            description: `A doughnut chart showing the breakdown of ${valueKey} by ${categoryKey}.`
          });
        }
      }
    }

    // If no charts generated, create a sample chart
    if (charts.length === 0) {
      charts.push({
        title: 'Sample Data Visualization',
        type: 'bar',
        labels: ['Category A', 'Category B', 'Category C', 'Category D'],
        data: [12, 19, 3, 5],
        description: 'This is a sample chart. Please provide structured data for better analysis.'
      });
    }

    return charts;
  };

  const getColorClasses = (color: string) => {
    const colors = {
      blue: "from-blue-500 to-blue-600 bg-blue-50 text-blue-600 border-blue-200",
      emerald:
        "from-emerald-500 to-emerald-600 bg-emerald-50 text-emerald-600 border-emerald-200",
      orange:
        "from-orange-500 to-orange-600 bg-orange-50 text-orange-600 border-orange-200",
      purple:
        "from-purple-500 to-purple-600 bg-purple-50 text-purple-600 border-purple-200",
    };
    return colors[color as keyof typeof colors] || colors.blue;
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="py-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto"
    >
      {/* Header with Data Analyzer Toggle */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="mb-8 text-center"
      >
        <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent mb-2">
          Business Intelligence Dashboard
        </h1>
        <p className="text-slate-600 text-lg mb-6">
          Monitor your business performance and analyze data with our intelligent dashboard
        </p>

        {/* Success notification for fresh data */}
        {hasNewData && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gradient-to-r from-emerald-50 to-green-50 border border-emerald-200 rounded-lg p-4 mb-6 mx-auto max-w-md"
          >
            <div className="flex items-center justify-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-r from-emerald-600 to-green-600 rounded-full flex items-center justify-center">
                <TrendingUp className="w-4 h-4 text-white" />
              </div>
              <div className="text-center">
                <p className="text-emerald-800 font-semibold text-sm">Analysis Complete!</p>
                <p className="text-emerald-600 text-xs">Fresh insights loaded from your business analysis</p>
              </div>
            </div>
          </motion.div>
        )}

        <button
          onClick={() => setShowAnalyzer(!showAnalyzer)}
          className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg hover:from-blue-700 hover:to-indigo-700 transition-all duration-200 shadow-lg hover:shadow-xl"
        >
          <Database className="w-5 h-5" />
          {showAnalyzer ? 'Hide' : 'Show'} Data Analyzer
        </button>
      </motion.div>

      {/* Tab Navigation */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="bg-white rounded-xl shadow-lg shadow-slate-200/50 border border-slate-200 p-2 mb-8"
      >
        <div className="flex space-x-2">
          {[
            { id: 'overview', label: 'Overview', icon: BarChart3 },
            { id: 'map', label: 'Regional Analysis', icon: Target },
            { id: 'recommendations', label: 'Recommendations', icon: TrendingUp },
            { id: 'report', label: 'Detailed Report', icon: Database },
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-6 py-3 rounded-lg font-medium transition-all duration-200 ${activeTab === tab.id
                  ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/25'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                  }`}
              >
                <Icon className="w-5 h-5" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </motion.div>

      {/* Data Analyzer Section */}
      {showAnalyzer && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="bg-white rounded-xl shadow-lg shadow-slate-200/50 border border-slate-200 p-6 mb-8"
        >
          <h2 className="text-2xl font-bold text-slate-800 mb-4 flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-blue-600" />
            Generative Data Analyzer
          </h2>

          <div className="space-y-4">
            <div>
              <label htmlFor="jsonInput" className="block text-sm font-medium text-slate-700 mb-2">
                Enter your data (JSON format):
              </label>
              <textarea
                id="jsonInput"
                value={jsonInput}
                onChange={(e) => {
                  setJsonInput(e.target.value);
                  validateJson(e.target.value);
                }}
                placeholder='Example: [{"category": "A", "value": 100}, {"category": "B", "value": 150}]'
                className={`w-full h-32 p-3 border rounded-lg font-mono text-sm resize-none ${jsonValid ? 'border-slate-300 focus:border-blue-500' : 'border-red-300 focus:border-red-500'
                  } focus:outline-none focus:ring-2 focus:ring-blue-500/20`}
              />
              {error && (
                <p className="text-red-600 text-sm mt-2">{error}</p>
              )}
            </div>

            <button
              onClick={analyzeData}
              disabled={loading || !jsonInput.trim() || !jsonValid}
              className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg hover:from-green-700 hover:to-emerald-700 transition-all duration-200 shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-5 h-5 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <BarChart3 className="w-5 h-5" />
                  Generate Charts
                </>
              )}
            </button>
          </div>
        </motion.div>
      )}

      {/* Generated Charts */}
      {analyzedCharts.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-2 mb-6">
            <BarChart3 className="w-6 h-6 text-blue-600" />
            Generated Visualizations
          </h2>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {analyzedCharts.map((chart, index) => (
              <AnalyzedChart key={index} chart={chart} />
            ))}
          </div>
        </motion.div>
      )}

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <>
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="mb-8"
          >
            <h3 className="text-3xl font-bold text-slate-900 mb-2">
              {reportData?.metadata?.company
                ? `${reportData.metadata.company} - Strategic Dashboard`
                : hasNewData || reportData
                  ? "Strategic Business Analysis Dashboard"
                  : "Tableau de Bord Stratégique"
              }
            </h3>
            <p className="text-slate-600">
              {reportData?.metadata?.sector && reportData?.metadata?.service
                ? `${reportData.metadata.sector} sector analysis for ${reportData.metadata.service} services`
                : hasNewData || reportData
                  ? "Real-time insights from your comprehensive business analysis"
                  : "Vue d'ensemble de vos opportunités de croissance"
              }
            </p>

            {/* Real Data Status Indicators */}
            {(reportData?.market_opportunities || reportData?.market_gaps || reportData?.strategic_recommendations) && (
              <div className="mt-4 space-y-3">
                <div className="flex flex-wrap gap-2">
                  {reportData.market_opportunities && (
                    <span className="px-3 py-1 bg-gradient-to-r from-blue-50 to-blue-100 text-blue-800 rounded-full text-sm font-medium border border-blue-200 flex items-center gap-1">
                      <TrendingUp className="w-3 h-3" />
                      {reportData.market_opportunities.length} Market Opportunities
                    </span>
                  )}
                  {reportData.market_gaps && (
                    <span className="px-3 py-1 bg-gradient-to-r from-orange-50 to-orange-100 text-orange-800 rounded-full text-sm font-medium border border-orange-200 flex items-center gap-1">
                      <Target className="w-3 h-3" />
                      {reportData.market_gaps.length} Market Gaps
                    </span>
                  )}
                  {reportData.strategic_recommendations && (
                    <span className="px-3 py-1 bg-gradient-to-r from-emerald-50 to-emerald-100 text-emerald-800 rounded-full text-sm font-medium border border-emerald-200 flex items-center gap-1">
                      <Target className="w-3 h-3" />
                      {reportData.strategic_recommendations.length} Strategic Recommendations
                    </span>
                  )}
                  {reportData.risk_assessment && (
                    <span className="px-3 py-1 bg-gradient-to-r from-red-50 to-red-100 text-red-800 rounded-full text-sm font-medium border border-red-200 flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" />
                      {reportData.risk_assessment.length} Risk Factors
                    </span>
                  )}
                  <span className="px-3 py-1 bg-gradient-to-r from-purple-50 to-purple-100 text-purple-800 rounded-full text-sm font-medium border border-purple-200 flex items-center gap-1">
                    <Database className="w-3 h-3" />
                    Live AI Analysis
                  </span>
                </div>

                {/* Analysis Summary */}
                {reportData.metadata?.analysis_timestamp && (
                  <div className="bg-gradient-to-r from-slate-50 to-slate-100 rounded-lg p-3 border border-slate-200">
                    <p className="text-xs text-slate-600 flex items-center gap-2">
                      <Clock className="w-3 h-3" />
                      Analysis completed: {new Date(reportData.metadata.analysis_timestamp).toLocaleString()}
                      {reportData.metadata.data_sources && (
                        <span className="ml-4 flex items-center gap-1">
                          <Database className="w-3 h-3" />
                          Sources: {reportData.metadata.data_sources.trends_analyzed || 0} trends, {reportData.metadata.data_sources.news_articles || 0} articles, {reportData.metadata.data_sources.competitor_pages || 0} competitors
                        </span>
                      )}
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Sample Data Indicator */}
            {!reportData?.market_opportunities && !hasNewData && (
              <div className="mt-4">
                <span className="px-3 py-1 bg-slate-100 text-slate-600 rounded-full text-sm font-medium inline-flex items-center gap-1">
                  <BarChart3 className="w-3 h-3" />
                  Demo Data - Submit your business form for real analysis
                </span>
              </div>
            )}
          </motion.div>

          {/* Enhanced KPI Cards with Real Data Insights */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {kpiData.map((kpi: ProcessedKpiData, index: number) => {
              const Icon = kpi.icon;
              const colorClasses = getColorClasses(kpi.color);
              const isRealData = reportData?.market_opportunities || reportData?.market_gaps;

              return (
                <motion.div
                  key={kpi.title}
                  initial={{ y: 20, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: index * 0.1 }}
                  className={`bg-white rounded-xl p-6 shadow-lg shadow-slate-200/50 border ${colorClasses
                    .split(" ")
                    .slice(2)
                    .join(" ")} hover:shadow-xl transition-all duration-300 ${isRealData ? 'ring-1 ring-blue-200' : ''}`}
                >
                  <div className="flex items-center justify-between mb-4">
                    <div
                      className={`w-12 h-12 rounded-lg bg-gradient-to-r ${colorClasses
                        .split(" ")
                        .slice(0, 2)
                        .join(" ")} flex items-center justify-center relative`}
                    >
                      <Icon className="w-6 h-6 text-white" />
                      {isRealData && (
                        <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full border-2 border-white"></div>
                      )}
                    </div>
                    <span
                      className={`text-sm font-medium px-2 py-1 rounded-full ${colorClasses
                        .split(" ")
                        .slice(2, 4)
                        .join(" ")}`}
                    >
                      {kpi.change}
                    </span>
                  </div>
                  <h3 className="text-2xl font-bold text-slate-900 mb-1">
                    {kpi.value}
                  </h3>
                  <p className="text-sm font-medium text-slate-900 mb-1">
                    {kpi.title}
                  </p>
                  <p className="text-xs text-slate-500">{kpi.description}</p>
                  {isRealData && (
                    <div className="mt-2 text-xs text-green-600 font-medium flex items-center gap-1">
                      <div className="w-1.5 h-1.5 bg-green-500 rounded-full"></div>
                      Based on AI analysis
                    </div>
                  )}
                </motion.div>
              );
            })}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
            {/* Enhanced Revenue Opportunities Chart */}
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.4 }}
              className={`bg-white rounded-xl p-6 shadow-lg shadow-slate-200/50 border border-slate-200 ${reportData?.market_opportunities ? 'ring-1 ring-blue-200' : ''}`}
            >
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-2">
                  <PieChart className="w-5 h-5 text-blue-600" />
                  <h3 className="text-lg font-semibold text-slate-900">
                    {reportData?.market_opportunities
                      ? "Market Opportunity Distribution"
                      : "Opportunités de Revenus"
                    }
                  </h3>
                </div>
                {reportData?.market_opportunities && (
                  <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium flex items-center gap-1">
                    <Database className="w-3 h-3" />
                    Real Data
                  </span>
                )}
              </div>
              <ResponsiveContainer width="100%" height={300}>
                <RechartsPieChart>
                  <RechartsPie data={revenueData} cx="50%" cy="50%" outerRadius={80} fill="#8884d8" dataKey="value">
                    {revenueData.map((entry: RevenueData, index: number) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </RechartsPie>
                  <Tooltip
                    formatter={(value: number) => [
                      `${(value / 1000).toFixed(0)}K€`,
                      "Potential",
                    ]}
                  />
                </RechartsPieChart>
              </ResponsiveContainer>
              <div className="grid grid-cols-2 gap-2 mt-4">
                {revenueData.map((item: RevenueData, index: number) => (
                  <div key={index} className="flex items-center space-x-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: item.fill }}
                    ></div>
                    <span className="text-sm text-slate-600 truncate" title={item.name}>
                      {item.name}
                    </span>
                  </div>
                ))}
              </div>
              {reportData?.market_opportunities && (
                <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <p className="text-xs text-blue-800">
                    Generated from {reportData.market_opportunities.length} identified market opportunities with potential revenue ranging from €{Math.min(...revenueData.map(r => r.value)).toLocaleString()} to €{Math.max(...revenueData.map(r => r.value)).toLocaleString()}
                  </p>
                </div>
              )}
            </motion.div>

            {/* Enhanced Profitability Projection */}
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.5 }}
              className={`bg-white rounded-xl p-6 shadow-lg shadow-slate-200/50 border border-slate-200 ${reportData?.trend_analysis?.emerging_trends ? 'ring-1 ring-emerald-200' : ''}`}
            >
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-2">
                  <BarChart3 className="w-5 h-5 text-emerald-600" />
                  <h3 className="text-lg font-semibold text-slate-900">
                    {reportData?.trend_analysis?.emerging_trends
                      ? "Growth Projection Based on Trends"
                      : "Projection de Profitabilité"
                    }
                  </h3>
                </div>
                {reportData?.trend_analysis?.emerging_trends && (
                  <span className="px-2 py-1 bg-emerald-100 text-emerald-800 rounded-full text-xs font-medium flex items-center gap-1">
                    <TrendingUp className="w-3 h-3" />
                    Trend-Based
                  </span>
                )}
              </div>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={profitabilityData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                  <XAxis dataKey="month" stroke="#64748B" />
                  <YAxis
                    stroke="#64748B"
                    tickFormatter={(value) => `${value / 1000}K`}
                  />
                  <Tooltip
                    formatter={(value: number) => [
                      `€${value.toLocaleString()}`,
                      "Profit",
                    ]}
                  />
                  <Bar
                    dataKey="profit"
                    fill="url(#profitGradient)"
                    radius={[4, 4, 0, 0]}
                  />
                  <defs>
                    <linearGradient id="profitGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10B981" stopOpacity={0.9} />
                      <stop offset="95%" stopColor="#10B981" stopOpacity={0.6} />
                    </linearGradient>
                  </defs>
                </BarChart>
              </ResponsiveContainer>
              {reportData?.trend_analysis?.emerging_trends && (
                <div className="mt-4 p-3 bg-emerald-50 rounded-lg border border-emerald-200">
                  <p className="text-xs text-emerald-800">
                    Projection based on {reportData.trend_analysis.emerging_trends.length} emerging trends: {reportData.trend_analysis.emerging_trends.slice(0, 2).join(', ')}{reportData.trend_analysis.emerging_trends.length > 2 ? '...' : ''}
                  </p>
                </div>
              )}
            </motion.div>
          </div>

          {/* Enhanced ROI Actions Table */}
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.6 }}
            className={`bg-white rounded-xl p-6 shadow-lg shadow-slate-200/50 border border-slate-200 ${reportData?.strategic_recommendations ? 'ring-1 ring-orange-200' : ''}`}
          >
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-2">
                <Target className="w-5 h-5 text-orange-600" />
                <h3 className="text-lg font-semibold text-slate-900">
                  {reportData?.strategic_recommendations
                    ? "Strategic Recommendations ROI Analysis"
                    : "ROI par Action Stratégique"
                  }
                </h3>
              </div>
              {reportData?.strategic_recommendations && (
                <span className="px-2 py-1 bg-orange-100 text-orange-800 rounded-full text-xs font-medium flex items-center gap-1">
                  <Target className="w-3 h-3" />
                  AI Recommended
                </span>
              )}
            </div>

            {reportData?.strategic_recommendations && (
              <div className="mb-4 p-3 bg-orange-50 rounded-lg border border-orange-200">
                <p className="text-xs text-orange-800">
                  These recommendations are generated from your comprehensive business analysis, prioritized by implementation complexity and expected impact.
                </p>
              </div>
            )}

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="text-left py-3 px-4 font-semibold text-slate-900">
                      Action
                    </th>
                    <th className="text-left py-3 px-4 font-semibold text-slate-900">
                      ROI
                    </th>
                    <th className="text-left py-3 px-4 font-semibold text-slate-900">
                      Complexity
                    </th>
                    <th className="text-left py-3 px-4 font-semibold text-slate-900">
                      Impact
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {roiActions.map((action: RoiAction, index: number) => (
                    <motion.tr
                      key={index}
                      initial={{ x: -20, opacity: 0 }}
                      animate={{ x: 0, opacity: 1 }}
                      transition={{ delay: 0.7 + index * 0.1 }}
                      className="border-b border-slate-100 hover:bg-slate-50 transition-colors duration-200"
                    >
                      <td className="py-4 px-4">
                        <div className="flex items-start gap-2">
                          <span className="font-medium text-slate-900">
                            {action.action}
                          </span>
                          {reportData?.strategic_recommendations && (
                            <span className="px-1.5 py-0.5 bg-green-100 text-green-700 rounded text-xs font-medium">
                              AI
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="py-4 px-4">
                        <span className="font-bold text-emerald-600">
                          {action.roi}%
                        </span>
                      </td>
                      <td className="py-4 px-4">
                        <span
                          className={`px-2 py-1 rounded-full text-xs font-medium ${action.complexity === "Faible"
                            ? "bg-green-100 text-green-700"
                            : action.complexity === "Moyen"
                              ? "bg-yellow-100 text-yellow-700"
                              : "bg-red-100 text-red-700"
                            }`}
                        >
                          {action.complexity}
                        </span>
                      </td>
                      <td className="py-4 px-4">
                        <span
                          className={`px-2 py-1 rounded-full text-xs font-medium ${action.impact === "Fort"
                            ? "bg-blue-100 text-blue-700"
                            : "bg-slate-100 text-slate-700"
                            }`}
                        >
                          {action.impact}
                        </span>
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>
        </>
      )}

      {/* Map Component Tab */}
      {activeTab === 'map' && (
        <MapComponent
          reportData={reportData || undefined}
          title="Regional Market Analysis"
          description="Explore market opportunities across different regions based on analysis"
          className="mb-8"
        />
      )}

      {/* Recommendations Component Tab */}
      {activeTab === 'recommendations' && (
        <RecommendationsComponent
          reportData={reportData || undefined}
          strategicRecommendations={reportData?.strategic_recommendations || sampleStrategicRecommendations}
          riskAssessment={reportData?.risk_assessment || sampleRiskAssessment}
          title="Strategic Action Plan"
          description="Prioritized recommendations and risk assessment based on analysis"
          className="mb-8"
        />
      )}

      {/* Report Component Tab */}
      {activeTab === 'report' && (
        <ReportComponent
          reportData={currentBackendData || sampleReportData}
          dataCharts={currentBackendData && 'data' in currentBackendData ? currentBackendData.data.data_charts : undefined}
          title="Comprehensive Business Analysis"
          description="Complete market analysis with AI-powered insights"
          showChat={true}
          className="mb-8"
        />
      )}
    </motion.div>
  );
};

export default DashboardPage;
