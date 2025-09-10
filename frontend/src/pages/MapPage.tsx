import React, { useState } from "react";
import { motion } from "framer-motion";
import {
  Map,
  TrendingUp,
  Users,
  Target,
  ChevronRight,
  MapPin,
} from "lucide-react";

const MapPage: React.FC = () => {
  const [selectedRegion, setSelectedRegion] = useState<string | null>(null);

  const regions = {
    "ile-de-france": {
      name: "Île-de-France",
      opportunity: "Very High",
      color: "#10B981",
      potential: "€1.2M",
      competition: "High",
      score: 92,
      population: "12.3M",
      businesses: "156K",
      recommendations: [
        "Focus on peripheral districts",
        "Partnerships with local incubators",
        "Increased presence at trade shows",
      ],
      keyMetrics: {
        marketSize: "€1.2M",
        competitors: 45,
        growthRate: "+18%",
        avgRevenue: "€85K",
      },
    },
    "rhone-alpes": {
      name: "Auvergne-Rhône-Alpes",
      opportunity: "High",
      color: "#3B82F6",
      potential: "€680K",
      competition: "Moderate",
      score: 85,
      population: "8.1M",
      businesses: "92K",
      recommendations: [
        "Target Lyon’s tech SMEs",
        "Expand towards Grenoble and Annecy",
        "Develop regional partner network",
      ],
      keyMetrics: {
        marketSize: "€680K",
        competitors: 28,
        growthRate: "+22%",
        avgRevenue: "€67K",
      },
    },
    paca: {
      name: "Provence-Alpes-Côte d'Azur",
      opportunity: "High",
      color: "#F59E0B",
      potential: "€520K",
      competition: "Moderate",
      score: 78,
      population: "5.1M",
      businesses: "68K",
      recommendations: [
        "Opportunities in the tourism sector",
        "Partnerships with Marseille businesses",
        "Develop specialized offerings in Nice-Cannes",
      ],
      keyMetrics: {
        marketSize: "€520K",
        competitors: 22,
        growthRate: "+15%",
        avgRevenue: "€58K",
      },
    },
    "nouvelle-aquitaine": {
      name: "Nouvelle-Aquitaine",
      opportunity: "Medium",
      color: "#8B5CF6",
      potential: "€390K",
      competition: "Low",
      score: 65,
      population: "6.0M",
      businesses: "54K",
      recommendations: [
        "Focus on Bordeaux and surroundings",
        "Develop services tailored to local SMEs",
        "Opportunities in agro-food sector",
      ],
      keyMetrics: {
        marketSize: "€390K",
        competitors: 15,
        growthRate: "+12%",
        avgRevenue: "€45K",
      },
    },
    "grand-est": {
      name: "Grand Est",
      opportunity: "Medium",
      color: "#EF4444",
      potential: "€280K",
      competition: "Low",
      score: 58,
      population: "5.5M",
      businesses: "48K",
      recommendations: [
        "Target industrial companies",
        "Stronger presence in Strasbourg",
        "Cross-border partnerships",
      ],
      keyMetrics: {
        marketSize: "€280K",
        competitors: 12,
        growthRate: "+8%",
        avgRevenue: "€38K",
      },
    },
  };

  const getOpportunityColor = (opportunity: string) => {
    switch (opportunity) {
      case "Very High":
        return "bg-emerald-100 text-emerald-800 border-emerald-200";
      case "High":
        return "bg-blue-100 text-blue-800 border-blue-200";
      case "Medium":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      default:
        return "bg-slate-100 text-slate-800 border-slate-200";
    }
  };

  const getCompetitionColor = (competition: string) => {
    switch (competition) {
      case "High":
        return "text-red-600";
      case "Moderate":
        return "text-yellow-600";
      case "Low":
        return "text-green-600";
      default:
        return "text-slate-600";
    }
  };

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
          Opportunity Mapping
        </h1>
        <p className="text-slate-600">
          Regional development potential analysis
        </p>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Interactive Map */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-xl p-6 shadow-lg shadow-slate-200/50 border border-slate-200"
        >
          <div className="flex items-center space-x-2 mb-6">
            <Map className="w-6 h-6 text-blue-600" />
            <h2 className="text-2xl font-bold text-slate-900">
              Interactive Map - France
            </h2>
          </div>

          {/* Simplified France Map */}
          <div className="relative bg-slate-50 rounded-lg p-8 h-96 flex items-center justify-center">
            <svg viewBox="0 0 400 400" className="w-full h-full max-w-80">
              {/* Île-de-France */}
              <circle
                cx="200"
                cy="150"
                r="20"
                fill={regions["ile-de-france"].color}
                className="cursor-pointer hover:opacity-80 transition-opacity duration-200"
                onClick={() => setSelectedRegion("ile-de-france")}
              />
              <text
                x="200"
                y="140"
                textAnchor="middle"
                className="text-xs font-medium fill-white"
              >
                IDF
              </text>

              {/* Rhône-Alpes */}
              <circle
                cx="280"
                cy="200"
                r="18"
                fill={regions["rhone-alpes"].color}
                className="cursor-pointer hover:opacity-80 transition-opacity duration-200"
                onClick={() => setSelectedRegion("rhone-alpes")}
              />
              <text
                x="280"
                y="205"
                textAnchor="middle"
                className="text-xs font-medium fill-white"
              >
                ARA
              </text>

              {/* PACA */}
              <circle
                cx="250"
                cy="280"
                r="16"
                fill={regions["paca"].color}
                className="cursor-pointer hover:opacity-80 transition-opacity duration-200"
                onClick={() => setSelectedRegion("paca")}
              />
              <text
                x="250"
                y="285"
                textAnchor="middle"
                className="text-xs font-medium fill-white"
              >
                PACA
              </text>

              {/* Nouvelle-Aquitaine */}
              <circle
                cx="120"
                cy="220"
                r="14"
                fill={regions["nouvelle-aquitaine"].color}
                className="cursor-pointer hover:opacity-80 transition-opacity duration-200"
                onClick={() => setSelectedRegion("nouvelle-aquitaine")}
              />
              <text
                x="120"
                y="225"
                textAnchor="middle"
                className="text-xs font-medium fill-white"
              >
                NA
              </text>

              {/* Grand Est */}
              <circle
                cx="320"
                cy="140"
                r="12"
                fill={regions["grand-est"].color}
                className="cursor-pointer hover:opacity-80 transition-opacity duration-200"
                onClick={() => setSelectedRegion("grand-est")}
              />
              <text
                x="320"
                y="145"
                textAnchor="middle"
                className="text-xs font-medium fill-white"
              >
                GE
              </text>
            </svg>

            <div className="absolute bottom-4 left-4 text-xs text-slate-500">
              Click a region for more details
            </div>
          </div>

          {/* Legend */}
          <div className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-emerald-500 rounded-full"></div>
              <span className="text-sm text-slate-700">Very High</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-blue-500 rounded-full"></div>
              <span className="text-sm text-slate-700">High</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-yellow-500 rounded-full"></div>
              <span className="text-sm text-slate-700">Medium</span>
            </div>
          </div>
        </motion.div>

        {/* Region Details */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="space-y-6"
        >
          {selectedRegion ? (
            <div className="bg-white rounded-xl p-6 shadow-lg shadow-slate-200/50 border border-slate-200">
              <div className="flex items-center space-x-3 mb-6">
                <MapPin className="w-6 h-6 text-blue-600" />
                <h3 className="text-2xl font-bold text-slate-900">
                  {regions[selectedRegion as keyof typeof regions].name}
                </h3>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="bg-slate-50 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-slate-700 mb-1">
                    Regional Potential
                  </h4>
                  <p className="text-2xl font-bold text-slate-900">
                    {regions[selectedRegion as keyof typeof regions].potential}
                  </p>
                </div>
                <div className="bg-slate-50 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-slate-700 mb-1">
                    Opportunity Score
                  </h4>
                  <p className="text-2xl font-bold text-slate-900">
                    {regions[selectedRegion as keyof typeof regions].score}/100
                  </p>
                </div>
                <div className="bg-slate-50 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-slate-700 mb-1">
                    Population
                  </h4>
                  <p className="text-lg font-semibold text-slate-900">
                    {regions[selectedRegion as keyof typeof regions].population}
                  </p>
                </div>
                <div className="bg-slate-50 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-slate-700 mb-1">
                    Businesses
                  </h4>
                  <p className="text-lg font-semibold text-slate-900">
                    {regions[selectedRegion as keyof typeof regions].businesses}
                  </p>
                </div>
              </div>

              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium text-slate-700">
                    Opportunity Level:
                  </span>
                  <span
                    className={`px-2 py-1 rounded-full text-xs font-medium border ${getOpportunityColor(
                      regions[selectedRegion as keyof typeof regions]
                        .opportunity
                    )}`}
                  >
                    {
                      regions[selectedRegion as keyof typeof regions]
                        .opportunity
                    }
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium text-slate-700">
                    Competition:
                  </span>
                  <span
                    className={`text-sm font-semibold ${getCompetitionColor(
                      regions[selectedRegion as keyof typeof regions]
                        .competition
                    )}`}
                  >
                    {
                      regions[selectedRegion as keyof typeof regions]
                        .competition
                    }
                  </span>
                </div>
              </div>

              <div className="mb-6">
                <h4 className="text-lg font-semibold text-slate-900 mb-3 flex items-center">
                  <Target className="w-5 h-5 text-blue-600 mr-2" />
                  Key Metrics
                </h4>
                <div className="grid grid-cols-2 gap-4">
                  {Object.entries(
                    regions[selectedRegion as keyof typeof regions].keyMetrics
                  ).map(([key, value]) => (
                    <div key={key} className="flex justify-between">
                      <span className="text-sm text-slate-600 capitalize">
                        {key === "marketSize"
                          ? "Market Size"
                          : key === "competitors"
                          ? "Competitors"
                          : key === "growthRate"
                          ? "Growth"
                          : "Avg Revenue"}
                        :
                      </span>
                      <span className="text-sm font-semibold text-slate-900">
                        {value}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="text-lg font-semibold text-slate-900 mb-3 flex items-center">
                  <TrendingUp className="w-5 h-5 text-emerald-600 mr-2" />
                  Recommendations
                </h4>
                <ul className="space-y-2">
                  {regions[
                    selectedRegion as keyof typeof regions
                  ].recommendations.map((rec, index) => (
                    <li
                      key={index}
                      className="flex items-start space-x-2 text-sm text-slate-700"
                    >
                      <ChevronRight className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-xl p-12 shadow-lg shadow-slate-200/50 border border-slate-200 text-center">
              <Map className="w-16 h-16 text-slate-400 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-slate-900 mb-2">
                Select a Region
              </h3>
              <p className="text-slate-600">
                Click a region on the map to view details and recommendations
              </p>
            </div>
          )}

          {/* Regional Rankings */}
          <div className="bg-white rounded-xl p-6 shadow-lg shadow-slate-200/50 border border-slate-200">
            <h3 className="text-xl font-bold text-slate-900 mb-4 flex items-center">
              <Users className="w-5 h-5 text-blue-600 mr-2" />
              Regional Ranking
            </h3>
            <div className="space-y-3">
              {Object.entries(regions)
                .sort((a, b) => b[1].score - a[1].score)
                .map(([key, region], index) => (
                  <div
                    key={key}
                    className={`flex items-center justify-between p-3 rounded-lg cursor-pointer transition-all duration-200 ${
                      selectedRegion === key
                        ? "bg-blue-50 border border-blue-200"
                        : "bg-slate-50 hover:bg-slate-100"
                    }`}
                    onClick={() => setSelectedRegion(key)}
                  >
                    <div className="flex items-center space-x-3">
                      <span className="text-lg font-bold text-slate-500">
                        #{index + 1}
                      </span>
                      <div
                        className="w-4 h-4 rounded-full"
                        style={{ backgroundColor: region.color }}
                      ></div>
                      <span className="font-medium text-slate-900">
                        {region.name}
                      </span>
                    </div>
                    <div className="flex items-center space-x-4">
                      <span className="text-sm font-semibold text-slate-900">
                        {region.potential}
                      </span>
                      <span className="text-sm text-slate-600">
                        {region.score}/100
                      </span>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
};

export default MapPage;
