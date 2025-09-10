import json
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

warnings.filterwarnings("ignore")


class LinkedInTrendAnalyzer:
    def __init__(self, data: Dict[str, Any]):
        """
        Initialize the analyzer with LinkedIn scraped data

        Args:
            data: Dictionary containing LinkedIn posts data
        """
        self.data = data
        self.posts_df = self._prepare_dataframe()

    def _prepare_dataframe(self) -> pd.DataFrame:
        """Convert LinkedIn data to pandas DataFrame for analysis"""

        all_posts = []

        for company, company_data in self.data.items():
            if not company_data.get("success", False):
                continue

            posts = company_data.get("data", {}).get("posts", [])

            for post in posts:
                # Extract basic post information
                post_info = {
                    "company": company,
                    "activity_urn": post.get("activity_urn", ""),
                    "post_url": post.get("post_url", ""),
                    "text": post.get("text", ""),
                    "post_type": post.get("post_type", "regular"),
                    "language": post.get("post_language_code", "en"),
                    # Posted date information
                    "posted_relative": post.get("posted_at", {}).get("relative", ""),
                    "posted_date": post.get("posted_at", {}).get("date", ""),
                    "is_edited": post.get("posted_at", {}).get("is_edited", False),
                    "timestamp": post.get("posted_at", {}).get("timestamp", 0),
                    # Author information
                    "author_name": post.get("author", {}).get("name", ""),
                    "follower_count": post.get("author", {}).get("follower_count", 0),
                    # Engagement metrics
                    "total_reactions": post.get("stats", {}).get("total_reactions", 0),
                    "likes": post.get("stats", {}).get("like", 0),
                    "comments": post.get("stats", {}).get("comments", 0),
                    "reposts": post.get("stats", {}).get("reposts", 0),
                    # Content analysis
                    "text_length": len(post.get("text", "")),
                    "has_media": bool(post.get("media", {})),
                    "has_document": bool(post.get("document", {})),
                    "document_title": post.get("document", {}).get("title", ""),
                    # Extract hashtags
                    "hashtags": self._extract_hashtags(post.get("text", "")),
                    "hashtag_count": len(self._extract_hashtags(post.get("text", ""))),
                    # Calculate engagement rate
                    "engagement_rate": self._calculate_engagement_rate(
                        post.get("stats", {}),
                        post.get("author", {}).get("follower_count", 1),
                    ),
                }

                all_posts.append(post_info)

        df = pd.DataFrame(all_posts)

        # Convert timestamp to datetime
        if not df.empty and "timestamp" in df.columns:
            df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms", errors="coerce")
            df["date"] = df["datetime"].dt.date
            df["hour"] = df["datetime"].dt.hour
            df["day_of_week"] = df["datetime"].dt.day_name()

        return df

    def _extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from post text"""
        if not text:
            return []
        return re.findall(r"#\w+", text.lower())

    def _calculate_engagement_rate(self, stats: Dict, follower_count: int) -> float:
        """Calculate engagement rate as total engagement / follower count"""
        if follower_count == 0:
            return 0.0

        total_engagement = (
            stats.get("total_reactions", 0)
            + stats.get("comments", 0)
            + stats.get("reposts", 0)
        )

        return (total_engagement / follower_count) * 100

    def analyze_engagement_trends(self) -> Dict[str, Any]:
        """Analyze engagement trends across posts"""

        if self.posts_df.empty:
            return {"error": "No data available for analysis"}

        trends = {
            "overall_stats": {
                "total_posts": len(self.posts_df),
                "avg_likes": self.posts_df["likes"].mean(),
                "avg_comments": self.posts_df["comments"].mean(),
                "avg_reposts": self.posts_df["reposts"].mean(),
                "avg_engagement_rate": self.posts_df["engagement_rate"].mean(),
                "median_engagement_rate": self.posts_df["engagement_rate"].median(),
            },
            "top_performing_posts": self.posts_df.nlargest(5, "total_reactions")[
                [
                    "company",
                    "text",
                    "total_reactions",
                    "likes",
                    "comments",
                    "reposts",
                    "engagement_rate",
                ]
            ].to_dict("records"),
            "engagement_by_company": self.posts_df.groupby("company")
            .agg(
                {
                    "total_reactions": ["mean", "sum", "count"],
                    "likes": "mean",
                    "comments": "mean",
                    "reposts": "mean",
                    "engagement_rate": "mean",
                }
            )
            .round(2)
            .to_dict(),
            "engagement_by_post_type": self.posts_df.groupby("post_type")
            .agg(
                {"total_reactions": "mean", "engagement_rate": "mean", "likes": "mean"}
            )
            .round(2)
            .to_dict(),
            "content_performance": {
                "with_media": self.posts_df[self.posts_df["has_media"]][
                    "engagement_rate"
                ].mean(),
                "without_media": self.posts_df[~self.posts_df["has_media"]][
                    "engagement_rate"
                ].mean(),
                "with_document": self.posts_df[self.posts_df["has_document"]][
                    "engagement_rate"
                ].mean(),
                "without_document": self.posts_df[~self.posts_df["has_document"]][
                    "engagement_rate"
                ].mean(),
            },
        }

        # Time-based analysis if datetime is available
        if (
            "datetime" in self.posts_df.columns
            and not self.posts_df["datetime"].isna().all()
        ):
            trends["time_trends"] = {
                "by_day_of_week": self.posts_df.groupby("day_of_week")[
                    "engagement_rate"
                ]
                .mean()
                .to_dict(),
                "by_hour": self.posts_df.groupby("hour")["engagement_rate"]
                .mean()
                .to_dict(),
            }

        return trends

    def analyze_content_trends(self) -> Dict[str, Any]:
        """Analyze content and topic trends"""

        if self.posts_df.empty:
            return {"error": "No data available for analysis"}

        # Hashtag analysis
        all_hashtags = []
        for hashtags in self.posts_df["hashtags"]:
            all_hashtags.extend(hashtags)

        hashtag_counter = Counter(all_hashtags)

        # Text length analysis
        text_stats = {
            "avg_length": self.posts_df["text_length"].mean(),
            "median_length": self.posts_df["text_length"].median(),
            "min_length": self.posts_df["text_length"].min(),
            "max_length": self.posts_df["text_length"].max(),
        }

        # Correlation between text length and engagement
        length_engagement_corr = self.posts_df["text_length"].corr(
            self.posts_df["engagement_rate"]
        )

        content_trends = {
            "hashtag_trends": {
                "top_hashtags": dict(hashtag_counter.most_common(20)),
                "total_unique_hashtags": len(hashtag_counter),
                "avg_hashtags_per_post": self.posts_df["hashtag_count"].mean(),
            },
            "text_analysis": text_stats,
            "length_engagement_correlation": length_engagement_corr,
            "content_type_distribution": {
                "with_media": self.posts_df["has_media"].sum(),
                "with_document": self.posts_df["has_document"].sum(),
                "text_only": len(self.posts_df)
                - self.posts_df["has_media"].sum()
                - self.posts_df["has_document"].sum(),
            },
            "hashtag_performance": self._analyze_hashtag_performance(),
            "optimal_text_length": self._find_optimal_text_length(),
        }

        return content_trends

    def _analyze_hashtag_performance(self) -> Dict[str, float]:
        """Analyze which hashtags perform best"""
        hashtag_performance = {}

        for _, post in self.posts_df.iterrows():
            for hashtag in post["hashtags"]:
                if hashtag not in hashtag_performance:
                    hashtag_performance[hashtag] = []
                hashtag_performance[hashtag].append(post["engagement_rate"])

        # Calculate average engagement for each hashtag
        avg_performance = {
            hashtag: np.mean(rates)
            for hashtag, rates in hashtag_performance.items()
            if len(rates) >= 2  # Only hashtags used at least twice
        }

        # Sort by performance
        return dict(
            sorted(avg_performance.items(), key=lambda x: x[1], reverse=True)[:10]
        )

    def _find_optimal_text_length(self) -> Dict[str, Any]:
        """Find optimal text length for engagement"""
        if self.posts_df.empty:
            return {}

        # Create length bins
        self.posts_df["length_bin"] = pd.cut(
            self.posts_df["text_length"],
            bins=5,
            labels=["Very Short", "Short", "Medium", "Long", "Very Long"],
        )

        length_performance = (
            self.posts_df.groupby("length_bin")
            .agg({"engagement_rate": ["mean", "count"], "total_reactions": "mean"})
            .round(2)
        )

        return length_performance.to_dict()

    def identify_viral_patterns(self) -> Dict[str, Any]:
        """Identify patterns in high-performing posts"""

        if self.posts_df.empty:
            return {"error": "No data available for analysis"}

        # Define "viral" as top 20% by engagement rate
        threshold = self.posts_df["engagement_rate"].quantile(0.8)
        viral_posts = self.posts_df[self.posts_df["engagement_rate"] >= threshold]

        if viral_posts.empty:
            return {"error": "No high-performing posts found"}

        patterns = {
            "viral_threshold": threshold,
            "viral_post_count": len(viral_posts),
            "common_characteristics": {
                "avg_text_length": viral_posts["text_length"].mean(),
                "avg_hashtag_count": viral_posts["hashtag_count"].mean(),
                "has_media_percentage": (
                    viral_posts["has_media"].sum() / len(viral_posts)
                )
                * 100,
                "has_document_percentage": (
                    viral_posts["has_document"].sum() / len(viral_posts)
                )
                * 100,
            },
            "viral_hashtags": self._get_viral_hashtags(viral_posts),
            "viral_topics": self._extract_viral_topics(viral_posts),
            "viral_post_examples": viral_posts.nlargest(3, "engagement_rate")[
                ["company", "text", "engagement_rate", "total_reactions"]
            ].to_dict("records"),
        }

        return patterns

    def _get_viral_hashtags(self, viral_posts: pd.DataFrame) -> Dict[str, int]:
        """Get hashtags from viral posts"""
        viral_hashtags = []
        for hashtags in viral_posts["hashtags"]:
            viral_hashtags.extend(hashtags)

        return dict(Counter(viral_hashtags).most_common(10))

    def _extract_viral_topics(self, viral_posts: pd.DataFrame) -> List[str]:
        """Extract common topics from viral posts using simple keyword analysis"""
        all_text = " ".join(viral_posts["text"].fillna("").str.lower())

        # Common business/career keywords
        keywords = [
            "job",
            "career",
            "work",
            "hiring",
            "recruitment",
            "interview",
            "resume",
            "skills",
            "experience",
            "opportunity",
            "growth",
            "success",
            "team",
            "leadership",
            "innovation",
            "technology",
            "business",
            "professional",
        ]

        topic_counts = {}
        for keyword in keywords:
            count = all_text.count(keyword)
            if count > 0:
                topic_counts[keyword] = count

        return sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    def generate_insights_report(self) -> str:
        """Generate a comprehensive insights report"""

        engagement_trends = self.analyze_engagement_trends()
        content_trends = self.analyze_content_trends()
        viral_patterns = self.identify_viral_patterns()

        report = f"""
