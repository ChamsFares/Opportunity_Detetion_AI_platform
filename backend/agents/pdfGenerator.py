import json
import os
from datetime import datetime
from agents.ollama_api import OllamaQwen3Client


def load_json_data(filepath):
    """Load JSON data from file."""
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError as e:
        print(f"JSON error in {filepath}: {e}")
        return None
    except FileNotFoundError:
        print(f"File not found: {filepath}")
        return None


def generate_llm_conclusion(report_content):
    """Generate a conclusion for the report using Ollama Qwen3."""
    client = OllamaQwen3Client()

    prompt = f"""As an expert in strategic analysis and opportunity detection, carefully read the following report and write a **unique, concise, and decision-oriented conclusion** (150-200 words maximum).

This conclusion should synthesize the **key findings**, highlight **what the client can do better** to seize identified opportunities or fill strategic gaps, and propose the **best improvement or innovation paths**.

The text should be written **as a single flowing paragraph**, with a **professional, direct, and business-impact-focused tone**. The objective is to guide decision-making by providing a clear vision that is immediately actionable.

Here is the report to analyze:

{report_content}

Strategic Conclusion:
"""

    try:
        response = client.generate(prompt)
        return response.strip()
    except Exception as e:
        print(f"Error calling Ollama LLM: {e}")
        return "An AI-generated conclusion could not be produced due to an error."


def generate_markdown_report(data):
    """Generate the Markdown report from JSON data."""

    if not data:
        return "Error: Unable to load JSON data."

    # Start of report
    report = "# Strategic Analysis Report\n\n"
    report += (
        f"**Generation Date:** {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}\n\n"
    )

    # Executive Summary
    report += "## Executive Summary\n\n"
    if "metadata" in data and "data_sources" in data["metadata"]:
        sources = data["metadata"]["data_sources"]
        report += f"This report, based on the analysis of {sources.get('trends_analyzed', 'N/A')} trends and {sources.get('news_articles', 'N/A')} news articles, provides a synthesis of opportunities, gaps, strategic recommendations and risks in the financial sector, with a focus on AI adoption, digital transformation and regulatory compliance.\n\n"
    else:
        report += "This report provides a structured synthesis of identified performance gaps, highlighting improvement opportunities and strategic action levers.\n\n"

    # Section 1: Trend Analysis
    report += "## 1. Trend Analysis\n\n"
    if "trends" in data and data["trends"]:
        for trend in data["trends"][:5]:  # Limit to first 5 trends
            title = trend.get("title", "Untitled Trend")
            description = trend.get("description", "No description available")
            report += f"### {title}\n{description}\n\n"
    else:
        report += "No trend data available.\n\n"

    # Section 2: News Analysis
    report += "## 2. Market Intelligence\n\n"
    if "news" in data and data["news"]:
        for article in data["news"][:3]:  # Limit to first 3 articles
            title = article.get("title", "Untitled Article")
            summary = article.get("summary", "No summary available")
            report += f"### {title}\n{summary}\n\n"
    else:
        report += "No news data available.\n\n"

    # Section 3: Competitive Analysis
    report += "## 3. Competitive Landscape\n\n"
    if "competitors" in data and data["competitors"]:
        report += "### Key Competitors Identified\n\n"
        for competitor in data["competitors"][:5]:  # Limit to first 5 competitors
            name = competitor.get("name", "Unknown Company")
            website = competitor.get("website", "No website available")
            description = competitor.get("description", "No description available")
            report += f"**{name}** ({website})\n{description}\n\n"
    else:
        report += "No competitor data available.\n\n"

    # Section 4: Opportunities & Recommendations
    report += "## 4. Strategic Opportunities & Recommendations\n\n"
    if "analysis" in data:
        analysis = data["analysis"]
        
        if "opportunities" in analysis:
            report += "### Market Opportunities\n\n"
            for opp in analysis["opportunities"][:3]:
                title = opp.get("title", "Opportunity")
                description = opp.get("description", "No description")
                report += f"- **{title}**: {description}\n"
            report += "\n"
            
        if "recommendations" in analysis:
            report += "### Strategic Recommendations\n\n"
            for rec in analysis["recommendations"][:3]:
                title = rec.get("title", "Recommendation")
                description = rec.get("description", "No description")
                priority = rec.get("priority", "Medium")
                report += f"- **{title}** (Priority: {priority}): {description}\n"
            report += "\n"
    else:
        report += "No strategic analysis data available.\n\n"

    # Section 5: Risk Assessment
    report += "## 5. Risk Assessment\n\n"
    if "analysis" in data and "risks" in data["analysis"]:
        for risk in data["analysis"]["risks"][:3]:
            title = risk.get("title", "Risk")
            description = risk.get("description", "No description")
            probability = risk.get("probability", "Unknown")
            report += f"- **{title}** (Probability: {probability}): {description}\n"
        report += "\n"
    else:
        report += "No risk assessment data available.\n\n"

    return report


def generate_report(analysis_result):
    """Generate a report from analysis result data."""
    try:
        # Save the analysis result to a JSON file for processing
        data_file = "analysed_data.json"
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(analysis_result, f, indent=2, ensure_ascii=False)
        
        # Use the existing create_pdf_report function
        return create_pdf_report()
    except Exception as e:
        print(f"Error generating report: {e}")
        return None


def create_pdf_report():
    """Main function to create the PDF report."""
    # Load data
    data_file = "analysed_data.json"
    if not os.path.exists(data_file):
        print(f"Data file {data_file} not found.")
        return
    
    data = load_json_data(data_file)
    if not data:
        print("Failed to load data.")
        return
    
    # Generate markdown report
    markdown_content = generate_markdown_report(data)
    
    # Generate AI conclusion
    ai_conclusion = generate_llm_conclusion(markdown_content)
    
    # Add conclusion to markdown
    final_report = markdown_content + f"\n## AI Strategic Conclusion\n\n{ai_conclusion}\n"
    
    # Save markdown file
    output_file = f"strategic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_report)
    
    print(f"Strategic report generated: {output_file}")
    return output_file


if __name__ == "__main__":
    create_pdf_report()
