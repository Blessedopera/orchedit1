#!/usr/bin/env python3
"""
Google News Scraper Node - Orchestra compatible
Converts Tkinter GUI + Apify API script to stdin/stdout JSON node
"""
import sys
import json
import random
from typing import Dict, Any, List

def get_time_period_value(period: str) -> str:
    """Convert human readable time period to Apify format"""
    mapping = {
        "Last hour": "h",
        "Last 24 hours": "d", 
        "Last week": "w",
        "Last month": "m",
        "Last year": "y"
    }
    return mapping.get(period, "h")

def get_region_code(region: str) -> str:
    """Convert human readable region to Apify format"""
    mapping = {
        "United States (English)": "US:en",
        "United Kingdom (English)": "GB:en",
        "Canada (English)": "CA:en",
        "Australia (English)": "AU:en",
        "Germany (German)": "DE:de",
        "France (French)": "FR:fr",
        "Spain (Spanish)": "ES:es",
        "Italy (Italian)": "IT:it",
        "Japan (Japanese)": "JP:ja",
        "India (English)": "IN:en"
    }
    return mapping.get(region, "US:en")

def scrape_google_news(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Main scraping function"""
    try:
        from apify_client import ApifyClient
    except ImportError:
        return {
            "error": "apify-client not installed. Run: pip install apify-client",
            "articles": [],
            "total_count": 0
        }
    
    # Extract and validate inputs
    api_token = input_data.get("api_token")
    if not api_token:
        return {
            "error": "api_token is required",
            "articles": [],
            "total_count": 0
        }
    
    keywords = input_data.get("keywords", [])
    if not keywords:
        return {
            "error": "keywords list is required",
            "articles": [],
            "total_count": 0
        }
    
    # Set defaults
    max_news = input_data.get("max_news", 10)
    time_period = get_time_period_value(input_data.get("time_period", "Last hour"))
    region_code = get_region_code(input_data.get("region_code", "United States (English)"))
    decode_urls = input_data.get("decode_urls", False)
    extract_descriptions = input_data.get("extract_descriptions", False)
    use_proxy = input_data.get("use_proxy", True)
    
    try:
        # Initialize the ApifyClient
        client = ApifyClient(api_token)
        
        # Prepare the Actor input
        run_input = {
            "keywords": keywords,
            "maxNews": max_news,
            "timePeriod": time_period,
            "regionAndLanguage": region_code,
            "decodeGoogleNewsUrls": decode_urls,
            "extractArticleDescriptions": extract_descriptions
        }
        
        # Add proxy configuration if enabled
        if use_proxy:
            run_input["proxyConfiguration"] = {"useApifyProxy": True}
        
        # Run the Actor and wait for it to finish
        run = client.actor("data_xplorer/google-news-scraper-fast").call(run_input=run_input)
        
        # Fetch results
        articles = []
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            articles.append(item)
        
        result = {
            "articles": articles,
            "total_count": len(articles),
            "dataset_id": run["defaultDatasetId"],
            "keywords_used": keywords,
            "time_period": time_period,
            "region_code": region_code
        }
        
        # Assembly logic - select one article for next step
        selected_url = None
        if articles:
            # Simple fallback - just provide first article URL for compatibility
            selected_url = articles[0].get("url")
        
        result["selected_article_url"] = selected_url
        return result
        
    except Exception as e:
        return {
            "error": f"Apify API error: {str(e)}",
            "articles": [],
            "total_count": 0
        }

def main():
    """Main entry point for the node"""
    try:
        # Read JSON input from stdin
        input_data = json.loads(sys.stdin.read())
        
        # Process the request
        result = scrape_google_news(input_data)
        
        # Output JSON to stdout
        print(json.dumps(result, indent=2))
        
    except json.JSONDecodeError:
        error_result = {
            "error": "Invalid JSON input",
            "articles": [],
            "total_count": 0
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)
        
    except Exception as e:
        error_result = {
            "error": f"Unexpected error: {str(e)}",
            "articles": [],
            "total_count": 0
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()