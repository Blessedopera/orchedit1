# 🎼 Orchestra - Node-Based Automation System

## Overview

Orchestra is a prototype system for building plug-and-play automation workflows using reusable nodes. This implementation demonstrates the core architecture with three example nodes that form a complete AI news processing pipeline.

## Architecture

```
orchestra/
├── backend/
│   └── glue_runner.py      # Core execution engine
├── nodes/                  # Plug-and-play nodes
│   ├── google-news-scraper/
│   ├── article-page-scraper/
│   └── article-processor/
├── workflows/              # JSON workflow definitions
├── dashboard/              # Streamlit GUI
└── utils/                  # Shared utilities
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Playwright (for article scraping)

```bash
playwright install chromium
```

### 3. Run the Dashboard

```bash
cd orchestra/dashboard
streamlit run central_dashboard.py
```

### 4. Test Individual Nodes

```bash
# Test Google News Scraper
cd orchestra/nodes/google-news-scraper
echo '{"api_token":"your-token","keywords":["AI"],"max_news":3}' | python run.py

# Test Article Scraper
cd orchestra/nodes/article-page-scraper  
echo '{"url":"https://example.com/article"}' | python run.py

# Test Article Processor
cd orchestra/nodes/article-processor
echo '{"openrouter_api_key":"your-key","html_content":"<p>Test content</p>"}' | python run.py
```

### 5. Run Complete Workflow

```bash
cd orchestra/backend
python glue_runner.py ../workflows/test_workflow.json
```

## Node Structure

Each node follows this standard structure:

```
node-name/
├── config.json        # Node metadata and schema
├── run.py             # Main execution script (stdin/stdout JSON)
└── example_input.json # Test data
```

### Node Communication

- **Input**: JSON via stdin
- **Output**: JSON via stdout  
- **Variables**: Use `{{node-name.field}}` for chaining

## Example Workflow

The included test workflow demonstrates:

1. **Google News Scraper** → Fetches AI news articles
2. **Article Page Scraper** → Scrapes full content from first article
3. **Article Processor** → Summarizes content using OpenRouter API

## API Keys Required

- **Apify API Token** - For Google News scraping
- **OpenRouter API Key** - For AI processing

## Features

- ✅ **Plug-and-play nodes** - Easy to add new functionality
- ✅ **Variable substitution** - Chain node outputs to inputs
- ✅ **Visual dashboard** - Test nodes and build workflows
- ✅ **Error handling** - Robust execution with detailed logging
- ✅ **Async support** - Handle browser automation and API calls
- ✅ **Extensible** - Add unlimited nodes following the standard

## Adding New Nodes

1. Create node directory in `orchestra/nodes/`
2. Add `config.json` with schema definition
3. Create `run.py` that reads JSON from stdin, outputs to stdout
4. Add `example_input.json` for testing
5. Node appears automatically in dashboard

## Development

This is a **prototype system** designed to validate the Orchestra architecture. The three included nodes demonstrate the pattern that will be used for many more nodes in the production system.

## Next Steps

- Add more node types (databases, APIs, file processing, etc.)
- Implement visual workflow builder
- Add scheduling and monitoring
- Create node marketplace/registry