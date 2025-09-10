import json
import re

from services.web_scraper import ScrapingTool


class BusinessTrends:
    """
    MCP-style agent that uses an LLM and a scraping tool to extract domain trends and web content.
    """

    def __init__(self, llm, tool=None):
        self.llm = llm
        self.tool = tool or ScrapingTool()

    def get_prompt(self, domain):
        return f"""
Given the domain "{domain}", generate a list of 20 high-relevance keywords that capture the key concepts, trends, technologies, challenges, and subfields within that domain.
Output format:
[keyword1, keyword2, ..., keyword20]
"""

    def get_urls_prompt(self, domain):
        return f"""
Given the domain "{domain}", generate a list of 20 high-relevance URLs that capture the latest news, concepts, trends, technologies, challenges, and subfields within that domain.
Output format:
["https://example1.com", "https://example2.com",..., "https://example20.com" ]
"""

    def run(self, domain):
        prompt = self.get_prompt(domain)
        response = self.llm(prompt)
        cleaned_response = clean_response(response)
        try:
            keywords = eval(cleaned_response)
        except Exception:
            keywords = []
        urls_prompt = self.get_urls_prompt(domain)
        urls_response = self.llm(urls_prompt)
        cleaned_urls = clean_response(urls_response)
        try:
            start_urls = json.loads(cleaned_urls)
        except Exception:
            try:
                start_urls = eval(cleaned_urls)
            except Exception:
                start_urls = []
        target_fields = {domain: keywords}
        tool_input = {"start_urls": start_urls, "target_fields": target_fields}
        tool_output = self.tool.run(tool_input)
        return tool_output["results"]


def clean_response(response_text):
    match = re.search(r"```json\n(.*)\n```", response_text, re.DOTALL)
    if match:
        return match.group(1)
    match_python = re.search(r"```python\n(.*)\n```", response_text, re.DOTALL)
    if match_python:
        return match_python.group(1)
    return response_text.strip()
