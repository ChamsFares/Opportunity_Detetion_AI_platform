import json
import logging
import os

import asyncio
from typing import Any, Dict, List, Optional


from agents.ollama_api import OllamaQwen3Client

from utils.memory_manager import mcp_memory_manager

# Configure logging
logger = logging.getLogger(__name__)


class ChartAnalysisAgent:
    """
    Agent responsible for analyzing data and generating chart configurations using Ollama Qwen3.
    Supports all Chart.js and react-chartjs-2 visualization types with intelligent selection.
    """

    def __init__(self):
        # Initialize Ollama Qwen3 client
        self.ollama_client = OllamaQwen3Client()

        # (Optional) Initialize rate limiter if needed for Ollama
        # self.rate_limiter = get_rate_limiter()

        # Supported chart types for validation (based on Chart.js official documentation)
        self.supported_chart_types = [
            # Basic Chart Types
            "line",  # Line charts for trends and time series
            "bar",  # Vertical bar charts for categorical data
            "pie",  # Pie charts for parts of a whole
            "doughnut",  # Doughnut charts (pie with cutout center)
            "polarArea",  # Polar area charts for magnitude comparisons
            "radar",  # Radar/spider charts for multi-dimensional data
            "scatter",  # Scatter plots for correlation analysis
            "bubble",  # Bubble charts for 3D data (x, y, size)
            # Advanced Chart Types (available in Chart.js 4.x)
            "area",  # Area charts (line charts with filled areas)
            "mixed",  # Mixed chart types in one chart
            # Specialized Types
            "horizontalBar",  # Horizontal bar charts (deprecated but supported via indexAxis)
        ]

        # Chart type categories for intelligent selection
        self.chart_categories = {
            "temporal": ["line", "area", "bar"],
            "categorical": ["bar", "horizontalBar", "pie", "doughnut", "polarArea"],
            "comparative": ["bar", "horizontalBar", "radar", "polarArea"],
            "compositional": ["pie", "doughnut", "polarArea"],
            "correlational": ["scatter", "bubble"],
            "multidimensional": ["radar", "bubble"],
            "distribution": ["scatter", "bubble", "polarArea"],
            "hierarchical": ["pie", "doughnut"],
            "geospatial": ["bubble", "scatter"],  # For location-based data
        }

    def _create_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """
        Create an intelligent prompt for Ollama to analyze data and generate chart configurations.

        Args:
            data: The JSON data to analyze

        Returns:
            Formatted prompt string for Ollama
        """
        return self._create_enhanced_analysis_prompt(data)

    def _create_enhanced_analysis_prompt(
        self,
        data: Dict[str, Any],
        user_request: Optional[str] = None,
        preferred_chart_type: Optional[str] = None,
        data_categories: Optional[List[str]] = None,
        memory_context: Optional[Dict] = None,
    ) -> str:
        """
        Create an enhanced intelligent prompt for Ollama with user preferences and memory context.

        Args:
            data: The JSON data to analyze
            user_request: User's natural language request
            preferred_chart_type: Specific chart type requested
            data_categories: Specific data categories to focus on
            memory_context: Previous chart generation context from memory

        Returns:
            Formatted prompt string for Ollama
        """
        data_json = json.dumps(data, indent=2)

        # Build user-specific instructions
        user_instructions = ""
        if user_request:
            user_instructions += f"\nUSER REQUEST: {user_request}\n"
            user_instructions += "Please prioritize creating charts that fulfill this specific user request.\n"

        if preferred_chart_type:
            user_instructions += f"\nPREFERRED CHART TYPE: {preferred_chart_type}\n"
            user_instructions += f"Please try to use '{preferred_chart_type}' chart type when appropriate for the data.\n"

        if data_categories:
            user_instructions += (
                f"\nFOCUS ON DATA CATEGORIES: {', '.join(data_categories)}\n"
            )
            user_instructions += "Please prioritize data related to these categories when generating charts.\n"

        # === MEMORY CONTEXT INTEGRATION ===
        memory_instructions = ""
        if memory_context:
            memory_instructions += "\n=== MEMORY CONTEXT ===\n"

            # Include user preferences from memory
            if memory_context.get("user_preferences"):
                prefs = memory_context["user_preferences"]
                if prefs.get("preferred_types"):
                    memory_instructions += f"USER'S PREFERRED CHART TYPES (from history): {', '.join(prefs['preferred_types'])}\n"
                if prefs.get("avoided_types"):
                    memory_instructions += f"USER'S AVOIDED CHART TYPES (from history): {', '.join(prefs['avoided_types'])}\n"

            # Include successful patterns from memory
            if memory_context.get("successful_patterns"):
                patterns = memory_context["successful_patterns"]
                if patterns.get("chart_type_success"):
                    top_types = sorted(
                        patterns["chart_type_success"].items(),
                        key=lambda x: x[1],
                        reverse=True,
                    )[:3]
                    memory_instructions += f"MOST SUCCESSFUL CHART TYPES FOR THIS USER: {', '.join([t[0] for t in top_types])}\n"

            # Include recent chart context
            if memory_context.get("recent_charts"):
                recent = memory_context["recent_charts"]
                chart_types_used = []
                for entry in recent[:2]:  # Last 2 entries
                    chart_types_used.extend(entry.get("chart_types", []))
                if chart_types_used:
                    memory_instructions += f"RECENTLY GENERATED CHART TYPES: {', '.join(set(chart_types_used))}\n"
                    memory_instructions += "Consider chart type diversity - avoid overusing the same types unless specifically requested.\n"

            memory_instructions += "Please leverage this memory context to provide better, more personalized chart recommendations.\n"
            memory_instructions += "=== END MEMORY CONTEXT ===\n"

        return f"""
Analyze the following JSON data and determine what charts can be generated from it.
{user_instructions}
{memory_instructions}
Data to analyze:
{data_json}

Requirements:
1. Identify all numeric data that can be visualized
2. Determine appropriate chart types based on the data structure and content
3. Generate chart configurations for the most meaningful visualizations
4. Consider data relationships, patterns, and business context
5. Prioritize Chart.js native types for optimal performance
6. If user specified preferences, incorporate them while ensuring data compatibility
7. Use memory context to provide personalized and diverse chart recommendations

Return ONLY a valid JSON array of chart configurations. Each chart object must have:
- "title": descriptive title for the chart
- "type": chart type (see available types below)
- "labels": array of string labels for data points
- "data": array of numeric values corresponding to labels
- "description": brief description of what the chart shows

AVAILABLE CHART TYPES (Chart.js 4.x Official):

**PRIMARY CHART TYPES:**
- "line": Time series, trends, continuous data over time
- "bar": Categorical comparisons, discrete values (vertical bars)
- "pie": Parts of a whole, percentages (complete circle, max 8 segments)
- "doughnut": Similar to pie but with center hollow, better for modern UI
- "polarArea": Circular chart showing magnitude and categories (equal angles, varying radius)
- "radar": Multi-dimensional data, comparing multiple metrics (spider/web chart)
- "scatter": Correlation between two variables, x-y relationships
- "bubble": Three-dimensional data (x, y, and bubble size)

**SPECIALIZED TYPES:**
- "area": Line charts with filled areas underneath (for cumulative data)
- "mixed": Combination of different chart types in one chart
- "horizontalBar": Horizontal bar chart (use bar with indexAxis: 'y')

INTELLIGENT CHART SELECTION GUIDELINES:

1. **TEMPORAL DATA** (dates, quarters, months, years, time series):
   - PRIMARY: "line" for trends and changes over time
   - SECONDARY: "area" for cumulative or volume data over time
   - ALTERNATIVE: "bar" for comparing discrete time periods

2. **CATEGORICAL DATA** (regions, products, departments, categories):
   - PRIMARY: "bar" for comparing quantities across categories
   - MODERN: "doughnut" for parts of a whole (≤8 categories)
   - HORIZONTAL: "horizontalBar" if category names are long
   - CIRCULAR: "polarArea" for magnitude comparison with circular display

3. **COMPOSITIONAL DATA** (market share, budget allocation, percentages):
   - PREFERRED: "doughnut" over "pie" for modern UI
   - CLASSIC: "pie" for traditional percentage display
   - RADIAL: "polarArea" for magnitude-based composition

4. **MULTI-DIMENSIONAL DATA**:
   - METRICS: "radar" for comparing multiple metrics per category
   - CORRELATION: "scatter" for showing correlation between two variables
   - 3D DATA: "bubble" if you have three dimensions (x, y, size)

5. **BUSINESS DATA PATTERNS**:
   - Revenue over time → "line" or "area"
   - Department budgets → "doughnut" or "bar"
   - Regional performance → "bar" or "polarArea"
   - Product comparisons → "bar" or "horizontalBar"
   - Market share → "doughnut" (preferred) or "pie"
   - Performance metrics → "radar"
   - Sales vs profit → "scatter" or "bubble"

6. **CHART SELECTION PRIORITIES**:
   - TIME PROGRESSION: Always prefer "line" or "area"
   - COMPOSITION: Prefer "doughnut" over "pie" for better UX
   - COMPARISON: Use "bar" for straightforward comparisons
   - CORRELATION: Use "scatter" for relationships
   - MULTIDIMENSIONAL: Use "radar" for 3+ metrics
   - CIRCULAR DATA: Use "polarArea" for equal-angle magnitude display

7. **ADVANCED TECHNIQUES**:
   - Use "mixed" charts for datasets with different scales
   - Use "bubble" charts for financial data (sales, profit, market size)
   - Use "polarArea" for geographic/regional data visualization
   - Use "area" charts for cumulative metrics (running totals)

ENHANCED DATA PATTERN RECOGNITION:
- Detect quarterly patterns (Q1-Q4) → "line" with temporal styling
- Identify hierarchical data → "doughnut" with nested structure
- Recognize percentage/ratio data → "doughnut" or "pie"
- Find correlation opportunities → "scatter" or "bubble"
- Suggest multiple visualization angles for rich datasets
- Prioritize accessibility and color-blind friendly options

CHART.JS SPECIFIC OPTIMIZATIONS:
- Use "doughnut" instead of "pie" for better performance and aesthetics
- Leverage "polarArea" for data with natural circular properties
- Use "radar" for multi-metric comparisons (KPIs, performance scores)
- Implement "bubble" charts for three-dimensional business metrics
- Use "area" charts for cumulative business data (running totals, growth)

Example format:
[
  {{
    "title": "Quarterly Revenue Trend",
    "type": "line",
    "labels": ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024"],
    "data": [150000, 180000, 165000, 210000],
    "description": "Revenue performance trend across quarters showing overall growth pattern with Q2 peak"
  }},
  {{
    "title": "Market Share Distribution",
    "type": "doughnut",
    "labels": ["North Region", "South Region", "East Region", "West Region"],
    "data": [125000, 98000, 145000, 87000],
    "description": "Regional market distribution with modern doughnut visualization for better readability"
  }},
  {{
    "title": "Product Performance Analysis",
    "type": "radar",
    "labels": ["Sales", "Customer Satisfaction", "Market Penetration", "Profit Margin", "Growth Rate"],
    "data": [85, 92, 78, 88, 94],
    "description": "Multi-dimensional product performance showing strengths and improvement areas"
  }}
]

CRITICAL REQUIREMENTS:
- Choose the most appropriate Chart.js native type for optimal performance
- Consider user experience and data readability
- Prioritize modern chart types (doughnut over pie, polarArea over basic pie)
- Ensure accessibility and responsive design compatibility
- Leverage memory context for personalized and diverse recommendations
- Return only the JSON array, no additional text or explanations"""

    def _clean_response(self, response_text: str) -> str:
        """
        Clean LLM response by removing markdown code blocks and extra whitespace.

        Args:
            response_text: Raw response from LLM

        Returns:
            Cleaned response text
        """
        if not response_text:
            return ""

        response_text = response_text.strip()

        # Remove code block markers if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        return response_text.strip()


    async def _call_ollama_api(self, prompt: str) -> Any:
        """
        Call Ollama Qwen3 API for chart analysis.
        """
        return await asyncio.to_thread(self.ollama_client.generate, prompt)

    def _generate_fallback_chart_configs(
        self, data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate fallback chart configurations using heuristic analysis when API quota is exhausted.

        Args:
            data: The data to analyze

        Returns:
            List of fallback chart configurations
        """
        fallback_charts = []

        try:
            # Flatten the data to find numeric values
            def extract_numeric_data(obj, prefix=""):
                numeric_data = {}

                if isinstance(obj, dict):
                    for key, value in obj.items():
                        current_prefix = f"{prefix}.{key}" if prefix else key
                        if isinstance(value, (int, float)):
                            numeric_data[current_prefix] = value
                        elif isinstance(value, (dict, list)):
                            numeric_data.update(
                                extract_numeric_data(value, current_prefix)
                            )
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        current_prefix = f"{prefix}[{i}]"
                        if isinstance(item, (int, float)):
                            numeric_data[current_prefix] = item
                        elif isinstance(item, (dict, list)):
                            numeric_data.update(
                                extract_numeric_data(item, current_prefix)
                            )

                return numeric_data

            numeric_fields = extract_numeric_data(data)

            if len(numeric_fields) >= 2:
                # Create a simple bar chart from the first few numeric fields
                chart_data = list(numeric_fields.items())[:8]  # Limit to 8 data points

                fallback_charts.append(
                    {
                        "title": "Data Overview (Fallback Analysis)",
                        "type": "bar",
                        "labels": [key.split(".")[-1] for key, _ in chart_data],
                        "data": [value for _, value in chart_data],
                        "description": "Basic chart generated from numeric data (API quota exhausted - using fallback analysis)",
                    }
                )

                # If we have enough data, create a pie chart as well
                if len(chart_data) >= 3:
                    # Use absolute values for pie chart (negative values don't work well)
                    pie_data = [
                        (key, abs(value)) for key, value in chart_data if value != 0
                    ]

                    if pie_data:
                        fallback_charts.append(
                            {
                                "title": "Data Distribution (Fallback Analysis)",
                                "type": "doughnut",
                                "labels": [key.split(".")[-1] for key, _ in pie_data],
                                "data": [value for _, value in pie_data],
                                "description": "Distribution chart generated from data (API quota exhausted - using fallback analysis)",
                            }
                        )

        except Exception as e:
            logger.warning(f"Failed to generate fallback chart configurations: {e}")

        return fallback_charts

    def _validate_chart_config(
        self, chart: Dict[str, Any], index: int
    ) -> Optional[Dict[str, Any]]:
        """
        Validate a single chart configuration.

        Args:
            chart: Chart configuration to validate
            index: Index of the chart for logging

        Returns:
            Validated chart config or None if invalid
        """
        if not isinstance(chart, dict):
            logger.warning(
                f"Skipping invalid chart config at index {index}: not a dict"
            )
            return None

        # Check required fields
        required_fields = ["title", "type", "labels", "data"]
        missing_fields = [field for field in required_fields if field not in chart]

        if missing_fields:
            logger.warning(
                f"Skipping chart config at index {index}: missing fields {missing_fields}"
            )
            return None

        # Validate data types
        if not isinstance(chart["title"], str) or not chart["title"].strip():
            logger.warning(f"Skipping chart config at index {index}: invalid title")
            return None

        if chart["type"] not in self.supported_chart_types:
            logger.warning(
                f"Skipping chart config at index {index}: invalid chart type {chart['type']}"
            )
            return None

        if not isinstance(chart["labels"], list) or not chart["labels"]:
            logger.warning(f"Skipping chart config at index {index}: invalid labels")
            return None

        if not isinstance(chart["data"], list) or not chart["data"]:
            logger.warning(f"Skipping chart config at index {index}: invalid data")
            return None

        # Validate that data contains only numbers
        try:
            numeric_data = [float(val) for val in chart["data"]]
            chart["data"] = numeric_data
        except (ValueError, TypeError):
            logger.warning(
                f"Skipping chart config at index {index}: data contains non-numeric values"
            )
            return None

        # Validate that labels and data have same length
        if len(chart["labels"]) != len(chart["data"]):
            logger.warning(
                f"Skipping chart config at index {index}: labels and data length mismatch"
            )
            return None

        # Add default description if missing
        if "description" not in chart:
            chart["description"] = (
                f"{chart['type'].title()} chart showing {chart['title']}"
            )

        return chart

    def _generate_fallback_chart_configs(
        self, data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate fallback chart configurations using heuristic analysis when API quota is exhausted.

        Args:
            data: The data to analyze

        Returns:
            List of fallback chart configurations
        """
        fallback_charts = []

        try:
            # Flatten the data to find numeric values
            def extract_numeric_data(obj, prefix=""):
                numeric_data = {}

                if isinstance(obj, dict):
                    for key, value in obj.items():
                        current_prefix = f"{prefix}.{key}" if prefix else key
                        if isinstance(value, (int, float)):
                            numeric_data[current_prefix] = value
                        elif isinstance(value, (dict, list)):
                            numeric_data.update(
                                extract_numeric_data(value, current_prefix)
                            )
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        current_prefix = f"{prefix}[{i}]"
                        if isinstance(item, (int, float)):
                            numeric_data[current_prefix] = item
                        elif isinstance(item, (dict, list)):
                            numeric_data.update(
                                extract_numeric_data(item, current_prefix)
                            )

                return numeric_data

            numeric_fields = extract_numeric_data(data)

            if len(numeric_fields) >= 2:
                # Create a simple bar chart from the first few numeric fields
                chart_data = list(numeric_fields.items())[:8]  # Limit to 8 data points

                fallback_charts.append(
                    {
                        "title": "Data Overview (Fallback Analysis)",
                        "type": "bar",
                        "labels": [key.split(".")[-1] for key, _ in chart_data],
                        "data": [value for _, value in chart_data],
                        "description": "Basic chart generated from numeric data (API quota exhausted - using fallback analysis)",
                    }
                )

                # If we have enough data, create a pie chart as well
                if len(chart_data) >= 3:
                    # Use absolute values for pie chart (negative values don't work well)
                    pie_data = [
                        (key, abs(value)) for key, value in chart_data if value != 0
                    ]

                    if pie_data:
                        fallback_charts.append(
                            {
                                "title": "Data Distribution (Fallback Analysis)",
                                "type": "doughnut",
                                "labels": [key.split(".")[-1] for key, _ in pie_data],
                                "data": [value for _, value in pie_data],
                                "description": "Distribution chart generated from data (API quota exhausted - using fallback analysis)",
                            }
                        )

        except Exception as e:
            logger.warning(f"Failed to generate fallback chart configurations: {e}")

        return fallback_charts

    def _validate_chart_configurations(
        self, chart_configs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Validate all chart configurations.

        Args:
            chart_configs: List of chart configurations to validate

        Returns:
            List of validated chart configurations
        """
        validated_charts = []

        for i, chart in enumerate(chart_configs):
            validated_chart = self._validate_chart_config(chart, i)
            if validated_chart:
                validated_charts.append(validated_chart)

        return validated_charts

    async def analyze_data_for_charts(
        self,
        data: Dict[str, Any],
        session_id: Optional[str] = None,
        user_specific_request: Optional[str] = None,
        preferred_chart_type: Optional[str] = None,
        data_categories: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze data and generate chart configurations using Ollama Qwen3 with memory integration.

        Args:
            data: JSON data to analyze
            session_id: Optional session identifier for tracking and memory
            user_specific_request: User's natural language request for specific charts
            preferred_chart_type: Specific chart type requested by user
            data_categories: Specific data categories to focus on

        Returns:
            Dictionary containing analysis results and chart configurations
        """
        try:
            # Input validation
            if not isinstance(data, dict):
                return {
                    "success": False,
                    "error": "Input must be a JSON object",
                    "error_code": "INVALID_INPUT",
                }

            if not data:
                return {
                    "success": False,
                    "error": "Data cannot be empty",
                    "error_code": "EMPTY_DATA",
                }


            # Check if Ollama client is available
            if not self.ollama_client:
                return {
                    "success": False,
                    "error": "Ollama Qwen3 service is not available.",
                    "error_code": "SERVICE_UNAVAILABLE",
                }

            # === MEMORY INTEGRATION: Retrieve previous context ===
            previous_context = (
                self._get_memory_context(session_id) if session_id else {}
            )

            # Create enhanced analysis prompt with user preferences and memory context
            analysis_prompt = self._create_enhanced_analysis_prompt(
                data,
                user_specific_request,
                preferred_chart_type,
                data_categories,
                previous_context,
            )


            # Call Ollama Qwen3 API for chart analysis
            try:
                response_text = await self._call_ollama_api(analysis_prompt)

                if not response_text:
                    return {
                        "success": False,
                        "error": "Ollama Qwen3 returned no response",
                        "error_code": "NO_RESPONSE",
                    }

                # Clean and parse the response
                response_text = self._clean_response(response_text)

                # Parse JSON response
                try:
                    chart_configs = json.loads(response_text)
                except json.JSONDecodeError as json_err:
                    logger.error(f"Failed to parse Ollama response as JSON: {json_err}")
                    logger.error(f"Raw response: {response_text}")
                    return {
                        "success": False,
                        "error": "Ollama Qwen3 returned invalid JSON format",
                        "error_code": "INVALID_JSON",
                        "raw_response": response_text[:500],
                    }

                # Validate chart configurations
                if not isinstance(chart_configs, list):
                    return {
                        "success": False,
                        "error": "Ollama Qwen3 must return an array of chart configurations",
                        "error_code": "INVALID_FORMAT",
                    }

                # Validate each chart configuration
                validated_charts = self._validate_chart_configurations(chart_configs)

                # === MEMORY INTEGRATION: Store successful charts ===
                if validated_charts and session_id:
                    generation_context = {
                        "user_request": user_specific_request,
                        "preferred_chart_type": preferred_chart_type,
                        "data_categories": data_categories,
                        "data_size": len(json.dumps(data)),
                        "chart_count": len(validated_charts),
                        "chart_types": [
                            chart.get("type") for chart in validated_charts
                        ],
                        "analysis_method": "ollama_qwen3",
                        "memory_enhanced": bool(previous_context),
                    }

                    # Store in both short-term and long-term memory
                    mcp_memory_manager.store_charts_short_term(
                        session_id=session_id,
                        charts=validated_charts,
                        user_prompt=user_specific_request or "chart generation",
                        generation_context=generation_context,
                    )

                    # Store in long-term memory if charts are high quality
                    success_score = mcp_memory_manager._calculate_chart_success_score(
                        validated_charts
                    )
                    if (
                        success_score > 70
                    ):  # Store high-quality charts in long-term memory
                        tags = []
                        if preferred_chart_type:
                            tags.append(f"type:{preferred_chart_type}")
                        if data_categories:
                            tags.extend([f"category:{cat}" for cat in data_categories])

                        mcp_memory_manager.store_charts_long_term(
                            session_id=session_id,
                            charts=validated_charts,
                            user_prompt=user_specific_request or "chart generation",
                            generation_context=generation_context,
                            tags=tags,
                        )

                    # Update user preferences based on successful generation
                    if preferred_chart_type:
                        current_prefs = mcp_memory_manager.get_chart_preferences(session_id)
                        preferred_types = current_prefs.get("preferred_types", [])
                        if preferred_chart_type not in preferred_types:
                            preferred_types.append(preferred_chart_type)

                        mcp_memory_manager.update_chart_preferences(
                            session_id=session_id, preferred_types=preferred_types
                        )

                if not validated_charts:
                    return {
                        "success": True,
                        "message": "No visualizable data found in the provided dataset",
                        "charts": [],
                        "analysis_summary": {
                            "total_charts_generated": 0,
                            "data_points_analyzed": len(str(data)),
                            "session_id": session_id,
                            "memory_context_used": bool(previous_context),
                        },
                    }

                # Log successful analysis
                logger.info(
                    f"Successfully generated {len(validated_charts)} chart configurations from data analysis"
                )

                return {
                    "success": True,
                    "message": f"Successfully generated {len(validated_charts)} chart configurations",
                    "charts": validated_charts,
                    "analysis_summary": {
                        "total_charts_generated": len(validated_charts),
                        "chart_types": list(
                            set(chart["type"] for chart in validated_charts)
                        ),
                        "data_points_analyzed": len(str(data)),
                        "session_id": session_id,
                        "memory_context_used": bool(previous_context),
                        "memory_enhanced_generation": session_id is not None,
                    },
                    "raw_data_size": len(json.dumps(data)),
                    "memory_stats": (
                        mcp_memory_manager.get_memory_stats(session_id)
                        if session_id
                        else None
                    ),
                }

            except Exception as ollama_err:
                logger.error(f"Ollama Qwen3 API call failed: {ollama_err}")
                return {
                    "success": False,
                    "error": "Failed to analyze data with Ollama Qwen3. Please try again later.",
                    "error_code": "OLLAMA_API_ERROR",
                    "details": str(ollama_err),
                }

        except Exception as e:
            logger.error(f"Unexpected error in chart analysis: {e}", exc_info=True)
            return {
                "success": False,
                "error": "An internal error occurred while analyzing the data",
                "error_code": "INTERNAL_ERROR",
                "details": str(e),
            }

    def is_service_available(self) -> bool:
        """
        Check if the Ollama Qwen3 service is available.

        Returns:
            True if service is available, False otherwise
        """
        return self.ollama_client is not None

    def get_supported_chart_types(self) -> List[str]:
        """
        Get list of supported chart types.

        Returns:
            List of supported chart type strings
        """
        return self.supported_chart_types.copy()

    def _get_memory_context(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieve memory context for enhanced chart generation.

        Args:
            session_id: Session identifier

        Returns:
            Dictionary containing memory context for chart generation
        """
        try:
            if not session_id:
                return {}

            # Get user preferences
            user_preferences = mcp_memory_manager.get_chart_preferences(session_id)

            # Get successful patterns
            successful_patterns = mcp_memory_manager.get_successful_patterns(session_id)

            # Get recent charts for diversity
            recent_charts = mcp_memory_manager.get_recent_charts(session_id, limit=3)

            # Get memory statistics
            memory_stats = mcp_memory_manager.get_memory_stats(session_id)

            # Clean expired charts to keep memory fresh
            mcp_memory_manager.clear_expired_charts(session_id)

            context = {
                "session_id": session_id,
                "user_preferences": user_preferences,
                "successful_patterns": successful_patterns,
                "recent_charts": recent_charts,
                "memory_stats": memory_stats,
                "has_context": bool(
                    user_preferences or successful_patterns or recent_charts
                ),
            }

            if context["has_context"]:
                logger.info(
                    f"Retrieved memory context for session {session_id}: {memory_stats.get('total_chart_entries', 0)} chart entries"
                )

            return context

        except Exception as e:
            logger.error(f"Error retrieving memory context: {e}")
            return {}

    def get_memory_insights(self, session_id: str) -> Dict[str, Any]:
        """
        Get insights about chart generation patterns from memory.

        Args:
            session_id: Session identifier

        Returns:
            Dictionary containing insights about chart generation patterns
        """
        try:
            if not session_id:
                return {"error": "No session ID provided"}

            # Get comprehensive memory data
            memory_stats = mcp_memory_manager.get_memory_stats(session_id)
            user_preferences = mcp_memory_manager.get_chart_preferences(session_id)
            successful_patterns = mcp_memory_manager.get_successful_patterns(session_id)
            recent_charts = mcp_memory_manager.get_recent_charts(session_id, limit=5)

            # Analyze patterns
            insights = {
                "session_id": session_id,
                "memory_summary": memory_stats,
                "chart_generation_insights": {
                    "total_charts_generated": memory_stats.get(
                        "total_chart_entries", 0
                    ),
                    "favorite_chart_types": memory_stats.get(
                        "chart_type_distribution", {}
                    ),
                    "has_established_preferences": bool(user_preferences),
                    "chart_diversity_score": len(
                        memory_stats.get("chart_type_distribution", {})
                    ),
                },
                "user_behavior": {
                    "preferred_types": user_preferences.get("preferred_types", []),
                    "avoided_types": user_preferences.get("avoided_types", []),
                    "last_activity": memory_stats.get("last_chart_generated"),
                },
                "recommendations": [],
            }

            # Generate recommendations based on patterns
            chart_distribution = memory_stats.get("chart_type_distribution", {})
            if chart_distribution:
                # Recommend less-used chart types for diversity
                all_types = [
                    "bar",
                    "line",
                    "pie",
                    "doughnut",
                    "radar",
                    "scatter",
                    "area",
                    "polarArea",
                ]
                unused_types = [t for t in all_types if t not in chart_distribution]
                if unused_types:
                    insights["recommendations"].append(
                        f"Try using {', '.join(unused_types[:3])} charts for more diverse visualizations"
                    )

                # Check for overused types
                if chart_distribution:
                    max_used_type = max(chart_distribution.items(), key=lambda x: x[1])
                    if max_used_type[1] > 5:
                        insights["recommendations"].append(
                            f"You've used {max_used_type[0]} charts frequently. Consider trying other visualization types."
                        )

            # Recent activity insights
            if recent_charts:
                recent_types = []
                for entry in recent_charts:
                    recent_types.extend(entry.get("chart_types", []))
                unique_recent = set(recent_types)
                if len(unique_recent) < 3:
                    insights["recommendations"].append(
                        "Consider diversifying your chart types for better data storytelling"
                    )

            return insights

        except Exception as e:
            logger.error(f"Error getting memory insights: {e}")
            return {"error": str(e), "session_id": session_id}


# Create a global instance
chart_analysis_agent = ChartAnalysisAgent()


# Convenience function for direct usage
async def analyze_data_for_charts(
    data: Dict[str, Any],
    session_id: Optional[str] = None,
    user_specific_request: Optional[str] = None,
    preferred_chart_type: Optional[str] = None,
    data_categories: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Convenience function to analyze data and generate chart configurations.

    Args:
        data: JSON data to analyze
        session_id: Optional session identifier
        user_specific_request: User's natural language request for specific charts
        preferred_chart_type: Specific chart type requested by user
        data_categories: Specific data categories to focus on

    Returns:
        Dictionary containing analysis results and chart configurations
    """
    return await chart_analysis_agent.analyze_data_for_charts(
        data, session_id, user_specific_request, preferred_chart_type, data_categories
    )
