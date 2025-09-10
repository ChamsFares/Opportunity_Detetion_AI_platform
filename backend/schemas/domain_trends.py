"""
Domain Trends Schemas for MCP Backend
Pydantic models for domain trend analysis requests and responses.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from pydantic import BaseModel, Field


class DomainTrendsRequest(BaseModel):
    """
    Request model for domain trends analysis.
    """
    
    domain: str = Field(
        ..., 
        description="Business domain or industry sector for trend analysis",
        min_length=2,
        max_length=100,
        example="artificial intelligence"
    )
    
    # Enhanced parameters for comprehensive analysis
    region: Optional[str] = Field(
        None,
        description="Geographic region for localized trends",
        example="North America"
    )
    
    time_horizon: Optional[str] = Field(
        "medium_term",
        description="Time horizon for trend analysis",
        pattern="^(short_term|medium_term|long_term)$"
    )
    
    analysis_depth: Optional[str] = Field(
        "standard",
        description="Depth of analysis required",
        pattern="^(basic|standard|comprehensive)$"
    )
    
    specific_keywords: Optional[List[str]] = Field(
        None,
        description="Specific keywords to focus the trend analysis"
    )
    
    exclude_keywords: Optional[List[str]] = Field(
        None,
        description="Keywords to exclude from trend analysis"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "domain": "fintech",
                "region": "Europe",
                "time_horizon": "medium_term",
                "analysis_depth": "comprehensive",
                "specific_keywords": ["blockchain", "digital payments", "neobanks"],
                "exclude_keywords": ["cryptocurrency mining"]
            }
        }


class TrendInsight(BaseModel):
    """
    Individual trend insight model.
    """
    
    trend_name: str = Field(..., description="Name or title of the trend")
    description: str = Field(..., description="Detailed description of the trend")
    impact_level: str = Field(
        ..., 
        description="Impact level of the trend",
        pattern="^(low|medium|high|critical)$"
    )
    confidence_score: float = Field(
        ..., 
        description="Confidence score for this trend prediction",
        ge=0.0,
        le=1.0
    )
    time_horizon: str = Field(
        ...,
        description="Expected time horizon for this trend",
        pattern="^(immediate|short_term|medium_term|long_term)$"
    )
    supporting_evidence: List[str] = Field(
        default=[],
        description="Evidence supporting this trend"
    )
    affected_sectors: List[str] = Field(
        default=[],
        description="Business sectors affected by this trend"
    )
    opportunities: List[str] = Field(
        default=[],
        description="Business opportunities arising from this trend"
    )
    challenges: List[str] = Field(
        default=[],
        description="Challenges or risks associated with this trend"
    )
    sources: List[str] = Field(
        default=[],
        description="Data sources for this trend analysis"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "trend_name": "AI-Powered Personalization",
                "description": "Increasing adoption of AI for personalized customer experiences",
                "impact_level": "high",
                "confidence_score": 0.85,
                "time_horizon": "medium_term",
                "supporting_evidence": [
                    "70% increase in AI personalization investments",
                    "Major tech companies expanding AI recommendation systems"
                ],
                "affected_sectors": ["e-commerce", "entertainment", "financial services"],
                "opportunities": ["Enhanced customer engagement", "Improved conversion rates"],
                "challenges": ["Privacy concerns", "Implementation complexity"]
            }
        }


class MarketIndicator(BaseModel):
    """
    Market indicator for quantitative trend analysis.
    """
    
    indicator_name: str = Field(..., description="Name of the market indicator")
    current_value: Optional[float] = Field(None, description="Current value of the indicator")
    trend_direction: str = Field(
        ...,
        description="Direction of the trend",
        pattern="^(increasing|decreasing|stable|volatile)$"
    )
    growth_rate: Optional[float] = Field(None, description="Growth rate percentage")
    market_size: Optional[str] = Field(None, description="Market size information")
    forecast_period: Optional[str] = Field(None, description="Forecast time period")
    data_source: Optional[str] = Field(None, description="Source of the indicator data")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "indicator_name": "Global AI Market Size",
                "current_value": 136.6,
                "trend_direction": "increasing", 
                "growth_rate": 20.1,
                "market_size": "$136.6 billion USD",
                "forecast_period": "2024-2030",
                "data_source": "Market Research Reports"
            }
        }


class DomainTrendsResponse(BaseModel):
    """
    Response model for domain trends analysis.
    """
    
    domain: str = Field(..., description="Analyzed domain")
    analysis_timestamp: datetime = Field(..., description="When the analysis was performed")
    
    # Core trend analysis results
    key_trends: List[TrendInsight] = Field(
        default=[],
        description="Key trends identified in the domain"
    )
    
    emerging_trends: List[TrendInsight] = Field(
        default=[],
        description="Emerging trends with early indicators"
    )
    
    declining_trends: List[TrendInsight] = Field(
        default=[],
        description="Trends showing signs of decline"
    )
    
    market_indicators: List[MarketIndicator] = Field(
        default=[],
        description="Quantitative market indicators"
    )
    
    # Analysis metadata
    analysis_summary: str = Field(..., description="Executive summary of trend analysis")
    methodology: str = Field(..., description="Analysis methodology used")
    data_sources: List[str] = Field(default=[], description="Data sources consulted")
    limitations: List[str] = Field(default=[], description="Analysis limitations")
    
    # Actionable insights
    strategic_recommendations: List[str] = Field(
        default=[],
        description="Strategic recommendations based on trends"
    )
    
    investment_opportunities: List[str] = Field(
        default=[],
        description="Investment opportunities identified"
    )
    
    risk_factors: List[str] = Field(
        default=[],
        description="Risk factors to consider"
    )
    
    # Technical metadata
    processing_time: Optional[float] = Field(None, description="Analysis processing time in seconds")
    confidence_level: Optional[float] = Field(None, description="Overall confidence in analysis")
    mcp_tools_used: List[str] = Field(default=[], description="MCP tools used for analysis")

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "domain": "fintech",
                "analysis_timestamp": "2024-01-15T10:30:00Z",
                "key_trends": [],
                "analysis_summary": "The fintech domain shows strong growth in digital payments and blockchain adoption...",
                "methodology": "Multi-source trend analysis using news, market reports, and patent data",
                "strategic_recommendations": [
                    "Focus on mobile payment solutions",
                    "Explore blockchain integration opportunities"
                ],
                "confidence_level": 0.88,
                "processing_time": 45.2
            }
        }


class TrendAnalysisRequest(BaseModel):
    """
    Extended request model for comprehensive trend analysis.
    """
    
    domains: List[str] = Field(..., description="Multiple domains to analyze")
    comparative_analysis: bool = Field(
        default=False,
        description="Whether to perform comparative analysis between domains"
    )
    focus_areas: Optional[List[str]] = Field(
        None,
        description="Specific focus areas for the analysis"
    )
    business_context: Optional[Dict[str, Any]] = Field(
        None,
        description="Business context for targeted analysis"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "domains": ["artificial intelligence", "machine learning", "robotics"],
                "comparative_analysis": True,
                "focus_areas": ["market size", "investment trends", "technological barriers"],
                "business_context": {
                    "company_stage": "startup",
                    "target_market": "enterprise",
                    "budget_range": "500k-2M"
                }
            }
        }
