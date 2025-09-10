"""
Web Scraping Service for MCP Backend
Enhanced web scraping with robots.txt compliance, rate limiting, and data extraction.
Integrates with MCP tools for comprehensive web data collection.
"""

import json
import os
import time
import urllib.robotparser
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional, Any
import asyncio

import requests
from bs4 import BeautifulSoup

from utils.logger import get_logger


def is_allowed_by_robots(url: str, user_agent: str = "*") -> bool:
    """
    Check if crawling is allowed by robots.txt.
    Returns True if robots.txt is not available (crawl freely).
    Returns the actual robots.txt permission if available.
    
    Args:
        url: URL to check
        user_agent: User agent string for robots.txt checking
        
    Returns:
        bool: True if crawling is allowed, False otherwise
    """
    logger = get_logger("robots_checker")

    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    
    try:
        rp.read()
        # If robots.txt is successfully read, respect its rules
        allowed = rp.can_fetch(user_agent, url)
        if not allowed:
            logger.info(
                f"Robots.txt disallows crawling {url} for user-agent '{user_agent}'"
            )
        return allowed
    except Exception as e:
        # If robots.txt is not available or cannot be read, allow crawling
        logger.info(
            f"Robots.txt not available for {parsed.netloc}, crawling freely: {e}"
        )
        return True


