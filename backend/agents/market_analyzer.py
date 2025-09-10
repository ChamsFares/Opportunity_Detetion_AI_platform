import json
import os
import re
from typing import Dict, List, Optional

from agents.ollama_api import OllamaQwen3Client
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from utils.memory_manager import MemoryManager

# Initialize Ollama client
ollama_client = OllamaQwen3Client()

# Initialize Memory Manager
memory_manager = MemoryManager()

import asyncio
import json
from typing import Dict, List, Optional


async def market_analyzer(
    extracted_info: Dict[str, str], session_id: Optional[str] = "default"
) -> Dict:
    """
    Analyzes the market based on extracted business information, crawling public data sources
    to identify similar businesses, high-demand/low-competition areas, and relevant KPIs.

    Args:
        extracted_info: Dictionary containing business information as per the provided schema
        session_id: Session identifier for memory management

    Returns:
        Dictionary with market analysis results in JSON format
    """
    # Validate required fields
    required_fields = [
        "business_domain",
        "product_or_service",
        "target_audience",
        "region_or_market",
    ]
    # missing_fields = [
    #     field
    #     for field in required_fields
    #     if extracted_info.get(field) in [None, "", "N/A"]
    # ]

    # if missing_fields:
    #     return {
    #         "response_code": 400,
    #         "message": f"Missing required fields: {', '.join(missing_fields)}",
    #     }

    # Extract all fields from the schema
    # fields = {
    #     "company_name": extracted_info.get("company_name", "N/A"),
    #     "business_domain": extracted_info["business_domain"],
    #     "region_or_market": extracted_info["region_or_market"],
    #     "business_needs": extracted_info.get("business_needs", "N/A"),
    #     "product_or_service": extracted_info["product_or_service"],
    #     "target_audience": extracted_info["target_audience"],
    #     "unique_value_proposition": extracted_info.get(
    #         "unique_value_proposition", "N/A"
    #     ),
    #     "distribution_channels": extracted_info.get("distribution_channels", "N/A"),
    #     "revenue_model": extracted_info.get("revenue_model", "N/A"),
    #     "key_partners": extracted_info.get("key_partners", "N/A"),
    #     "kpis_or_outcomes": extracted_info.get("kpis_or_outcomes", "N/A"),
    #     "technologies_involved": extracted_info.get("technologies_involved", "N/A"),
    #     "document_references": extracted_info.get("document_references", "N/A"),
    #     "start_date": extracted_info.get("start_date", "N/A"),
    #     "urls": extracted_info.get("urls", []),
    # }

    # Get conversation history for context
    try:
        chat_history = memory_manager.get_full_chat_history(session_id)
        long_term_mem = memory_manager.get_long_term_memory(session_id)
    except Exception as e:
        chat_history = f"Error retrieving chat history: {str(e)}"
        long_term_mem = f"Error retrieving long-term memory: {str(e)}"

    # Construct prompt for market analysis
    analysis_prompt = f"""
You are an expert market research AI specializing in competitive intelligence and market opportunity analysis. Your task is to conduct a comprehensive, data-driven analysis of the provided business idea using credible public data sources. Simulate real-time crawling of authoritative platforms to gather realistic, up-to-date insights—even when live access isn't available—by generating plausible mock data grounded in industry standards and regional market dynamics.

### INPUTS
{chr(10).join([f"- **{key.replace('_', ' ').title()}**: {{{key}}}" for key in extracted_info])}

### CONTEXT
- **Chat History**: {chat_history}
- **Long-Term Memory**: {long_term_mem}
 
### INSTRUCTIONS

1. **Crawl Public Data Sources**  
   Simulate exploration of reputable sources such as:
   - Industry reports (e.g., Statista, IBISWorld, McKinsey, Gartner)
   - Business directories (e.g., Crunchbase, ZoomInfo, LinkedIn, Bloomberg, Dun & Bradstreet)
   - Government and trade association databases
   - Review platforms (e.g., Yelp, Google Business, Trustpilot) where applicable  
   Generate realistic, contextually accurate mock data if real-time retrieval is not possible, ensuring alignment with the business domain, target region, and audience.

2. **Identify Top Competitors (Exactly 10)**  
   Identify the **10 most well-known and influential competitors** operating in the same niche or offering similar products/services. For each competitor, extract:
   - Full company name
   - Official company website (must be a valid URL, e.g., https://www.example.com)
   - Brief note on core offering (for internal context — not part of final output unless specified)

3. **Analyze Similar Businesses**  
   List additional similar businesses (3–5 examples) with:
   - Name
   - Location (city/country or region)
   - Primary product or service offered

4. **Detect High-Demand / Low-Competition Opportunities**  
   Based on market gaps, customer needs, and the provided value proposition, identify specific geographic areas, customer segments, or sub-niches with:
   - Strong demand signals (e.g., search volume, growth trends)
   - Limited saturation or few dominant players

5. **Extract Key Performance Indicators (KPIs)**  
   Provide realistic estimates for:
   - Total market size (value or units)
   - Annual growth rate (CAGR %)
   - Market share leaders
   - Average customer acquisition cost (CAC)
   - Average revenue per user (ARPU)
   - Other relevant metrics (e.g., churn, retention, LTV)

6. **Cite Data Sources**  
   Include 3–5 credible or representative sources used (real or realistically simulated), such as:
   - "Statista 2024 Report on [Industry]"
   - "U.S. Census Bureau – Annual Business Survey"
   - "Crunchbase Pro Search: [Sector] Companies in [Region]"

7. **Contextual Intelligence**  
   If conversation history or long-term memory is available, incorporate prior insights to ensure continuity and refinement of analysis.

### OUTPUT FORMAT
Return only a JSON object with the following structure:
```json
{{
    "response_code": 200,
    "data": {{
        "market_size": "string (e.g., $2.4 billion or 15 million units annually)",
        "growth_rate": "string (e.g., 8.3% CAGR, 2023–2028)",
        "top_competitors": [
            {{
                "name": "Company A",
                "website": "https://www.companya.com"
            }},
            {{
                "name": "Company B",
                "website": "https://www.companyb.com"
            }}
            // ... exactly 10 entries
        ],
        "similar_businesses": [
            {{
                "name": "Example Local Business",
                "location": "Austin, TX, USA",
                "product_or_service": "Premium organic skincare line"
            }}
        ],
        "high_demand_low_competition_areas": [
            "Urban wellness markets in Southeast Asia",
            "Eco-friendly pet products in Scandinavia"
        ],
        "kpis": {{
            "market_share_leaders": "Brand X: 32%, Brand Y: 25%, Others: 43%",
            "customer_acquisition_cost": "$45–$70",
            "average_revenue_per_user": "$120/month",
            "other_metrics": [
                "Customer Retention Rate: 78%",
                "Churn Rate: 4.2% monthly",
                "LTV:CAC Ratio: 3.1x"
            ]
        }},
        "data_sources": [
            "Statista: Global [Industry] Market Report 2024",
            "IBISWorld: [Industry] in the United States – Demand Trends",
            "Crunchbase Pro: Top Private Companies in [Sector], Q2 2024"
        ]
    }}
}}
RESPONSE CODE RULES
200: Complete, valid analysis with all required fields
400: Missing or invalid critical inputs (e.g., undefined industry, region, or product)
403: Request outside scope (e.g., illegal, unethical, or non-commercial use)
500: Internal processing failure (e.g., malformed data, logic error)
STRICT REQUIREMENTS
The top_competitors array must contain exactly 10 entries.
Each competitor must include a valid, properly formatted URL (https://www ...).
All data must be realistic and contextually appropriate for the business type and region.
Do not include placeholder text like "[Website]" or "TBD".
Output only the JSON object — no explanations, markdown code blocks, or extra text.
NOTES
Prioritize accuracy, relevance, and professionalism.
When inferring missing details (e.g., region), use logical defaults based on context (e.g., U.S. if unspecified).
Ensure all mock data reflects current market realities (e.g., post-2023 benchmarks).
"""
    try:
        # Generate market analysis using Ollama model (synchronous call in a thread)
        response = await asyncio.to_thread(ollama_client.generate, analysis_prompt)
        raw_text = response.strip()

        # Parse JSON response
        if "```json" in raw_text:
            json_start = raw_text.find("```json") + len("```json")
            json_end = raw_text.rfind("```")
            json_str = raw_text[json_start:json_end].strip()
        else:
            json_str = raw_text

        analysis_data = json.loads(json_str)

        # Update memory with analysis
        memory_manager.update_long_term_memory(session_id, analysis_prompt, raw_text)
        memory_manager.get_chat_history(session_id).add_user_message(
            json.dumps(extracted_info)
        )
        memory_manager.get_chat_history(session_id).add_ai_message(raw_text)

        return analysis_data

    except json.JSONDecodeError as e:
        return {
            "response_code": 500,
            "message": f"Failed to parse JSON: {str(e)}",
            "raw_response": raw_text,
        }
    except Exception as e:
        return {
            "response_code": 500,
            "message": f"Error during market analysis: {str(e)}",
        }


