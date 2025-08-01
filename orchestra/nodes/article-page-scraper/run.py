#!/usr/bin/env python3
"""
Article Page Scraper Node - Orchestra compatible
Uses bulletproof scraping methods with multiple fallbacks
"""
import sys
import json
import asyncio
import os
import time
from pathlib import Path
from typing import Dict, Any

def resolve_google_news_url(google_news_url: str) -> str:
    """Resolve Google News redirect URL to actual article URL"""
    try:
        import requests
        
        # Follow redirects to get the actual article URL
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        }
        
        response = requests.get(google_news_url, headers=headers, allow_redirects=True, timeout=10)
        return response.url
        
    except Exception as e:
        print(f"Warning: Could not resolve Google News URL: {e}", file=sys.stderr)
        return google_news_url
async def scrape_article_async(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Async function to scrape article content with bulletproof methods"""
    try:
        from playwright.async_api import async_playwright
        import html2text
    except ImportError as e:
        return {
            "error": f"Required package not installed: {str(e)}. Run: pip install playwright html2text",
            "html_file": None,
            "article_text": None,
            "success": False
        }
    
    # Extract inputs
    url = input_data.get("url")
    if not url:
        return {
            "error": "url is required",
            "html_file": None,
            "article_text": None,
            "success": False
        }
    
    # Resolve Google News URLs
    if "news.google.com/read/" in url:
        print(f"Resolving Google News URL...", file=sys.stderr)
        resolved_url = resolve_google_news_url(url)
        print(f"Resolved to: {resolved_url}", file=sys.stderr)
        url = resolved_url
    
    output_filename = input_data.get("output_filename", "scraped_article.html")
    headless = input_data.get("headless", True)
    wait_time = input_data.get("wait_time", 3000)
    
    try:
        async with async_playwright() as p:
            # Launch browser with stealth settings
            browser = await p.chromium.launch(
                headless=headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            # Create context with realistic settings
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080},
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
            )
            
            page = await context.new_page()
            
            # Navigate with increased timeout and retry attempts
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    print(f"Attempt {attempt + 1}: Loading {url}", file=sys.stderr)
                    await page.goto(url, wait_until='domcontentloaded', timeout=45000)
                    break
                except Exception as e:
                    print(f"Attempt {attempt + 1} failed: {e}", file=sys.stderr)
                    if attempt == max_retries - 1:
                        raise e
                    await asyncio.sleep(3)
            
            # Wait for content to load
            print(f"Waiting {wait_time}ms for content to load...", file=sys.stderr)
            await page.wait_for_timeout(wait_time)
            
            # Try to dismiss common popups/overlays
            popup_selectors = [
                '[class*="popup"]', '[class*="modal"]', '[class*="overlay"]',
                '[id*="popup"]', '[id*="modal"]', '[id*="overlay"]',
                '.cookie-banner', '.newsletter-signup', '.subscription-popup',
                'button[aria-label*="close"]', 'button[aria-label*="dismiss"]'
            ]
            
            for selector in popup_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        if await element.is_visible():
                            await element.click(timeout=1000)
                except:
                    continue
            
            # Get full HTML content
            html_content = await page.content()
            
            # Extract article text using multiple methods
            article_text = await extract_article_content(page, html_content)
            
            await browser.close()
            
            # Validate extracted content
            if not article_text or len(article_text.strip()) < 100:
                return {
                    "error": f"Could not extract sufficient article content. Got {len(article_text) if article_text else 0} characters. URL may be blocked or require special handling.",
                    "html_file": None,
                    "article_text": article_text,
                    "url": url,
                    "success": False,
                    "debug_info": {
                        "original_url": input_data.get("url"),
                        "resolved_url": url,
                        "html_length": len(html_content)
                    }
                }
            
            # Save HTML file if requested
            html_file_path = None
            if output_filename:
                # Create styled HTML output
                styled_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Scraped Article</title>
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            padding: 2rem; 
            max-width: 800px; 
            margin: auto; 
            line-height: 1.6;
            color: #333;
        }}
        h1, h2, h3 {{ color: #222; margin-top: 1.5em; }}
        p {{ margin-bottom: 1em; }}
        pre, code {{ 
            background: #f4f4f4; 
            padding: 0.5em; 
            border-radius: 5px; 
            overflow-x: auto; 
            display: block; 
        }}
        blockquote {{
            border-left: 4px solid #ddd;
            margin: 0;
            padding-left: 1rem;
            color: #666;
        }}
        .article-meta {{
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 5px;
            margin-bottom: 2rem;
        }}
    </style>
</head>
<body>
    <div class="article-meta">
        <p><strong>Source URL:</strong> <a href="{url}" target="_blank">{url}</a></p>
        <p><strong>Scraped on:</strong> {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
        <hr>
    </div>
    <div class="article-content">
        {article_text.replace(chr(10), '<br>').replace(chr(13), '')}
    </div>
</body>
</html>"""
                
                html_file_path = Path(output_filename).absolute()
                with open(html_file_path, "w", encoding="utf-8") as f:
                    f.write(styled_html)
            
            return {
                "html_file": str(html_file_path) if html_file_path else None,
                "article_text": article_text,
                "url": url,
                "success": True,
                "content_length": len(article_text),
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
    except Exception as e:
        return {
            "error": f"Scraping failed: {str(e)}",
            "html_file": None,
            "article_text": None,
            "url": url,
            "success": False
        }

async def extract_article_content(page, html_content: str) -> str:
    """Extract article content using multiple intelligent methods"""
    
    # Method 1: Try to find article content using Playwright selectors
    article_selectors = [
        'article',
        '[role="main"]',
        'main',
        '.article-content',
        '.post-content', 
        '.entry-content',
        '.content',
        '#content',
        '.article-body',
        '.story-body',
        '.post-body',
        '.article-text',
        '.story-content',
        '[class*="article"]',
        '[class*="content"]',
        '[id*="article"]',
        '[id*="content"]'
    ]
    
    best_content = ""
    max_length = 0
    
    for selector in article_selectors:
        try:
            elements = await page.query_selector_all(selector)
            for element in elements:
                text = await element.inner_text()
                if len(text) > max_length and len(text) > 200:
                    max_length = len(text)
                    best_content = text
        except:
            continue
    
    # Method 2: If no good content found, use BeautifulSoup fallback
    if len(best_content) < 200:
        try:
            from bs4 import BeautifulSoup
            import html2text
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 
                               'aside', 'advertisement', 'ads', 'sidebar', 'menu']):
                element.decompose()
            
            # Try article selectors with BeautifulSoup
            for selector in ['article', 'main', '[role="main"]']:
                elements = soup.select(selector)
                if elements:
                    text = elements[0].get_text(separator=' ', strip=True)
                    if len(text) > max_length:
                        max_length = len(text)
                        best_content = text
                        break
            
            # If still no good content, find largest text block
            if len(best_content) < 200:
                divs = soup.find_all(['div', 'section', 'p'])
                for div in divs:
                    text = div.get_text(separator=' ', strip=True)
                    if len(text) > max_length and len(text) > 200:
                        max_length = len(text)
                        best_content = text
            
        except ImportError:
            # Fallback to simple text extraction
            pass
    
    # Method 3: Last resort - extract all visible text
    if len(best_content) < 200:
        try:
            # Get all text from body
            body_element = await page.query_selector('body')
            if body_element:
                best_content = await body_element.inner_text()
        except:
            best_content = "Could not extract article content"
    
    # Clean up the text
    import re
    best_content = re.sub(r'\s+', ' ', best_content)
    best_content = re.sub(r'\n+', '\n', best_content)
    
    return best_content.strip()

def scrape_article(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Sync wrapper for async scraping function"""
    return asyncio.run(scrape_article_async(input_data))

def main():
    """Main entry point for the node"""
    try:
        # Read JSON input from stdin
        input_data = json.loads(sys.stdin.read())
        
        # Process the request
        result = scrape_article(input_data)
        
        # Output JSON to stdout
        print(json.dumps(result, indent=2))
        
    except json.JSONDecodeError:
        error_result = {
            "error": "Invalid JSON input",
            "html_file": None,
            "article_text": None,
            "success": False
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)
        
    except Exception as e:
        error_result = {
            "error": f"Unexpected error: {str(e)}",
            "html_file": None,
            "article_text": None,
            "success": False
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()