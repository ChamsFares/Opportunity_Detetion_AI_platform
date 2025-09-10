import asyncio
import concurrent.futures
import http.client
import json
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import aiohttp
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from agents.ollama_api import OllamaQwen3Client


class Competitors:
    def __init__(self):
        self.visited = set()
        self.all_results = []
        # --- CONFIG : Ollama API ---
        try:
            self.client = OllamaQwen3Client()
            print("✅ Ollama client initialized for competitor analysis")
        except Exception as e:
            print(f"❌ Failed to initialize Ollama client: {e}")
            self.client = None

        # --- CONFIG : Serper API ---
        self.api_key = "5be1c22775b16c6b4a4892cc90ef7f5324f57f78"  # Serper.dev

        # Performance optimizations
        self._driver_pool = []
        self._max_drivers = 3  # Pool of reusable Chrome drivers
        self._session = None  # Reusable HTTP session

    def _get_optimized_chrome_options(self):
        """Get optimized Chrome options for faster loading"""
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-images")  # Skip image loading
        options.add_argument("--disable-css")  # Skip CSS loading
        options.add_argument(
            "--disable-javascript"
        )  # Skip JS execution for faster loading
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-extensions")
        options.add_argument("--no-first-run")
        options.add_argument("--disable-default-apps")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        # Optimize page load strategy
        options.page_load_strategy = "eager"  # Don't wait for all resources

        return options

    def _get_driver_from_pool(self):
        """Get a driver from the pool or create a new one"""
        if self._driver_pool:
            return self._driver_pool.pop()
        else:
            return webdriver.Chrome(options=self._get_optimized_chrome_options())

    def _return_driver_to_pool(self, driver):
        """Return a driver to the pool for reuse"""
        if len(self._driver_pool) < self._max_drivers:
            try:
                # Clear the current page to free memory
                driver.get("about:blank")
                self._driver_pool.append(driver)
            except:
                driver.quit()
        else:
            driver.quit()

    def _get_http_session(self):
        """Get a reusable HTTP session with connection pooling"""
        if self._session is None:
            self._session = requests.Session()
            # Configure session for better performance
            adapter = requests.adapters.HTTPAdapter(
                pool_connections=10, pool_maxsize=20, max_retries=2
            )
            self._session.mount("http://", adapter)
            self._session.mount("https://", adapter)
            self._session.headers.update(
                {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )
        return self._session

    def cleanup(self):
        """Clean up resources"""
        # Close all drivers in pool
        for driver in self._driver_pool:
            try:
                driver.quit()
            except:
                pass
        self._driver_pool.clear()

        # Close HTTP session
        if self._session:
            self._session.close()
            self._session = None

    # --- Extraire un nom propre depuis une URL ---
    def extraire_nom_domaine(self, url):
        domaine = urlparse(url).netloc
        nom = domaine.replace("www.", "").split(".")[0]
        return nom.capitalize()

    # --- Vérifier via LLM si l'entreprise est un vrai concurrent (avec cache et batch processing) ---
    def verifier_concurrent_llm_batch(self, candidates_batch, secteur, service, cible):
        """Process multiple candidates at once for better efficiency"""
        if not candidates_batch:
            return []
            
        if not self.client:
            print("⚠️ Ollama client not available, accepting all candidates by default")
            return [True] * len(candidates_batch)

        print(f"🔍 LLM evaluating {len(candidates_batch)} candidates for {cible}")
        for i, (nom, desc) in enumerate(candidates_batch):
            print(f"   {i+1}. {nom}: {desc[:100]}...")

        # Create batch prompt for multiple candidates
        candidates_text = "\n".join(
            [f"{i+1}. {nom}: {desc}" for i, (nom, desc) in enumerate(candidates_batch)]
        )

        prompt = f"""
You are an expert competitive strategy analyst. Your task is to evaluate potential competitors for {cible} in the "{secteur}" sector, specifically in "{service}" services.

Companies to evaluate:
{candidates_text}

EVALUATION CRITERIA (be inclusive and strategic):
- Companies operating in the same or adjacent sectors
- Businesses offering similar, complementary, or competing services
- Organizations that could target the same customer base
- Consulting firms, service providers, or technology companies that could be relevant
- Startups or established companies with overlapping value propositions
- When uncertain, lean towards "YES" rather than "NO" to capture potential strategic insights

For each company, respond with its number followed by "YES" or "NO" and a brief justification.
Format: "1. YES - reason" or "1. NO - reason"

Focus on strategic relevance rather than perfect matches. Consider indirect competition and market adjacency.
"""

        try:
            response = self.client.generate(prompt)
            print(f"📝 LLM Response: {response[:200]}...")
            results = []

            # Parse batch results
            lines = response.split("\n")
            for line in lines:
                if re.match(r"^\d+\.", line):
                    if "YES" in line.upper() or "OUI" in line.upper():
                        results.append(True)
                    else:
                        results.append(False)

            # Ensure we have results for all candidates
            while len(results) < len(candidates_batch):
                results.append(False)

            print(f"📊 Results: {results}")
            return results[: len(candidates_batch)]

        except Exception as e:
            print(f"LLM batch error: {e}")
            return [False] * len(candidates_batch)

    # --- Fonction principale de recherche de concurrents avec optimisations ---
    def chercher_concurrents(self, nom_entreprise, secteur, service):
        print(f"🎯 Competitor search for:")
        print(f"   - Company: {nom_entreprise}")
        print(f"   - Sector: {secteur}")
        print(f"   - Service: {service}")
        
        requetes = [
            f"companies similar to {nom_entreprise} in {secteur} sector offering {service} services",
            f"competitors of {nom_entreprise} in {secteur} domain with {service} offerings",
            f"startups competing with {nom_entreprise} specialized in {service} for {secteur} sector",
            f"consulting firms in {secteur} sector offering {service}",
            f"{secteur} {service} companies market leaders",
            f"top {service} providers in {secteur} industry",
        ]

        concurrents = {}  # nom : url
        candidates_batch = []  # For batch LLM processing

        session = self._get_http_session()

        for query in requetes:
            print(f"\n🔎 Search: {query}")

            headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}
            payload = {
                "q": query,
                "gl": "fr",
                "hl": "fr",
                "num": 15,
            }  # Get more results per query

            try:
                response = session.post(
                    "https://google.serper.dev/search",
                    headers=headers,
                    json=payload,
                    timeout=10,
                )
                results = response.json().get("organic", [])
            except Exception as e:
                print(f"Serper API error: {e}")
                continue

            # Collect candidates for batch processing
            for item in results:
                url = item.get("link", "")
                titre = item.get("title", "")
                description = item.get("snippet", "")

                if not url or not description:
                    continue

                # Filtres basiques optimisés
                skip_domains = {
                    "linkedin",
                    "pdf",
                    "facebook",
                    "blog",
                    "latribune",
                    "lesechos",
                    "senat",
                    "usine-digitale",
                    "wikipedia",
                    "youtube",
                    "twitter",
                    "instagram",
                }

                if any(domain in url.lower() for domain in skip_domains):
                    continue

                nom_nettoye = self.extraire_nom_domaine(url)
                if (
                    nom_nettoye.lower() == nom_entreprise.lower()
                    or nom_nettoye in concurrents
                    or len(nom_nettoye) < 2
                ):
                    continue

                candidates_batch.append((nom_nettoye, description, url))

                # Process in batches of 5 for efficiency
                if len(candidates_batch) >= 5:
                    self._process_candidates_batch(
                        candidates_batch, secteur, service, nom_entreprise, concurrents
                    )
                    candidates_batch = []

        # Process remaining candidates
        if candidates_batch:
            self._process_candidates_batch(
                candidates_batch, secteur, service, nom_entreprise, concurrents
            )

        # Sauvegarde dans un fichier JSON
        with open("competitors.json", "w", encoding="utf-8") as f:
            json.dump(concurrents, f, ensure_ascii=False, indent=2)

        print(f"🎯 Total competitors found: {len(concurrents)}")
        return concurrents

    def _process_candidates_batch(
        self, candidates_batch, secteur, service, nom_entreprise, concurrents
    ):
        """Process a batch of candidates with LLM verification"""
        # Prepare batch for LLM
        llm_batch = [(nom, desc) for nom, desc, url in candidates_batch]

        # Get LLM decisions for the batch
        decisions = self.verifier_concurrent_llm_batch(
            llm_batch, secteur, service, nom_entreprise
        )

        # Apply decisions
        for i, (nom_nettoye, description, url) in enumerate(candidates_batch):
            if i < len(decisions) and decisions[i]:
                concurrents[nom_nettoye] = url
                print(f"✅ Accepted: {nom_nettoye}")
            else:
                print(f"❌ Rejected: {nom_nettoye}")

    # --- Optimized content extraction with faster methods ---
    def extract_content_fast(self, url, timeout=10):
        """Try fast HTTP request first, fallback to Selenium if needed"""
        try:
            # Try HTTP request first (much faster)
            session = self._get_http_session()
            response = session.get(url, timeout=timeout)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "html.parser")

                # Remove unwanted tags
                for tag in soup(
                    [
                        "script",
                        "style",
                        "meta",
                        "noscript",
                        "iframe",
                        "nav",
                        "footer",
                        "header",
                    ]
                ):
                    tag.decompose()

                text = soup.get_text(separator=" ", strip=True)

                if len(text) > 200:  # If we got meaningful content
                    print(f"✅ HTTP extraction successful for {url}")
                    return [{"url": url, "content": text[:8000]}], []

        except Exception as e:
            print(f"HTTP extraction failed for {url}: {e}")

        # Fallback to Selenium for JavaScript-heavy sites
        return self.extract_with_selenium(url)

    def extract_with_selenium(self, url):
        """Selenium extraction with optimized settings"""
        driver = self._get_driver_from_pool()
        results = []

        try:
            # Fast page load with timeout
            driver.set_page_load_timeout(8)  # Reduced timeout
            driver.get(url)

            # Wait for basic content to load (reduced wait time)
            WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Extract content
            soup = BeautifulSoup(driver.page_source, "html.parser")

            # Remove unwanted tags
            for tag in soup(
                [
                    "script",
                    "style",
                    "meta",
                    "noscript",
                    "iframe",
                    "nav",
                    "footer",
                    "header",
                ]
            ):
                tag.decompose()

            text = soup.get_text(separator=" ", strip=True)
            results.append({"url": url, "content": text[:8000]})  # Reduced content size

            print(f"✅ Selenium extraction successful for {url}")

        except Exception as e:
            print(f"❌ Selenium extraction failed for {url}: {e}")
        finally:
            self._return_driver_to_pool(driver)

        return results, []

    def scrapping_competitors(self, competitors):
        """Optimized competitor scraping with parallel processing and intelligent content extraction"""

        # Extract URLs from dictionary
        base_urls = list(competitors.values())
        print(f"🚀 Starting optimized scraping for {len(base_urls)} URLs")

        self.all_results = []  # Reset results

        # Use ThreadPoolExecutor for parallel processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            # Submit all scraping tasks
            future_to_url = {
                executor.submit(self._scrape_single_competitor, url): url
                for url in base_urls
                if url and url not in self.visited
            }

            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_url, timeout=120):
                url = future_to_url[future]
                try:
                    results = future.result(timeout=30)
                    if results:
                        self.all_results.extend(results)
                        print(f"✅ Successfully scraped {url} - {len(results)} pages")
                    else:
                        print(f"⚠️ No content extracted from {url}")

                except concurrent.futures.TimeoutError:
                    print(f"⏰ Timeout scraping {url}")
                except Exception as e:
                    print(f"❌ Error scraping {url}: {e}")

        # Cleanup resources
        self.cleanup()

        print(f"🎯 Total content extracted: {len(self.all_results)} pages")
        return self.all_results

    def _scrape_single_competitor(self, base_url):
        """Scrape a single competitor website with optimized strategy"""
        if not base_url or base_url in self.visited:
            return []

        domain = urlparse(base_url).netloc
        results = []

        try:
            # Mark as visited immediately to avoid duplicates
            self.visited.add(base_url)

            # Extract main page content (fast method first)
            main_results, _ = self.extract_content_fast(base_url)
            results.extend(main_results)

            # Try to get important internal pages (limited to key pages for speed)
            important_pages = self._get_important_internal_pages(base_url, domain)

            # Process up to 2 additional important pages per competitor
            for page_url in important_pages[:2]:
                if page_url not in self.visited:
                    self.visited.add(page_url)
                    try:
                        page_results, _ = self.extract_content_fast(page_url, timeout=8)
                        results.extend(page_results)
                        time.sleep(0.5)  # Small delay between requests
                    except Exception as e:
                        print(f"❌ Error extracting {page_url}: {e}")

        except Exception as e:
            print(f"❌ Error processing {base_url}: {e}")

        return results

    def _get_important_internal_pages(self, base_url, domain):
        """Quickly identify important internal pages without full crawling"""
        important_pages = []

        try:
            session = self._get_http_session()
            response = session.get(base_url, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "html.parser")

                # Look for important page patterns
                important_patterns = [
                    "about",
                    "apropos",
                    "services",
                    "solutions",
                    "produits",
                    "products",
                    "qui-sommes-nous",
                    "notre-equipe",
                    "team",
                    "expertise",
                    "offres",
                ]

                # Find links matching important patterns
                for a in soup.find_all("a", href=True):
                    href = a.get("href", "").lower()
                    full_url = urljoin(base_url, a["href"])

                    if (
                        domain in full_url
                        and any(pattern in href for pattern in important_patterns)
                        and full_url != base_url
                    ):
                        important_pages.append(full_url)

                        if len(important_pages) >= 5:  # Limit to avoid too many pages
                            break

        except Exception as e:
            print(f"Error finding internal pages for {base_url}: {e}")

        return important_pages
