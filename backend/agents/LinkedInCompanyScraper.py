import http.client
import json
import os
import re
import time
from typing import Any, Dict, Optional


class LinkedInCompanyScraper:
    def __init__(self: str):
        self.api_key = "9de31aa9a2msh6372c54394ae502p1d985bjsn3e18c43a677d"
        self.host = "m"
        self.headers = {"x-rapidapi-key": self.api_key, "x-rapidapi-host": self.host}

    def get_company_posts(
        self, company_name: str, page_number: int = 1
    ) -> Optional[Dict[Any, Any]]:
        """
        Get company posts/updates using the new API endpoint
        """
        conn = http.client.HTTPSConnection(self.host)
        query_path = (
            f"/company/posts?company_name={company_name}&page_number={page_number}"
        )

        try:
            print(f"Making request to: {self.host}{query_path}")
            print(f"Parameters: company_name={company_name}, page_number={page_number}")

            conn.request("GET", query_path, headers=self.headers)
            response = conn.getresponse()
            print(f"Response status code: {response.status}")

            # Print rate limit info
            for key, value in response.getheaders():
                if "ratelimit" in key.lower():
                    print(f"  {key}: {value}")

            if response.status == 200:
                print("✅ Success!")
                data = response.read().decode("utf-8")
                return json.loads(data)
            else:
                print(f"❌ Error: {response.reason}")

        except Exception as e:
            print(f"Unexpected error: {e}")
        finally:
            conn.close()

        return None


def main():
    print("🚀 LINKEDIN COMPANY SCRAPER - MULTI-COMPANY SCRAPING")
    print("=" * 70)

    # Configuration
    API_KEY = "d0f55aef94mshc3505182eb5a1ddp1a5857jsn3b0f155fdd15"

    # Initialize scraper
    scraper = LinkedInCompanyScraper(API_KEY)

    # Load companies from competitors.json
    try:
        with open("competitors.json", "r", encoding="utf-8") as f:
            competitors = json.load(f)
        company_names = (
            list(competitors.keys())
            if all(isinstance(k, str) for k in competitors.keys())
            else list(competitors.values())
        )
        company_urls = (
            list(competitors.values())
            if all(isinstance(v, str) for v in competitors.values())
            else list(competitors.keys())
        )
        print(
            f"Companies extracted from competitors.json: {list(zip(company_names, company_urls))}"
        )
    except Exception as e:
        print(f"[ERROR] Erreur lors de la lecture de competitors.json : {e}")
        company_names = []
        company_urls = []

    # Loop through each company
    all_company_data = {}
    for company_name, company_url in zip(company_names, company_urls):
        print(f"\n🎯 Scraping data for: {company_name} (URL: {company_url})")
        print("=" * 50)

        # Extract valid company name from URL if necessary
        valid_company_name = re.search(r"www\.([^.]+)", company_url)
        valid_company_name = (
            valid_company_name.group(1)
            if valid_company_name
            else company_name.replace(" ", "_")
        )

        # Scrape company posts
        posts_data = scraper.get_company_posts(valid_company_name)
        if posts_data:
            all_company_data[company_name] = posts_data

        # Wait to respect rate limits
        time.sleep(2)
