import asyncio
import json
import logging
import os
from typing import Dict, List, Optional


from langdetect import LangDetectException, detect
from agents.ollama_api import OllamaQwen3Client

# Configure logging
logger = logging.getLogger("summarization_agent")




class SummarizationAgent:
    """
    An intelligent agent for summarizing crawled website content and extracting business information.
    Uses Ollama Qwen3 for all LLM-based summarization. Supports English, French, and Arabic languages and focuses on content-only processing.
    """

    def __init__(self):
        self.allowed_languages = {"en", "fr", "ar"}
        self.max_content_length = 8000
        self.ollama_client = OllamaQwen3Client()

    async def summarize_crawled_data(
        self, crawled_data: dict, company_name: str
    ) -> dict:
        """
        Summarizes crawled data from a single company and extracts key business information.
        Only processes content in English, French, or Arabic languages.

        Args:
            crawled_data: Dictionary containing crawled website data
            company_name: Name of the company being analyzed

        Returns:
            Dictionary containing structured business summary or error information
        """
        if not crawled_data or "error" in crawled_data:
            return {"error": "No valid crawled data to summarize"}

        # Prepare the data for summarization - focus only on "content" field
        content_to_analyze = ""
        page_count = 0
        total_removed_stopwords = 0
        skipped_pages = 0

        for url, page_data in crawled_data.items():
            if isinstance(page_data, dict) and "content" in page_data:
                page_content = page_data.get("content", "")

                # Skip empty content
                if not page_content.strip():
                    continue

                # Detect language and filter
                try:
                    detected_lang = detect(page_content)
                except LangDetectException:
                    detected_lang = page_data.get("detected_language", "unknown")

                # Only process content in allowed languages
                if detected_lang in self.allowed_languages:
                    content_to_analyze += f"\n--- Page {page_count + 1} ({url}) [Language: {detected_lang}] ---\n"
                    content_to_analyze += page_content

                    # Track stopword removal stats
                    if "removed_stopwords_count" in page_data:
                        total_removed_stopwords += page_data.get(
                            "removed_stopwords_count", 0
                        )

                    page_count += 1
                else:
                    skipped_pages += 1
                    logger.info(
                        f"[summarize] Skipped page {url} (language: {detected_lang}) for {company_name}"
                    )

        if not content_to_analyze.strip():
            return {
                "error": "No valid content found to summarize in supported languages (English, French, Arabic)",
                "skipped_pages": skipped_pages,
                "supported_languages": list(self.allowed_languages),
            }

        # Limit content length to avoid token limits while preserving important information
        if len(content_to_analyze) > self.max_content_length:
            # Take first part and last part to capture intro and conclusion
            first_part = content_to_analyze[: self.max_content_length // 2]
            last_part = content_to_analyze[-(self.max_content_length // 2) :]
            content_to_analyze = (
                first_part
                + "\n\n... [content truncated for length] ...\n\n"
                + last_part
            )

        # Generate the summary using LLM
        try:
            summary = await self._generate_business_summary(
                content_to_analyze, company_name, page_count
            )

            # Add metadata about the analysis
            summary["analysis_metadata"] = {
                "pages_analyzed": page_count,
                "pages_skipped": skipped_pages,
                "supported_languages": list(self.allowed_languages),
                "total_content_length": len(content_to_analyze),
                "total_stopwords_removed": total_removed_stopwords,
                "content_sources": "website_content_only",  # Only using content field
                "analysis_timestamp": json.dumps({"timestamp": "auto-generated"}),
            }

            logger.info(
                f"[summarize] Successfully summarized {page_count} pages for {company_name} "
                f"(skipped: {skipped_pages}, confidence: {summary.get('summary_confidence', 'unknown')}, "
                f"quality: {summary.get('content_quality', 'unknown')})"
            )
            return summary

        except Exception as e:
            logger.error(f"[summarize] Summarization failed for {company_name}: {e}")
            return {
                "error": f"Summarization failed: {str(e)}",
                "analysis_metadata": {
                    "pages_analyzed": page_count,
                    "pages_skipped": skipped_pages,
                    "supported_languages": list(self.allowed_languages),
                    "total_content_length": len(content_to_analyze),
                    "total_stopwords_removed": total_removed_stopwords,
                    "content_sources": "website_content_only",
                },
            }

    async def _generate_business_summary(
        self, content: str, company_name: str, page_count: int
    ) -> dict:
        """
        Generate business summary using Ollama Qwen3 LLM analysis.
        """
        summarization_prompt = (
            f"You are a business intelligence analyst. Analyze the following website content for {company_name} and extract ONLY the most relevant business information. "
            f"The content is from {page_count} pages in supported languages (English, French, Arabic). "
            "Return a concise JSON object with the following structure. Only include information that is clearly stated or strongly implied:\n\n"
            "{\n"
            '  "company_overview": "Concise company description (max 150 words)",\n'
            '  "main_products_services": ["Primary products/services only"],\n'
            '  "target_markets": ["Main industries/markets served"],\n'
            '  "key_technologies": ["Technologies explicitly mentioned"],\n'
            '  "business_model": "Core business model if clear",\n'
            '  "competitive_advantages": ["Key differentiators mentioned"],\n'
            '  "geographic_presence": ["Countries/regions explicitly mentioned"],\n'
            '  "partnerships": ["Major partners/clients mentioned by name"],\n'
            '  "financial_info": "Revenue/funding/financial data if mentioned",\n'
            '  "recent_developments": ["Recent news/announcements if any"],\n'
            '  "contact_locations": "Office locations or headquarters",\n'
            '  "key_achievements": ["Awards, certifications, major milestones"],\n'
            '  "content_quality": "high/medium/low - how informative was the content",\n'
            '  "summary_confidence": "high/medium/low - confidence in extracted data"\n'
            "}\n\n"
            "IMPORTANT RULES:\n"
            "- Only extract facts explicitly stated in the content\n"
            "- Use empty strings for missing text fields, empty arrays for missing lists\n"
            "- Prioritize recent and specific information over generic statements\n"
            "- If content is in multiple languages, synthesize information from all\n"
            f"Website content to analyze:\n{content}\n"
            "Return only valid JSON with no additional text:"
        )

        response = await asyncio.to_thread(self.ollama_client.generate, summarization_prompt)
        raw_text = response.strip()

        # Extract JSON from response
        if "```json" in raw_text:
            json_start = raw_text.find("```json") + len("```json")
            json_end = raw_text.rfind("```")
            json_str = raw_text[json_start:json_end].strip()
        else:
            json_str = raw_text

        return json.loads(json_str)

    def generate_competitors_overview(self, competitors_data: List[dict]) -> dict:
        """
        Generates a high-level overview of all analyzed competitors.

        Args:
            competitors_data: List of competitor data with business summaries

        Returns:
            Dictionary containing aggregated competitor analysis
        """
        overview = {
            "total_competitors": len(competitors_data),
            "successfully_analyzed": 0,
            "failed_analysis": 0,
            "main_business_domains": [],
            "geographic_coverage": [],
            "common_technologies": [],
            "analysis_summary": [],
        }

        for competitor in competitors_data:
            if (
                "business_summary" in competitor
                and "error" not in competitor["business_summary"]
            ):
                overview["successfully_analyzed"] += 1
                summary = competitor["business_summary"]

                # Collect business domains
                if "target_markets" in summary:
                    overview["main_business_domains"].extend(summary["target_markets"])

                # Collect geographic presence
                if "geographic_presence" in summary:
                    overview["geographic_coverage"].extend(
                        summary["geographic_presence"]
                    )

                # Collect technologies
                if "key_technologies" in summary:
                    overview["common_technologies"].extend(summary["key_technologies"])

                # Create brief summary for each competitor
                overview["analysis_summary"].append(
                    {
                        "company": competitor.get("company", "Unknown"),
                        "overview": (
                            summary.get("company_overview", "")[:150] + "..."
                            if len(summary.get("company_overview", "")) > 150
                            else summary.get("company_overview", "")
                        ),
                        "confidence": summary.get("summary_confidence", "unknown"),
                        "content_quality": summary.get("content_quality", "unknown"),
                        "pages_processed": summary.get("analysis_metadata", {}).get(
                            "pages_analyzed", 0
                        ),
                    }
                )
            else:
                overview["failed_analysis"] += 1

        # Remove duplicates and clean up
        overview["main_business_domains"] = list(
            set([domain for domain in overview["main_business_domains"] if domain])
        )
        overview["geographic_coverage"] = list(
            set([region for region in overview["geographic_coverage"] if region])
        )
        overview["common_technologies"] = list(
            set([tech for tech in overview["common_technologies"] if tech])
        )

        return overview


# Create a global instance for easy import
summarization_agent = SummarizationAgent()
