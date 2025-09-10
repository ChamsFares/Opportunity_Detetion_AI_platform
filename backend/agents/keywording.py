import json
import os
from typing import Any, Dict, List, Optional

from agents.ollama_api import OllamaQwen3Client


class KeywordIdentifier:
    def __init__(self):
        self.client = OllamaQwen3Client()

    def identify_keywords(
        self, company_name: str, sector_name: str, service_name: str
    ) -> Dict[str, Any]:
        """
        Identify keywords directly and indirectly related to company, sector, and service
        for comprehensive analysis use cases.

        Args:
            company_name: Name of the company
            sector_name: Industry sector
            service_name: Specific service or product

        Returns:
            Dictionary containing categorized keywords or error information
        """

        # Enhanced function declaration with more detailed structure
        keyword_function = {
            "name": "identify_analysis_keywords",
            "description": "Identify comprehensive keywords for business analysis, including direct and indirect terms related to company, sector, and services",
            "parameters": {
                "type": "object",
                "properties": {
                    "direct_keywords": {
                        "type": "array",
                        "description": "Keywords directly related to the company, sector, or service",
                        "items": {
                            "type": "string",
                            "description": "A keyword directly related to the business",
                        },
                    },
                    "indirect_keywords": {
                        "type": "array",
                        "description": "Keywords indirectly related that could impact the business",
                        "items": {
                            "type": "string",
                            "description": "A keyword indirectly related to the business",
                        },
                    },
                    "industry_terms": {
                        "type": "array",
                        "description": "Industry-specific terminology and jargon",
                        "items": {
                            "type": "string",
                            "description": "Industry-specific term",
                        },
                    },
                    "competitive_keywords": {
                        "type": "array",
                        "description": "Keywords related to competitors and market positioning",
                        "items": {
                            "type": "string",
                            "description": "Competitive or market-related keyword",
                        },
                    },
                    "trend_keywords": {
                        "type": "array",
                        "description": "Keywords related to current trends affecting the sector",
                        "items": {
                            "type": "string",
                            "description": "Trend-related keyword",
                        },
                    },
                    "regulatory_keywords": {
                        "type": "array",
                        "description": "Keywords related to regulations, compliance, and legal aspects",
                        "items": {
                            "type": "string",
                            "description": "Regulatory or compliance keyword",
                        },
                    },
                },
                "required": ["direct_keywords", "indirect_keywords", "industry_terms"],
            },
        }

        # Create comprehensive prompt for better keyword generation
        prompt = f"""
        As an expert business analyst, identify comprehensive keywords for analysis purposes related to:
        
        Company: {company_name}
        Sector: {sector_name} 
        Service: {service_name}
        
        Please provide keywords in the following categories:
        
        1. DIRECT KEYWORDS: Terms directly related to the company name, sector, and service
        2. INDIRECT KEYWORDS: Terms that could indirectly impact the business (economic factors, social trends, etc.)
        3. INDUSTRY TERMS: Technical jargon, industry-specific terminology
        4. COMPETITIVE KEYWORDS: Terms related to competitors, market share, positioning
        5. TREND KEYWORDS: Current trends, emerging technologies, market shifts affecting this sector
        6. REGULATORY KEYWORDS: Compliance, regulations, legal requirements relevant to this sector
        
        Focus on keywords that would be valuable for:
        - Market analysis and research
        - Competitive intelligence
        - Trend monitoring
        - Risk assessment
        - Opportunity identification
        
        Provide 5-15 keywords per category where applicable.
        """

        try:
            # Send request to Ollama
            response = self.client.generate(prompt)

            # Try to parse JSON response
            try:
                keywords_data = json.loads(response)
            except json.JSONDecodeError:
                # If not valid JSON, try to extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    try:
                        keywords_data = json.loads(json_match.group())
                    except json.JSONDecodeError:
                        keywords_data = None
                else:
                    keywords_data = None

            if keywords_data:
                # Add metadata
                keywords_data["metadata"] = {
                    "company_name": company_name,
                    "sector_name": sector_name,
                    "service_name": service_name,
                    "total_keywords": sum(
                        len(v)
                        for v in keywords_data.values()
                        if isinstance(v, list)
                    ),
                    "generation_successful": True,
                }

                return keywords_data
            else:
                return {
                    "error": "Could not parse keywords from response",
                    "raw_response": response[:500] if len(response) > 500 else response,
                    "metadata": {
                        "company_name": company_name,
                        "sector_name": sector_name,
                        "service_name": service_name,
                        "generation_successful": False,
                    },
                }

        except Exception as e:
            print(f"Error generating keywords: {str(e)}")
            return {
                "error": str(e),
                "metadata": {
                    "company_name": company_name,
                    "sector_name": sector_name,
                    "service_name": service_name,
                    "generation_successful": False,
                },
            }

    def get_all_keywords_flat(self, keywords_data: Dict[str, Any]) -> List[str]:
        """
        Extract all keywords into a single flat list for simple analysis use cases

        Args:
            keywords_data: Result from identify_keywords()

        Returns:
            List of all keywords combined
        """
        all_keywords = []

        keyword_categories = [
            "direct_keywords",
            "indirect_keywords",
            "industry_terms",
            "competitive_keywords",
            "trend_keywords",
            "regulatory_keywords",
        ]

        for category in keyword_categories:
            if category in keywords_data and isinstance(keywords_data[category], list):
                all_keywords.extend(keywords_data[category])

        # Remove duplicates while preserving order
        return list(dict.fromkeys(all_keywords))

    def print_keywords_summary(self, keywords_data: Dict[str, Any]) -> None:
        """Print a formatted summary of the identified keywords"""

        if "error" in keywords_data:
            print(f"❌ Error: {keywords_data['error']}")
            return

        metadata = keywords_data.get("metadata", {})
        print(f"\n🎯 Keywords for: {metadata.get('company_name', 'N/A')}")
        print(f"📊 Sector: {metadata.get('sector_name', 'N/A')}")
        print(f"🔧 Service: {metadata.get('service_name', 'N/A')}")
        print(f"📈 Total Keywords: {metadata.get('total_keywords', 0)}")
        print("-" * 60)

        categories = {
            "direct_keywords": "🎯 Direct Keywords",
            "indirect_keywords": "🔄 Indirect Keywords",
            "industry_terms": "🏭 Industry Terms",
            "competitive_keywords": "⚔️ Competitive Keywords",
            "trend_keywords": "📈 Trend Keywords",
            "regulatory_keywords": "📋 Regulatory Keywords",
        }

        for key, title in categories.items():
            if key in keywords_data and keywords_data[key]:
                print(f"\n{title}:")
                for keyword in keywords_data[key]:
                    print(f"  • {keyword}")


