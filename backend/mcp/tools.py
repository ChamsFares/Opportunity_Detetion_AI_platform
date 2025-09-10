"""
MCP Tool definitions and schemas for OpportunityDetection backend
"""

from typing import Dict, Any, List, Optional, Union, Type
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ToolType(str, Enum):
    """MCP Tool types"""
    ANALYSIS = "analysis"
    DATA_EXTRACTION = "data_extraction"
    VISUALIZATION = "visualization"
    REPORTING = "reporting"
    MARKET_RESEARCH = "market_research"
    COMPETITOR_ANALYSIS = "competitor_analysis"
    TREND_IDENTIFICATION = "trend_identification"
    PDF_GENERATION = "pdf_generation"
    BUSINESS_TRENDS = "business_trends"
    CHART_ANALYSIS = "chart_analysis"
    NEWS_PROCESSING = "news_processing"
    SUMMARIZATION = "summarization"
    LINKEDIN_SCRAPING = "linkedin_scraping"
    WEB_SCRAPING = "web_scraping"


class ToolStatus(str, Enum):
    """Tool execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MCPToolSchema(BaseModel):
    """Base schema for MCP tools"""
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    tool_type: ToolType = Field(..., description="Type of tool")
    version: str = Field(default="1.0.0", description="Tool version")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters schema")
    required_parameters: List[str] = Field(default_factory=list, description="Required parameters")
    output_schema: Optional[Dict[str, Any]] = Field(None, description="Output schema")
    tags: List[str] = Field(default_factory=list, description="Tool tags")
    enabled: bool = Field(default=True, description="Tool enabled status")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ToolExecutionResult(BaseModel):
    """Tool execution result"""
    tool_name: str
    execution_id: str
    status: ToolStatus
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class AnalysisToolSchema(MCPToolSchema):
    """Schema for analysis tools"""
    analysis_type: str = Field(..., description="Type of analysis")
    input_format: List[str] = Field(..., description="Supported input formats")
    processing_time_estimate: Optional[int] = Field(None, description="Estimated processing time in seconds")


class CompetitorAnalysisSchema(BaseModel):
    """Schema for competitor analysis input"""
    company_name: str = Field(..., description="Target company name")
    industry: str = Field(..., description="Industry sector")
    region: Optional[str] = Field(None, description="Geographic region")
    analysis_depth: str = Field(default="standard", description="Analysis depth: basic, standard, comprehensive")
    include_financials: bool = Field(default=True, description="Include financial analysis")
    include_market_share: bool = Field(default=True, description="Include market share analysis")
    competitor_limit: int = Field(default=10, description="Maximum number of competitors to analyze")


class TrendAnalysisSchema(BaseModel):
    """Schema for trend analysis input"""
    industry: str = Field(..., description="Industry to analyze")
    time_period: str = Field(default="12m", description="Time period for analysis")
    region: Optional[str] = Field(None, description="Geographic region")
    trend_types: List[str] = Field(default=["market", "technology", "consumer"], description="Types of trends to identify")
    data_sources: List[str] = Field(default=["news", "social_media", "financial"], description="Data sources to use")


class MarketAnalysisSchema(BaseModel):
    """Schema for market analysis input"""
    company_name: str = Field(..., description="Company name")
    market_segment: str = Field(..., description="Market segment")
    geographic_scope: str = Field(default="global", description="Geographic scope")
    analysis_period: str = Field(default="1y", description="Analysis period")
    include_swot: bool = Field(default=True, description="Include SWOT analysis")
    include_pestle: bool = Field(default=True, description="Include PESTLE analysis")


class ChartGenerationSchema(BaseModel):
    """Schema for chart generation input"""
    data: Dict[str, Any] = Field(..., description="Data to visualize")
    chart_type: str = Field(..., description="Type of chart to generate")
    title: str = Field(..., description="Chart title")
    styling_options: Dict[str, Any] = Field(default_factory=dict, description="Chart styling options")


class NewsProcessingSchema(BaseModel):
    """Schema for news processing input"""
    sources: List[str] = Field(..., description="News sources to process")
    keywords: List[str] = Field(..., description="Keywords to search for")
    date_range: Dict[str, str] = Field(..., description="Date range for news search")
    sentiment_analysis: bool = Field(default=True, description="Include sentiment analysis")


def get_all_tools() -> Dict[str, MCPToolSchema]:
    """Get all predefined tools"""
    tools = {
        "market_analyzer": MCPToolSchema(
            name="market_analyzer",
            description="Analyzes market opportunities and competitive landscape",
            tool_type=ToolType.MARKET_RESEARCH,
            parameters={
                "business_domain": {"type": "string", "description": "Business domain"},
                "product_or_service": {"type": "string", "description": "Product or service"},
                "target_audience": {"type": "string", "description": "Target audience"},
                "region_or_market": {"type": "string", "description": "Geographic region or market"}
            },
            required_parameters=["business_domain", "product_or_service", "target_audience", "region_or_market"],
            tags=["market", "analysis", "opportunity"]
        ),
        
        "competitor_analyzer": MCPToolSchema(
            name="competitor_analyzer",
            description="Performs comprehensive competitor analysis",
            tool_type=ToolType.COMPETITOR_ANALYSIS,
            parameters={
                "company_name": {"type": "string", "description": "Company name"},
                "industry": {"type": "string", "description": "Industry sector"},
                "region": {"type": "string", "description": "Geographic region"},
                "analysis_depth": {"type": "string", "description": "Analysis depth level"}
            },
            required_parameters=["company_name", "industry"],
            tags=["competitor", "analysis", "market"]
        ),
        
        "trend_analyzer": MCPToolSchema(
            name="trend_analyzer",
            description="Identifies and analyzes business trends",
            tool_type=ToolType.TREND_IDENTIFICATION,
            parameters={
                "industry": {"type": "string", "description": "Industry to analyze"},
                "time_period": {"type": "string", "description": "Time period for analysis"},
                "region": {"type": "string", "description": "Geographic region"},
                "trend_types": {"type": "array", "description": "Types of trends to identify"}
            },
            required_parameters=["industry"],
            tags=["trend", "analysis", "forecasting"]
        ),
        
        "chart_generator": MCPToolSchema(
            name="chart_generator",
            description="Generates dynamic charts and visualizations",
            tool_type=ToolType.VISUALIZATION,
            parameters={
                "data": {"type": "object", "description": "Data to visualize"},
                "chart_type": {"type": "string", "description": "Type of chart"},
                "title": {"type": "string", "description": "Chart title"},
                "styling_options": {"type": "object", "description": "Chart styling"}
            },
            required_parameters=["data", "chart_type", "title"],
            tags=["chart", "visualization", "data"]
        ),
        
        "news_processor": MCPToolSchema(
            name="news_processor",
            description="Processes and analyzes news content",
            tool_type=ToolType.NEWS_PROCESSING,
            parameters={
                "sources": {"type": "array", "description": "News sources"},
                "keywords": {"type": "array", "description": "Keywords to search"},
                "date_range": {"type": "object", "description": "Date range"},
                "sentiment_analysis": {"type": "boolean", "description": "Include sentiment analysis"}
            },
            required_parameters=["sources", "keywords"],
            tags=["news", "processing", "sentiment"]
        ),
        
        "pdf_generator": MCPToolSchema(
            name="pdf_generator",
            description="Generates PDF reports from analysis data",
            tool_type=ToolType.PDF_GENERATION,
            parameters={
                "data": {"type": "object", "description": "Report data"},
                "template": {"type": "string", "description": "Report template"},
                "output_path": {"type": "string", "description": "Output file path"}
            },
            required_parameters=["data", "template"],
            tags=["pdf", "report", "generation"]
        ),
        
        "summarization_agent": MCPToolSchema(
            name="summarization_agent",
            description="Summarizes text content and analysis results",
            tool_type=ToolType.SUMMARIZATION,
            parameters={
                "content": {"type": "string", "description": "Content to summarize"},
                "max_length": {"type": "integer", "description": "Maximum summary length"},
                "summary_type": {"type": "string", "description": "Type of summary"}
            },
            required_parameters=["content"],
            tags=["summary", "text", "processing"]
        ),
        
        "linkedin_scraper": MCPToolSchema(
            name="linkedin_scraper",
            description="Scrapes LinkedIn company and trend data",
            tool_type=ToolType.LINKEDIN_SCRAPING,
            parameters={
                "company_name": {"type": "string", "description": "Company name"},
                "data_types": {"type": "array", "description": "Types of data to scrape"},
                "depth": {"type": "string", "description": "Scraping depth"}
            },
            required_parameters=["company_name"],
            tags=["linkedin", "scraping", "company"]
        )
    }
    
    return tools


def get_tool_schema(tool_name: str) -> Optional[MCPToolSchema]:
    """Get schema for a specific tool"""
    tools = get_all_tools()
    return tools.get(tool_name)


def get_tools_by_type(tool_type: ToolType) -> List[MCPToolSchema]:
    """Get all tools of a specific type"""
    tools = get_all_tools()
    return [tool for tool in tools.values() if tool.tool_type == tool_type]


def validate_tool_parameters(tool_name: str, parameters: Dict[str, Any]) -> bool:
    """Validate tool parameters against schema"""
    tool = get_tool_schema(tool_name)
    if not tool:
        return False
    
    # Check required parameters
    for required_param in tool.required_parameters:
        if required_param not in parameters:
            return False
    
    return True