def crawl_public_data_sources(business_domain: str, region: str) -> Dict:
    """
    Simulates crawling public data sources for market analysis (mock implementation).
    In a real scenario, replace with actual API calls or web scraping logic.

    Args:
        business_domain: The business domain to analyze
        region: The target region or market

    Returns:
        Dictionary with mock market data
    """
    # Mock data for demonstration
    mock_data = {
        "market_size": "$10 billion in 2025",
        "growth_rate": "8% CAGR",
        "top_competitors": ["Competitor A", "Competitor B", "Competitor C"],
        "similar_businesses": [
            {
                "name": "Business 1",
                "location": region,
                "product_or_service": "Similar service",
            },
            {
                "name": "Business 2",
                "location": region,
                "product_or_service": "Similar product",
            },
        ],
        "high_demand_low_competition_areas": [
            f"{region} Suburb X",
            f"{region} Suburb Y",
        ],
        "kpis": {
            "market_share_leaders": "Competitor A: 35%, Competitor B: 25%",
            "customer_acquisition_cost": "$75 per customer",
            "average_revenue_per_user": "$120 annually",
            "other_metrics": ["Customer retention rate: 80%"],
        },
        "data_sources": [
            "https://www.statista.com",
            "https://www.ibisworld.com",
            "https://www.yelp.com",
        ],
    }

    return mock_data