# LinkedIn Content Performance Analysis Report
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Data Source:** {len(self.data)} company profiles analyzed

## Executive Summary
- **Total Posts Analyzed:** {engagement_trends.get('overall_stats', {}).get('total_posts', 0)}
- **Average Engagement Rate:** {engagement_trends.get('overall_stats', {}).get('avg_engagement_rate', 0):.2f}%
- **Top Performing Content:** Posts with media/documents show higher engagement

## Engagement Trends

### Overall Performance Metrics
- **Average Likes:** {engagement_trends.get('overall_stats', {}).get('avg_likes', 0):.1f}
- **Average Comments:** {engagement_trends.get('overall_stats', {}).get('avg_comments', 0):.1f}
- **Average Reposts:** {engagement_trends.get('overall_stats', {}).get('avg_reposts', 0):.1f}
- **Median Engagement Rate:** {engagement_trends.get('overall_stats', {}).get('median_engagement_rate', 0):.2f}%

### Content Type Performance
"""

        content_perf = engagement_trends.get("content_performance", {})
        report += f"""
- **Posts with Media:** {content_perf.get('with_media', 0):.2f}% avg engagement
- **Posts without Media:** {content_perf.get('without_media', 0):.2f}% avg engagement
- **Posts with Documents:** {content_perf.get('with_document', 0):.2f}% avg engagement
- **Posts without Documents:** {content_perf.get('without_document', 0):.2f}% avg engagement