def extract_info_from_html(html: str, base_url: str) -> Dict[str, Any]:
    """
    Extract structured information from HTML content.
    
    Args:
        html: HTML content to parse
        base_url: Base URL for resolving relative links
        
    Returns:
        Dict containing extracted information
    """
    soup = BeautifulSoup(html, "html.parser")
    info = {}
    
    # Title
    info["title"] = (
        soup.title.string.strip() if soup.title and soup.title.string else ""
    )
    
    # Meta description
    desc = soup.find("meta", attrs={"name": "description"})
    info["meta_description"] = (
        desc["content"].strip() if desc and desc.get("content") else ""
    )
    
    # Meta keywords
    keywords = soup.find("meta", attrs={"name": "keywords"})
    info["meta_keywords"] = (
        keywords["content"].strip() if keywords and keywords.get("content") else ""
    )
    
    # All visible text (shortened)
    texts = soup.stripped_strings
    text_list = list(texts)
    info["text_sample"] = " ".join(text_list[:100])  # First 100 words
    info["full_text"] = " ".join(text_list)  # Full text for analysis
    
    # All links
    links = []
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        absolute_url = urljoin(base_url, href)
        link_text = a_tag.get_text(strip=True)
        links.append({
            "url": absolute_url,
            "text": link_text,
            "rel": a_tag.get("rel", [])
        })
    info["links"] = links
    
    # Images
    images = []
    for img_tag in soup.find_all("img", src=True):
        src = img_tag["src"]
        absolute_url = urljoin(base_url, src)
        images.append({
            "url": absolute_url,
            "alt": img_tag.get("alt", ""),
            "title": img_tag.get("title", "")
        })
    info["images"] = images
    
    # Emails
    import re
    emails = set(re.findall(r"[\w\.-]+@[\w\.-]+", html))
    info["emails"] = list(emails)
    
    # Phone numbers (basic pattern)
    phones = set(re.findall(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", html))
    info["phones"] = list(phones)
    
    # Social media links
    social_patterns = {
        "twitter": r"twitter\.com/[\w]+",
        "linkedin": r"linkedin\.com/(?:in|company)/[\w-]+",
        "facebook": r"facebook\.com/[\w.]+",
        "instagram": r"instagram\.com/[\w.]+",
        "youtube": r"youtube\.com/(?:channel/|user/|c/)?[\w-]+",
        "github": r"github\.com/[\w-]+",
    }
    
    social_links = {}
    for platform, pattern in social_patterns.items():
        matches = re.findall(pattern, html, re.IGNORECASE)
        if matches:
            social_links[platform] = [f"https://{match}" for match in matches]
    info["social_links"] = social_links
    
    # Structured data (JSON-LD)
    structured_data = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            structured_data.append(data)
        except (json.JSONDecodeError, AttributeError):
            continue
    info["structured_data"] = structured_data
    
    return info


class ScrapingTool:
    """
    MCP-compatible scraping tool for extracting relevant web content.
    Enhanced with rate limiting, error handling, and comprehensive data extraction.
    """

    def __init__(
        self, 
        user_agent: str = "OpporTunaBot/1.0 (+https://opportuna.ai)",
        max_pages: int = 5,
        delay: float = 1.0,
        depth: int = 10,
        timeout: int = 10,
        respect_robots: bool = True
    ):
        """
        Initialize the scraping tool.
        
        Args:
            user_agent: User agent string for requests
            max_pages: Maximum number of pages to crawl
            delay: Delay between requests in seconds
            depth: Maximum crawl depth
            timeout: Request timeout in seconds
            respect_robots: Whether to respect robots.txt
        """
        self.user_agent = user_agent
        self.max_pages = max_pages
        self.delay = delay
        self.depth = depth
        self.timeout = timeout
        self.respect_robots = respect_robots
        self.logger = get_logger("ScrapingTool")
        
        # Request session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})

    def run(self, input_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the scraping tool with given parameters.
        
        Args:
            input_params: Dictionary containing scraping parameters
                - start_urls: List of URLs to start crawling from
                - target_fields: Dictionary of fields to look for (optional)
                - max_pages: Maximum pages to crawl (optional)
                - delay: Delay between requests (optional)
                - depth: Maximum crawl depth (optional)
                
        Returns:
            Dictionary containing crawling results
        """
        start_urls = input_params.get("start_urls", [])
        target_fields = input_params.get("target_fields", {})
        max_pages = input_params.get("max_pages", self.max_pages)
        delay = input_params.get("delay", self.delay)
        depth = input_params.get("depth", self.depth)
        
        self.logger.info(
            f"Starting crawl: {len(start_urls)} start URLs, max_depth={depth}, max_pages={max_pages}"
        )
        
        try:
            results = self._run_crawler(start_urls, target_fields, max_pages, delay, depth)
            
            self.logger.info(f"Crawl finished. Total pages crawled: {len(results)}")
            
            return {
                "success": True,
                "results": results,
                "total_pages": len(results),
                "start_urls": start_urls,
                "crawl_metadata": {
                    "max_pages": max_pages,
                    "max_depth": depth,
                    "delay": delay,
                    "user_agent": self.user_agent,
                    "respect_robots": self.respect_robots
                }
            }
            
        except Exception as e:
            self.logger.error(f"Crawling failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": [],
                "start_urls": start_urls
            }

    def _fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch a page while respecting robots.txt rules and handling errors.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content if successful, None otherwise
        """
        # Check robots.txt compliance first
        if self.respect_robots and not is_allowed_by_robots(url, self.user_agent):
            self.logger.info(f"Robots.txt disallows crawling: {url}")
            return None

        try:
            response = self.session.get(url, timeout=self.timeout)
            
            # Check if response is successful and is HTML
            if (response.status_code == 200 and 
                "text/html" in response.headers.get("Content-Type", "")):
                return response.text
            else:
                self.logger.warning(
                    f"Non-HTML response or error status {response.status_code} for {url}"
                )
                
        except requests.RequestException as e:
            self.logger.warning(f"Failed to fetch {url}: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error fetching {url}: {e}")
            
        return None

    def _is_relevant_link(
        self, link_url: str, anchor_text: str, target_fields: Dict[str, List[str]]
    ) -> tuple[bool, Optional[str]]:
        """
        Check if a link is relevant based on target fields.
        
        Args:
            link_url: URL of the link
            anchor_text: Anchor text of the link
            target_fields: Dictionary of target fields and their keywords
            
        Returns:
            Tuple of (is_relevant, field_name)
        """
        link_url_lower = link_url.lower()
        anchor_text_lower = anchor_text.lower()
        
        for field, keywords in target_fields.items():
            for keyword in keywords:
                if keyword.lower() in link_url_lower or keyword.lower() in anchor_text_lower:
                    return True, field
                    
        return False, None

    def _is_relevant_content(
        self, text_content: str, target_fields: Dict[str, List[str]]
    ) -> List[str]:
        """
        Check if content is relevant based on target fields.
        
        Args:
            text_content: Text content to check
            target_fields: Dictionary of target fields and their keywords
            
        Returns:
            List of relevant field names
        """
        relevant_fields = []
        text_content_lower = text_content.lower()
        
        for field, keywords in target_fields.items():
            if any(keyword.lower() in text_content_lower for keyword in keywords):
                relevant_fields.append(field)
                
        return relevant_fields

    def _extract_all_visible_text(self, soup: BeautifulSoup) -> str:
        """
        Extract all visible text from HTML soup.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Concatenated visible text
        """
        texts = []
        
        # Headings
        for tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            texts.extend([h.get_text(strip=True) for h in soup.find_all(tag)])
            
        # Paragraphs
        texts.extend([p.get_text(strip=True) for p in soup.find_all("p")])
        
        # List items
        texts.extend([li.get_text(strip=True) for li in soup.find_all("li")])
        
        # Table cells
        texts.extend([td.get_text(strip=True) for td in soup.find_all("td")])
        texts.extend([th.get_text(strip=True) for th in soup.find_all("th")])
        
        # Captions
        texts.extend(
            [caption.get_text(strip=True) for caption in soup.find_all("caption")]
        )
        
        # Other visible text (spans, divs with limited nesting)
        for tag in ["span", "div"]:
            for element in soup.find_all(tag):
                # Avoid deeply nested elements to prevent duplication
                if len(element.find_parents(tag)) < 2:
                    text = element.get_text(strip=True)
                    if text and len(text) > 10:  # Only meaningful text
                        texts.append(text)
        
        # Remove empty strings and join
        all_text = " ".join([t for t in texts if t])
        return all_text

    def _parse_html(
        self, html_content: str, base_url: str, root_netloc: str
    ) -> tuple[Optional[Dict[str, Any]], List[str]]:
        """
        Parse HTML content and extract information and internal links.
        
        Args:
            html_content: HTML content to parse
            base_url: Base URL for resolving relative links
            root_netloc: Root network location for filtering internal links
            
        Returns:
            Tuple of (extracted_data, internal_links)
        """
        if not html_content:
            return None, []
            
        soup = BeautifulSoup(html_content, "html.parser")
        extracted_data = {}
        internal_links = set()
        
        # Basic page information
        title_tag = soup.find("title")
        extracted_data["title"] = (
            title_tag.get_text(strip=True) if title_tag else "No Title"
        )
        
        # Extract comprehensive information
        comprehensive_info = extract_info_from_html(html_content, base_url)
        extracted_data.update(comprehensive_info)
        
        # Find all internal links (same netloc as root)
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            absolute_url = urljoin(base_url, href)
            parsed_absolute_url = urlparse(absolute_url)
            
            if (parsed_absolute_url.scheme in ["http", "https"] and 
                parsed_absolute_url.netloc == root_netloc):
                # Remove fragment and trailing slash for normalization
                clean_url = absolute_url.split("#")[0].rstrip("/")
                internal_links.add(clean_url)
        
        extracted_data["found_internal_urls"] = list(internal_links)
        
        return extracted_data, list(internal_links)

    def _run_crawler(
        self,
        start_urls: List[str],
        target_fields: Dict[str, List[str]],
        max_pages: int,
        delay: float,
        max_depth: int
    ) -> List[Dict[str, Any]]:
        """
        Run the actual crawling process.
        
        Args:
            start_urls: List of starting URLs
            target_fields: Target fields for relevance checking
            max_pages: Maximum pages to crawl
            delay: Delay between requests
            max_depth: Maximum crawl depth
            
        Returns:
            List of crawled page data
        """
        # url_queue: list of (url, depth, root_netloc)
        url_queue = []
        for url in start_urls:
            parsed = urlparse(url)
            url_queue.append((url, 0, parsed.netloc))
            
        visited_urls = set()
        crawled_data = []
        pages_crawled_count = 0
        robots_blocked_count = 0

        while url_queue and pages_crawled_count < max_pages:
            current_url, current_depth, root_netloc = url_queue.pop(0)
            current_url = current_url.split("#")[0].rstrip("/")
            
            if current_url in visited_urls or current_depth > max_depth:
                continue

            # Check robots.txt before attempting to crawl
            if (self.respect_robots and 
                not is_allowed_by_robots(current_url, self.user_agent)):
                self.logger.info(
                    f"Robots.txt blocked (depth={current_depth}): {current_url}"
                )
                robots_blocked_count += 1
                visited_urls.add(current_url)  # Mark as visited to avoid re-checking
                continue

            self.logger.info(f"Crawling (depth={current_depth}): {current_url}")
            html_content = self._fetch_page(current_url)
            visited_urls.add(current_url)
            pages_crawled_count += 1

            if html_content:
                # Parse HTML and extract all internal links
                page_data, new_internal_links = self._parse_html(
                    html_content, current_url, root_netloc
                )
                
                if page_data:
                    page_data["url"] = current_url
                    page_data["depth"] = current_depth
                    page_data["crawl_timestamp"] = time.time()
                    page_data["root_netloc"] = root_netloc
                    
                    # Add relevance scoring if target_fields provided
                    if target_fields:
                        relevant_fields = self._is_relevant_content(
                            page_data.get("full_text", ""), target_fields
                        )
                        page_data["relevant_fields"] = relevant_fields
                        page_data["relevance_score"] = len(relevant_fields) / len(target_fields) if target_fields else 0
                    
                    crawled_data.append(page_data)
                    
                    self.logger.info(
                        f"  -> Found {len(new_internal_links)} internal links on this page."
                    )
                    
                # Add new internal links to queue
                for link in new_internal_links:
                    if link not in visited_urls and all(link != u for u, _, _ in url_queue):
                        url_queue.append((link, current_depth + 1, root_netloc))
                        self.logger.debug(f"    + Queued new internal link: {link}")

            # Respect delay between requests
            if delay > 0:
                time.sleep(delay)

        self.logger.info(
            f"Crawling summary: {pages_crawled_count} pages crawled, "
            f"{robots_blocked_count} blocked by robots.txt"
        )
        
        return crawled_data

    def close(self):
        """Close the requests session."""
        if hasattr(self, 'session'):
            self.session.close()


def save_crawled_info_to_json(
    results: List[Dict[str, Any]], 
    company_name: str, 
    output_dir: str = "crawled_results"
) -> str:
    """
    Save crawled information to JSON file.
    
    Args:
        results: Crawled results to save
        company_name: Company name for filename
        output_dir: Output directory
        
    Returns:
        Path to saved file
    """
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{company_name.replace(' ', '_')}_website_info.json"
    filepath = os.path.join(output_dir, filename)
    
    # Add metadata to the saved file
    save_data = {
        "company_name": company_name,
        "crawl_timestamp": time.time(),
        "total_pages": len(results),
        "results": results
    }
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2, default=str)
        
    return filepath


def crawl_company_website_if_existing(extracted_json: Dict[str, Any]) -> Optional[str]:
    """
    Crawl company website if it exists in the extracted data.
    
    Args:
        extracted_json: Extracted company information
        
    Returns:
        Path to saved crawl results or None
    """
    data = extracted_json.get("data", extracted_json)
    
    if data.get("start_date") == "existing" and data.get("urls"):
        # Use the first URL as the main website
        main_url = data["urls"][0]
        company_name = data.get("company_name", "company")
        
        # Create scraping tool and crawl
        tool = ScrapingTool(max_pages=10, depth=3)
        try:
            results = crawl_website(main_url, max_pages=10, depth=3)
            path = save_crawled_info_to_json(list(results.values()), company_name)
            return path
        finally:
            tool.close()
            
    return None


def crawl_website(
    start_url: str,
    max_pages: int = 5,
    depth: int = 20,
    user_agent: str = "OpporTunaBot/1.0"
) -> Dict[str, Dict[str, Any]]:
    """
    Legacy function for crawling a single website.
    
    Args:
        start_url: Starting URL to crawl
        max_pages: Maximum pages to crawl
        depth: Maximum crawl depth
        user_agent: User agent string
        
    Returns:
        Dictionary of crawled data keyed by URL
    """
    tool = ScrapingTool(user_agent=user_agent, max_pages=max_pages, depth=depth)
    
    try:
        # For legacy compatibility
        tool_input = {
            "start_urls": [start_url],
            "target_fields": {},  # No specific target fields for legacy mode
            "max_pages": max_pages,
        }
        
        result = tool.run(tool_input)
        
        if result.get("success"):
            results = result["results"]
            # Return as dict keyed by URL for legacy compatibility
            return {item["url"]: item for item in results if "url" in item}
        else:
            return {}
            
    finally:
        tool.close()


# Create async wrapper for integration with MCP tools
async def async_crawl_website(
    start_url: str,
    max_pages: int = 5,
    depth: int = 10,
    target_fields: Optional[Dict[str, List[str]]] = None
) -> Dict[str, Any]:
    """
    Async wrapper for website crawling to integrate with MCP tools.
    
    Args:
        start_url: Starting URL to crawl
        max_pages: Maximum pages to crawl
        depth: Maximum crawl depth
        target_fields: Optional target fields for relevance
        
    Returns:
        Crawling results
    """
    loop = asyncio.get_event_loop()
    
    def sync_crawl():
        tool = ScrapingTool(max_pages=max_pages, depth=depth)
        try:
            tool_input = {
                "start_urls": [start_url],
                "target_fields": target_fields or {},
                "max_pages": max_pages,
                "depth": depth
            }
            return tool.run(tool_input)
        finally:
            tool.close()
    
    # Run in thread pool to avoid blocking the event loop
    return await loop.run_in_executor(None, sync_crawl)
