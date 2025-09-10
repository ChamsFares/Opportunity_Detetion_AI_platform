"""
Enhanced Data Storage Service for MCP Backend
Centralized MongoDB and ChromaDB storage with data cleaning and embedding generation.
Integrates with MCP tools for comprehensive data management.
"""

import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from db.mongo import db_manager
from utils.crawled_info_saver import (
    generate_embedding,
    generate_embeddings_batch,
    get_or_create_chroma_collection,
    store_embedding_in_chroma,
)
from utils.logger import get_logger

logger = get_logger("data_storage_service")


class DataStorageService:
    """
    MCP-compatible centralized service for storing and managing analysis data.
    Handles MongoDB and ChromaDB operations with embedding generation.
    """

    def __init__(self):
        self.chroma_collections = {}
        self.batch_size = 10  # For batch processing
        self.max_retries = 3  # For error resilience

    async def store_extracted_info(
        self,
        extracted_info: Dict[str, Any],
        session_id: str,
        is_confirmation: bool = False,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Store extracted business information with validation and embedding.

        Args:
            extracted_info: Business information extracted from prompts/files
            session_id: Session identifier
            is_confirmation: Whether this is confirmed information
            progress_callback: Optional progress callback

        Returns:
            Dict with storage results
        """
        try:
            if progress_callback:
                progress_callback({
                    "step": "storing_extracted_info",
                    "message": "💾 Storing extracted business information...",
                    "phase": "data_storage",
                })

            # Add metadata
            document = {
                **extracted_info,
                "session_id": session_id,
                "is_confirmation": is_confirmation,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "data_source": "info_extraction",
                "validation_status": "confirmed" if is_confirmation else "extracted"
            }

            # Choose collection based on confirmation status
            collection_name = "confirmed_infos" if is_confirmation else "extracted_infos"
            collection = getattr(db_manager.database, collection_name)

            # Store in MongoDB
            result = await collection.insert_one(document)
            mongo_id = str(result.inserted_id)

            # Generate embedding for semantic search
            embedding_result = await self._generate_and_store_business_embedding(
                document, mongo_id
            )

            logger.info(
                f"✅ Stored {'confirmed' if is_confirmation else 'extracted'} info for session {session_id}"
            )

            return {
                "success": True,
                "mongo_id": mongo_id,
                "session_id": session_id,
                "embedding_success": embedding_result.get("success", False),
                "collection": collection_name,
                "is_confirmation": is_confirmation
            }

        except Exception as e:
            logger.error(f"❌ Error storing extracted info: {e}")
            return {"success": False, "error": str(e)}

    async def clean_and_store_competitor_data(
        self, 
        competitor_data: Dict, 
        analysis_session: str,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Clean competitor data and store in MongoDB with embeddings in ChromaDB.

        Args:
            competitor_data: Raw competitor data from scraping
            analysis_session: Analysis session identifier
            progress_callback: Optional progress callback function

        Returns:
            Dict with storage results
        """
        try:
            if progress_callback:
                progress_callback({
                    "step": "cleaning_competitor_data",
                    "message": "🧹 Cleaning and structuring competitor data...",
                    "phase": "data_storage",
                })

            cleaned_data = await self._clean_competitor_data(competitor_data, analysis_session)

            if progress_callback:
                progress_callback({
                    "step": "storing_competitor_data",
                    "message": f"💾 Storing {len(cleaned_data)} competitors in database...",
                    "phase": "data_storage",
                })

            # Store in MongoDB with batch processing
            collection = db_manager.database.competitors
            storage_results = []

            for i in range(0, len(cleaned_data), self.batch_size):
                batch = cleaned_data[i:i + self.batch_size]
                
                for company_data in batch:
                    try:
                        # Upsert competitor data
                        result = await collection.update_one(
                            {
                                "company_name": company_data["company_name"],
                                "analysis_session": company_data.get("analysis_session"),
                            },
                            {
                                "$set": {
                                    **company_data,
                                    "updated_at": datetime.now(timezone.utc),
                                }
                            },
                            upsert=True,
                        )

                        # Generate and store embedding
                        embedding_result = await self._generate_and_store_competitor_embedding(
                            company_data,
                            str(result.upserted_id) if result.upserted_id else None,
                        )

                        storage_results.append({
                            "company_name": company_data["company_name"],
                            "mongo_success": True,
                            "embedding_success": embedding_result.get("success", False),
                            "mongo_id": (
                                str(result.upserted_id)
                                if result.upserted_id
                                else "updated"
                            ),
                        })

                    except Exception as e:
                        logger.error(
                            f"Error storing competitor {company_data.get('company_name', 'unknown')}: {e}"
                        )
                        storage_results.append({
                            "company_name": company_data.get("company_name", "unknown"),
                            "mongo_success": False,
                            "embedding_success": False,
                            "error": str(e),
                        })

            successful_stores = sum(1 for r in storage_results if r["mongo_success"])
            successful_embeddings = sum(1 for r in storage_results if r["embedding_success"])

            logger.info(
                f"✅ Stored {successful_stores}/{len(cleaned_data)} competitors, {successful_embeddings} embeddings"
            )

            return {
                "success": True,
                "total_competitors": len(cleaned_data),
                "successful_stores": successful_stores,
                "successful_embeddings": successful_embeddings,
                "storage_results": storage_results,
                "analysis_session": analysis_session
            }

        except Exception as e:
            logger.error(f"❌ Error in competitor data storage: {e}")
            return {"success": False, "error": str(e)}

    async def clean_and_store_news_data(
        self,
        news_data: Dict,
        keywords: List[str],
        analysis_session: str,
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Clean news data and store in MongoDB with embeddings in ChromaDB.

        Args:
            news_data: Raw news data from extraction
            keywords: Keywords used for news extraction
            analysis_session: Unique session identifier
            progress_callback: Optional progress callback function

        Returns:
            Dict with storage results
        """
        try:
            if progress_callback:
                progress_callback({
                    "step": "cleaning_news_data",
                    "message": "📰 Cleaning and categorizing news articles...",
                    "phase": "data_storage",
                })

            cleaned_articles = await self._clean_news_data(
                news_data, keywords, analysis_session
            )

            if progress_callback:
                progress_callback({
                    "step": "storing_news_data",
                    "message": f"💾 Storing {len(cleaned_articles)} news articles...",
                    "phase": "data_storage",
                })

            # Store in MongoDB with deduplication
            collection = db_manager.database.market_news
            storage_results = []

            for article in cleaned_articles:
                try:
                    # Check for existing article (deduplication)
                    existing = await collection.find_one({
                        "title": article["title"],
                        "source": article.get("source")
                    })

                    if existing:
                        # Update existing article with new analysis session
                        await collection.update_one(
                            {"_id": existing["_id"]},
                            {
                                "$addToSet": {"analysis_sessions": analysis_session},
                                "$set": {"updated_at": datetime.now(timezone.utc)},
                            },
                        )
                        storage_results.append({
                            "title": article["title"],
                            "action": "updated",
                            "mongo_success": True,
                        })
                    else:
                        # Insert new article
                        result = await collection.insert_one(article)

                        # Generate and store embedding
                        embedding_result = await self._generate_and_store_news_embedding(
                            article, str(result.inserted_id)
                        )

                        storage_results.append({
                            "title": article["title"],
                            "action": "created",
                            "mongo_success": True,
                            "embedding_success": embedding_result.get("success", False),
                            "mongo_id": str(result.inserted_id),
                        })

                except Exception as e:
                    logger.error(
                        f"Error storing news article {article.get('title', 'unknown')}: {e}"
                    )
                    storage_results.append({
                        "title": article.get("title", "unknown"),
                        "mongo_success": False,
                        "embedding_success": False,
                        "error": str(e),
                    })

            successful_stores = sum(1 for r in storage_results if r["mongo_success"])
            successful_embeddings = sum(
                1 for r in storage_results if r.get("embedding_success", False)
            )

            logger.info(
                f"✅ Processed {successful_stores}/{len(cleaned_articles)} news articles, {successful_embeddings} embeddings"
            )

            return {
                "success": True,
                "total_articles": len(cleaned_articles),
                "successful_stores": successful_stores,
                "successful_embeddings": successful_embeddings,
                "storage_results": storage_results,
                "analysis_session": analysis_session
            }

        except Exception as e:
            logger.error(f"❌ Error in news data storage: {e}")
            return {"success": False, "error": str(e)}

    async def clean_and_store_trends_data(
        self,
        trends_data: Dict,
        analysis_session: str,
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Clean trends data and store in MongoDB with embeddings in ChromaDB.

        Args:
            trends_data: Raw trends data from analysis
            analysis_session: Unique session identifier
            progress_callback: Optional progress callback function

        Returns:
            Dict with storage results
        """
        try:
            if progress_callback:
                progress_callback({
                    "step": "cleaning_trends_data",
                    "message": "📈 Processing and structuring trend insights...",
                    "phase": "data_storage",
                })

            cleaned_trends = await self._clean_trends_data(trends_data, analysis_session)

            if progress_callback:
                progress_callback({
                    "step": "storing_trends_data",
                    "message": f"💾 Storing {len(cleaned_trends)} trend insights...",
                    "phase": "data_storage",
                })

            # Store in MongoDB
            collection = db_manager.database.market_trends
            storage_results = []

            for trend in cleaned_trends:
                try:
                    result = await collection.insert_one(trend)

                    # Generate and store embedding
                    embedding_result = await self._generate_and_store_trend_embedding(
                        trend, str(result.inserted_id)
                    )

                    storage_results.append({
                        "trend_category": trend.get("category", "unknown"),
                        "mongo_success": True,
                        "embedding_success": embedding_result.get("success", False),
                        "mongo_id": str(result.inserted_id),
                    })

                except Exception as e:
                    logger.error(f"Error storing trend {trend.get('category', 'unknown')}: {e}")
                    storage_results.append({
                        "trend_category": trend.get("category", "unknown"),
                        "mongo_success": False,
                        "embedding_success": False,
                        "error": str(e),
                    })

            successful_stores = sum(1 for r in storage_results if r["mongo_success"])
            successful_embeddings = sum(1 for r in storage_results if r["embedding_success"])

            logger.info(
                f"✅ Stored {successful_stores}/{len(cleaned_trends)} trends, {successful_embeddings} embeddings"
            )

            return {
                "success": True,
                "total_trends": len(cleaned_trends),
                "successful_stores": successful_stores,
                "successful_embeddings": successful_embeddings,
                "storage_results": storage_results,
                "analysis_session": analysis_session
            }

        except Exception as e:
            logger.error(f"❌ Error in trends data storage: {e}")
            return {"success": False, "error": str(e)}

    async def store_final_analysis(
        self,
        analysis_data: Dict,
        analysis_session: str,
        company: str,
        sector: str,
        service: str,
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Store final comprehensive analysis with embeddings.

        Args:
            analysis_data: Final analysis results
            analysis_session: Unique session identifier
            company: Company name
            sector: Industry sector
            service: Service type
            progress_callback: Optional progress callback function

        Returns:
            Dict with storage results
        """
        try:
            if progress_callback:
                progress_callback({
                    "step": "storing_final_analysis",
                    "message": "📊 Storing comprehensive market analysis...",
                    "phase": "data_storage",
                })

            # Prepare final analysis document
            final_doc = {
                "analysis_session": analysis_session,
                "company": company,
                "sector": sector,
                "service": service,
                "analysis_data": analysis_data,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "data_size": len(str(analysis_data)),
                "analysis_type": "comprehensive_market_analysis",
                "mcp_version": "1.0",  # Track MCP backend version
                "processing_metadata": {
                    "storage_timestamp": datetime.now(timezone.utc).isoformat(),
                    "data_categories": list(analysis_data.keys()) if isinstance(analysis_data, dict) else [],
                    "analysis_complexity": "comprehensive" if len(str(analysis_data)) > 10000 else "standard"
                }
            }

            # Store in MongoDB
            collection = db_manager.database.market_analyses
            result = await collection.insert_one(final_doc)
            mongo_id = str(result.inserted_id)

            # Generate comprehensive summary for embedding
            summary_text = await self._create_analysis_summary(
                analysis_data, company, sector, service
            )

            # Generate and store embedding
            embedding_result = await self._generate_and_store_analysis_embedding(
                final_doc, mongo_id, summary_text
            )

            logger.info(f"✅ Stored final analysis for {company} (ID: {mongo_id})")

            return {
                "success": True,
                "mongo_id": mongo_id,
                "analysis_session": analysis_session,
                "embedding_success": embedding_result.get("success", False),
                "data_size": final_doc["data_size"],
                "company": company,
                "sector": sector,
                "service": service
            }

        except Exception as e:
            logger.error(f"❌ Error storing final analysis: {e}")
            return {"success": False, "error": str(e)}

    async def store_chart_data(
        self,
        charts: List[Dict],
        session_id: str,
        user_id: Optional[str] = None,
        generation_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Store generated chart data with metadata.

        Args:
            charts: List of chart configurations
            session_id: Session identifier
            user_id: Optional user identifier
            generation_context: Optional context about chart generation

        Returns:
            Dict with storage results
        """
        try:
            document = {
                "session_id": session_id,
                "user_id": user_id,
                "charts": charts,
                "chart_count": len(charts),
                "generation_context": generation_context or {},
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "data_source": "chart_generation",
                "mcp_version": "1.0"
            }

            collection = db_manager.database.charts
            result = await collection.insert_one(document)

            logger.info(f"✅ Stored {len(charts)} charts for session {session_id}")

            return {
                "success": True,
                "mongo_id": str(result.inserted_id),
                "session_id": session_id,
                "chart_count": len(charts)
            }

        except Exception as e:
            logger.error(f"❌ Error storing chart data: {e}")
            return {"success": False, "error": str(e)}

    # Private helper methods for data cleaning and processing
    async def _clean_competitor_data(self, competitor_data: Dict, analysis_session: str) -> List[Dict]:
        """Clean and structure competitor data."""
        cleaned_competitors = []
        current_time = datetime.now(timezone.utc)

        if isinstance(competitor_data, dict) and "relevant_pages" in competitor_data:
            relevant_pages = competitor_data["relevant_pages"]

            for page in relevant_pages:
                if isinstance(page, dict):
                    cleaned_competitor = {
                        "company_name": page.get("company_name", "Unknown"),
                        "website_url": page.get("url", ""),
                        "relevance_score": page.get("relevance_score", 0),
                        "business_summary": page.get("business_summary", {}),
                        "competitive_analysis": page.get("competitive_analysis", {}),
                        "market_position": page.get("market_position", ""),
                        "key_offerings": page.get("key_offerings", []),
                        "target_markets": page.get("target_markets", []),
                        "analysis_session": analysis_session,
                        "created_at": current_time,
                        "updated_at": current_time,
                        "data_source": "competitor_analysis",
                        "mcp_processed": True
                    }
                    cleaned_competitors.append(cleaned_competitor)

        return cleaned_competitors

    async def _clean_news_data(
        self, news_data: Dict, keywords: List[str], analysis_session: str
    ) -> List[Dict]:
        """Clean and structure news data."""
        cleaned_articles = []
        current_time = datetime.now(timezone.utc)

        # Handle different news data structures
        articles = []
        if isinstance(news_data, dict):
            if "articles" in news_data:
                articles = news_data["articles"]
            elif "news" in news_data:
                articles = news_data["news"]
            else:
                # Treat the entire dict as a collection of articles
                for key, value in news_data.items():
                    if isinstance(value, list):
                        articles.extend(value)
                    elif isinstance(value, dict):
                        articles.append(value)
        elif isinstance(news_data, list):
            articles = news_data

        for article in articles:
            if isinstance(article, dict):
                cleaned_article = {
                    "title": article.get("title", ""),
                    "content": article.get("content", article.get("description", "")),
                    "source": article.get("source", ""),
                    "url": article.get("url", ""),
                    "published_date": article.get("published_date", article.get("publishedAt")),
                    "keywords_matched": keywords,
                    "analysis_sessions": [analysis_session],
                    "relevance_score": article.get("relevance_score"),
                    "sentiment": article.get("sentiment"),
                    "category": self._categorize_news_article(article, keywords),
                    "created_at": current_time,
                    "updated_at": current_time,
                    "data_source": "news_extraction",
                    "mcp_processed": True
                }

                # Only add articles with meaningful content
                if cleaned_article["title"] and (
                    cleaned_article["content"] or cleaned_article["url"]
                ):
                    cleaned_articles.append(cleaned_article)

        return cleaned_articles

    async def _clean_trends_data(self, trends_data: Dict, analysis_session: str) -> List[Dict]:
        """Clean and structure trends data."""
        cleaned_trends = []
        current_time = datetime.now(timezone.utc)

        # Handle different trends data structures
        if isinstance(trends_data, dict):
            for trend_category, trend_info in trends_data.items():
                if isinstance(trend_info, dict):
                    cleaned_trend = {
                        "category": trend_category,
                        "description": trend_info.get("description", ""),
                        "impact_level": trend_info.get("impact_level", "medium"),
                        "confidence_score": trend_info.get("confidence_score", 0.5),
                        "supporting_evidence": trend_info.get("supporting_evidence", []),
                        "implications": trend_info.get("implications", []),
                        "time_horizon": trend_info.get("time_horizon", "medium_term"),
                        "affected_markets": trend_info.get("affected_markets", []),
                        "analysis_session": analysis_session,
                        "created_at": current_time,
                        "updated_at": current_time,
                        "data_source": "trends_analysis",
                        "mcp_processed": True
                    }
                    cleaned_trends.append(cleaned_trend)
                elif isinstance(trend_info, list):
                    for item in trend_info:
                        if isinstance(item, dict):
                            cleaned_trend = {
                                "category": trend_category,
                                "description": item.get("description", str(item)),
                                "analysis_session": analysis_session,
                                "created_at": current_time,
                                "updated_at": current_time,
                                "data_source": "trends_analysis",
                                "mcp_processed": True
                            }
                            cleaned_trends.append(cleaned_trend)

        return cleaned_trends

    def _categorize_news_article(self, article: Dict, keywords: List[str]) -> str:
        """Categorize news article based on content and keywords."""
        title = article.get("title", "").lower()
        content = article.get("content", "").lower()

        # Define category keywords
        categories = {
            "technology": [
                "ai", "artificial intelligence", "machine learning", "blockchain",
                "cloud", "digital", "software", "tech", "innovation"
            ],
            "finance": [
                "funding", "investment", "ipo", "acquisition", "merger",
                "revenue", "financial", "capital", "venture"
            ],
            "market": [
                "market", "industry", "competition", "share", "growth",
                "expansion", "sector", "business"
            ],
            "product": [
                "product", "launch", "feature", "service", "offering",
                "innovation", "development", "release"
            ],
            "partnership": [
                "partnership", "collaboration", "alliance", "joint venture",
                "agreement", "deal", "cooperation"
            ],
            "regulatory": [
                "regulation", "compliance", "policy", "government",
                "legal", "law", "regulatory", "approval"
            ],
        }

        # Score each category
        category_scores = {}
        for category, category_keywords in categories.items():
            score = 0
            for keyword in category_keywords:
                if keyword in title:
                    score += 3  # Title matches are weighted higher
                if keyword in content:
                    score += 1
            category_scores[category] = score

        # Return category with highest score, or "general" if no clear category
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            if category_scores[best_category] > 0:
                return best_category

        return "general"

    async def _create_analysis_summary(
        self, analysis_data: Dict, company: str, sector: str, service: str
    ) -> str:
        """Create comprehensive summary for final analysis embedding."""
        summary_parts = [
            f"Market Analysis for {company} in {sector} sector providing {service} services."
        ]

        # Extract key insights from analysis data
        if isinstance(analysis_data, dict):
            # Market gaps
            if "market_gaps" in analysis_data:
                gaps = analysis_data["market_gaps"]
                if isinstance(gaps, list) and gaps:
                    summary_parts.append(
                        f"Market Gaps: {'; '.join(str(gap) for gap in gaps[:3])}"
                    )
                elif isinstance(gaps, str):
                    summary_parts.append(f"Market Gaps: {gaps}")

            # Opportunities
            if "opportunities" in analysis_data:
                opps = analysis_data["opportunities"]
                if isinstance(opps, list) and opps:
                    summary_parts.append(
                        f"Opportunities: {'; '.join(str(opp) for opp in opps[:3])}"
                    )
                elif isinstance(opps, str):
                    summary_parts.append(f"Opportunities: {opps}")

            # Competitive analysis
            if "competitive_analysis" in analysis_data:
                comp = analysis_data["competitive_analysis"]
                if isinstance(comp, dict):
                    if "key_competitors" in comp:
                        competitors = comp["key_competitors"]
                        if isinstance(competitors, list):
                            summary_parts.append(
                                f"Key Competitors: {', '.join(competitors[:5])}"
                            )

            # Market trends
            if "trends" in analysis_data:
                trends = analysis_data["trends"]
                if isinstance(trends, dict):
                    trend_summaries = []
                    for trend_category, trend_data in trends.items():
                        if isinstance(trend_data, dict) and "description" in trend_data:
                            trend_summaries.append(
                                f"{trend_category}: {trend_data['description']}"
                            )
                        elif isinstance(trend_data, str):
                            trend_summaries.append(f"{trend_category}: {trend_data}")
                    if trend_summaries:
                        summary_parts.append(
                            f"Market Trends: {'; '.join(trend_summaries[:3])}"
                        )

        return ". ".join(summary_parts)

    async def _generate_and_store_business_embedding(
        self, business_data: Dict, mongo_id: str
    ) -> Dict:
        """Generate and store embedding for business information."""
        try:
            # Create summary text for embedding
            summary_parts = [
                f"Company: {business_data.get('company_name', 'Unknown')}"
            ]

            if business_data.get("business_domain"):
                summary_parts.append(f"Domain: {business_data['business_domain']}")

            if business_data.get("unique_value_proposition"):
                summary_parts.append(f"Value Proposition: {business_data['unique_value_proposition']}")

            if business_data.get("target_audience"):
                summary_parts.append(f"Target Audience: {business_data['target_audience']}")

            if business_data.get("region_or_market"):
                summary_parts.append(f"Market: {business_data['region_or_market']}")

            summary_text = ". ".join(summary_parts)

            # Generate embedding
            embedding = await generate_embedding(summary_text)
            if not embedding:
                return {"success": False, "error": "Failed to generate embedding"}

            # Store in ChromaDB
            collection = get_or_create_chroma_collection("business_info")
            if not collection:
                return {"success": False, "error": "ChromaDB collection not available"}

            chroma_result = await store_embedding_in_chroma(
                collection=collection,
                mongo_id=mongo_id,
                summary=summary_text,
                embedding=embedding,
                company_name=business_data.get("company_name", "Unknown"),
                sector=business_data.get("business_domain", ""),
                region=business_data.get("region_or_market", ""),
                services=business_data.get("unique_value_proposition", ""),
            )

            return chroma_result

        except Exception as e:
            logger.error(f"Error generating business embedding: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_and_store_competitor_embedding(
        self, competitor_data: Dict, mongo_id: str
    ) -> Dict:
        """Generate and store embedding for competitor data."""
        try:
            # Create summary text for embedding
            summary_parts = [
                f"Company: {competitor_data.get('company_name', 'Unknown')}"
            ]

            if competitor_data.get("business_summary"):
                if isinstance(competitor_data["business_summary"], dict):
                    summary_parts.append(
                        f"Business: {str(competitor_data['business_summary'])}"
                    )
                else:
                    summary_parts.append(
                        f"Business: {competitor_data['business_summary']}"
                    )

            if competitor_data.get("key_offerings"):
                offerings = competitor_data["key_offerings"]
                if isinstance(offerings, list):
                    summary_parts.append(f"Offerings: {', '.join(offerings)}")
                else:
                    summary_parts.append(f"Offerings: {offerings}")

            if competitor_data.get("target_markets"):
                markets = competitor_data["target_markets"]
                if isinstance(markets, list):
                    summary_parts.append(f"Target Markets: {', '.join(markets)}")
                else:
                    summary_parts.append(f"Target Markets: {markets}")

            summary_text = ". ".join(summary_parts)

            # Generate embedding
            embedding = await generate_embedding(summary_text)
            if not embedding:
                return {"success": False, "error": "Failed to generate embedding"}

            # Store in ChromaDB
            collection = get_or_create_chroma_collection("competitors")
            if not collection:
                return {"success": False, "error": "ChromaDB collection not available"}

            chroma_result = await store_embedding_in_chroma(
                collection=collection,
                mongo_id=mongo_id or f"competitor_{int(time.time())}",
                summary=summary_text,
                embedding=embedding,
                company_name=competitor_data.get("company_name", "Unknown"),
                sector=competitor_data.get("market_position", ""),
                region="",
                services=", ".join(competitor_data.get("key_offerings", [])),
            )

            return chroma_result

        except Exception as e:
            logger.error(f"Error generating competitor embedding: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_and_store_news_embedding(
        self, article_data: Dict, mongo_id: str
    ) -> Dict:
        """Generate and store embedding for news article."""
        try:
            # Create summary text for embedding
            summary_text = f"Title: {article_data.get('title', '')}. Content: {article_data.get('content', '')[:500]}"

            # Generate embedding
            embedding = await generate_embedding(summary_text)
            if not embedding:
                return {"success": False, "error": "Failed to generate embedding"}

            # Store in ChromaDB
            collection = get_or_create_chroma_collection("market_news")
            if not collection:
                return {"success": False, "error": "ChromaDB collection not available"}

            chroma_result = await store_embedding_in_chroma(
                collection=collection,
                mongo_id=mongo_id,
                summary=summary_text,
                embedding=embedding,
                company_name=article_data.get("source", "Unknown Source"),
                sector=article_data.get("category", "general"),
                region="",
                services="",
            )

            return chroma_result

        except Exception as e:
            logger.error(f"Error generating news embedding: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_and_store_trend_embedding(
        self, trend_data: Dict, mongo_id: str
    ) -> Dict:
        """Generate and store embedding for trend data."""
        try:
            # Create summary text for embedding
            summary_parts = [
                f"Trend Category: {trend_data.get('category', 'Unknown')}",
                f"Description: {trend_data.get('description', '')}",
            ]

            if trend_data.get("implications"):
                implications = trend_data["implications"]
                if isinstance(implications, list):
                    summary_parts.append(f"Implications: {'; '.join(implications)}")
                else:
                    summary_parts.append(f"Implications: {implications}")

            summary_text = ". ".join(summary_parts)

            # Generate embedding
            embedding = await generate_embedding(summary_text)
            if not embedding:
                return {"success": False, "error": "Failed to generate embedding"}

            # Store in ChromaDB
            collection = get_or_create_chroma_collection("market_trends")
            if not collection:
                return {"success": False, "error": "ChromaDB collection not available"}

            chroma_result = await store_embedding_in_chroma(
                collection=collection,
                mongo_id=mongo_id,
                summary=summary_text,
                embedding=embedding,
                company_name=trend_data.get("category", "Unknown"),
                sector=trend_data.get("category", ""),
                region="",
                services="",
            )

            return chroma_result

        except Exception as e:
            logger.error(f"Error generating trend embedding: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_and_store_analysis_embedding(
        self, analysis_doc: Dict, mongo_id: str, summary_text: str
    ) -> Dict:
        """Generate and store embedding for final analysis."""
        try:
            # Generate embedding
            embedding = await generate_embedding(summary_text)
            if not embedding:
                return {"success": False, "error": "Failed to generate embedding"}

            # Store in ChromaDB
            collection = get_or_create_chroma_collection("market_analyses")
            if not collection:
                return {"success": False, "error": "ChromaDB collection not available"}

            chroma_result = await store_embedding_in_chroma(
                collection=collection,
                mongo_id=mongo_id,
                summary=summary_text,
                embedding=embedding,
                company_name=analysis_doc.get("company", "Unknown"),
                sector=analysis_doc.get("sector", ""),
                region="",
                services=analysis_doc.get("service", ""),
            )

            return chroma_result

        except Exception as e:
            logger.error(f"Error generating analysis embedding: {e}")
            return {"success": False, "error": str(e)}


# Global service instance
data_storage_service = DataStorageService()