# Example usage and testing
if __name__ == "__main__":
    # Initialize the keyword identifier (no API key needed for Ollama)
    keyword_identifier = KeywordIdentifier()

    # Test the function
    company = "Talan"
    sector = "Banking"
    service = "Artificial Intelligence"

    print("Generating keywords...")
    result = keyword_identifier.identify_keywords(company, sector, service)

    # Display results
    keyword_identifier.print_keywords_summary(result)

    # Get flat list for analysis
    if "error" not in result:
        flat_keywords = keyword_identifier.get_all_keywords_flat(result)
        print(f"\n📋 All Keywords (Flat List): {len(flat_keywords)} total")
        print(
            f"Keywords: {', '.join(flat_keywords[:10])}..."
            if len(flat_keywords) > 10
            else f"Keywords: {', '.join(flat_keywords)}"
        )

        # Save to JSON for further analysis
        with open("keywords_analysis.json", "w") as f:
            json.dump(result, f, indent=2)
        print("\n💾 Keywords saved to 'keywords_analysis.json'")


# Alternative simpler version if you prefer your original structure
def identify_keywords_simple(
    company_name: str, sector_name: str, service_name: str
) -> Dict[str, Any]:
    """Simplified version using Ollama Qwen3"""

    client = OllamaQwen3Client()

    enhanced_prompt = f"""
    Generate comprehensive keywords for business analysis related to:
    - Company: {company_name}
    - Sector: {sector_name}  
    - Service: {service_name}
    
    Include both direct keywords (company/sector/service related) and indirect keywords 
    (market trends, economic factors, regulatory changes, competitive landscape, etc.)
    that could be valuable for analysis and monitoring purposes.
    
    Return a JSON object with the following structure:
    {{
        "keywords": ["keyword1", "keyword2", ...],
        "keyword_categories": {{
            "direct": ["direct keyword1", ...],
            "indirect": ["indirect keyword1", ...],
            "industry": ["industry keyword1", ...],
            "competitive": ["competitive keyword1", ...]
        }}
    }}
    
    Provide 20-40 total keywords optimized for:
    - Market research and analysis
    - Competitive intelligence  
    - Trend monitoring
    - Risk assessment
    """

    try:
        response = client.generate(enhanced_prompt)
        
        # Try to parse JSON response
        try:
            result = json.loads(response)
            return result
        except json.JSONDecodeError:
            # If not valid JSON, try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    return result
                except json.JSONDecodeError:
                    pass
            
            # Fallback: return a basic structure
            return {
                "error": "Could not parse keywords from response",
                "raw_response": response[:500] if len(response) > 500 else response
            }

    except Exception as e:
        return {"error": str(e)}
