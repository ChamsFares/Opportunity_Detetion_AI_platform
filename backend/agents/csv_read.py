import logging
import os
import re
from datetime import datetime
from typing import List, Optional

import feedparser
import pandas as pd
from pydantic import BaseModel
from config.llm_config import COMMON_TOPICS

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Article(BaseModel):

    title: str
    url: str
    description: str
    source: str
    published_date: str
    guid: Optional[str] = None


class GoogleNewsRSSScaper:
    """Article data model"""
    """Google News RSS scraper"""

    def __init__(self, output_file: str = "news_articles.csv"):
        self.output_file = output_file
        self.logger = logger

    def _clean_description(self, description: str) -> str:
        """Clean and extract meaningful description from RSS summary"""
        if not description:
            return ""

        # Remove HTML tags
        clean_desc = re.sub(r"<[^>]+>", "", description)

        # Remove extra whitespace
        clean_desc = " ".join(clean_desc.split())

        # Sometimes RSS descriptions contain source info at the end, try to clean it
        # Example: "Article text ... - CNN" -> "Article text ..."
        if " - " in clean_desc:
            parts = clean_desc.split(" - ")
            if len(parts) > 1 and len(parts[-1]) < 50:  # Likely a source name
                clean_desc = " - ".join(parts[:-1])

        return clean_desc.strip()

    def _extract_source(self, entry) -> str:
        """Extract source name from RSS entry"""
        # Try different fields where source might be stored
        if hasattr(entry, "source") and entry.source:
            if hasattr(entry.source, "title"):
                return entry.source.title
            elif hasattr(entry.source, "value"):
                return entry.source.value

        # Try to extract from title (format: "Article Title - Source Name")
        if " - " in entry.title:
            return entry.title.split(" - ")[-1]

        # Try to extract from summary
        if hasattr(entry, "summary") and " - " in entry.summary:
            parts = entry.summary.split(" - ")
            if len(parts) > 1 and len(parts[-1]) < 50:
                return parts[-1]

        return "Unknown Source"

    # def _save_to_csv(self, articles: List[Article]) -> None:
    #     """Save articles to CSV file"""
    #     self.logger.info(f"Saving {len(articles)} articles to {self.output_file}")

    #     # Convert to dictionaries
    #     article_dicts = [article.model_dump() for article in articles]

    #     # Create DataFrame and save
    #     df = pd.DataFrame(article_dicts)
    #     df.to_csv(self.output_file, index=False, encoding='utf-8')

    #     self.logger.info(f"Successfully saved articles to {self.output_file}")

    def _save_to_csv(self, articles: List[Article]) -> None:
        """Save articles to CSV file, appending to existing data"""
        self.logger.info(f"Saving {len(articles)} articles to {self.output_file}")

        # Convert to dictionaries
        article_dicts = [article.model_dump() for article in articles]
        df = pd.DataFrame(article_dicts)

        # Check if file exists to determine if we need headers
        file_exists = os.path.exists(self.output_file)

        # Append to CSV (header=False if file exists, True if new file)
        df.to_csv(
            self.output_file,
            mode="a" if file_exists else "w",
            header=not file_exists,
            index=False,
            encoding="utf-8",
        )

        self.logger.info(
            f"Successfully {'appended' if file_exists else 'saved'} articles to {self.output_file}"
        )

    def scrape_topic(
        self, topic_id: str, language: str = "fr-FR", country: str = "FR"
    ) -> List[Article]:
        """
        Scrape articles from Google News RSS feed for a specific topic

        Args:
            topic_id: Google News topic ID (e.g., 'CAAqJggKIiBDQkFTRWdvSUwyMHZNRFZxYUdjU0FtVnVHZ0pWVXlnQVAB' for Technology)
            language: Language code (default: en-US)
            country: Country code (default: US)

        Returns:
            List of Article objects
        """
        rss_url = f"https://news.google.com/rss/topics/{topic_id}?hl={language}&gl={country}&ceid={country}:{language.split('-')[0]}"

        self.logger.info(f"Fetching RSS feed from: {rss_url}")

        try:
            # Parse the RSS feed
            feed = feedparser.parse(rss_url)

            if feed.bozo:
                self.logger.warning(
                    f"RSS feed might have issues: {feed.bozo_exception}"
                )

            if not feed.entries:
                self.logger.error("No articles found in RSS feed")
                return []

            articles = []

            for entry in feed.entries:
                try:
                    # Extract article data
                    title = entry.title if hasattr(entry, "title") else "No Title"
                    url = entry.link if hasattr(entry, "link") else ""
                    description = self._clean_description(
                        entry.summary if hasattr(entry, "summary") else ""
                    )
                    source = self._extract_source(entry)

                    # Format published date
                    published_date = ""
                    if hasattr(entry, "published"):
                        try:
                            # Parse and format the date
                            pub_date = datetime(*entry.published_parsed[:6])
                            published_date = pub_date.strftime("%Y-%m-%d %H:%M:%S")
                        except (AttributeError, TypeError, ValueError):
                            published_date = entry.published

                    # Create article object
                    article = Article(
                        title=title,
                        url=url,
                        description=description,
                        source=source,
                        published_date=published_date,
                        guid=entry.id if hasattr(entry, "id") else None,
                    )

                    articles.append(article)

                except Exception as e:
                    self.logger.warning(f"Error processing article: {e}")
                    continue

            self.logger.info(f"Successfully extracted {len(articles)} articles")
            return articles

        except Exception as e:
            self.logger.error(f"Error fetching RSS feed: {e}")
            return []

    def scrape_search_query(
        self, query: str, language: str = "fr-FR", country: str = "FR"
    ) -> List[Article]:
        """
        Scrape articles from Google News RSS feed for a search query

        Args:
            query: Search query (e.g., "artificial intelligence")
            language: Language code (default: fr-FR)
            country: Country code (default: FR)

        Returns:
            List of Article objects
        """
        # URL encode the query
        import urllib.parse

        encoded_query = urllib.parse.quote(query)

        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl={language}&gl={country}&ceid={country}:{language.split('-')[0]}"

        self.logger.info(f"Searching for: '{query}'")
        self.logger.info(f"RSS URL: {rss_url}")

        try:
            feed = feedparser.parse(rss_url)

            if not feed.entries:
                self.logger.error(f"No articles found for query: '{query}'")
                return []

            articles = []

            for entry in feed.entries:
                try:
                    article = Article(
                        title=entry.title if hasattr(entry, "title") else "No Title",
                        url=entry.link if hasattr(entry, "link") else "",
                        description=self._clean_description(
                            entry.summary if hasattr(entry, "summary") else ""
                        ),
                        source=self._extract_source(entry),
                        published_date=(
                            entry.published if hasattr(entry, "published") else ""
                        ),
                        guid=entry.id if hasattr(entry, "id") else None,
                    )

                    articles.append(article)

                except Exception as e:
                    self.logger.warning(f"Error processing article: {e}")
                    continue

            self.logger.info(
                f"Successfully extracted {len(articles)} articles for query: '{query}'"
            )
            return articles

        except Exception as e:
            self.logger.error(f"Error fetching RSS feed for query '{query}': {e}")
            return []


