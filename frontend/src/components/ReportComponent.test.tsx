import { render, screen } from '@testing-library/react';
import ReportComponent from './ReportComponent';

// Sample backend response data
const sampleBackendResponse = {
    "status": "success",
    "message": "🎉 Comprehensive market analysis for Talan completed successfully!",
    "data": {
        "report_data": {
            "risk_assessment": [
                {
                    "risk_description": "The AI landscape evolves extremely rapidly, with new models, frameworks, and tools emerging constantly. There's a risk that current expertise could quickly become outdated.",
                    "risk_type": "Technological",
                    "mitigation_strategy": "Implement a robust continuous learning program for all consultants, allocate dedicated R&D time for exploring new AI advancements, and foster partnerships with leading AI research institutions.",
                    "probability": "high"
                }
            ],
            "trend_analysis": {
                "trend_based_opportunities": [
                    "Offering specialized workshops on Generative AI deployment for enterprises",
                    "Developing consulting packages focused on AI ethics and compliance audits"
                ],
                "trend_implications": [
                    "Need for consultants to guide businesses on responsible and ethical AI adoption",
                    "Demand for integration strategies for Generative AI into existing workflows"
                ],
                "emerging_trends": [
                    "Proliferation of Generative AI models (e.g., LLMs, image generation models)",
                    "Increasing emphasis on Responsible AI, ethics, and bias mitigation"
                ]
            },
            "market_opportunities": [
                {
                    "market_size_potential": "large",
                    "opportunity_type": "Regulatory & Ethical Compliance",
                    "urgency": "immediate",
                    "competitive_advantage": "Ability to combine technical AI knowledge with legal and ethical frameworks.",
                    "opportunity_description": "Growing concerns and emerging regulations around AI ethics, fairness, transparency, and accountability create a significant demand for specialized consulting services to ensure responsible AI development and deployment."
                }
            ],
            "strategic_recommendations": [
                {
                    "implementation_complexity": "medium",
                    "priority": "high",
                    "expected_impact": "Enhance brand recognition, attract inbound leads, and establish the company as an authority, mitigating the \"Unknown Company\" weakness.",
                    "recommendation": "Develop a strong thought leadership presence in a specific AI niche (e.g., Generative AI ethics or AI for X industry) through webinars, whitepapers, and industry events."
                }
            ],
            "market_gaps": [
                {
                    "gap_description": "Many Small and Medium-sized Enterprises (SMEs) struggle with the practical implementation of AI solutions, lacking internal expertise and clear roadmaps for integration and ROI measurement.",
                    "gap_category": "Implementation & Adoption",
                    "impact_level": "high",
                    "evidence": "General market observations and common challenges faced by businesses attempting AI adoption without dedicated in-house teams."
                }
            ],
            "competitive_insights": {
                "market_positioning": "Positioned as a specialized, high-expertise AI consulting boutique focusing on practical implementation and emerging AI domains.",
                "competitive_weaknesses": [
                    "Limited brand recognition as an \"Unknown Company\"",
                    "Potentially smaller client base compared to established players"
                ],
                "competitive_strengths": [
                    "Deep technical expertise in AI/ML",
                    "Agile and customizable consulting approach",
                    "Client-centric solution development"
                ],
                "differentiation_opportunities": [
                    "Specialization in niche industry verticals (e.g., AI in healthcare compliance, AI for sustainable energy)",
                    "Developing proprietary AI diagnostic tools for business readiness"
                ]
            },
            "metadata": {
                "analysis_timestamp": "2025-08-10T11:04:46.131661",
                "company": "Talan",
                "sector": "AI",
                "service": "Consulting",
                "data_sources": {
                    "trends_analyzed": 5,
                    "news_articles": 12,
                    "competitor_pages": 8
                },
                "analysis_successful": true
            }
        }
    }
};

describe('ReportComponent', () => {
    it('renders with backend response data', () => {
        render(<ReportComponent reportData={sampleBackendResponse} />);

        // Check if the component renders basic elements
        expect(screen.getByText('Comprehensive Report')).toBeInTheDocument();
        expect(screen.getByText('Show All')).toBeInTheDocument();
        expect(screen.getByText('Opportunities')).toBeInTheDocument();
        expect(screen.getByText('Risks')).toBeInTheDocument();
    });

    it('displays market opportunities', () => {
        render(<ReportComponent reportData={sampleBackendResponse} />);

        expect(screen.getByText('Market Opportunities')).toBeInTheDocument();
        expect(screen.getByText('Regulatory & Ethical Compliance')).toBeInTheDocument();
    });

    it('displays risk assessment', () => {
        render(<ReportComponent reportData={sampleBackendResponse} />);

        expect(screen.getByText('Risk Assessment')).toBeInTheDocument();
        expect(screen.getByText('Technological')).toBeInTheDocument();
    });

    it('displays metadata', () => {
        render(<ReportComponent reportData={sampleBackendResponse} />);

        expect(screen.getByText('Analysis Details')).toBeInTheDocument();
        expect(screen.getByText('Talan')).toBeInTheDocument();
    });

    it('handles empty data gracefully', () => {
        render(<ReportComponent reportData={null} />);

        expect(screen.getByText('No Report Data Available')).toBeInTheDocument();
        expect(screen.getByText('Generate a report to view detailed analysis here.')).toBeInTheDocument();
    });
});
