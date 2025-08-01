# 🎼 Orchestra v2 - AI-Powered Workflow Automation

## 🚀 What's New in v2

Orchestra v2 introduces **LangChain AI agents** that can intelligently create, optimize, and manage automation workflows. Instead of manually writing JSON workflows, you can now describe what you want in natural language and let the AI agent build the workflow for you.

## 🤖 AI Agent Capabilities

### 1. **Intelligent Workflow Creation**
- Describe your automation need in plain English
- AI agent analyzes available nodes and creates optimal workflow
- Automatically generates assembly steps for data transformation
- Validates workflow before execution

### 2. **Smart Assembly Logic**
- AI decides what data to pass between workflow steps
- Creates intelligent transformations instead of random selections
- Optimizes data flow for maximum efficiency

### 3. **Workflow Memory & Learning**
- Remembers successful workflows for reuse
- Learns from execution patterns
- Suggests similar workflows for new requests

### 4. **Error Analysis & Recovery**
- AI agent analyzes workflow failures
- Provides specific recommendations for fixes
- Helps debug complex workflow issues

## 🏗️ Architecture v2

```
orchestra/
├── agents/                 # 🆕 AI Agents
│   ├── workflow_composer.py    # Main LangChain agent
│   ├── workflow_memory.py      # Learning & memory system
│   └── workflow_templates.py   # Workflow templates
├── backend/
│   ├── glue_runner.py          # Original runner (unchanged)
│   └── enhanced_glue_runner.py # 🆕 AI-enhanced runner
├── nodes/                      # Unchanged - pure & reusable
│   ├── google-news-scraper/
│   ├── article-page-scraper/
│   └── article-processor/
├── workflows/                  # AI-generated workflows
├── dashboard/
│   ├── central_dashboard.py    # Original dashboard
│   └── agent_dashboard.py      # 🆕 AI-powered dashboard
└── data/                       # 🆕 Workflow memory database
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
python -m pip install -r requirements.txt
python -m pip install langchain langchain-openai langchain-community
```

### 2. Get OpenRouter API Key
- Sign up at [OpenRouter](https://openrouter.ai/)
- Get your free API key for Qwen3 Coder model

### 3. Run AI Dashboard
```bash
cd orchestra/dashboard
streamlit run agent_dashboard.py
```

### 4. Create Your First AI Workflow
1. Enter your OpenRouter API key in the sidebar
2. Go to "🤖 AI Workflow Creator"
3. Describe what you want: *"Monitor AI startup news and create summaries"*
4. Watch the AI agent create a complete workflow
5. Execute and refine as needed

## 🎯 Example AI Workflow Creation

**User Request:**
> "I want to monitor AI news about healthcare startups, pick the most relevant articles, and create summaries for my newsletter"

**AI Agent Response:**
1. Analyzes available nodes (news scraper, article scraper, processor)
2. Creates intelligent assembly steps
3. Generates complete workflow JSON
4. Validates the workflow structure
5. Provides execution-ready automation

## 🧠 Key Innovations

### **1. Natural Language to Workflow**
```
"Monitor AI news" → Complete JSON workflow with proper assembly steps
```

### **2. Intelligent Assembly**
Instead of random selection:
```json
{
  "assembly": {
    "relevant_article": {
      "action": "select_most_relevant",
      "from": "articles", 
      "criteria": "healthcare AND startup"
    }
  }
}
```

### **3. Workflow Memory**
- Stores successful patterns
- Suggests improvements
- Enables rapid workflow reuse

### **4. Error Intelligence**
- AI analyzes failures
- Suggests specific fixes
- Learns from mistakes

## 🔧 Technical Details

### **LangChain Integration**
- Uses OpenRouter with free Qwen3 Coder model
- Conversational agents with memory
- Tool-based architecture for node integration

### **Backward Compatibility**
- All v1 nodes work unchanged
- Original glue runner still available
- Existing workflows continue to work

### **Database Storage**
- SQLite for workflow memory
- Execution tracking and analytics
- Performance optimization data

## 🎯 Use Cases

### **Content Creation**
- News monitoring and summarization
- Social media content generation
- Research report automation

### **Data Processing**
- Web scraping and analysis
- Document processing pipelines
- API data aggregation

### **Business Intelligence**
- Competitor monitoring
- Market research automation
- Trend analysis workflows

## 🚀 Future Enhancements

### **Planned Features**
- Visual workflow builder with AI assistance
- Multi-agent collaboration
- Advanced workflow optimization
- Custom node generation
- Enterprise deployment features

### **AI Improvements**
- Better workflow pattern recognition
- Predictive workflow optimization
- Natural language workflow editing
- Automated testing and validation

## 🎉 Getting Started

1. **Try the AI Dashboard** - Experience intelligent workflow creation
2. **Explore Examples** - See AI-generated workflows in action
3. **Build Custom Workflows** - Describe your automation needs
4. **Monitor Performance** - Track success rates and optimize

Orchestra v2 represents the future of automation - where AI agents understand your needs and build the workflows for you, making complex automation accessible to everyone.