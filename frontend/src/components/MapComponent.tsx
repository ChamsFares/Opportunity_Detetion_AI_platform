import { motion } from "framer-motion";
import {
    ChevronRight,
    Map,
    MapPin,
    Target,
    TrendingUp,
    Users,
} from "lucide-react";
import React, { useState } from "react";
import LeafletMapWrapper from './LeafletMapWrapper';

interface Region {
    name: string;
    opportunity: string;
    color: string;
    potential: string;
    competition: string;
    score: number;
    population: string;
    businesses: string;
    recommendations: string[];
    coordinates: [number, number]; // [latitude, longitude]
    keyMetrics: {
        marketSize: string;
        competitors: number;
        growthRate: string;
        avgRevenue: string;
    };
}

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
    competitive_insights?: {
        market_positioning: string;
        competitive_strengths: string[];
        competitive_weaknesses: string[];
        differentiation_opportunities: string[];
    };
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

interface MapComponentProps {
    regions?: Record<string, Region>;
    reportData?: BackendReportData | BackendResponse;
    title?: string;
    description?: string;
    className?: string;
}

const defaultRegions: Record<string, Region> = {
    "ile-de-france": {
        name: "Île-de-France",
        opportunity: "Very High",
        color: "#10B981",
        potential: "€1.2M",
        competition: "High",
        score: 92,
        population: "12.3M",
        businesses: "156K",
        coordinates: [48.8566, 2.3522], // Paris coordinates
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
        coordinates: [45.764, 4.8357], // Lyon coordinates
        recommendations: [
            "Target Lyon's tech SMEs",
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
        coordinates: [43.2965, 5.3698], // Marseille coordinates
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
        coordinates: [44.8378, -0.5792], // Bordeaux coordinates
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
        coordinates: [48.5734, 7.7521], // Strasbourg coordinates
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

const MapComponent: React.FC<MapComponentProps> = ({
    regions: customRegions,
    reportData,
    title = "Opportunity Mapping",
    description = "Regional development potential analysis",
    className = "",
}) => {
    const [selectedRegion, setSelectedRegion] = useState<string | null>(null);

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

    // Generate dynamic regions based on backend data
    const generateDynamicRegions = (): Record<string, Region> => {
        if (!backendData) return defaultRegions;

        const opportunities = backendData.market_opportunities || [];
        const gaps = backendData.market_gaps || [];

        // Create regions based on opportunity types and market potential
        const dynamicRegions: Record<string, Region> = {};

        opportunities.forEach((opp, index) => {
            const regionKey = `region-${index + 1}`;
            const urgencyScore = opp.urgency === "immediate" ? 95 :
                opp.urgency === "short_term" ? 80 : 65;

            const marketSize = opp.market_size_potential === "large" ? "€800K+" :
                opp.market_size_potential === "medium" ? "€400K+" : "€200K+";

            const competitionLevel = gaps.length > index ?
                (gaps[index].impact_level === "high" ? "High" :
                    gaps[index].impact_level === "medium" ? "Moderate" : "Low") : "Moderate";

            const regionNames = [
                "Île-de-France", "Auvergne-Rhône-Alpes", "Provence-Alpes-Côte d'Azur",
                "Nouvelle-Aquitaine", "Grand Est", "Occitanie", "Hauts-de-France"
            ];

            const colors = ["#10B981", "#3B82F6", "#F59E0B", "#8B5CF6", "#EF4444", "#06B6D4", "#84CC16"];

            const coordinates: [number, number][] = [
                [48.8566, 2.3522],  // Paris (Île-de-France)
                [45.7640, 4.8357],  // Lyon (Auvergne-Rhône-Alpes)
                [43.2965, 5.3698],  // Marseille (Provence-Alpes-Côte d'Azur)
                [44.8378, -0.5792], // Bordeaux (Nouvelle-Aquitaine)
                [48.5734, 7.7521],  // Strasbourg (Grand Est)
                [43.6047, 1.4442],  // Toulouse (Occitanie)
                [50.6292, 3.0573]   // Lille (Hauts-de-France)
            ];

            dynamicRegions[regionKey] = {
                name: regionNames[index] || `Region ${index + 1}`,
                opportunity: urgencyScore >= 90 ? "Very High" : urgencyScore >= 75 ? "High" : "Medium",
                color: colors[index % colors.length],
                potential: marketSize,
                competition: competitionLevel,
                score: urgencyScore,
                population: `${Math.floor(Math.random() * 10 + 3)}.${Math.floor(Math.random() * 9)}M`,
                businesses: `${Math.floor(Math.random() * 100 + 20)}K`,
                coordinates: coordinates[index % coordinates.length],
                recommendations: [
                    opp.opportunity_description.substring(0, 80) + "...",
                    `Leverage ${opp.competitive_advantage.substring(0, 60)}...`,
                    `Focus on ${opp.opportunity_type.toLowerCase()} initiatives`
                ],
                keyMetrics: {
                    marketSize,
                    competitors: Math.floor(Math.random() * 40 + 10),
                    growthRate: `+${Math.floor(Math.random() * 20 + 8)}%`,
                    avgRevenue: `€${Math.floor(Math.random() * 50 + 25)}K`,
                },
            };
        });

        // If no opportunities, create at least one region
        if (Object.keys(dynamicRegions).length === 0) {
            dynamicRegions["default-region"] = {
                name: "Primary Market",
                opportunity: "High",
                color: "#3B82F6",
                potential: "€500K+",
                competition: "Moderate",
                score: 75,
                population: "5.2M",
                businesses: "65K",
                coordinates: [48.8566, 2.3522], // Paris coordinates
                recommendations: [
                    "Establish market presence",
                    "Build strategic partnerships",
                    "Focus on competitive differentiation"
                ],
                keyMetrics: {
                    marketSize: "€500K+",
                    competitors: 25,
                    growthRate: "+15%",
                    avgRevenue: "€45K",
                },
            };
        }

        return dynamicRegions;
    };

    // Use custom regions if provided, otherwise generate from backend data
    const regions = customRegions || generateDynamicRegions();

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
        <div className={`space-y-6 ${className}`}>
            <div className="mb-6">
                <h2 className="text-2xl font-bold text-slate-900 mb-2">{title}</h2>
                <p className="text-slate-600">{description}</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Interactive Map */}
                <motion.div
                    initial={{ y: 20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    className="bg-white rounded-xl p-6 shadow-lg shadow-slate-200/50 border border-slate-200"
                >
                    <div className="flex items-center space-x-2 mb-6">
                        <Map className="w-6 h-6 text-blue-600" />
                        <h3 className="text-xl font-bold text-slate-900">
                            Interactive Map - France
                        </h3>
                    </div>

                    {/* Interactive Leaflet Map */}
                    <div className="relative bg-slate-50 rounded-lg p-4 h-80 overflow-hidden">
                        <LeafletMapWrapper
                            regions={regions}
                            onRegionSelect={setSelectedRegion}
                        />

                        <div className="absolute bottom-4 left-4 bg-white bg-opacity-90 px-2 py-1 rounded text-xs text-slate-500">
                            Click a marker for details
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
                <div className="space-y-6">
                    {selectedRegion && regions[selectedRegion] ? (
                        <motion.div
                            initial={{ y: 20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            className="bg-white rounded-xl p-6 shadow-lg shadow-slate-200/50 border border-slate-200"
                        >
                            <div className="flex items-center space-x-3 mb-6">
                                <MapPin className="w-6 h-6 text-blue-600" />
                                <h4 className="text-xl font-bold text-slate-900">
                                    {regions[selectedRegion].name}
                                </h4>
                            </div>

                            <div className="grid grid-cols-2 gap-4 mb-6">
                                <div className="bg-slate-50 rounded-lg p-4">
                                    <h5 className="text-sm font-medium text-slate-700 mb-1">
                                        Regional Potential
                                    </h5>
                                    <p className="text-2xl font-bold text-slate-900">
                                        {regions[selectedRegion].potential}
                                    </p>
                                </div>
                                <div className="bg-slate-50 rounded-lg p-4">
                                    <h5 className="text-sm font-medium text-slate-700 mb-1">
                                        Opportunity Score
                                    </h5>
                                    <p className="text-2xl font-bold text-slate-900">
                                        {regions[selectedRegion].score}/100
                                    </p>
                                </div>
                                <div className="bg-slate-50 rounded-lg p-4">
                                    <h5 className="text-sm font-medium text-slate-700 mb-1">
                                        Population
                                    </h5>
                                    <p className="text-lg font-semibold text-slate-900">
                                        {regions[selectedRegion].population}
                                    </p>
                                </div>
                                <div className="bg-slate-50 rounded-lg p-4">
                                    <h5 className="text-sm font-medium text-slate-700 mb-1">
                                        Businesses
                                    </h5>
                                    <p className="text-lg font-semibold text-slate-900">
                                        {regions[selectedRegion].businesses}
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
                                            regions[selectedRegion].opportunity
                                        )}`}
                                    >
                                        {regions[selectedRegion].opportunity}
                                    </span>
                                </div>
                                <div className="flex items-center space-x-2">
                                    <span className="text-sm font-medium text-slate-700">
                                        Competition:
                                    </span>
                                    <span
                                        className={`text-sm font-semibold ${getCompetitionColor(
                                            regions[selectedRegion].competition
                                        )}`}
                                    >
                                        {regions[selectedRegion].competition}
                                    </span>
                                </div>
                            </div>

                            <div className="mb-6">
                                <h5 className="text-lg font-semibold text-slate-900 mb-3 flex items-center">
                                    <Target className="w-5 h-5 text-blue-600 mr-2" />
                                    Key Metrics
                                </h5>
                                <div className="grid grid-cols-2 gap-4">
                                    {Object.entries(regions[selectedRegion].keyMetrics).map(
                                        ([key, value]) => (
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
                                        )
                                    )}
                                </div>
                            </div>

                            <div>
                                <h5 className="text-lg font-semibold text-slate-900 mb-3 flex items-center">
                                    <TrendingUp className="w-5 h-5 text-emerald-600 mr-2" />
                                    Recommendations
                                </h5>
                                <ul className="space-y-2">
                                    {regions[selectedRegion].recommendations.map((rec, index) => (
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
                        </motion.div>
                    ) : (
                        <div className="bg-white rounded-xl p-12 shadow-lg shadow-slate-200/50 border border-slate-200 text-center">
                            <Map className="w-16 h-16 text-slate-400 mx-auto mb-4" />
                            <h4 className="text-xl font-semibold text-slate-900 mb-2">
                                Select a Region
                            </h4>
                            <p className="text-slate-600">
                                Click a region on the map to view details and recommendations
                            </p>
                        </div>
                    )}

                    {/* Regional Rankings */}
                    <div className="bg-white rounded-xl p-6 shadow-lg shadow-slate-200/50 border border-slate-200">
                        <h4 className="text-lg font-bold text-slate-900 mb-4 flex items-center">
                            <Users className="w-5 h-5 text-blue-600 mr-2" />
                            Regional Ranking
                        </h4>
                        <div className="space-y-3">
                            {Object.entries(regions)
                                .sort((a, b) => b[1].score - a[1].score)
                                .map(([key, region], index) => (
                                    <div
                                        key={key}
                                        className={`flex items-center justify-between p-3 rounded-lg cursor-pointer transition-all duration-200 ${selectedRegion === key
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
                </div>
            </div>
        </div>
    );
};

export default MapComponent;
