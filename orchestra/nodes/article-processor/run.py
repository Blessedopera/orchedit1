#!/usr/bin/env python3
"""
Article Processor Node - Orchestra compatible
Processes articles using OpenRouter API for summarization and rewriting
"""
import sys
import json
import re
from typing import Dict, Any, Optional

def extract_main_content_from_html(html_content: str) -> str:
    """Extract the main article content from HTML using BeautifulSoup"""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        # If BeautifulSoup not available, try simple HTML stripping
        import re
        # Remove HTML tags
        clean = re.compile('<.*?>')
        return re.sub(clean, '', html_content)
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove unwanted elements
    for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'advertisement']):
        element.decompose()
    
    # Try to find main content using common selectors
    content_selectors = [
        'article',
        '[role="main"]',
        'main',
        '.article-content',
        '.post-content',
        '.entry-content',
        '.content',
        '#content',
        '.article-body',
        '.story-body'
    ]
    
    main_content = None
    for selector in content_selectors:
        elements = soup.select(selector)
        if elements:
            main_content = elements[0]
            break
    
    # If no specific content area found, try to find the largest text block
    if not main_content:
        divs = soup.find_all('div')
        best_div = None
        max_text_length = 0
        
        for div in divs:
            text = div.get_text(strip=True)
            if len(text) > max_text_length and len(text) > 500:
                max_text_length = len(text)
                best_div = div
        
        main_content = best_div
    
    if not main_content:
        main_content = soup.find('body') or soup
    
    # Extract and clean text
    text = main_content.get_text(separator=' ', strip=True)
    
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n+', '\n', text)
    
    return text.strip()

def fetch_html_from_url(url: str) -> str:
    """Fetch HTML content from a URL"""
    try:
        import requests
    except ImportError:
        raise ImportError("requests package required for URL fetching")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.text

def call_openrouter_api(api_key: str, model: str, messages: list, max_tokens: int = 500, temperature: float = 0.3) -> str:
    """Call OpenRouter API for text processing"""
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("openai package required for OpenRouter API")
    
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    
    completion = client.chat.completions.create(
        extra_headers={
            "HTTP-Referer": "https://orchestra-ai.com",
            "X-Title": "Orchestra Article Processor",
        },
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature
    )
    
    return completion.choices[0].message.content

def process_article(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Main article processing function"""
    # Extract inputs
    api_key = input_data.get("openrouter_api_key")
    if not api_key:
        return {
            "error": "openrouter_api_key is required",
            "success": False
        }
    
    model = input_data.get("model", "qwen/qwen3-coder:free")
    max_tokens = input_data.get("max_tokens", 500)
    temperature = input_data.get("temperature", 0.3)
    
    # Get content from various sources
    article_text = None
    source_info = {}
    
    # Priority 1: Direct text input (for testing and workflow assembly)
    if input_data.get("article_text"):
        article_text = input_data["article_text"]
        source_info["source"] = "direct_text"
    
    # Priority 2: HTML file
    elif input_data.get("html_file"):
        try:
            with open(input_data["html_file"], 'r', encoding='utf-8') as f:
                html_content = f.read()
            article_text = extract_main_content_from_html(html_content)
            source_info["source"] = "file"
            source_info["file_path"] = input_data["html_file"]
        except Exception as e:
            return {
                "error": f"Could not read HTML file: {str(e)}",
                "success": False
            }
    
    # Priority 3: Direct HTML content
    elif input_data.get("html_content"):
        article_text = extract_main_content_from_html(input_data["html_content"])
        source_info["source"] = "direct_html"
    
    # Priority 4: Fetch from URL
    elif input_data.get("url"):
        try:
            html_content = fetch_html_from_url(input_data["url"])
            article_text = extract_main_content_from_html(html_content)
            source_info["source"] = "url"
            source_info["url"] = input_data["url"]
        except Exception as e:
            return {
                "error": f"Could not fetch URL: {str(e)}",
                "success": False
            }
    
    else:
        return {
            "error": "One of article_text, html_file, html_content, or url must be provided",
            "success": False
        }
    
    # Validate article content
    if not article_text or len(article_text.strip()) < 50:
        return {
            "error": "Could not extract sufficient article content (minimum 50 characters required)",
            "success": False,
            "extracted_length": len(article_text) if article_text else 0
        }
    
    # Generate summary
    try:
        summary_messages = [
            {
                "role": "system",
                "content": "You are an expert at creating concise, informative summaries. Provide a clear summary that captures the main points and key insights of the article."
            },
            {
                "role": "user",
                "content": f"Please provide a comprehensive summary of the following article:\n\n{article_text}"
            }
        ]
        
        summary = call_openrouter_api(api_key, model, summary_messages, max_tokens, temperature)
        
    except Exception as e:
        return {
            "error": f"Summary generation failed: {str(e)}",
            "success": False
        }
    
    # Generate rewritten version (optional, only if requested)
    rewritten = None
    if input_data.get("include_rewrite", False):
        try:
            rewrite_messages = [
                {
                    "role": "system",
                    "content": "You are a skilled writer and editor. Rewrite articles to be more engaging, well-structured, and beautifully written while maintaining all the original information and facts. Use clear headings, smooth transitions, and compelling language."
                },
                {
                    "role": "user",
                    "content": f"Please rewrite the following article to make it more engaging and beautifully written, while preserving all the original information:\n\n{article_text}"
                }
            ]
            
            rewritten = call_openrouter_api(api_key, model, rewrite_messages, max_tokens * 4, 0.7)
            
        except Exception as e:
            # Don't fail the whole process if rewrite fails
            rewritten = f"Rewrite failed: {str(e)}"
    
    return {
        "original_text": article_text,
        "summary": summary,
        "rewritten_article": rewritten,
        "model_used": model,
        "success": True,
        "source_info": source_info,
        "stats": {
            "original_length": len(article_text),
            "summary_length": len(summary),
            "rewritten_length": len(rewritten) if rewritten else 0
        }
    }

def main():
    """Main entry point for the node"""
    try:
        # Read JSON input from stdin
        input_data = json.loads(sys.stdin.read())
        
        # Process the request
        result = process_article(input_data)
        
        # Output JSON to stdout
        print(json.dumps(result, indent=2))
        
    except json.JSONDecodeError:
        error_result = {
            "error": "Invalid JSON input",
            "success": False
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)
        
    except Exception as e:
        error_result = {
            "error": f"Unexpected error: {str(e)}",
            "success": False
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()