# Example usage and common topic IDs


if __name__ == "__main__":
    # Create scraper instance
    scraper = GoogleNewsRSSScaper("google_news_articles.csv")

    # Example 1: Scrape by topic
    print("Scraping Technology news...")
    articles = scraper.scrape_topic(
        "CAAqIQgKIhtDQkFTRGdvSUwyMHZNR3QwTlRFU0FtWnlLQUFQAQ"
    )

    if articles:
        scraper._save_to_csv(articles)
        print(f"Scraped {len(articles)} health articles")

        # Display first few articles
        print("\nFirst 3 articles:")
        for i, article in enumerate(articles[:3], 1):
            print(i)
            print(f"\n{i}. {article.title}")
            print(f"   Source: {article.source}")
            print(f"   Description: {article.description}...")
            print(f"   URL: {article.url}")
            if i == 1:
                with open("data.txt", "w", encoding="utf-8") as f:
                    f.write(article.description)

        # writing dictionary to a file as JSON

    # Example 2: Search for specific topic
    # print("\n" + "="*50)
    # print("Searching for 'artificial intelligence'...")
    # ai_articles = scraper.scrape_search_query("Banque and Finance")

    # if ai_articles:
    #     scraper.output_file = "sector.csv"  # Change output file
    #     scraper._save_to_csv(ai_articles)
    #     print(f"Found {len(ai_articles)} talan-related articles")