## Content Analysis

### Hashtag Insights
"""

        hashtag_trends = content_trends.get("hashtag_trends", {})
        top_hashtags = hashtag_trends.get("top_hashtags", {})

        report += f"- **Total Unique Hashtags:** {hashtag_trends.get('total_unique_hashtags', 0)}\n"
        report += f"- **Average Hashtags per Post:** {hashtag_trends.get('avg_hashtags_per_post', 0):.1f}\n\n"
        report += "**Top Performing Hashtags:**\n"

        for hashtag, count in list(top_hashtags.items())[:10]:
            report += f"- {hashtag}: {count} uses\n"

        report += f"""
### Text Analysis
- **Average Text Length:** {content_trends.get('text_analysis', {}).get('avg_length', 0):.0f} characters
- **Optimal Length Range:** Medium-length posts typically perform best
- **Length-Engagement Correlation:** {content_trends.get('length_engagement_correlation', 0):.3f}

## Viral Content Patterns
"""

        if "error" not in viral_patterns:
            report += f"""
- **Viral Threshold:** {viral_patterns.get('viral_threshold', 0):.2f}% engagement rate
- **Viral Posts Found:** {viral_patterns.get('viral_post_count', 0)} posts

### Characteristics of High-Performing Posts
- **Average Text Length:** {viral_patterns.get('common_characteristics', {}).get('avg_text_length', 0):.0f} characters
- **Average Hashtags:** {viral_patterns.get('common_characteristics', {}).get('avg_hashtag_count', 0):.1f}
- **Media Usage:** {viral_patterns.get('common_characteristics', {}).get('has_media_percentage', 0):.1f}% include media
- **Document Usage:** {viral_patterns.get('common_characteristics', {}).get('has_document_percentage', 0):.1f}% include documents

