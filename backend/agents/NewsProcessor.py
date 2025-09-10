# Ollama-based trend identifier using Qwen3
from agents.ollama_api import OllamaQwen3Client
import asyncio
import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any, Dict, List, Optional

class OllamaTrendIdentifier:
    def __init__(self, max_workers: int = 3):
        self.client = OllamaQwen3Client()
        self.max_workers = max_workers
        self._content_cache = {}

    def _get_content_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def _summarize_content(self, text: str) -> str:
        return text

    def _analyze_hashtag(self, hashtag, news_list):
        try:
            content_parts = []
            for news_item in news_list:
                content_parts.append(news_item.get("title", ""))
                content_parts.append(news_item.get("description", ""))
            text_to_analyze = " ".join(content_parts)
            content_hash = self._get_content_hash(text_to_analyze)
            if content_hash in self._content_cache:
                cached_result = self._content_cache[content_hash]
                return {"hashtag": hashtag, "topics": cached_result}
            summarized_text = self._summarize_content(text_to_analyze)
            prompt = f"""Analyze the following text and identify the 5 main trends or most important topics. The text is about the hashtag {hashtag}. Provide a concise list of relevant topics, one per line.\n\nText: {summarized_text}\n\nMain trends:"""
            response = self.client.generate(prompt)
            topics = [
                {"topic": topic.strip()}
                for topic in response.split("\n")
                if topic.strip() and not topic.strip().startswith("*")
            ][:5]
            self._content_cache[content_hash] = topics
            if topics:
                return {"hashtag": hashtag, "topics": topics}
        except Exception as e:
            print(f"Error analyzing {hashtag}: {e}")
        return None

    def identify_trends(self, news_items: dict) -> dict:
        from concurrent.futures import ThreadPoolExecutor
        trends_output = {"trends": []}
        if not news_items:
            return trends_output
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(self._analyze_hashtag, hashtag, news_list)
                for hashtag, news_list in news_items.items() if news_list
            ]
            for future in futures:
                result = future.result()
                if isinstance(result, dict) and result:
                    trends_output["trends"].append(result)
        return trends_output



class NewsProcessor:
    def __init__(self, news_data: Dict[str, List[Dict]]):
        self.news_data = news_data
        self._date_cache = {}
        self._date_formats = (
            "%Y-%m-%dT%H:%M:%SZ",
            "%a, %d %b %Y %H:%M:%S %z",
            "%Y-%m-%d %H:%M:%S",
            "%a, %d %b %Y %H:%M:%S GMT",
        )
    @lru_cache(maxsize=1000)
    def _parse_date_cached(self, date_str: str) -> Optional[datetime]:
        """Cache date parsing results for better performance."""
        if not date_str:
            return None
        if date_str in self._date_cache:
            return self._date_cache[date_str]
        for fmt in self._date_formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                self._date_cache[date_str] = parsed_date
                return parsed_date
            except ValueError:
                continue
        self._date_cache[date_str] = None
        return None

    def parse_news(self) -> Dict[str, List[Dict]]:
        """Optimized news parsing with list comprehensions."""
        return {
            hashtag: [
                {
                    "title": news_item.get("title", ""),
                    "url": news_item.get("url", ""),
                    "description": news_item.get("description", ""),
                    "source": news_item.get("source", ""),
                    "published_date": news_item.get("published_date", ""),
                    "guid": news_item.get("guid", ""),
                }
                for news_item in news_list
            ]
            for hashtag, news_list in self.news_data.items()
        }

    def filter_old_news(self, days_threshold: int = 30) -> Dict[str, List[Dict]]:
        """Optimized news filtering with cached date parsing."""
        threshold_date = datetime.now() - timedelta(days=days_threshold)
        current_time = datetime.now()
        filtered_data = {}
        for hashtag, news_list in self.news_data.items():
            filtered_news = []
            for news_item in news_list:
                try:
                    published_date_str = news_item.get("published_date")
                    if not published_date_str:
                        continue
                    published_date = self._parse_date_cached(published_date_str)
                    if published_date and (
                        published_date >= threshold_date or published_date > current_time
                    ):
                        filtered_news.append(news_item)
                except Exception as e:
                    print(
                        f'Error processing news item: {news_item.get("title", "Unknown")} - {e}'
                    )
                    continue
            if filtered_news:
                filtered_data[hashtag] = filtered_news
        return filtered_data

    def get_cache_stats(self) -> Dict[str, int]:
        """Get statistics about the date parsing cache."""
        return {
            "cache_size": len(self._date_cache),
            "lru_cache_info": str(self._parse_date_cached.cache_info()),
        }

    def identify_trends(self):
        # This is now handled by OllamaTrendIdentifier
        pass


if __name__ == "__main__":
    # Example usage with dummy data
    dummy_data = {
        "#Blockchain": [
            {
                "title": "Blockchain révolutionne la finance",
                "url": "http://example.com/blockchain-finance",
                "description": "La technologie blockchain transforme les services financiers.",
                "source": "Finance Daily",
                "published_date": "2025-07-28T10:00:00Z",
                "guid": "1",
            },
            {
                "title": "Nouvelles applications de la blockchain",
                "url": "http://example.com/blockchain-apps",
                "description": "Exploration des cas d'utilisation innovants de la blockchain.",
                "source": "Tech Weekly",
                "published_date": "2025-06-01T12:00:00Z",
                "guid": "2",
            },
            {
                "title": "Ancienne actualité blockchain",
                "url": "http://example.com/old-blockchain",
                "description": "Un article de l'année dernière sur la blockchain.",
                "source": "Old News",
                "published_date": "2024-01-15T08:00:00Z",
                "guid": "3",
            },
        ],
        "#IA": [
            {
                "title": "L'IA dans la santé",
                "url": "http://example.com/ia-health",
                "description": "Comment l'intelligence artificielle améliore les diagnostics.",
                "source": "Health Tech",
                "published_date": "2025-07-29T09:30:00Z",
                "guid": "4",
            }
        ],
    }

    processor = NewsProcessor(dummy_data)
    parsed_news = processor.parse_news()
    print("Parsed News:", json.dumps(parsed_news, indent=2))

