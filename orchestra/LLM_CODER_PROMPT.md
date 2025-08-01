# 🎯 LLM CODER PROMPT — ORCHESTRA NODE CONVERSION (STEPS 2 + 5)

You are a code agent inside the Orchestra system. Your job is to build a functional prototype of the glue runner and node system that powers custom automation workflows.

This prototype is used to test:
- The structure and behavior of plug-and-play nodes (step 2)
- A working glue runner that connects nodes using reusable logic (step 5)
- A simple dashboard UI that lets me manually run workflows

You do NOT need to build full agent logic or Langchain integration yet.

---

## 📁 FOLDER STRUCTURE STANDARD FOR NODES

Each node must live in its own folder like this:

```
orchestra/nodes/
  └── [node-name]/
      ├── config.json        ✅ Defines input/output schema and metadata
      ├── run.py             ✅ Receives JSON on stdin and returns JSON on stdout
      └── example_input.json ✅ Test data to simulate manual execution
```

---

## 🧩 GLUE RUNNER GOALS

The glue runner must:
- Load config.json for each node
- Accept a JSON workflow like:

```json
{
  "steps": [
    {
      "node": "google-news-scraper",
      "inputs": {
        "keywords": ["AI", "startup"],
        "max_news": 5,
        "api_token": "your-apify-token"
      }
    },
    {
      "node": "article-page-scraper",
      "inputs": {
        "url": "{{google-news-scraper.articles[0].url}}"
      }
    },
    {
      "node": "article-processor",
      "inputs": {
        "html_file": "{{article-page-scraper.output_file}}",
        "openrouter_api_key": "your-openrouter-key"
      }
    }
  ]
}
```

- Replace input placeholders ({{...}}) with previous node outputs
- Execute nodes by:
  - Reading run.py for the node
  - Passing JSON input via stdin
  - Capturing JSON output via stdout
- Print the final output

You can use Python's subprocess, json, and string template logic to implement this.

---

## 🧪 NODE CONVERSION TASK

You will receive 3 existing working Python code snippets (real API wrappers). Your job is to convert each of them into a compatible node folder using the structure described above.

Each should contain:
- `run.py` (converted to receive JSON from stdin and return clean JSON output)
- `config.json` (standard input/output schema)
- `example_input.json` (used for testing the runner manually)

### Node 1: Google News Scraper
- **Purpose**: Uses Apify API to scrape Google News articles
- **Input**: keywords, max_news, api_token, time_period, region_code
- **Output**: List of articles with title, url, source, publishedAt, snippet
- **Location**: `orchestra/nodes/google-news-scraper/`

### Node 2: Article Page Scraper  
- **Purpose**: Uses Playwright to scrape full article content from URL
- **Input**: url, output_filename (optional)
- **Output**: html_file path, markdown_content
- **Location**: `orchestra/nodes/article-page-scraper/`

### Node 3: Article Processor
- **Purpose**: Uses OpenRouter API to summarize and rewrite articles
- **Input**: html_file OR html_content, openrouter_api_key, model (optional)
- **Output**: original_text, summary, rewritten_article
- **Location**: `orchestra/nodes/article-processor/`

---

## 🖥️ SIMPLE CENTRAL DASHBOARD UI

Create a small UI using Streamlit that:
- Lists available nodes (based on folders inside `orchestra/nodes/`)
- Shows basic info from each node's config.json
- Allows me to manually trigger a single-node execution using example_input.json
- Allows me to test a full workflow by loading a workflow.json
- **Location**: `orchestra/dashboard/central_dashboard.py`

This is a test UI only. It will later evolve into the Langchain-based Composer dashboard.

---

## 🎯 GOAL WORKFLOW (EXAMPLE)

This is the test flow to verify everything works:
1. Use `google-news-scraper` to get top 5 news articles about AI
2. Choose 1 article URL and send it to `article-page-scraper` (uses headless browser)
3. Scrape article HTML and send it to `article-processor` (OpenRouter API) for summary

---

## 💡 TECHNOLOGY STACK

- 🐍 Python 3.9+
- 📦 Streamlit (for GUI)
- 📦 subprocess, json, re (for glue runner)
- 🧪 apify-client, playwright, requests, bs4 (existing dependencies)
- 🤖 OpenAI-compatible call via OpenRouter

---

## 🔥 FINAL DELIVERABLES

- `orchestra/backend/glue_runner.py`: The core script that loads and runs a JSON workflow
- `orchestra/dashboard/central_dashboard.py`: A Streamlit GUI that allows:
  - Listing all nodes
  - Running example input manually
  - Loading a workflow.json and running it
- `orchestra/nodes/` with 3 working nodes:
  - `google-news-scraper/`
  - `article-page-scraper/`
  - `article-processor/`
- `orchestra/workflows/test_workflow.json`: The test JSON flow that chains the three nodes

---

## 📋 NODE CONVERSION REQUIREMENTS

For each node you convert:

1. **config.json** must include:
```json
{
  "name": "Node Name",
  "description": "What this node does",
  "input_schema": {
    "required": ["field1", "field2"],
    "optional": ["field3"]
  },
  "output_schema": ["output1", "output2"],
  "dependencies": ["package1", "package2"]
}
```

2. **run.py** must:
   - Read JSON from stdin: `input_data = json.loads(sys.stdin.read())`
   - Process the data using your existing logic
   - Output JSON to stdout: `print(json.dumps(result))`
   - Handle errors gracefully
   - Be completely self-contained

3. **example_input.json** must contain valid test data

---

## 🚨 CRITICAL REQUIREMENTS

- Each node must be STATELESS and REUSABLE
- Nodes must NOT depend on each other directly
- All file paths should be absolute or relative to the orchestra/ root
- Error handling must be robust
- The glue runner must support variable substitution like `{{node-name.field}}`

---

**Please wait for me to paste the working code for the three nodes before you begin converting them.**

The three working scripts I will provide are:
1. `google_news_scraper.py` (Tkinter GUI + Apify API)
2. `playwright_scraper.py` (Playwright browser automation)  
3. `article_processor.py` (OpenRouter API + BeautifulSoup)

Convert these into the Orchestra node architecture described above.