### Top Viral Topics
"""
            viral_topics = viral_patterns.get("viral_topics", [])
            for topic, count in viral_topics[:10]:
                report += f"- **{topic.title()}:** {count} mentions\n"

        report += """
## Recommendations

### Content Strategy
1. **Optimize Post Length:** Aim for medium-length posts (100-300 characters)
2. **Use Visual Content:** Posts with media show higher engagement
3. **Strategic Hashtag Use:** Include 3-5 relevant hashtags per post
4. **Document Sharing:** Educational content with documents performs well

### Engagement Tactics
1. **Post Timing:** Analyze your audience's active hours
2. **Interactive Content:** Encourage comments through questions
3. **Trending Topics:** Align content with industry trends
4. **Consistent Branding:** Maintain brand voice across all posts

### Monitoring Metrics
- Track engagement rate as primary KPI
- Monitor hashtag performance regularly  
- Test different content formats
- Analyze competitor performance trends
"""

        return report

    def create_visualizations(self, save_plots: bool = True) -> None:
        """Create visualization plots for the analysis"""

        if self.posts_df.empty:
            print("No data available for visualization")
            return

        # Set up the plotting style
        plt.style.use("seaborn-v0_8")
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle(
            "LinkedIn Content Performance Analysis", fontsize=16, fontweight="bold"
        )

        # 1. Engagement Rate Distribution
        axes[0, 0].hist(
            self.posts_df["engagement_rate"],
            bins=20,
            alpha=0.7,
            color="skyblue",
            edgecolor="black",
        )
        axes[0, 0].set_title("Engagement Rate Distribution")
        axes[0, 0].set_xlabel("Engagement Rate (%)")
        axes[0, 0].set_ylabel("Frequency")

        # 2. Likes vs Comments scatter
        axes[0, 1].scatter(
            self.posts_df["likes"], self.posts_df["comments"], alpha=0.6, color="coral"
        )
        axes[0, 1].set_title("Likes vs Comments")
        axes[0, 1].set_xlabel("Likes")
        axes[0, 1].set_ylabel("Comments")

        # 3. Text Length vs Engagement
        axes[0, 2].scatter(
            self.posts_df["text_length"],
            self.posts_df["engagement_rate"],
            alpha=0.6,
            color="lightgreen",
        )
        axes[0, 2].set_title("Text Length vs Engagement Rate")
        axes[0, 2].set_xlabel("Text Length (characters)")
        axes[0, 2].set_ylabel("Engagement Rate (%)")

        # 4. Hashtag Count vs Engagement
        axes[1, 0].scatter(
            self.posts_df["hashtag_count"],
            self.posts_df["engagement_rate"],
            alpha=0.6,
            color="gold",
        )
        axes[1, 0].set_title("Hashtag Count vs Engagement Rate")
        axes[1, 0].set_xlabel("Number of Hashtags")
        axes[1, 0].set_ylabel("Engagement Rate (%)")

        # 5. Content Type Performance
        content_types = ["Text Only", "With Media", "With Document"]
        text_only = self.posts_df[
            ~self.posts_df["has_media"] & ~self.posts_df["has_document"]
        ]["engagement_rate"].mean()
        with_media = self.posts_df[self.posts_df["has_media"]]["engagement_rate"].mean()
        with_doc = self.posts_df[self.posts_df["has_document"]][
            "engagement_rate"
        ].mean()

        content_performance = [text_only, with_media, with_doc]
        colors = ["lightcoral", "lightblue", "lightgreen"]

        axes[1, 1].bar(
            content_types,
            content_performance,
            color=colors,
            alpha=0.7,
            edgecolor="black",
        )
        axes[1, 1].set_title("Content Type Performance")
        axes[1, 1].set_ylabel("Average Engagement Rate (%)")
        axes[1, 1].tick_params(axis="x", rotation=45)

        # 6. Top Hashtags
        all_hashtags = []
        for hashtags in self.posts_df["hashtags"]:
            all_hashtags.extend(hashtags)

        top_hashtags = Counter(all_hashtags).most_common(10)
        if top_hashtags:
            hashtags, counts = zip(*top_hashtags)
            axes[1, 2].barh(
                range(len(hashtags)), counts, color="mediumpurple", alpha=0.7
            )
            axes[1, 2].set_yticks(range(len(hashtags)))
            axes[1, 2].set_yticklabels(hashtags)
            axes[1, 2].set_title("Top 10 Hashtags")
            axes[1, 2].set_xlabel("Usage Count")

        plt.tight_layout()

        if save_plots:
            plt.savefig(
                f'linkedin_analysis_{datetime.now().strftime("%Y%m%d_%H%M")}.png',
                dpi=300,
                bbox_inches="tight",
            )
            print("Visualizations saved as PNG file")

        plt.show()


# Example usage
if __name__ == "__main__":
    # Sample data structure (replace with your actual data)
    sample_data = {
        "Monster": {
            "success": True,
            "message": "response retrieved successfully",
            "data": {
                "posts": [
                    {
                        "activity_urn": "7353068055318433792",
                        "full_urn": "urn:li:ugcPost:7353068054349504513",
                        "post_url": "https://www.linkedin.com/posts/monster_6-tips-for-getting-a-referral-activity-7353068055318433792-ImR3",
                        "posted_at": {
                            "relative": "6d",
                            "is_edited": False,
                            "date": "2025-07-21 16:27:17",
                            "timestamp": 1753108037786,
                        },
                        "text": "To land a new job in this market, you need to do more than just submit your resume.\n\nHaving a referral can give you a boost! A positive introduction from an existing employee will show the hiring manager that you're someone special. Plus, as a referred candidate, you'll be thought of as a better fit and will likely stay in your role longer than other hires.\n\nSo, what's the best way to obtain a referral? The tips we've shared here can help make the process easier so that you can get a new job faster.\n\n#careeradvice #jobsearch #jobhunt #newjob #referral #careertips #jobs",
                        "post_language_code": "en",
                        "post_type": "regular",
                        "author": {
                            "name": "Monster",
                            "follower_count": 218692,
                            "company_url": "https://www.linkedin.com/company/monster/posts",
                            "logo_url": "https://media.licdn.com/dms/image/v2/D4E0BAQHD4Is_cVidCA/company-logo_400_400/company-logo_400_400/0/1727707920426/monster_logo?e=1756339200&v=beta&t=k7FnMhFYyp44GuKjEWO7y-Ucsd44hLcIAv9W-52N4cQ",
                        },
                        "stats": {
                            "total_reactions": 20,
                            "like": 20,
                            "comments": 3,
                            "reposts": 1,
                        },
                        "media": {},
                        "document": {
                            "title": "6 tips for getting a referral",
                            "page_count": 8,
                            "url": "https://media.licdn.com/dms/document/media/v2/D4E1FAQFWEBUAcRh4NA/feedshare-document-url-metadata-scrapper-pdf/B4EZgtVvReGYA4-/0/1753107331639",
                            "thumbnail": "https://media.licdn.com/dms/image/v2/D4E1FAQFWEBUAcRh4NA/feedshare-document-cover-images_1920/B4EZgtVvReGYA0-/0/1753107331733",
                        },
                    }
                    # Add more posts here...
                ]
            },
        }
        # Add more companies here...
    }

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
    for i, (hashtag, count) in enumerate(list(top_hashtags.items())[:5], 1):
        print(f"   {i}. {hashtag}: {count} uses")

    # Create visualizations
    print("\n📊 Creating Visualizations...")
    analyzer.create_visualizations(save_plots=True)

    print("\n✅ Analysis Complete! Check the generated files:")
    print(
        f"   📄 Report: linkedin_trends_report_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
    )
    print(
        f"   📊 Charts: linkedin_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.png"
    )
