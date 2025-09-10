
import json
from agents.csv_read import GoogleNewsRSSScaper
from agents.ollama_api import OllamaQwen3Client



def extract_news(company_name, activity_sctor, service_name):
    try:
        # Initialize the Ollama Qwen3 client
        ollama_client = OllamaQwen3Client()

        print(f"\n{'='*50}")
        print(f"Testing sector: {activity_sctor}")
        print("=" * 50)
        print(activity_sctor)

        # Use Ollama to generate topics (specify_topics)
        result = ollama_client.specify_topics(activity_sctor + service_name)

        if result and result.get("selected_topics"):
            print(f"\nSelected topics for {activity_sctor}:")
            for i, topic in enumerate(result["selected_topics"], 1):
                print(f"{i}. {topic.get('topic_name')}: {topic.get('topic_key')}")

            # now we will discuss with the llm to return to us the related news topic directly or even indirectly by sector
            scraper = GoogleNewsRSSScaper("google_news_articles.csv")
            articles_dict = {}
            for i, topic in enumerate(result["selected_topics"], 1):
                print(f"Scraping {topic.get('topic_name')}")
                articles = scraper.scrape_topic(topic.get("topic_key", ""))
                articles_dict[topic.get("topic_name")] = [e.__dict__ for e in articles]
            print("\n" + "=" * 50)
            print(f"Searching for the company{company_name}...")
            search_company = scraper.scrape_search_query(company_name)

            if search_company:
                articles_dict[company_name] = [e.__dict__ for e in search_company]
                print(f"Found {len(search_company)} company-related news")

            #   search by the activity sector
            print("\n" + "=" * 50)
            print(f"Searching for the company{activity_sctor}...")
            articles_sctor = scraper.scrape_search_query(activity_sctor + service_name)

            if articles_sctor:
                articles_dict[activity_sctor] = [e.__dict__ for e in articles_sctor]
                print(f"Found {len(articles_sctor)} sector-related news")

            # writing dictionary to a file as JSON
            with open("data.json", "w") as f:
                json.dump(articles_dict, f)
            return articles_dict
        else:
            print(f"No topics selected for {activity_sctor}")
    except Exception as e:
        print(f"Main execution error: {e}")
        return None


def extract_news_by_keywords(keywords):
    articles_dict = {}
    scraper = GoogleNewsRSSScaper("google_news_articles.csv")
    for key in keywords:
        search_company = scraper.scrape_search_query(key)
        articles_dict[key] = [e.__dict__ for e in search_company]

    # writing dictionary to a file as JSON
    with open("data.json", "w") as f:
        json.dump(articles_dict, f)
    return articles_dict
