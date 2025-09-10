import asyncio
import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from db.mongo import db as mongo_db
from utils.gemini_rate_limiter import get_rate_limiter
from utils.logger import get_logger
from utils.memory_manager import memory_manager

logger = get_logger("dynamic_chart_agent")


class DynamicChartAgent:
    """
    Dynamic Chart Agent that processes user prompts to either:
    1. Regenerate charts based on user specifications
    2. Fetch specific data from MongoDB and embedding databases

    The agent analyzes user intent and routes to appropriate sub-agents.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set or no API key provided")
        self.rate_limiter = get_rate_limiter()
        self.mongo_db = mongo_db

        # Intent classification patterns
        self.chart_generation_patterns = [
            r"generate.*chart",
            r"create.*chart",
            r"show.*chart",
            r"visualize",
            r"plot",
            r"graph",
            r"regenerate.*chart",
            r"update.*chart",
            r"modify.*chart",
            r"change.*chart",
        ]

        self.data_fetch_patterns = [
            r"get.*data",
            r"fetch.*data",
            r"show.*data",
            r"find.*data",
            r"retrieve",
            r"search",
            r"what.*data",
            r"give.*me.*data",
            r"display.*data",
        ]

        self.chart_types = {
            "bar": ["bar", "column", "histogram"],
            "line": ["line", "trend", "time series", "timeline"],
            "pie": ["pie", "donut", "distribution"],
            "area": ["area", "filled"],
            "scatter": ["scatter", "bubble", "correlation"],
            "radar": ["radar", "spider"],
            "doughnut": ["doughnut", "ring"],
        }

    async def process_user_request(
        self,
        user_prompt: str,
        session_id: Optional[str] = None,
        existing_charts: Optional[List[Dict]] = None,
        previous_analysis_data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Main entry point that processes user requests and routes to appropriate handlers.
        Now enhanced with memory integration for better chart generation.

        Args:
            user_prompt: User's natural language request
            session_id: Session identifier for data retrieval and memory (uses default if None)
            existing_charts: Previously generated charts from multi-agent
            previous_analysis_data: Previous analysis data from multi-agent

        Returns:
            Dict containing either regenerated charts or fetched data
        """
        try:
            logger.info(f"Processing user request: {user_prompt[:100]}...")

            # Check if user is requesting a specific chart by name
            specific_chart_name = self._extract_chart_name_from_prompt(user_prompt)

            # If specific chart requested, try to find it in memory
            if specific_chart_name:
                logger.info(f"Looking for specific chart: {specific_chart_name}")
                specific_chart = memory_manager.find_chart_by_name(
                    specific_chart_name, session_id
                )
                if specific_chart:
                    logger.info(
                        f"Found specific chart in {specific_chart['found_in']} memory"
                    )
                    return {
                        "success": True,
                        "type": "specific_chart_retrieval",
                        "chart": specific_chart,
                        "chart_name": specific_chart_name,
                        "memory_source": specific_chart["found_in"],
                        "session_id": specific_chart["session_id"],
                    }
                else:
                    logger.warning(
                        f"Specific chart '{specific_chart_name}' not found in memory"
                    )

            # === MEMORY INTEGRATION: Retrieve chart memory context ===
            memory_context = memory_manager.get_memory_context(
                session_id=session_id, include_all_sessions=True
            )

            # If no existing charts provided and no specific chart found, get all from memory
            if not existing_charts and not specific_chart_name:
                all_memory_charts = memory_manager.get_charts_from_memory(
                    session_id=session_id, include_all_sessions=True
                )
                if all_memory_charts:
                    logger.info(
                        f"Using {len(all_memory_charts)} charts from memory as existing charts"
                    )
                    existing_charts = all_memory_charts

            # Analyze user intent with memory context
            intent = await self._analyze_user_intent(user_prompt, memory_context)

            # Store user interaction for learning
            if session_id:
                memory_manager.update_long_term_memory(
                    session_id=session_id,
                    input_text=user_prompt,
                    output_text=f"Intent: {intent.get('type', 'unknown')}",
                )

            if intent["type"] == "chart_generation":
                result = await self._handle_chart_generation_request(
                    user_prompt,
                    session_id,
                    existing_charts,
                    previous_analysis_data,
                    intent,
                    memory_context,
                )
            elif intent["type"] == "data_fetch":
                result = await self._handle_data_fetch_request(
                    user_prompt, session_id, intent
                )
            else:
                result = await self._handle_hybrid_request(
                    user_prompt,
                    session_id,
                    existing_charts,
                    previous_analysis_data,
                    intent,
                    memory_context,
                )

            # === MEMORY INTEGRATION: Store successful results ===
            if result.get("success") and session_id:
                self._store_successful_interaction(
                    session_id, user_prompt, result, intent
                )

            return result

        except Exception as e:
            logger.error(f"Error processing user request: {e}")
            return {"success": False, "error": str(e), "type": "error"}

    async def _analyze_user_intent(
        self, user_prompt: str, memory_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Analyze user prompt to determine intent and extract key parameters.
        Now enhanced with memory context for better intent detection.
        """
        try:
            prompt_lower = user_prompt.lower()

            # Check for chart generation intent
            chart_score = sum(
                1
                for pattern in self.chart_generation_patterns
                if re.search(pattern, prompt_lower)
            )

            # Check for data fetch intent
            data_score = sum(
                1
                for pattern in self.data_fetch_patterns
                if re.search(pattern, prompt_lower)
            )

            # === MEMORY INTEGRATION: Enhance intent detection with memory ===
            if memory_context and memory_context.get("has_context"):
                # Boost chart generation score if user has chart preferences
                user_preferences = memory_context.get("user_preferences", {})
                if user_preferences.get("preferred_types"):
                    for chart_type in user_preferences["preferred_types"]:
                        if chart_type in prompt_lower:
                            chart_score += 2  # Boost score for preferred types

                # Consider recent successful patterns
                successful_patterns = memory_context.get("successful_patterns", {})
                if successful_patterns.get("prompt_patterns"):
                    for word, frequency in successful_patterns[
                        "prompt_patterns"
                    ].items():
                        if word in prompt_lower and frequency > 2:
                            chart_score += (
                                1  # Boost score for successful prompt patterns
                            )

            # Determine primary intent
            if chart_score > data_score:
                intent_type = "chart_generation"
            elif data_score > chart_score:
                intent_type = "data_fetch"
            else:
                intent_type = "hybrid"

            # Extract chart type if mentioned (enhanced with memory preferences)
            chart_type = None
            for chart_name, keywords in self.chart_types.items():
                if any(keyword in prompt_lower for keyword in keywords):
                    chart_type = chart_name
                    break

            # If no explicit chart type but user has preferences, suggest preferred type
            if (
                not chart_type
                and memory_context
                and memory_context.get("user_preferences")
            ):
                preferred_types = memory_context["user_preferences"].get(
                    "preferred_types", []
                )
                if preferred_types:
                    chart_type = preferred_types[0]  # Suggest most preferred type

            # Extract data categories
            data_categories = self._extract_data_categories(prompt_lower)

            # Extract specific metrics or KPIs
            metrics = self._extract_metrics(prompt_lower)

            return {
                "type": intent_type,
                "chart_type": chart_type,
                "data_categories": data_categories,
                "metrics": metrics,
                "confidence": max(chart_score, data_score) / 10,
                "original_prompt": user_prompt,
                "memory_enhanced": bool(
                    memory_context and memory_context.get("has_context")
                ),
                "suggested_by_memory": chart_type
                and not any(
                    chart_type in keywords
                    for keywords in self.chart_types.values()
                    for keyword in keywords
                    if keyword in prompt_lower
                ),
            }

        except Exception as e:
            logger.error(f"Error analyzing user intent: {e}")
            return {"type": "unknown", "error": str(e)}

    def _extract_data_categories(self, prompt_lower: str) -> List[str]:
        """Extract data categories from user prompt."""
        categories = []

        category_keywords = {
            "competitors": ["competitor", "competition", "rival"],
            "revenue": ["revenue", "income", "earnings", "sales"],
            "trends": ["trend", "pattern", "movement"],
            "market": ["market", "industry", "sector"],
            "kpi": ["kpi", "metric", "performance", "indicator"],
            "profitability": ["profit", "margin", "profitability"],
            "roi": ["roi", "return on investment", "investment return"],
            "news": ["news", "article", "press"],
            "social": ["social", "linkedin", "post"],
        }

        for category, keywords in category_keywords.items():
            if any(keyword in prompt_lower for keyword in keywords):
                categories.append(category)

        return categories

    def _extract_metrics(self, prompt_lower: str) -> List[str]:
        """Extract specific metrics from user prompt."""
        metrics = []

        metric_keywords = [
            "revenue",
            "profit",
            "margin",
            "roi",
            "growth",
            "market share",
            "customer acquisition",
            "retention",
            "conversion rate",
            "engagement",
            "reach",
        ]

        for metric in metric_keywords:
            if metric in prompt_lower:
                metrics.append(metric)

        return metrics

    def _has_user_provided_specific_data(
        self,
        user_prompt: str,
        intent: Dict[str, Any],
        existing_charts: Optional[List[Dict]],
    ) -> bool:
        """
        Determine if user provided specific data/requirements or wants all regenerated.

        Returns True if user specified particular data/charts to work with.
        Returns False if user wants everything regenerated.
        """
        prompt_lower = user_prompt.lower()

        # Check for specific chart mentions
        specific_chart_indicators = [
            "this chart",
            "that chart",
            "the chart",
            "specific chart",
            "only the",
            "just the",
            "update the",
            "modify the",
            "change the",
            "show only",
            "display only",
        ]

        # Check for specific data category mentions
        has_specific_categories = bool(intent.get("data_categories"))
        has_specific_chart_type = bool(intent.get("chart_type"))
        has_specific_metrics = bool(intent.get("metrics"))

        # Check for "all" or "everything" keywords
        regenerate_all_indicators = [
            "all charts",
            "all data",
            "everything",
            "complete",
            "full",
            "entire",
            "whole",
            "regenerate all",
            "update all",
            "show all",
        ]

        # If user explicitly asks for "all"
        if any(indicator in prompt_lower for indicator in regenerate_all_indicators):
            return False

        # If user mentions specific elements or has existing charts and uses specific language
        if (
            any(indicator in prompt_lower for indicator in specific_chart_indicators)
            or (
                existing_charts
                and any(word in prompt_lower for word in ["update", "modify", "change"])
            )
            or has_specific_categories
            or has_specific_chart_type
            or has_specific_metrics
        ):
            return True

        # Default: if no clear indicators, assume user wants specific handling if they provided existing data
        return bool(existing_charts)

    async def _handle_chart_generation_request(
        self,
        user_prompt: str,
        session_id: Optional[str],
        existing_charts: Optional[List[Dict]],
        previous_analysis_data: Optional[Dict],
        intent: Dict[str, Any],
        memory_context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Handle chart generation/regeneration requests with enhanced memory integration.

        Priority order for data sources:
        1. Memory-stored charts and their original data (from /analyze-data endpoints)
        2. Previous analysis data from multi-agent system
        3. Existing charts provided in the request
        4. Fresh data fetched from MongoDB

        This ensures that dynamic chart regeneration leverages the most recent and
        relevant data stored in memory from initial chart generation.
        """
        try:
            logger.info("Processing chart generation request with memory context")

            # Determine if user provided specific data or wants all regenerated
            user_provided_specific_data = self._has_user_provided_specific_data(
                user_prompt, intent, existing_charts
            )

            # Get data for chart generation (prioritizing memory-stored data)
            chart_data = await self._prepare_chart_data(
                session_id,
                intent["data_categories"],
                previous_analysis_data,
                existing_charts,
                memory_context,  # Pass memory context for prioritized data access
            )

            # Check if we have any usable data (including existing charts)
            if not chart_data and not existing_charts:
                return {
                    "success": False,
                    "error": "No data available for chart generation",
                    "type": "chart_generation",
                }

            # Use chart analysis agent to generate charts
            try:
                from agents.chart_analysis_agent import chart_analysis_agent

                # Prepare enhanced data for chart analysis (prioritizing memory data)
                chart_analysis_data = {
                    "chart_data": chart_data,
                    "user_request": user_prompt,
                    "chart_type_preference": intent.get("chart_type"),
                    "data_categories": intent.get("data_categories", []),
                    "metrics": intent.get("metrics", []),
                    "existing_charts": existing_charts or [],
                    "regenerate_all": not user_provided_specific_data,
                    "specific_request": user_provided_specific_data,
                    "memory_context": memory_context,  # Pass memory context to chart agent
                    "memory_charts": chart_data.get(
                        "memory_charts", []
                    ),  # Prioritize memory charts
                    "memory_enhanced": chart_data.get("memory_enhanced", False),
                    "use_memory_data": True,  # Flag to prioritize memory data in chart generation
                }

                # Call the enhanced chart analysis agent
                chart_result = await chart_analysis_agent.analyze_data_for_charts(
                    data=chart_analysis_data,
                    session_id=session_id,
                    user_specific_request=user_prompt,
                    preferred_chart_type=intent.get("chart_type"),
                    data_categories=intent.get("data_categories", []),
                )

                if chart_result.get("success"):
                    # === MEMORY INTEGRATION: Store successful charts with enhanced metadata ===
                    generated_charts = chart_result.get("charts", [])
                    if generated_charts and session_id:
                        # Store in short-term memory for immediate access
                        memory_manager.store_charts_short_term(
                            charts=generated_charts,
                            user_id=session_id,
                            context="dynamic_chart_regeneration",
                            metadata={
                                "dynamic_agent": True,
                                "intent": intent,
                                "user_provided_specific_data": user_provided_specific_data,
                                "memory_enhanced": bool(memory_context),
                                "original_prompt": user_prompt,
                                "chart_data_keys": list(chart_data.keys()),
                                "regeneration_type": (
                                    "memory_enhanced" if memory_context else "standard"
                                ),
                                "data_categories": intent.get("data_categories", []),
                                "timestamp": datetime.utcnow().isoformat(),
                            },
                        )

                        # Store high-quality charts in long-term memory
                        if len(generated_charts) >= 1:  # Store if any charts generated
                            tags = ["dynamic_agent"]
                            if intent.get("chart_type"):
                                tags.append(f"type:{intent['chart_type']}")
                            if intent.get("data_categories"):
                                tags.extend(
                                    [
                                        f"category:{cat}"
                                        for cat in intent["data_categories"]
                                    ]
                                )

                            memory_manager.store_charts_long_term(
                                charts=generated_charts,
                                user_id=session_id,
                                context="dynamic_chart_regeneration_longterm",
                                success_metrics={
                                    "chart_count": len(generated_charts),
                                    "memory_enhanced": bool(memory_context),
                                    "regeneration_success": True,
                                    "user_satisfaction": "high",  # Assume high since generation succeeded
                                },
                                metadata={
                                    "dynamic_agent": True,
                                    "intent": intent,
                                    "regeneration_scope": (
                                        "specific"
                                        if user_provided_specific_data
                                        else "all"
                                    ),
                                    "original_prompt": user_prompt,
                                    "chart_data_source": (
                                        "memory_enhanced"
                                        if memory_context
                                        else "database"
                                    ),
                                    "tags": tags,
                                    "timestamp": datetime.utcnow().isoformat(),
                                },
                            )

                        # Update user preferences based on successful generation
                        self._update_user_preferences_from_success(
                            session_id, intent, generated_charts
                        )

                    return {
                        "success": True,
                        "type": "chart_generation",
                        "charts": generated_charts,
                        "data_used": chart_data,
                        "user_request": user_prompt,
                        "regeneration_scope": (
                            "specific" if user_provided_specific_data else "all"
                        ),
                        "generated_at": datetime.now().isoformat(),
                        "memory_enhanced": bool(memory_context),
                        "chart_count": len(generated_charts),
                    }
                else:
                    return {
                        "success": False,
                        "error": chart_result.get("error", "Chart generation failed"),
                        "type": "chart_generation",
                    }

            except ImportError:
                logger.warning("Chart analysis agent not available, using fallback")
                return await self._generate_fallback_charts(
                    chart_data,
                    intent,
                    existing_charts,
                    user_provided_specific_data,
                    memory_context,
                )

        except Exception as e:
            logger.error(f"Error in chart generation: {e}")
            # Try fallback generation with existing charts if available
            if existing_charts:
                logger.info("Attempting fallback chart generation with existing charts")
                try:
                    user_provided_specific_data = self._has_user_provided_specific_data(
                        user_prompt, intent, existing_charts
                    )
                    return await self._generate_fallback_charts(
                        {},
                        intent,
                        existing_charts,
                        user_provided_specific_data,
                        memory_context,
                    )
                except Exception as fallback_error:
                    logger.error(f"Fallback generation also failed: {fallback_error}")
            return {"success": False, "error": str(e), "type": "chart_generation"}

    async def _handle_data_fetch_request(
        self, user_prompt: str, session_id: str, intent: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle data fetching requests from MongoDB and embedding databases.
        """
        try:
            logger.info("Processing data fetch request")

            # Fetch data based on categories
            fetched_data = {}

            for category in intent.get("data_categories", []):
                data = await self._fetch_category_data(session_id, category)
                if data:
                    fetched_data[category] = data

            # If no specific categories, fetch general session data
            if not fetched_data:
                fetched_data = await self._fetch_general_session_data(session_id)

            # Apply any metric filters
            if intent.get("metrics"):
                fetched_data = self._filter_data_by_metrics(
                    fetched_data, intent["metrics"]
                )

            return {
                "success": True,
                "type": "data_fetch",
                "data": fetched_data,
                "categories": intent.get("data_categories", []),
                "metrics": intent.get("metrics", []),
                "user_request": user_prompt,
                "fetched_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error in data fetch: {e}")
            return {"success": False, "error": str(e), "type": "data_fetch"}

    async def _handle_hybrid_request(
        self,
        user_prompt: str,
        session_id: str,
        existing_charts: Optional[List[Dict]],
        previous_analysis_data: Optional[Dict],
        intent: Dict[str, Any],
        memory_context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Handle requests that require both data fetching and chart generation with memory context.
        """
        try:
            logger.info("Processing hybrid request with memory context")

            # First fetch the requested data
            data_result = await self._handle_data_fetch_request(
                user_prompt, session_id, intent
            )

            if not data_result.get("success"):
                return data_result

            # Then generate charts from the fetched data
            chart_result = await self._handle_chart_generation_request(
                user_prompt,
                session_id,
                existing_charts,
                data_result.get("data"),
                intent,
                memory_context,  # Pass memory context
            )

            return {
                "success": True,
                "type": "hybrid",
                "data": data_result.get("data"),
                "charts": (
                    chart_result.get("charts", [])
                    if chart_result.get("success")
                    else []
                ),
                "user_request": user_prompt,
                "processed_at": datetime.now().isoformat(),
                "memory_enhanced": bool(memory_context),
            }

        except Exception as e:
            logger.error(f"Error in hybrid request: {e}")
            return {"success": False, "error": str(e), "type": "hybrid"}

    async def _prepare_chart_data(
        self,
        session_id: str,
        categories: List[str],
        previous_analysis_data: Optional[Dict],
        existing_charts: Optional[List[Dict]] = None,
        memory_context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Prepare data for chart generation from various sources, prioritizing memory-stored data.
        """
        try:
            chart_data = {}

            # === PRIORITY 1: Use memory-stored chart data ===
            if memory_context and memory_context.get("recent_charts"):
                memory_charts = memory_context["recent_charts"]
                logger.info(
                    f"Found {len(memory_charts)} charts in memory for regeneration"
                )

                # Extract data from memory-stored charts and their metadata
                if memory_charts:
                    chart_data["memory_charts"] = memory_charts

                    # Extract original data from memory metadata if available
                    for chart in memory_charts:
                        chart_metadata = chart.get("metadata", {})
                        if chart_metadata.get("original_data"):
                            chart_data["memory_original_data"] = chart_metadata[
                                "original_data"
                            ]
                            break  # Use the first available original data

                    # Extract data categories from memory
                    memory_metadata = memory_context.get("metadata", {})
                    if memory_metadata.get("data_categories"):
                        memory_data_categories = memory_metadata["data_categories"]
                        logger.info(f"Memory data categories: {memory_data_categories}")

                        # Create structured data from memory categories
                        for category in memory_data_categories:
                            if category not in chart_data:
                                chart_data[f"memory_{category}"] = {
                                    "source": "memory",
                                    "category": category,
                                    "available": True,
                                }

            # === PRIORITY 2: Use previous analysis data if available ===
            if previous_analysis_data:
                chart_data["analysis_data"] = previous_analysis_data

            # === PRIORITY 3: Include existing charts if available ===
            if existing_charts:
                chart_data["existing_charts"] = existing_charts

            # === PRIORITY 4: Fetch additional data based on categories (only if not in memory) ===
            for category in categories:
                # Skip fetching if we already have this category from memory
                if f"memory_{category}" not in chart_data:
                    data = await self._fetch_category_data(session_id, category)
                    if data:
                        chart_data[category] = data

            # === PRIORITY 5: If no specific categories, get comprehensive data ===
            if not categories and not chart_data.get("memory_charts"):
                comprehensive_data = await self._fetch_general_session_data(session_id)
                chart_data.update(comprehensive_data)

            # === FALLBACK: Ensure we have something to work with ===
            if not chart_data:
                if existing_charts:
                    chart_data = {
                        "existing_charts": existing_charts,
                        "fallback_mode": True,
                    }
                elif memory_context and memory_context.get("recent_charts"):
                    chart_data = {
                        "memory_charts": memory_context["recent_charts"],
                        "memory_fallback": True,
                    }

            # Add memory enhancement indicator
            if memory_context:
                chart_data["memory_enhanced"] = True
                chart_data["memory_context_available"] = True

            logger.info(f"Prepared chart data with keys: {list(chart_data.keys())}")
            return chart_data

        except Exception as e:
            logger.error(f"Error preparing chart data: {e}")
            # Return at least existing charts or memory charts if available
            if memory_context and memory_context.get("recent_charts"):
                return {
                    "memory_charts": memory_context["recent_charts"],
                    "memory_fallback": True,
                    "error_fallback": True,
                }
            elif existing_charts:
                return {"existing_charts": existing_charts, "fallback_mode": True}
            return {}

    async def _fetch_category_data(
        self, session_id: str, category: str
    ) -> Optional[Dict]:
        """
        Fetch data for a specific category from MongoDB.
        """
        try:
            collections = [
                "competitors_data",
                "news_data",
                "trends_data",
                "analysis_results",
            ]

            if category == "competitors":
                collection = self.mongo_db.competitors_data
            elif category == "news":
                collection = self.mongo_db.news_data
            elif category == "trends":
                collection = self.mongo_db.trends_data
            elif category in ["revenue", "kpi", "profitability", "roi"]:
                collection = self.mongo_db.analysis_results
            else:
                # Try to find in analysis results
                collection = self.mongo_db.analysis_results  # Query by session_id
            cursor = collection.find({"session_id": session_id})
            documents = await cursor.to_list(length=100)

            if documents:
                return {
                    "category": category,
                    "data": documents,
                    "count": len(documents),
                }

            return None

        except Exception as e:
            logger.error(f"Error fetching {category} data: {e}")
            return None

    async def _fetch_general_session_data(self, session_id: str) -> Dict[str, Any]:
        """
        Fetch all available data for a session.
        """
        try:
            collections = [
                "competitors_data",
                "news_data",
                "trends_data",
                "analysis_results",
            ]

            session_data = {}

            for collection_name in collections:
                try:
                    collection = getattr(self.mongo_db, collection_name)
                    cursor = collection.find({"session_id": session_id})
                    documents = await cursor.to_list(length=100)

                    if documents:
                        session_data[collection_name] = {
                            "data": documents,
                            "count": len(documents),
                        }
                except Exception as e:
                    logger.warning(f"Error fetching from {collection_name}: {e}")
                    continue

            return session_data

        except Exception as e:
            logger.error(f"Error fetching general session data: {e}")
            return {}

    def _filter_data_by_metrics(self, data: Dict, metrics: List[str]) -> Dict:
        """
        Filter data based on requested metrics.
        """
        try:
            filtered_data = {}

            for category, category_data in data.items():
                if isinstance(category_data, dict) and "data" in category_data:
                    filtered_items = []
                    for item in category_data["data"]:
                        # Check if item contains any of the requested metrics
                        item_str = json.dumps(item, default=str).lower()
                        if any(metric.lower() in item_str for metric in metrics):
                            filtered_items.append(item)

                    if filtered_items:
                        filtered_data[category] = {
                            **category_data,
                            "data": filtered_items,
                            "count": len(filtered_items),
                            "filtered_by": metrics,
                        }

            return filtered_data

        except Exception as e:
            logger.error(f"Error filtering data by metrics: {e}")
            return data

    async def _generate_fallback_charts(
        self,
        chart_data: Dict,
        intent: Dict[str, Any],
        existing_charts: Optional[List[Dict]] = None,
        user_provided_specific_data: bool = False,
        memory_context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Generate fallback charts when chart analysis agent is not available.
        Now enhanced with memory context for better personalization.
        """
        try:
            fallback_charts = []

            # Get user's preferred chart type (enhanced with memory)
            preferred_type = intent.get("chart_type", "bar")

            # === MEMORY INTEGRATION: Use memory preferences ===
            if memory_context and memory_context.get("user_preferences"):
                user_preferred_types = memory_context["user_preferences"].get(
                    "preferred_types", []
                )
                if user_preferred_types and not preferred_type:
                    preferred_type = user_preferred_types[0]  # Use most preferred type
                elif (
                    user_preferred_types and preferred_type not in user_preferred_types
                ):
                    # User has preferences but requested a different type - respect their choice but note it
                    logger.info(
                        f"User requested {preferred_type} but usually prefers {user_preferred_types}"
                    )

            data_categories = intent.get("data_categories", [])

            # If user provided specific data, only generate what they asked for
            if user_provided_specific_data:
                # If user is asking to update/modify existing charts
                if existing_charts and any(
                    word in intent.get("original_prompt", "").lower()
                    for word in ["update", "modify", "change", "regenerate"]
                ):
                    # Update only the specific existing charts mentioned
                    for chart in existing_charts:
                        updated_chart = self._update_existing_chart(chart, intent)
                        fallback_charts.append(updated_chart)

                # Generate specific charts based on user's specific requests
                elif data_categories:
                    fallback_charts.extend(
                        self._generate_category_specific_charts(
                            data_categories, preferred_type, memory_context
                        )
                    )

                # If user specified a chart type but no categories, create one chart of that type
                elif preferred_type:
                    fallback_charts.append(
                        self._generate_chart_by_type(
                            preferred_type, "User Requested Chart", memory_context
                        )
                    )

            else:
                # User wants everything regenerated - generate comprehensive charts
                logger.info(
                    "Generating comprehensive chart set with memory enhancement"
                )

                # Include existing charts if available (updated versions)
                if existing_charts:
                    for i, existing_chart in enumerate(existing_charts):
                        updated_chart = self._update_existing_chart(
                            existing_chart, intent
                        )
                        updated_chart["title"] = (
                            f"Updated {existing_chart.get('title', f'Chart {i+1}')}"
                        )
                        fallback_charts.append(updated_chart)

                # Generate charts for all common categories
                all_categories = ["revenue", "competitors", "trends", "kpi"]
                fallback_charts.extend(
                    self._generate_category_specific_charts(
                        all_categories, preferred_type, memory_context
                    )
                )

            # === MEMORY INTEGRATION: Add diversity charts based on memory ===
            if memory_context and memory_context.get("recent_charts"):
                recent_types = []
                for entry in memory_context["recent_charts"]:
                    recent_types.extend(entry.get("chart_types", []))

                # Suggest diverse chart types not used recently
                diverse_types = ["radar", "polarArea", "scatter", "bubble"]
                for dtype in diverse_types:
                    if dtype not in recent_types and len(fallback_charts) < 4:
                        fallback_charts.append(
                            self._generate_chart_by_type(
                                dtype,
                                f"Diverse {dtype.capitalize()} Analysis (Memory-Enhanced)",
                                memory_context,
                            )
                        )
                        break

            # If still no charts generated, create a default one
            if not fallback_charts:
                chart_type = preferred_type or "bar"
                fallback_charts.append(
                    self._generate_chart_by_type(
                        chart_type,
                        f"Data Visualization ({chart_type.capitalize()})",
                        memory_context,
                    )
                )

            # === MEMORY INTEGRATION: Store fallback charts ===
            if fallback_charts and memory_context:
                session_id = memory_context.get("session_id")
                if session_id:
                    memory_manager.store_charts_short_term(
                        session_id=session_id,
                        charts=fallback_charts,
                        user_prompt=intent.get(
                            "original_prompt", "fallback generation"
                        ),
                        generation_context={
                            "fallback": True,
                            "memory_enhanced": True,
                            "preferred_type": preferred_type,
                            "user_provided_specific_data": user_provided_specific_data,
                        },
                    )

            return {
                "success": True,
                "type": "chart_generation",
                "charts": fallback_charts,
                "fallback": True,
                "user_preferences_applied": True,
                "preferred_chart_type": preferred_type,
                "regeneration_scope": (
                    "specific" if user_provided_specific_data else "all"
                ),
                "existing_charts_updated": (
                    len(existing_charts) if existing_charts else 0
                ),
                "generated_at": datetime.now().isoformat(),
                "memory_enhanced": bool(memory_context),
                "chart_count": len(fallback_charts),
            }

        except Exception as e:
            logger.error(f"Error generating fallback charts: {e}")
            return {"success": False, "error": str(e), "type": "chart_generation"}

    def _generate_category_specific_charts(
        self,
        categories: List[str],
        preferred_type: str = "bar",
        memory_context: Optional[Dict] = None,
    ) -> List[Dict]:
        """Generate charts for specific data categories with memory enhancement."""
        charts = []

        for category in categories:
            # === MEMORY INTEGRATION: Use memory to select better chart types ===
            chart_type = preferred_type

            # Override with memory preferences for specific categories if available
            if memory_context and memory_context.get("successful_patterns"):
                success_patterns = memory_context["successful_patterns"]
                category_success = success_patterns.get("context_patterns", {})

                # If this category has been successful with certain types, prefer those
                if category in category_success:
                    # Use successful patterns to guide chart type selection
                    chart_type = preferred_type  # Keep user preference as primary

            if category == "revenue" or category == "financial":
                chart_type = (
                    preferred_type
                    if preferred_type in ["bar", "line", "area", "pie", "doughnut"]
                    else "bar"
                )

                # Memory enhancement: prefer line charts for revenue if user has used them successfully
                if (
                    memory_context
                    and memory_context.get("successful_patterns", {})
                    .get("chart_type_success", {})
                    .get("line", 0)
                    > 2
                ):
                    chart_type = "line" if chart_type == "bar" else chart_type

                charts.append(
                    {
                        "type": chart_type,
                        "title": f"Revenue Analysis ({'Memory-Enhanced' if memory_context else 'Standard'})",
                        "data": {
                            "labels": ["Q1", "Q2", "Q3", "Q4"],
                            "datasets": [
                                {
                                    "label": "Revenue",
                                    "data": [100000, 120000, 140000, 160000],
                                    "backgroundColor": (
                                        "#3B82F6"
                                        if chart_type not in ["pie", "doughnut"]
                                        else [
                                            "#3B82F6",
                                            "#10B981",
                                            "#F59E0B",
                                            "#EF4444",
                                        ]
                                    ),
                                }
                            ],
                        },
                    }
                )

            elif category == "competitors" or category == "market":
                chart_type = (
                    preferred_type
                    if preferred_type in ["pie", "doughnut", "bar", "polarArea"]
                    else "doughnut"
                )

                # Memory enhancement: prefer doughnut for market share if successful before
                if (
                    memory_context
                    and memory_context.get("successful_patterns", {})
                    .get("chart_type_success", {})
                    .get("doughnut", 0)
                    > 1
                ):
                    chart_type = (
                        "doughnut" if chart_type in ["pie", "bar"] else chart_type
                    )

                charts.append(
                    {
                        "type": chart_type,
                        "title": f"Competitor Market Share ({'Memory-Enhanced' if memory_context else 'Standard'})",
                        "data": {
                            "labels": ["Company A", "Company B", "Company C", "Others"],
                            "datasets": [
                                {
                                    "data": [30, 25, 20, 25],
                                    "backgroundColor": [
                                        "#3B82F6",
                                        "#10B981",
                                        "#F59E0B",
                                        "#EF4444",
                                    ],
                                    "label": (
                                        "Market Share %" if chart_type == "bar" else ""
                                    ),
                                }
                            ],
                        },
                    }
                )

            elif category == "trends":
                chart_type = (
                    preferred_type
                    if preferred_type in ["line", "area", "bar"]
                    else "line"
                )

                # Memory enhancement: prefer area charts for trends if user likes filled charts
                if memory_context and memory_context.get("user_preferences", {}).get(
                    "style_preferences", {}
                ).get("filled_charts"):
                    chart_type = "area" if chart_type == "line" else chart_type

                charts.append(
                    {
                        "type": chart_type,
                        "title": f"Market Trends ({'Memory-Enhanced' if memory_context else 'Standard'})",
                        "data": {
                            "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                            "datasets": [
                                {
                                    "label": "Trend Growth",
                                    "data": [10, 15, 18, 22, 28, 35],
                                    "backgroundColor": (
                                        "#10B981" if chart_type == "area" else "#3B82F6"
                                    ),
                                    "borderColor": "#3B82F6",
                                    "fill": chart_type == "area",
                                }
                            ],
                        },
                    }
                )

            elif category == "kpi" or category == "metrics":
                chart_type = (
                    preferred_type
                    if preferred_type in ["radar", "bar", "polarArea"]
                    else "radar"
                )

                # Memory enhancement: use radar charts for KPIs if user has used them successfully
                if (
                    memory_context
                    and memory_context.get("successful_patterns", {})
                    .get("chart_type_success", {})
                    .get("radar", 0)
                    > 0
                ):
                    chart_type = "radar"

                charts.append(
                    {
                        "type": chart_type,
                        "title": f"Performance Metrics ({'Memory-Enhanced' if memory_context else 'Standard'})",
                        "data": {
                            "labels": [
                                "Quality",
                                "Speed",
                                "Efficiency",
                                "Innovation",
                                "Customer Satisfaction",
                            ],
                            "datasets": [
                                {
                                    "label": "Current Performance",
                                    "data": [85, 78, 92, 75, 88],
                                    "backgroundColor": "rgba(59, 130, 246, 0.2)",
                                    "borderColor": "#3B82F6",
                                    "pointBackgroundColor": "#3B82F6",
                                }
                            ],
                        },
                    }
                )

        return charts

    def _generate_chart_by_type(
        self, chart_type: str, title: str, memory_context: Optional[Dict] = None
    ) -> Dict:
        """Generate a single chart of specified type with memory enhancement."""

        # === MEMORY INTEGRATION: Enhance chart generation with user preferences ===
        memory_enhanced_title = title
        enhanced_colors = ["#3B82F6", "#10B981", "#F59E0B", "#EF4444"]  # Default colors

        if memory_context:
            # Add memory enhancement indicator to title
            memory_enhanced_title = f"{title} (Memory-Enhanced)"

            # Use user's preferred colors if available
            user_prefs = memory_context.get("user_preferences", {})
            if user_prefs.get("color_preferences"):
                enhanced_colors = user_prefs["color_preferences"][
                    :4
                ]  # Use up to 4 colors

            # Adjust chart complexity based on user preference
            complexity_pref = user_prefs.get("complexity_preference", "moderate")
            if complexity_pref == "simple":
                # Use fewer data points for simple preference
                data_points = [65, 59, 80]
                labels = ["Category A", "Category B", "Category C"]
            elif complexity_pref == "complex":
                # Use more data points for complex preference
                data_points = [65, 59, 80, 81, 76, 92, 45]
                labels = ["Cat A", "Cat B", "Cat C", "Cat D", "Cat E", "Cat F", "Cat G"]
            else:
                # Default moderate complexity
                data_points = [65, 59, 80, 81]
                labels = ["Category A", "Category B", "Category C", "Category D"]
        else:
            data_points = [65, 59, 80, 81]
            labels = ["Category A", "Category B", "Category C", "Category D"]

        return {
            "type": chart_type,
            "title": memory_enhanced_title,
            "data": {
                "labels": labels,
                "datasets": [
                    {
                        "label": "Values",
                        "data": data_points,
                        "backgroundColor": (
                            enhanced_colors[: len(data_points)]
                            if chart_type in ["pie", "doughnut"]
                            else enhanced_colors[0]
                        ),
                        "borderColor": (
                            enhanced_colors[0]
                            if chart_type in ["line", "area"]
                            else None
                        ),
                        "fill": (
                            (
                                memory_context
                                and memory_context.get("user_preferences", {})
                                .get("style_preferences", {})
                                .get("filled_charts", False)
                            )
                            if chart_type in ["line", "area"]
                            else False
                        ),
                    }
                ],
            },
            "memory_applied": bool(memory_context),
            "generation_context": "memory_enhanced" if memory_context else "standard",
        }

    def _update_existing_chart(
        self, existing_chart: Dict, intent: Dict[str, Any]
    ) -> Dict:
        """
        Update an existing chart based on user intent.
        """
        try:
            updated_chart = existing_chart.copy()
            user_prompt = intent.get("original_prompt", "").lower()

            # Check if user wants to change chart type
            if intent.get("chart_type"):
                updated_chart["type"] = intent["chart_type"]

            # Update data based on user request context
            if "quarterly" in user_prompt or "quarter" in user_prompt:
                # Update to quarterly data if requested
                updated_chart["data"]["labels"] = [
                    "Q1 2024",
                    "Q2 2024",
                    "Q3 2024",
                    "Q4 2024",
                ]

                # Update datasets with trend data
                if "datasets" in updated_chart["data"]:
                    for dataset in updated_chart["data"]["datasets"]:
                        if "revenue" in user_prompt:
                            dataset["data"] = [180000, 220000, 280000, 320000]
                        elif "trend" in user_prompt:
                            dataset["data"] = [15, 25, 35, 45]
                        else:
                            # General increase pattern
                            original_data = dataset.get("data", [100, 120, 140, 160])
                            dataset["data"] = [x * 1.2 for x in original_data]

            # Add trend indicators if requested
            if "trend" in user_prompt:
                updated_chart["title"] = (
                    f"{updated_chart.get('title', 'Chart')} - Trends"
                )

            # Update styling based on chart type change
            if (
                updated_chart["type"] in ["pie", "doughnut"]
                and "datasets" in updated_chart["data"]
            ):
                for dataset in updated_chart["data"]["datasets"]:
                    if not isinstance(dataset.get("backgroundColor"), list):
                        dataset["backgroundColor"] = [
                            "#3B82F6",
                            "#10B981",
                            "#F59E0B",
                            "#EF4444",
                        ]

            return updated_chart

        except Exception as e:
            logger.error(f"Error updating existing chart: {e}")
            return existing_chart

    def _extract_chart_name_from_prompt(self, user_prompt: str) -> Optional[str]:
        """
        Extract specific chart name from user prompt.

        Args:
            user_prompt: User's natural language request

        Returns:
            Chart name if found, None otherwise
        """
        try:
            prompt_lower = user_prompt.lower()

            # Patterns to detect chart name requests
            chart_name_patterns = [
                r"regenerate (?:the )?chart (?:called |named |titled )?['\"]([^'\"]+)['\"]",
                r"show (?:me )?(?:the )?chart (?:called |named |titled )?['\"]([^'\"]+)['\"]",
                r"update (?:the )?chart (?:called |named |titled )?['\"]([^'\"]+)['\"]",
                r"modify (?:the )?chart (?:called |named |titled )?['\"]([^'\"]+)['\"]",
                r"regenerate (?:the )?chart (?:called |named |titled )?(\w+(?:\s+\w+)*)",
                r"show (?:me )?(?:the )?chart (?:called |named |titled )?(\w+(?:\s+\w+)*)",
                r"chart (?:called |named |titled )?['\"]([^'\"]+)['\"]",
                r"the ['\"]([^'\"]+)['\"] chart",
            ]

            for pattern in chart_name_patterns:
                match = re.search(pattern, prompt_lower)
                if match:
                    chart_name = match.group(1).strip()
                    # Filter out common words that aren't chart names
                    excluded_words = {
                        "data",
                        "analysis",
                        "result",
                        "results",
                        "information",
                        "info",
                    }
                    if chart_name not in excluded_words and len(chart_name) > 2:
                        logger.info(f"Extracted chart name: {chart_name}")
                        return chart_name

            return None

        except Exception as e:
            logger.error(f"Error extracting chart name from prompt: {e}")
            return None

    def _get_chart_memory_context(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieve chart memory context for enhanced processing.

        Args:
            session_id: Session identifier

        Returns:
            Dictionary containing chart memory context
        """
        try:
            if not session_id:
                return {}

            # Get user preferences
            user_preferences = memory_manager.get_chart_preferences(session_id)

            # Get successful patterns
            successful_patterns = memory_manager.get_successful_patterns(session_id)

            # Get recent charts for context and diversity
            recent_charts = memory_manager.get_recent_charts(session_id, limit=3)

            # Get memory statistics
            memory_stats = memory_manager.get_memory_stats(session_id)

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
                logger.info(f"Retrieved chart memory context for session {session_id}")

            return context

        except Exception as e:
            logger.error(f"Error retrieving chart memory context: {e}")
            return {}

    def _store_successful_interaction(
        self,
        session_id: str,
        user_prompt: str,
        result: Dict[str, Any],
        intent: Dict[str, Any],
    ):
        """
        Store successful user interactions for learning.

        Args:
            session_id: Session identifier
            user_prompt: User's original prompt
            result: Successful result from processing
            intent: Analyzed user intent
        """
        try:
            if result.get("type") == "chart_generation" and result.get("charts"):
                charts = result["charts"]

                # Determine chart types from result
                chart_types = []
                if isinstance(charts, list):
                    for chart in charts:
                        if isinstance(chart, dict) and "type" in chart:
                            chart_types.append(chart["type"])

                # Update successful patterns in memory manager
                if chart_types:
                    # This will be handled by the memory manager when charts are stored
                    logger.info(
                        f"Stored successful interaction: {len(charts)} charts generated"
                    )

        except Exception as e:
            logger.error(f"Error storing successful interaction: {e}")

    def _update_user_preferences_from_success(
        self, session_id: str, intent: Dict[str, Any], generated_charts: List[Dict]
    ):
        """
        Update user preferences based on successful chart generation.

        Args:
            session_id: Session identifier
            intent: User intent that led to success
            generated_charts: Successfully generated charts
        """
        try:
            # Get current preferences
            current_prefs = memory_manager.get_chart_preferences(session_id)

            # Extract successful chart types
            chart_types = [
                chart.get("type") for chart in generated_charts if chart.get("type")
            ]

            # Update preferred types
            preferred_types = current_prefs.get("preferred_types", [])
            for chart_type in chart_types:
                if chart_type not in preferred_types:
                    preferred_types.append(chart_type)

            # Limit to top 5 preferred types to avoid bloat
            if len(preferred_types) > 5:
                preferred_types = preferred_types[-5:]

            # Update preferences
            memory_manager.update_chart_preferences(
                session_id=session_id, preferred_types=preferred_types
            )

            logger.info(
                f"Updated user preferences for session {session_id}: {preferred_types}"
            )

        except Exception as e:
            logger.error(f"Error updating user preferences: {e}")

    def get_user_chart_insights(self, session_id: str) -> Dict[str, Any]:
        """
        Get insights about user's chart generation patterns and preferences.

        Args:
            session_id: Session identifier

        Returns:
            Dictionary containing user insights and recommendations
        """
        try:
            # Get memory statistics and insights
            memory_stats = memory_manager.get_memory_stats(session_id)
            user_preferences = memory_manager.get_chart_preferences(session_id)
            successful_patterns = memory_manager.get_successful_patterns(session_id)
            recent_charts = memory_manager.get_recent_charts(session_id, limit=5)

            # Compile insights
            insights = {
                "session_id": session_id,
                "user_summary": {
                    "total_charts_generated": memory_stats.get(
                        "total_chart_entries", 0
                    ),
                    "preferred_chart_types": user_preferences.get(
                        "preferred_types", []
                    ),
                    "chart_diversity_score": len(
                        memory_stats.get("chart_type_distribution", {})
                    ),
                    "last_activity": memory_stats.get("last_chart_generated"),
                },
                "usage_patterns": {
                    "chart_type_distribution": memory_stats.get(
                        "chart_type_distribution", {}
                    ),
                    "successful_prompt_patterns": successful_patterns.get(
                        "prompt_patterns", {}
                    ),
                    "most_successful_chart_types": successful_patterns.get(
                        "chart_type_success", {}
                    ),
                },
                "recommendations": [],
                "recent_activity": [
                    {
                        "timestamp": entry.get("timestamp"),
                        "chart_count": entry.get("chart_count", 0),
                        "chart_types": entry.get("chart_types", []),
                        "memory_type": entry.get("memory_type"),
                    }
                    for entry in recent_charts
                ],
            }

            # Generate personalized recommendations
            chart_distribution = memory_stats.get("chart_type_distribution", {})
            if chart_distribution:
                # Suggest diversity if user overuses certain types
                max_used = max(chart_distribution.items(), key=lambda x: x[1])
                if max_used[1] > 3:
                    insights["recommendations"].append(
                        f"Consider trying chart types other than {max_used[0]} for more diverse visualizations"
                    )

                # Suggest underused chart types
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
                unused_types = [t for t in all_types if t not in chart_distribution][:3]
                if unused_types:
                    insights["recommendations"].append(
                        f"Try exploring {', '.join(unused_types)} charts for new visualization perspectives"
                    )
            else:
                insights["recommendations"].append(
                    "Start generating more charts to establish your preferences and get personalized recommendations"
                )

            return insights

        except Exception as e:
            logger.error(f"Error getting user chart insights: {e}")
            return {"error": str(e), "session_id": session_id}


# Global instance for easy access
dynamic_chart_agent = DynamicChartAgent()


async def process_dynamic_request(
    user_prompt: str,
    session_id: str,
    existing_charts: Optional[List[Dict]] = None,
    previous_analysis_data: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Convenience function to process dynamic chart/data requests.

    Args:
        user_prompt: User's natural language request
        session_id: Session identifier
        existing_charts: Previously generated charts
        previous_analysis_data: Previous analysis data

    Returns:
        Dict containing results based on user request
    """
    return await dynamic_chart_agent.process_user_request(
        user_prompt, session_id, existing_charts, previous_analysis_data
    )
