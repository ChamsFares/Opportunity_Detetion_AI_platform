import json
import os
import re
import warnings
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from textblob import TextBlob
from working_space import extract_news_by_keywords

from agents.LinkedInTrendAnalyzer import LinkedInTrendAnalyzer
from agents.NewsProcessor import OllamaTrendIdentifier, NewsProcessor

print(os.getcwd())


def emerging_trends(sample_data):
    # Initialize the analyzer
    analyzer = LinkedInTrendAnalyzer(sample_data)

    # Run different analyses
    print("🔍 Analyzing LinkedIn Content Trends...")
    print("=" * 50)

    # 1. Engagement Analysis
    engagement_trends = analyzer.analyze_engagement_trends()
    print("📈 Engagement Trends Analysis Complete")

    # 2. Content Analysis
    content_trends = analyzer.analyze_content_trends()
    print("📝 Content Trends Analysis Complete")

    # 3. Viral Patterns
    viral_patterns = analyzer.identify_viral_patterns()
    print("🚀 Viral Patterns Analysis Complete")

    # 4. Generate Report
    report = analyzer.generate_insights_report()

    # Save report to file
    with open(
        f'linkedin_trends_report_{datetime.now().strftime("%Y%m%d_%H%M")}.md',
        "w",
        encoding="utf-8",
    ) as f:
        f.write(report)

    print("\n📊 Full Report Generated and Saved!")
    print("\n" + "=" * 50)
    print("KEY INSIGHTS:")
    print("=" * 50)

    # Print key insights
    overall_stats = engagement_trends.get("overall_stats", {})
    print(f"📱 Total Posts: {overall_stats.get('total_posts', 0)}")
    print(f"❤️  Average Likes: {overall_stats.get('avg_likes', 0):.1f}")
    print(f"💬 Average Comments: {overall_stats.get('avg_comments', 0):.1f}")
    print(f"🔄 Average Reposts: {overall_stats.get('avg_reposts', 0):.1f}")
    print(
        f"📊 Average Engagement Rate: {overall_stats.get('avg_engagement_rate', 0):.2f}%"
    )

    # Top hashtags
    hashtag_trends = content_trends.get("hashtag_trends", {})
    top_hashtags = hashtag_trends.get("top_hashtags", {})
    print(f"\n🏷️  Top 5 Hashtags:")
    hashs = []
    for i, (hashtag, count) in enumerate(list(top_hashtags.items()), 1):
        print(f"   {i}. {hashtag}: {count} uses")
        hashs.append(hashtag)

    hash_news = extract_news_by_keywords(hashs)

    processor = NewsProcessor(hash_news)
    parsed_news = processor.parse_news()
    filtered_news = processor.filter_old_news(days_threshold=215)

    print("\nFiltered News (last 60 days):", json.dumps(filtered_news, indent=2))

    # Use OllamaTrendIdentifier instead of Gemini
    ollama_identifier = OllamaTrendIdentifier()
    trends = ollama_identifier.identify_trends(filtered_news)
    return trends


# # Create visualizations
# print("\n📊 Creating Visualizations...")
# analyzer.create_visualizations(save_plots=True)

# print("\n✅ Analysis Complete! Check the generated files:")
# print(f"   📄 Report: linkedin_trends_report_{datetime.now().strftime('%Y%m%d_%H%M')}.md")
# print(f"   📊 Charts: linkedin_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.png")
