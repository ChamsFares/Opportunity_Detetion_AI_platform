"""
Dynamic Chart Schemas for MCP Backend
Pydantic models for dynamic chart generation requests and responses.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ChartType(str, Enum):
    """Supported chart types."""
    LINE = "line"
    BAR = "bar"
    AREA = "area"
    PIE = "pie"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    CANDLESTICK = "candlestick"
    RADAR = "radar"
    TREEMAP = "treemap"
    SANKEY = "sankey"
    GAUGE = "gauge"
    FUNNEL = "funnel"


class DataSourceType(str, Enum):
    """Data source types for chart generation."""
    DATABASE = "database"
    API = "api"
    FILE = "file"
    REAL_TIME = "real_time"
    GENERATED = "generated"
    HYBRID = "hybrid"


class AggregationType(str, Enum):
    """Data aggregation types."""
    SUM = "sum"
    COUNT = "count"
    AVERAGE = "average"
    MEDIAN = "median"
    MIN = "min"
    MAX = "max"
    DISTINCT_COUNT = "distinct_count"
    PERCENTAGE = "percentage"


class DataField(BaseModel):
    """Data field specification for chart generation."""
    
    field_name: str = Field(..., description="Name of the data field")
    field_type: str = Field(
        ...,
        description="Data type of the field",
        pattern="^(string|number|date|boolean|object)$"
    )
    aggregation: Optional[AggregationType] = Field(
        None,
        description="Aggregation method for this field"
    )
    format: Optional[str] = Field(None, description="Display format for the field")
    alias: Optional[str] = Field(None, description="Display alias for the field")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "field_name": "revenue",
                "field_type": "number",
                "aggregation": "sum",
                "format": "currency",
                "alias": "Total Revenue"
            }
        }


class FilterCondition(BaseModel):
    """Filter condition for data queries."""
    
    field: str = Field(..., description="Field to filter on")
    operator: str = Field(
        ...,
        description="Filter operator",
        pattern="^(eq|ne|gt|gte|lt|lte|in|not_in|contains|starts_with|ends_with)$"
    )
    value: Union[str, int, float, List[Any]] = Field(..., description="Filter value")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "field": "date",
                "operator": "gte",
                "value": "2024-01-01"
            }
        }


class ChartStyling(BaseModel):
    """Chart styling and appearance configuration."""
    
    theme: Optional[str] = Field("default", description="Chart theme")
    color_palette: Optional[List[str]] = Field(None, description="Custom color palette")
    title: Optional[str] = Field(None, description="Chart title")
    subtitle: Optional[str] = Field(None, description="Chart subtitle")
    width: Optional[int] = Field(800, description="Chart width in pixels")
    height: Optional[int] = Field(600, description="Chart height in pixels")
    background_color: Optional[str] = Field(None, description="Background color")
    font_family: Optional[str] = Field(None, description="Font family for text")
    font_size: Optional[int] = Field(None, description="Base font size")
    show_legend: bool = Field(True, description="Whether to show legend")
    show_grid: bool = Field(True, description="Whether to show grid lines")
    animation_enabled: bool = Field(True, description="Whether to enable animations")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "theme": "dark",
                "color_palette": ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4"],
                "title": "Revenue Trends Over Time",
                "width": 1200,
                "height": 600,
                "show_legend": True,
                "animation_enabled": True
            }
        }


class AxisConfiguration(BaseModel):
    """Axis configuration for charts."""
    
    x_axis: Optional[Dict[str, Any]] = Field(None, description="X-axis configuration")
    y_axis: Optional[Dict[str, Any]] = Field(None, description="Y-axis configuration")
    dual_y_axis: bool = Field(False, description="Whether to use dual Y-axis")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "x_axis": {
                    "title": "Time Period",
                    "type": "datetime",
                    "format": "%Y-%m"
                },
                "y_axis": {
                    "title": "Revenue ($)",
                    "format": "currency"
                },
                "dual_y_axis": False
            }
        }


class DynamicChartRequest(BaseModel):
    """
    Request model for dynamic chart generation.
    """
    
    # Chart specification
    chart_type: ChartType = Field(..., description="Type of chart to generate")
    chart_id: Optional[str] = Field(None, description="Unique identifier for the chart")
    
    # Data configuration
    data_source: DataSourceType = Field(..., description="Type of data source")
    data_query: Optional[str] = Field(None, description="Query or path to data")
    data_fields: List[DataField] = Field(..., description="Data fields to include in chart")
    
    # Data processing
    filters: Optional[List[FilterCondition]] = Field(None, description="Filters to apply to data")
    group_by: Optional[List[str]] = Field(None, description="Fields to group data by")
    sort_by: Optional[List[Dict[str, str]]] = Field(None, description="Sort configuration")
    limit: Optional[int] = Field(None, description="Maximum number of data points")
    
    # Chart styling and configuration
    styling: Optional[ChartStyling] = Field(None, description="Chart styling configuration")
    axis_config: Optional[AxisConfiguration] = Field(None, description="Axis configuration")
    
    # Advanced features
    interactive: bool = Field(True, description="Whether chart should be interactive")
    real_time: bool = Field(False, description="Whether chart should update in real-time")
    export_formats: Optional[List[str]] = Field(
        None,
        description="Supported export formats"
    )
    
    # MCP integration
    analysis_context: Optional[Dict[str, Any]] = Field(
        None,
        description="Context for chart analysis"
    )
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "chart_type": "line",
                "chart_id": "revenue_trends_2024",
                "data_source": "database",
                "data_query": "SELECT date, revenue FROM sales WHERE year = 2024",
                "data_fields": [
                    {
                        "field_name": "date",
                        "field_type": "date",
                        "alias": "Time Period"
                    },
                    {
                        "field_name": "revenue",
                        "field_type": "number",
                        "aggregation": "sum",
                        "format": "currency",
                        "alias": "Total Revenue"
                    }
                ],
                "styling": {
                    "title": "Monthly Revenue Trends",
                    "theme": "professional",
                    "width": 1000,
                    "height": 500
                },
                "interactive": True,
                "real_time": False
            }
        }


class ChartDataPoint(BaseModel):
    """Individual data point in chart dataset."""
    
    x: Union[str, int, float, datetime] = Field(..., description="X-axis value")
    y: Union[int, float] = Field(..., description="Y-axis value")
    series: Optional[str] = Field(None, description="Series identifier for multi-series charts")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChartDataset(BaseModel):
    """Chart dataset with metadata."""
    
    data: List[ChartDataPoint] = Field(..., description="Chart data points")
    total_records: int = Field(..., description="Total number of records")
    data_source_info: Optional[Dict[str, Any]] = Field(
        None,
        description="Information about data source"
    )
    last_updated: Optional[datetime] = Field(None, description="When data was last updated")
    schema_info: Optional[Dict[str, Any]] = Field(None, description="Data schema information")

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChartConfiguration(BaseModel):
    """Final chart configuration after processing."""
    
    chart_config: Dict[str, Any] = Field(..., description="Chart.js or D3.js configuration")
    chart_library: str = Field(..., description="Chart library used (e.g., Chart.js, D3.js)")
    responsive_config: Optional[Dict[str, Any]] = Field(
        None,
        description="Responsive design configuration"
    )
    accessibility_config: Optional[Dict[str, Any]] = Field(
        None,
        description="Accessibility configuration"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "chart_config": {
                    "type": "line",
                    "data": {
                        "labels": ["Jan", "Feb", "Mar"],
                        "datasets": [
                            {
                                "label": "Revenue",
                                "data": [10000, 15000, 12000],
                                "borderColor": "#4ECDC4"
                            }
                        ]
                    },
                    "options": {
                        "responsive": True,
                        "plugins": {
                            "title": {
                                "display": True,
                                "text": "Monthly Revenue"
                            }
                        }
                    }
                },
                "chart_library": "Chart.js"
            }
        }


class DynamicChartResponse(BaseModel):
    """
    Response model for dynamic chart generation.
    """
    
    chart_id: str = Field(..., description="Unique identifier for the generated chart")
    chart_type: ChartType = Field(..., description="Type of chart generated")
    generation_timestamp: datetime = Field(..., description="When the chart was generated")
    
    # Chart data and configuration
    dataset: ChartDataset = Field(..., description="Chart dataset")
    configuration: ChartConfiguration = Field(..., description="Chart configuration")
    
    # Chart metadata
    title: Optional[str] = Field(None, description="Chart title")
    description: Optional[str] = Field(None, description="Chart description")
    data_summary: Optional[str] = Field(None, description="Summary of chart data")
    
    # Technical details
    processing_time: Optional[float] = Field(None, description="Generation time in seconds")
    data_quality_score: Optional[float] = Field(None, description="Data quality assessment")
    optimization_applied: Optional[List[str]] = Field(
        None,
        description="Optimizations applied during generation"
    )
    
    # Export and sharing
    export_urls: Optional[Dict[str, str]] = Field(None, description="URLs for exported formats")
    embed_code: Optional[str] = Field(None, description="HTML embed code")
    share_url: Optional[str] = Field(None, description="Shareable URL")
    
    # MCP integration
    mcp_tools_used: List[str] = Field(default=[], description="MCP tools used for generation")
    analysis_insights: Optional[List[str]] = Field(
        None,
        description="AI-generated insights about the chart"
    )
    recommended_actions: Optional[List[str]] = Field(
        None,
        description="Recommended actions based on chart analysis"
    )
    
    # Error handling
    warnings: Optional[List[str]] = Field(None, description="Warnings during generation")
    limitations: Optional[List[str]] = Field(None, description="Chart limitations")

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "chart_id": "chart_12345",
                "chart_type": "line",
                "generation_timestamp": "2024-01-15T10:30:00Z",
                "title": "Revenue Trends Analysis",
                "description": "Monthly revenue trends showing growth pattern",
                "processing_time": 2.5,
                "data_quality_score": 0.95,
                "mcp_tools_used": ["data_analyzer", "chart_generator"],
                "analysis_insights": [
                    "Revenue shows consistent upward trend",
                    "Peak performance in Q3"
                ]
            }
        }


class ChartUpdateRequest(BaseModel):
    """Request to update an existing chart."""
    
    chart_id: str = Field(..., description="ID of chart to update")
    updates: Dict[str, Any] = Field(..., description="Updates to apply")
    preserve_data: bool = Field(True, description="Whether to preserve existing data")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "chart_id": "chart_12345",
                "updates": {
                    "styling": {
                        "title": "Updated Revenue Analysis",
                        "color_palette": ["#FF6B6B", "#4ECDC4"]
                    }
                },
                "preserve_data": True
            }
        }
