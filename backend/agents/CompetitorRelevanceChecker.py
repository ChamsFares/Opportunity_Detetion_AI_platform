import asyncio
import hashlib
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from agents.ollama_api import OllamaQwen3Client


class CompetitorRelevanceChecker:
    def __init__(self):
        self.client = OllamaQwen3Client()
        
        # Performance optimizations
        self._cache = {}  # Simple in-memory cache for results
        self._content_summaries = {}  # Cache for content summaries
        self._batch_size = 5  # Process multiple pages in one API call
        self._max_content_length = 2500  # Reduced content size for faster processing
        
    def _get_content_hash(self, content: str) -> str:
        """Generate hash for content caching"""
        return hashlib.md5(content.encode()).hexdigest()[:16]
        
    def _summarize_content(self, content: str) -> str:
        """Extract key information from content for faster processing"""
        # Cache check
        content_hash = self._get_content_hash(content)
        if content_hash in self._content_summaries:
            return self._content_summaries[content_hash]
        
        # Extract key sections more efficiently
        content_lower = content.lower()
        
        # Look for key business terms and sections
        key_sections = []
        
        # Find service/product mentions
        service_keywords = ['service', 'solution', 'product', 'offering', 'expertise', 'consulting']
        for keyword in service_keywords:
            start = content_lower.find(keyword)
            if start != -1:
                # Extract surrounding context (100 chars before/after)
                section_start = max(0, start - 100)
                section_end = min(len(content), start + 200)
                key_sections.append(content[section_start:section_end])
        
        # Look for company description sections
        desc_keywords = ['about us', 'who we are', 'our mission', 'what we do', 'company']
        for keyword in desc_keywords:
            start = content_lower.find(keyword)
            if start != -1:
                section_start = max(0, start - 50)
                section_end = min(len(content), start + 300)
                key_sections.append(content[section_start:section_end])
        
        # If no key sections found, take the beginning
        if not key_sections:
            key_sections.append(content[:500])
        
        # Combine and limit
        summarized = ' '.join(key_sections)[:self._max_content_length]
        
        # Cache the result
        self._content_summaries[content_hash] = summarized
        return summarized

    async def check_page_relevance_fast(
        self, sector: str, service: str, url: str, content: str
    ) -> Dict[str, Any]:
        """
        Optimized version with caching and content summarization
        """
        # Check cache first
        cache_key = f"{sector}_{service}_{self._get_content_hash(content)}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Use summarized content for faster processing
        summarized_content = self._summarize_content(content)
        domain = urlparse(url).netloc

        # Simplified prompt for faster processing
        prompt = f"""
You are an expert competitive intelligence analyst. Analyze the following website content to determine its relevance to our target business context.

TARGET BUSINESS CONTEXT:
- Sector: {sector}
- Service: {service}
- Domain: {domain}

CONTENT TO ANALYZE:
{summarized_content}

EVALUATION CRITERIA:
- Is this company operating in the same or adjacent sector?
- Do they offer similar or competing services?
- Could they target the same customer base?
- Are they a potential strategic threat or opportunity?

RESPONSE FORMAT (JSON):
{{
    "is_relevant": true/false,
    "relevance_score": 0-100,
    "sector_match": true/false,
    "service_match": true/false,
    "content_type": "about_us|service_page|product_page|news|other",
    "relevance_reason": "Brief explanation of relevance assessment"
}}

Provide only the JSON response, no additional text.
"""

        try:
            # Use Ollama for the analysis
            response = self.client.generate(prompt)

            # Try to parse JSON response from Ollama
            try:
                result = json.loads(response)
            except json.JSONDecodeError:
                # If not valid JSON, try to extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group())
                    except json.JSONDecodeError:
                        result = None
                else:
                    result = None

            if result:
                # Add metadata
                result["metadata"] = {
                    "url": url,
                    "domain": domain,
                    "analysis_timestamp": datetime.now().isoformat(),
                    "analysis_successful": True,
                    "content_length": len(content),
                    "processing_time": "fast",
                    "api_status": "success"
                }
                
                # Cache the result
                self._cache[cache_key] = result
                return result
            else:
                return self._create_fallback_result(sector, service, url, content, "Could not parse response")
                
        except Exception as e:
            error_msg = str(e)
            print(f"⚠️  API error for {urlparse(url).netloc}: {error_msg}")
            return self._create_fallback_result(sector, service, url, content, error_msg)

    def _create_fallback_result(
        self, sector: str, service: str, url: str, content: str, error: str
    ) -> Dict[str, Any]:
        """Create a fallback result when API call fails"""
        return {
            "is_relevant": False,
            "relevance_score": 0.0,
            "sector_match": False,
            "service_match": False,
            "content_type": "other",
            "relevance_reason": f"Analysis failed: {error}",
            "error": error,
            "metadata": {
                "url": url,
                "domain": urlparse(url).netloc,
                "sector": sector,
                "service": service,
                "content_length": len(content),
                "analysis_timestamp": datetime.now().isoformat(),
                "analysis_successful": False,
                "api_status": "error"
            },
        }
        
    async def batch_analyze_competitors_fast(
        self,
        sector: str,
        service: str,
        competitor_data: List[Dict[str, str]],
        min_relevance_score: float = 0.6,
        delay_between_calls: float = 0.3,  # Reduced delay
    ) -> Dict[str, Any]:
        """
        Optimized batch analysis with parallel processing and caching
        """
        print(f"� Starting optimized batch analysis of {len(competitor_data)} competitor pages")
        print(f"🎯 Target: {sector} - {service}")
        print("=" * 60)

        results = {
            "relevant_pages": [],
            "irrelevant_pages": [],
            "analysis_summary": {
                "total_analyzed": 0,
                "relevant_count": 0,
                "irrelevant_count": 0,
                "error_count": 0,
                "average_relevance_score": 0.0,
                "content_types": {},
                "domains_analyzed": set(),
                "processing_time": 0.0,
                "cache_hits": 0,
            },
            "errors": [],
        }

        start_time = time.time()
        total_relevance_score = 0.0

        # Filter out invalid data
        valid_data = [
            page for page in competitor_data 
            if page.get("url") and page.get("content")
        ]

        # Process using async concurrency instead of ThreadPoolExecutor
        # Create tasks for all analyses
        tasks = []
        for page_data in valid_data:
            url = page_data["url"]
            content = page_data["content"]
            # Create a task for each analysis
            task = asyncio.create_task(
                self.check_page_relevance_fast(sector, service, url, content)
            )
            task.page_data = page_data  # Store page data for reference
            tasks.append(task)

        # Execute all tasks concurrently
        try:
            # Wait for all tasks to complete
            completed_analyses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(completed_analyses):
                page_data = tasks[i].page_data
                url = page_data["url"]
                
                try:
                    if isinstance(result, Exception):
                        # Handle exception
                        print(f"❌ Error analyzing {url}: {str(result)}")
                        results["analysis_summary"]["error_count"] += 1
                        results["errors"].append({"url": url, "error": str(result)})
                        continue
                    
                    analysis = result
                    
                    # Check if it was a cache hit
                    if analysis.get("metadata", {}).get("processing_time") == "fast":
                        results["analysis_summary"]["cache_hits"] += 1

                    # Update results
                    results["analysis_summary"]["total_analyzed"] += 1
                    total_relevance_score += analysis.get("relevance_score", 0.0)

                    # Track domain
                    domain = urlparse(url).netloc
                    results["analysis_summary"]["domains_analyzed"].add(domain)

                    # Track content type
                    content_type = analysis.get("content_type", "other")
                    results["analysis_summary"]["content_types"][content_type] = (
                        results["analysis_summary"]["content_types"].get(content_type, 0) + 1
                    )

                    # Check if relevant
                    if (analysis.get("is_relevant", False) and 
                        analysis.get("relevance_score", 0) >= min_relevance_score):
                        
                        results["relevant_pages"].append(analysis)
                        results["analysis_summary"]["relevant_count"] += 1
                        print(f"✅ RELEVANT: {domain} (Score: {analysis.get('relevance_score', 0):.2f})")
                    else:
                        results["irrelevant_pages"].append(analysis)
                        results["analysis_summary"]["irrelevant_count"] += 1
                        print(f"❌ NOT RELEVANT: {domain} (Score: {analysis.get('relevance_score', 0):.2f})")

                    # Handle errors
                    if "error" in analysis:
                        results["analysis_summary"]["error_count"] += 1
                        results["errors"].append({"url": url, "error": analysis["error"]})

                except Exception as e:
                    print(f"❌ Error processing analysis for {url}: {str(e)}")
                    results["analysis_summary"]["error_count"] += 1
                    results["errors"].append({"url": url, "error": str(e)})

                # Small delay to avoid overwhelming the API (optional, since we have rate limiting)
                if delay_between_calls > 0:
                    await asyncio.sleep(delay_between_calls / len(valid_data))  # Spread delay across all items

        except Exception as e:
            print(f"❌ Critical error in batch analysis: {str(e)}")
            results["errors"].append({"error": f"Batch analysis failed: {str(e)}"})
            results["analysis_summary"]["error_count"] += len(valid_data)

        # Calculate final metrics
        processing_time = time.time() - start_time
        results["analysis_summary"]["processing_time"] = processing_time

        if results["analysis_summary"]["total_analyzed"] > 0:
            results["analysis_summary"]["average_relevance_score"] = (
                total_relevance_score / results["analysis_summary"]["total_analyzed"]
            )

        # Convert sets to lists for JSON serialization
        results["analysis_summary"]["domains_analyzed"] = list(
            results["analysis_summary"]["domains_analyzed"]
        )

        print(f"\n🎯 Analysis Complete!")
        print(f"⏱️ Processing time: {processing_time:.2f} seconds")
        print(f"📊 Relevant pages: {results['analysis_summary']['relevant_count']}")
        print(f"🚀 Cache hits: {results['analysis_summary']['cache_hits']}")

        return results

    # Keep the original method for backward compatibility
    async def batch_analyze_competitors(self, *args, **kwargs):
        """Backward compatibility wrapper - uses the fast version"""
        return await self.batch_analyze_competitors_fast(*args, **kwargs)

    def clear_cache(self):
        """Clear the internal cache to free memory"""
        self._cache.clear()
        self._content_summaries.clear()
        print("🧹 Cache cleared")
        
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            "cache_size": len(self._cache),
            "summary_cache_size": len(self._content_summaries)
        }
