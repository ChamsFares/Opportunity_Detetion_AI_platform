import json
import os
import warnings
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
from agents.ollama_api import OllamaQwen3Client

warnings.filterwarnings("ignore")


class MarketAnalysisAI:
    def __init__(self):
        self.client = OllamaQwen3Client()

    def analyze_market_gaps_opportunities(
        self, market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Comprehensive AI-powered market analysis to identify gaps and opportunities"""

        # Prepare comprehensive prompt
        prompt = self._create_analysis_prompt(market_data)

        try:
            schema = {
                "name": "analyze_market_data",
                "description": "Analyze market data and provide structured insights",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "market_gaps": {
                            "type": "array",
                            "description": "Identified market gaps and unmet needs",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "gap_category": {"type": "string"},
                                    "gap_description": {"type": "string"},
                                    "impact_level": {
                                        "type": "string",
                                        "enum": ["high", "medium", "low"],
                                    },
                                    "evidence": {"type": "string"},
                                },
                                "required": [
                                    "gap_category",
                                    "gap_description",
                                    "impact_level",
                                ],
                            },
                        },
                        "market_opportunities": {
                            "type": "array",
                            "description": "Identified market opportunities",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "opportunity_type": {"type": "string"},
                                    "opportunity_description": {"type": "string"},
                                    "market_size_potential": {
                                        "type": "string",
                                        "enum": ["large", "medium", "small", "unknown"],
                                    },
                                    "urgency": {
                                        "type": "string",
                                        "enum": [
                                            "immediate",
                                            "short_term",
                                            "medium_term",
                                            "long_term",
                                        ],
                                    },
                                    "competitive_advantage": {"type": "string"},
                                },
                                "required": [
                                    "opportunity_type",
                                    "opportunity_description",
                                    "market_size_potential",
                                    "urgency",
                                ],
                            },
                        },
                        "competitive_insights": {
                            "type": "object",
                            "properties": {
                                "competitive_strengths": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "competitive_weaknesses": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "market_positioning": {"type": "string"},
                                "differentiation_opportunities": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                            },
                        },
                        "trend_analysis": {
                            "type": "object",
                            "properties": {
                                "emerging_trends": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "trend_implications": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "trend_based_opportunities": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                            },
                        },
                        "strategic_recommendations": {
                            "type": "array",
                            "description": "Strategic recommendations based on analysis",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "recommendation": {"type": "string"},
                                    "priority": {
                                        "type": "string",
                                        "enum": ["high", "medium", "low"],
                                    },
                                    "implementation_complexity": {
                                        "type": "string",
                                        "enum": ["low", "medium", "high"],
                                    },
                                    "expected_impact": {"type": "string"},
                                },
                                "required": [
                                    "recommendation",
                                    "priority",
                                    "implementation_complexity",
                                ],
                            },
                        },
                        "risk_assessment": {
                            "type": "array",
                            "description": "Identified risks and mitigation strategies",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "risk_type": {"type": "string"},
                                    "risk_description": {"type": "string"},
                                    "probability": {
                                        "type": "string",
                                        "enum": ["high", "medium", "low"],
                                    },
                                    "mitigation_strategy": {"type": "string"},
                                },
                                "required": [
                                    "risk_type",
                                    "risk_description",
                                    "probability",
                                ],
                            },
                        },
                    },
                    "required": [
                        "market_gaps",
                        "market_opportunities",
                        "competitive_insights",
                        "trend_analysis",
                        "strategic_recommendations",
                    ],
                },
            }

            # Generate content with Ollama
            response = self.client.generate(prompt)

            # Parse the JSON response from Ollama
            try:
                # Try to parse as JSON directly
                analysis_result = json.loads(response)
            except json.JSONDecodeError:
                # If not valid JSON, try to extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    try:
                        analysis_result = json.loads(json_match.group())
                    except json.JSONDecodeError:
                        analysis_result = None
                else:
                    analysis_result = None

            if analysis_result:

                    # Add metadata
                    analysis_result["metadata"] = {
                        "analysis_timestamp": datetime.now().isoformat(),
                        "company": market_data.get("company", ""),
                        "sector": market_data.get("sector", ""),
                        "service": market_data.get("service", ""),
                        "data_sources": {
                            "trends_analyzed": len(market_data.get("trends", [])),
                            "news_articles": sum(
                                len(articles)
                                for articles in market_data.get("news", {}).values()
                            ),
                            "competitor_pages": len(
                                market_data.get("competitors", {}).get(
                                    "relevant_pages", []
                                )
                            ),
                        },
                        "analysis_successful": True,
                    }
                    return analysis_result
            else:
                return self._create_fallback_analysis(
                    market_data, "Could not parse JSON from response"
                )

        except Exception as e:
            print(f"Error during analysis: {str(e)}")
            return self._create_fallback_analysis(market_data, str(e))

    def _create_analysis_prompt(self, market_data: Dict[str, Any]) -> str:
        """Create comprehensive analysis prompt"""

        company = market_data.get("Company", "Unknown Company")
        sector = market_data.get("Sector", "Unknown Sector")
        service = market_data.get("Service", "Unknown Service")

        # Process trends data
        trends_summary = self._summarize_trends(market_data.get("trends", []))

        # Process news data
        news_summary = self._summarize_news(market_data.get("news", {}))

        # Process competitor data
        competitor_summary = self._summarize_competitors(
            market_data.get("competitors", {})
        )

        prompt = f"""
You are a senior market analyst and strategy consultant. Analyze the following comprehensive market intelligence data to identify gaps, opportunities, and strategic insights for {company} in the {sector} sector, specifically for their {service} service.

## COMPANY PROFILE
- **Company:** {company}
- **Sector:** {sector}
- **Service:** {service}

## MARKET TRENDS ANALYSIS
{trends_summary}

## NEWS & MARKET INTELLIGENCE
{news_summary}

## COMPETITIVE LANDSCAPE
{competitor_summary}

## ANALYSIS REQUIREMENTS

Please provide a comprehensive analysis in JSON format covering:

1. **market_gaps**: Array of market gaps with gap_category, gap_description, impact_level, and evidence
2. **market_opportunities**: Array of opportunities with opportunity_type, opportunity_description, market_size_potential, urgency, and competitive_advantage
3. **competitive_insights**: Object with competitive_strengths, competitive_weaknesses, market_positioning, and differentiation_opportunities
4. **trend_analysis**: Object with emerging_trends, trend_implications, and trend_based_opportunities
5. **strategic_recommendations**: Array of recommendations with recommendation, priority, implementation_complexity, and expected_impact
6. **risk_assessment**: Array of risks with risk_type, risk_description, probability, and mitigation_strategy

Focus on actionable insights that can inform strategic decision-making.
        """

        return prompt

    def _summarize_trends(self, trends: List[Dict[str, Any]]) -> str:
        """Summarize trends data for analysis"""
        if not trends:
            return "No trend data available."

        summary = "### Market Trends Overview\n"
        print(trends)
        for trend in trends:
            print(trend)
            hashtag = trend.get("hashtag", "Unknown")
            topics = trend.get("topics", [])

            summary += f"**{hashtag}:**\n"
            for topic in topics[:3]:
                topic_text = (
                    topic.get("topic", "")[:200] + "..."
                    if len(topic.get("topic", "")) > 200
                    else topic.get("topic", "")
                )
                summary += f"- {topic_text}\n"
            summary += "\n"

        return summary

    def _summarize_news(self, news: Dict[str, List[Dict[str, Any]]]) -> str:
        """Summarize news data for analysis"""
        if not news:
            return "No news data available."

        summary = "### Recent News & Market Intelligence\n"
        total_articles = sum(len(articles) for articles in news.values())
        summary += f"**Total Articles Analyzed:** {total_articles}\n\n"

        for source, articles in news.items():
            summary += f"**{source} ({len(articles)} articles):**\n"
            for article in articles[:3]:
                title = (
                    article.get("title", "No title")[:100] + "..."
                    if len(article.get("title", "")) > 100
                    else article.get("title", "")
                )
                description = (
                    article.get("description", "")[:150] + "..."
                    if len(article.get("description", "")) > 150
                    else article.get("description", "")
                )
                summary += f"- {title}\n  {description}\n"
            summary += "\n"

        return summary

    def _summarize_competitors(self, competitors: Dict[str, Any]) -> str:
        """Summarize competitor data for analysis (adapted for content/insight competitor pages)"""
        if not competitors or not competitors.get("relevant_pages"):
            return "No competitor data available."

        relevant_pages = competitors.get("relevant_pages", [])
        summary = f"### Competitive Intelligence\n"
        summary += (
            f"**Relevant Competitor Content Analyzed:** {len(relevant_pages)}\n\n"
        )

        # Adapted collections for content-focused competitors
        all_products_services = set()
        all_target_markets = set()
        value_props = []
        key_features = []

        for page in relevant_pages:
            ci = page.get("competitive_intelligence", {})

            # Collect products/services (content offerings)
            products = ci.get("products_services", [])
            all_products_services.update(products)

            # Collect target markets
            target_market = ci.get("target_market", "")
            if target_market:
                all_target_markets.add(target_market)

            # Collect value propositions
            value_prop = ci.get("unique_value_proposition", "")
            if value_prop:
                value_props.append(value_prop)

            # Collect key features (capabilities/technologies)
            features = ci.get("key_features", [])
            key_features.extend(features)

        summary += f"**Content/Service Offerings:** {len(all_products_services)}\n"
        for item in list(all_products_services)[:5]:
            summary += f"- {item}\n"

        if all_target_markets:
            summary += f"\n**Target Markets:**\n"
            for market in list(all_target_markets)[:3]:
                summary += f"- {market}\n"

        if key_features:
            summary += f"\n**Key Capabilities/Technologies:**\n"
            for feature in list(set(key_features))[:5]:
                summary += f"- {feature}\n"

        if value_props:
            summary += f"\n**Value Propositions:**\n"
            for vp in value_props[:3]:
                summary += f"- {vp}\n"

        return summary

    def _create_fallback_analysis(
        self, market_data: Dict[str, Any], error: str
    ) -> Dict[str, Any]:
        """Create fallback analysis when AI analysis fails"""
        return {
            "market_gaps": [],
            "market_opportunities": [],
            "competitive_insights": {},
            "trend_analysis": {},
            "strategic_recommendations": [],
            "risk_assessment": [],
            "error": error,
            "metadata": {
                "analysis_timestamp": datetime.now().isoformat(),
                "company": market_data.get("company", ""),
                "sector": market_data.get("sector", ""),
                "service": market_data.get("service", ""),
                "analysis_successful": False,
            },
        }

    def generate_strategic_report(self, analysis_result: Dict[str, Any]) -> str:
        """Generate comprehensive strategic report"""

        if analysis_result.get("error"):
            return f"# Analysis Error Report\n\n**Error:** {analysis_result['error']}\n\nPlease check your API key and try again."

        metadata = analysis_result.get("metadata", {})
        company = metadata.get("company", "Unknown")
        sector = metadata.get("sector", "Unknown")
        service = metadata.get("service", "Unknown")

        report = f"""# Strategic Market Analysis Report
**Company:** {company}  
**Sector:** {sector}  
**Service:** {service}  
**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Executive Summary
This comprehensive market analysis identifies key gaps and opportunities in the {sector} sector for {service} services.

**Data Sources:**
- Trends Analyzed: {metadata.get('data_sources', {}).get('trends_analyzed', 0)}
- News Articles: {metadata.get('data_sources', {}).get('news_articles', 0)}
- Competitor Pages: {metadata.get('data_sources', {}).get('competitor_pages', 0)}
"""

        # Rest of the report generation remains the same...
        # [Include the complete report generation code here]

        return report

    def create_opportunity_matrix(
        self, analysis_result: Dict[str, Any]
    ) -> pd.DataFrame:
        """Create opportunity prioritization matrix"""

        opportunities = analysis_result.get("market_opportunities", [])
        if not opportunities:
            return pd.DataFrame()

        matrix_data = []
        for opp in opportunities:
            market_size_score = {"large": 3, "medium": 2, "small": 1, "unknown": 1}.get(
                opp.get("market_size_potential", "unknown"), 1
            )

            urgency_score = {
                "immediate": 4,
                "short_term": 3,
                "medium_term": 2,
                "long_term": 1,
            }.get(opp.get("urgency", "long_term"), 1)

            matrix_data.append(
                {
                    "Opportunity": opp.get("opportunity_description", "")[:100] + "...",
                    "Type": opp.get("opportunity_type", "Unknown"),
                    "Market Size Score": market_size_score,
                    "Urgency Score": urgency_score,
                    "Priority Score": market_size_score * urgency_score,
                    "Market Size": opp.get("market_size_potential", "unknown"),
                    "Urgency": opp.get("urgency", "unknown"),
                    "Competitive Advantage": opp.get("competitive_advantage", "")[:100]
                    + "...",
                }
            )

        df = pd.DataFrame(matrix_data)
        return df.sort_values("Priority Score", ascending=False) if not df.empty else df


# Updated example usage
def main():
    """Main function with proper error handling"""

    # Sample market data
    sample_market_data = {
        "company": "TechCorp",
        "sector": "Financial Technology",
        "service": "Digital Banking Solutions",
        "trends": [
            {
                "hashtag": "#fintech",
                "topics": [
                    {
                        "topic": "AI-powered financial services are becoming mainstream with focus on personalized customer experiences"
                    },
                    {
                        "topic": "Open banking regulations driving API-first approaches and third-party integrations"
                    },
                    {
                        "topic": "Cryptocurrency and digital wallet adoption accelerating among consumers"
                    },
                ],
            },
            {
                "hashtag": "#digitalbanking",
                "topics": [
                    {
                        "topic": "Mobile-first banking experiences with biometric authentication gaining traction"
                    },
                    {
                        "topic": "Small business banking digitization creating opportunities for specialized solutions"
                    },
                ],
            },
        ],
        "news": {
            "TechCorp": [
                {
                    "title": "TechCorp launches new AI-driven credit scoring platform",
                    "description": "Company introduces machine learning algorithms to improve loan approval processes",
                    "source": "FinTech News",
                }
            ],
            "Industry": [
                {
                    "title": "Digital banking adoption surges 40% in past year",
                    "description": "Report shows increasing consumer preference for mobile banking solutions",
                    "source": "Banking Today",
                }
            ],
        },
        "competitors": {
            "relevant_pages": [
                {
                    "service_match": True,
                    "relevance_score": 0.95,
                    "content_type": "service_page",
                    "competitive_intelligence": {
                        "products_services": [
                            "Mobile Banking App",
                            "Credit Scoring API",
                            "Small Business Loans",
                        ],
                        "key_features": [
                            "AI-powered insights",
                            "Real-time transactions",
                            "Multi-currency support",
                        ],
                        "pricing_info": "Starting at $99/month for basic plan",
                        "unique_value_proposition": "First platform to offer real-time credit decisions using alternative data",
                    },
                }
            ]
        },
    }

    try:
        print("🔍 Starting AI-Powered Market Analysis...")
        print("=" * 60)

        # Initialize analyzer
        analyzer = MarketAnalysisAI()

        # Run analysis
        analysis_result = analyzer.analyze_market_gaps_opportunities(sample_market_data)

        if analysis_result.get("error"):
            print(f"❌ Analysis failed: {analysis_result['error']}")
            return

        print("✅ Analysis completed successfully!")

        # Print key insights
        gaps = analysis_result.get("market_gaps", [])
        opportunities = analysis_result.get("market_opportunities", [])
        recommendations = analysis_result.get("strategic_recommendations", [])

        print(f"\n📊 KEY FINDINGS:")
        print(f"   🔍 Market Gaps Identified: {len(gaps)}")
        print(f"   🚀 Opportunities Found: {len(opportunities)}")
        print(f"   🎯 Strategic Recommendations: {len(recommendations)}")

        # Generate comprehensive report
        report = analyzer.generate_strategic_report(analysis_result)

        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        company_name = sample_market_data.get("Company", "unknown").replace(" ", "_")

        report_filename = f"strategic_analysis_{company_name}_{timestamp}.md"
        with open(report_filename, "w", encoding="utf-8") as f:
            f.write(report)

        # Save raw analysis data
        data_filename = f"analysis_data_{company_name}_{timestamp}.json"
        with open(data_filename, "w", encoding="utf-8") as f:
            json.dump(analysis_result, f, indent=2, ensure_ascii=False)

        # Create opportunity matrix
        opportunity_matrix = analyzer.create_opportunity_matrix(analysis_result)
        if not opportunity_matrix.empty:
            matrix_filename = f"opportunity_matrix_{company_name}_{timestamp}.csv"
            opportunity_matrix.to_csv(matrix_filename, index=False)
            print(f"📈 Opportunity matrix saved to: {matrix_filename}")

        print(f"\n📄 Reports generated:")
        print(f"   - Strategic Report: {report_filename}")
        print(f"   - Raw Analysis Data: {data_filename}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("Please check your API key and internet connection")
