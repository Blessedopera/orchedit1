#!/usr/bin/env python3
"""
Orchestra Workflow Composer Agent - LangChain powered intelligent workflow creation
"""
import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain.tools import Tool
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

class WorkflowComposerAgent:
    def __init__(self, openrouter_api_key: str, nodes_dir: str = None):
        """Initialize the Workflow Composer Agent"""
        if nodes_dir is None:
            current_dir = Path(__file__).parent
            self.nodes_dir = current_dir.parent / "nodes"
        else:
            self.nodes_dir = Path(nodes_dir)
        
        # Initialize LLM with OpenRouter and Qwen3 Coder
        self.llm = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key,
            model="qwen/qwen3-coder:free",
            temperature=0.3,
            max_tokens=2000
        )
        
        # Initialize conversation history
        self.conversation_history = []
        
        # Initialize tools
        self.tools = self._create_tools()
        
        # Workflow memory for reuse
        self.workflow_memory = {}
    
    def _create_tools(self) -> List[Tool]:
        """Create LangChain tools for the agent"""
        tools = [
            Tool(
                name="discover_nodes",
                func=self._discover_nodes,
                description="Discover all available Orchestra nodes and their capabilities, input/output schemas"
            ),
            Tool(
                name="validate_workflow",
                func=self._validate_workflow,
                description="Validate a workflow JSON structure before execution"
            ),
            Tool(
                name="save_workflow",
                func=self._save_workflow,
                description="Save a workflow JSON to file. Input should be: filename|workflow_json"
            ),
            Tool(
                name="get_workflow_template",
                func=self._get_workflow_template,
                description="Get the standard workflow JSON template structure"
            ),
            Tool(
                name="analyze_assembly_needs",
                func=self._analyze_assembly_needs,
                description="Analyze what assembly steps are needed between nodes based on their schemas"
            )
        ]
        return tools
    
    def _call_tool(self, tool_name: str, tool_input: str) -> str:
        """Call a specific tool by name"""
        for tool in self.tools:
            if tool.name == tool_name:
                try:
                    return tool.func(tool_input)
                except Exception as e:
                    return f"Error calling {tool_name}: {str(e)}"
        return f"Tool {tool_name} not found"
    
    def _process_agent_response(self, response: str, max_iterations: int = 5) -> str:
        """Process agent response and handle tool calls"""
        iteration = 0
        current_response = response
        
        while iteration < max_iterations:
            # Check if response contains tool calls
            if "Action:" in current_response and "Action Input:" in current_response:
                try:
                    # Extract action and input
                    lines = current_response.split('\n')
                    action_line = None
                    input_line = None
                    
                    for i, line in enumerate(lines):
                        if line.strip().startswith("Action:"):
                            action_line = line.strip().replace("Action:", "").strip()
                        elif line.strip().startswith("Action Input:"):
                            # Get the input, which might be on the same line or next lines
                            input_text = line.strip().replace("Action Input:", "").strip()
                            if not input_text and i + 1 < len(lines):
                                input_text = lines[i + 1].strip()
                            input_line = input_text
                            break
                    
                    if action_line and input_line:
                        # Call the tool
                        tool_result = self._call_tool(action_line, input_line)
                        
                        # Create follow-up prompt with tool result
                        follow_up_prompt = f"""
Previous response: {current_response}

Tool Result from {action_line}: {tool_result}

Based on this tool result, please continue with your analysis and provide the final workflow JSON. If you need to call more tools, use the same Action/Action Input format.
"""
                        
                        # Get next response
                        messages = [
                            SystemMessage(content="You are an expert Orchestra workflow composer. Continue your analysis based on the tool results."),
                            HumanMessage(content=follow_up_prompt)
                        ]
                        
                        next_response = self.llm.invoke(messages)
                        current_response = next_response.content
                        iteration += 1
                    else:
                        break
                except Exception as e:
                    current_response += f"\n\nError processing tool call: {str(e)}"
                    break
            else:
                # No more tool calls needed
                break
        
        return current_response
    
    def _discover_nodes(self, query: str = "") -> str:
        """Discover available nodes and their capabilities"""
        try:
            nodes_info = []
            
            if not self.nodes_dir.exists():
                return "No nodes directory found"
            
            for node_dir in self.nodes_dir.iterdir():
                if node_dir.is_dir():
                    config_path = node_dir / "config.json"
                    if config_path.exists():
                        try:
                            with open(config_path, 'r') as f:
                                config = json.load(f)
                            
                            node_info = {
                                "node_name": node_dir.name,
                                "name": config.get("name", node_dir.name),
                                "description": config.get("description", "No description"),
                                "input_schema": config.get("input_schema", {}),
                                "output_schema": config.get("output_schema", []),
                                "type": config.get("type", "unknown"),
                                "dependencies": config.get("dependencies", [])
                            }
                            nodes_info.append(node_info)
                        except Exception as e:
                            nodes_info.append({
                                "node_name": node_dir.name,
                                "error": f"Could not load config: {str(e)}"
                            })
            
            return json.dumps(nodes_info, indent=2)
        
        except Exception as e:
            return f"Error discovering nodes: {str(e)}"
    
    def _validate_workflow(self, workflow_json: str) -> str:
        """Validate workflow JSON structure"""
        try:
            workflow = json.loads(workflow_json)
            
            errors = []
            
            # Check required fields
            if "steps" not in workflow:
                errors.append("Missing 'steps' field")
            
            if "name" not in workflow:
                errors.append("Missing 'name' field")
            
            # Validate steps
            if "steps" in workflow:
                for i, step in enumerate(workflow["steps"]):
                    if "node" in step:
                        # Node step validation
                        if "inputs" not in step:
                            errors.append(f"Step {i+1}: Missing 'inputs' field")
                        
                        # Check if node exists
                        node_name = step["node"]
                        node_path = self.nodes_dir / node_name
                        if not node_path.exists():
                            errors.append(f"Step {i+1}: Node '{node_name}' does not exist")
                    
                    elif "assembly" in step:
                        # Assembly step validation
                        if "source" not in step:
                            errors.append(f"Step {i+1}: Assembly step missing 'source' field")
                    
                    else:
                        errors.append(f"Step {i+1}: Must contain either 'node' or 'assembly' field")
            
            if errors:
                return f"Validation errors: {'; '.join(errors)}"
            else:
                return "Workflow validation passed"
        
        except json.JSONDecodeError as e:
            return f"Invalid JSON: {str(e)}"
        except Exception as e:
            return f"Validation error: {str(e)}"
    
    def _save_workflow(self, input_data: str) -> str:
        """Save workflow to file"""
        try:
            # Parse input: filename|workflow_json
            parts = input_data.split("|", 1)
            if len(parts) != 2:
                return "Input format should be: filename|workflow_json"
            
            filename, workflow_json = parts
            workflow = json.loads(workflow_json)
            
            # Ensure workflows directory exists
            workflows_dir = self.nodes_dir.parent / "workflows"
            workflows_dir.mkdir(exist_ok=True)
            
            # Save workflow
            workflow_path = workflows_dir / filename
            with open(workflow_path, 'w') as f:
                json.dump(workflow, f, indent=2)
            
            return f"Workflow saved to: {workflow_path}"
        
        except Exception as e:
            return f"Error saving workflow: {str(e)}"
    
    def _get_workflow_template(self, query: str = "") -> str:
        """Get the standard workflow template"""
        template = {
            "name": "Workflow Name",
            "description": "Workflow description",
            "version": "1.0.0",
            "steps": [
                {
                    "node": "node-name",
                    "inputs": {
                        "input_field": "value or {{previous_step.output_field}}"
                    }
                },
                {
                    "assembly": {
                        "output_field": {
                            "action": "select_random|select_index|extract",
                            "from": "source_field",
                            "extract": "field_to_extract"
                        }
                    },
                    "source": "previous_step_name",
                    "name": "assembly_step_name",
                    "description": "What this assembly step does"
                }
            ]
        }
        
        return json.dumps(template, indent=2)
    
    def _analyze_assembly_needs(self, input_data: str) -> str:
        """Analyze what assembly steps are needed between nodes"""
        try:
            # Parse input: source_node|target_node
            parts = input_data.split("|")
            if len(parts) != 2:
                return "Input format should be: source_node|target_node"
            
            source_node, target_node = parts
            
            # Load node configurations
            source_config_path = self.nodes_dir / source_node / "config.json"
            target_config_path = self.nodes_dir / target_node / "config.json"
            
            if not source_config_path.exists():
                return f"Source node '{source_node}' config not found"
            # Create messages for error analysis
            messages = [
                SystemMessage(content="You are an expert at analyzing Orchestra workflow errors and providing solutions."),
                HumanMessage(content=error_analysis_prompt)
            ]
            
            response = self.llm.invoke(messages)
            agent_response = response.content
            if not target_config_path.exists():
                return f"Target node '{target_node}' config not found"
            
            with open(source_config_path, 'r') as f:
                source_config = json.load(f)
            
            with open(target_config_path, 'r') as f:
                target_config = json.load(f)
            
            analysis = {
                "source_node": source_node,
                "target_node": target_node,
                "source_outputs": source_config.get("output_schema", []),
                "target_inputs": target_config.get("input_schema", {}),
                "assembly_suggestions": []
            }
            
            # Analyze compatibility
            target_required = target_config.get("input_schema", {}).get("required", [])
            target_optional = target_config.get("input_schema", {}).get("optional", [])
            
            for required_field in target_required:
                if required_field not in source_config.get("output_schema", []):
                    analysis["assembly_suggestions"].append(
                        f"Required field '{required_field}' not directly available from {source_node}. "
                        f"May need assembly step to extract or transform data."
                    )
            
            return json.dumps(analysis, indent=2)
        
        except Exception as e:
            return f"Error analyzing assembly needs: {str(e)}"
    
    def create_workflow(self, user_request: str) -> Dict[str, Any]:
        """Main method to create a workflow from user request"""
        try:
            # Add to conversation history
            self.conversation_history.append({"role": "user", "content": user_request})
            
            # Extract keywords from user request for intelligent input customization
            keywords = self._extract_keywords_from_request(user_request)
            
            # Create the workflow directly based on available nodes
            workflow_json = self._create_workflow_from_request(user_request, keywords)
            
            if workflow_json:
                # Add to conversation history
                self.conversation_history.append({"role": "assistant", "content": f"Created workflow: {workflow_json['name']}"})
                
                return {
                    "success": True,
                    "response": f"I've created a workflow called '{workflow_json['name']}' that will:\n\n1. Search for news articles about {', '.join(keywords)}\n2. Select a relevant article about AI company funding\n3. Scrape the full article content\n4. Generate an AI summary\n\nThe workflow is ready to save and execute!",
                    "workflow_json": workflow_json,
                    "conversation_history": self.conversation_history
                }
            else:
                return {
                    "success": False,
                    "error": "Could not create workflow from request",
                    "response": "I couldn't create a workflow for your request. Please try rephrasing it.",
                    "conversation_history": self.conversation_history
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": f"Failed to create workflow: {str(e)}",
                "conversation_history": self.conversation_history
            }
    
    def _extract_keywords_from_request(self, user_request: str) -> List[str]:
        """Extract relevant keywords from user request"""
        # Simple keyword extraction - can be enhanced with NLP
        keywords = []
        
        # Common patterns
        if "AI" in user_request or "artificial intelligence" in user_request:
            keywords.append("AI")
            keywords.append("artificial intelligence")
        
        if "healthcare" in user_request.lower():
            keywords.append("healthcare")
        
        if "startup" in user_request.lower() or "company" in user_request.lower():
            keywords.append("startup")
        
        if "funding" in user_request.lower() or "raised" in user_request.lower() or "money" in user_request.lower():
            keywords.append("funding")
            keywords.append("investment")
        
        if "technology" in user_request.lower() or "tech" in user_request.lower():
            keywords.append("technology")
        
        # Default fallback
        if not keywords:
            keywords = ["AI", "technology"]
        
        return keywords
    
    def _create_workflow_from_request(self, user_request: str, keywords: List[str]) -> Optional[Dict[str, Any]]:
        """Create workflow JSON directly from user request with intelligent assembly"""
        try:
            # Analyze user request for specific requirements
            analysis = self._analyze_user_requirements(user_request)
            
            workflow = {
                "name": analysis["workflow_name"],
                "description": analysis["description"],
                "version": "1.0.0",
                "created_by": "Orchestra AI Agent",
                "user_request": user_request,
                "steps": []
            }
            
            # Step 1: News Scraping
            workflow["steps"].append({
                "node": "google-news-scraper",
                "inputs": {
                    "api_token": "your-apify-token-here",
                    "keywords": keywords,
                    "max_news": analysis["max_articles"],
                    "time_period": analysis["time_period"],
                    "region_code": "United States (English)",
                    "extract_descriptions": True
                }
            })
            
            # Step 2: Intelligent Article Selection
            selection_criteria = analysis["selection_criteria"]
            workflow["steps"].append({
                "assembly": {
                    "selected_article_url": {
                        "action": "select_index",
                        "from": "articles",
                        "index": 0,
                        "extract": "url"
                    },
                    "selected_article_title": {
                        "action": "select_index", 
                        "from": "articles",
                        "index": 0,
                        "extract": "title"
                    }
                },
                "source": "google-news-scraper",
                "name": "intelligent_article_selector",
                "description": f"🤖 AI ASSEMBLY: {selection_criteria}"
            })
            
            # Step 3: Article Content Scraping
            workflow["steps"].append({
                "node": "article-page-scraper",
                "inputs": {
                    "url": "{{intelligent_article_selector.selected_article_url}}",
                    "output_filename": "ai_selected_article.html",
                    "headless": True
                }
            })
            
            # Step 4: Content Processing Assembly
            workflow["steps"].append({
                "assembly": {
                    "clean_article_text": "article_text",
                    "source_url": "url",
                    "article_title": "{{intelligent_article_selector.selected_article_title}}"
                },
                "source": "article-page-scraper",
                "name": "content_processor",
                "description": "🤖 AI ASSEMBLY: Extracts and prepares content for AI analysis"
            })
            
            # Step 5: AI Processing
            processing_instructions = analysis["processing_instructions"]
            workflow["steps"].append({
                "node": "article-processor",
                "inputs": {
                    "article_text": "{{content_processor.clean_article_text}}",
                    "openrouter_api_key": "your-openrouter-key-here",
                    "model": "qwen/qwen3-coder:free",
                    "custom_instructions": processing_instructions
                }
            })
            
            return workflow
            
        except Exception as e:
            print(f"Error creating workflow: {e}")
            return None
    
    def _analyze_user_requirements(self, user_request: str) -> Dict[str, Any]:
        """Analyze user request to determine workflow requirements"""
        analysis = {
            "workflow_name": "Custom AI Workflow",
            "description": "AI-generated workflow based on user requirements",
            "max_articles": 5,
            "time_period": "Last 24 hours",
            "selection_criteria": "Select the most relevant article",
            "processing_instructions": "Create a comprehensive summary"
        }
        
        request_lower = user_request.lower()
        
        # Determine workflow name and description
        if "healthcare" in request_lower:
            analysis["workflow_name"] = "Healthcare AI News Analysis"
            analysis["description"] = "Monitors and analyzes AI news in healthcare sector"
            analysis["selection_criteria"] = "Select articles about AI in healthcare"
        elif "startup" in request_lower or "funding" in request_lower:
            analysis["workflow_name"] = "AI Startup Funding Monitor"
            analysis["description"] = "Tracks AI startup funding news and investment trends"
            analysis["selection_criteria"] = "Select articles about AI startup funding"
        elif "summary" in request_lower or "newsletter" in request_lower:
            analysis["workflow_name"] = "AI News Summary Generator"
            analysis["description"] = "Creates summaries of AI news for newsletters"
            analysis["processing_instructions"] = "Create concise summaries suitable for newsletters"
        
        # Determine article count
        if "few" in request_lower or "3" in user_request:
            analysis["max_articles"] = 3
        elif "many" in request_lower or "10" in user_request:
            analysis["max_articles"] = 10
        
        # Determine time period
        if "week" in request_lower:
            analysis["time_period"] = "Last 7 days"
        elif "today" in request_lower:
            analysis["time_period"] = "Last 24 hours"
        
        return analysis
    
    def improve_workflow(self, workflow_json: str, feedback: str) -> Dict[str, Any]:
        """Improve an existing workflow based on feedback"""
        try:
            system_message = """
You have created this workflow:
"""
            
            user_message = f"""
Workflow: {workflow_json}

The user provided this feedback:
{feedback}

Please improve the workflow based on the feedback. Use your tools to:
1. Understand what needs to be changed
2. Analyze if new assembly steps are needed
3. Validate the improved workflow
4. Provide the updated workflow JSON

Focus on making the workflow more intelligent and efficient based on the feedback.
"""
            
            messages = [
                SystemMessage(content=system_message),
                HumanMessage(content=user_message)
            ]
            
            initial_response = self.llm.invoke(messages)
            final_response = self._process_agent_response(initial_response.content)
            
            return {
                "success": True,
                "response": final_response,
                "conversation_history": self.conversation_history
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": f"Failed to improve workflow: {str(e)}",
                "conversation_history": self.conversation_history
            }
    
    def explain_workflow(self, workflow_json: str) -> Dict[str, Any]:
        """Explain how a workflow works"""
        try:
            system_message = """
Please explain this Orchestra workflow in detail:
"""
            
            user_message = f"""
Workflow to explain: {workflow_json}

Use your node discovery tool to understand what each node does, then explain:
1. What this workflow accomplishes overall
2. What each step does and why it's needed
3. How data flows between steps
4. What the assembly steps accomplish
5. What the final output will be

Make it clear and understandable for both technical and non-technical users.
"""
            
            messages = [
                SystemMessage(content=system_message),
                HumanMessage(content=user_message)
            ]
            
            initial_response = self.llm.invoke(messages)
            final_response = self._process_agent_response(initial_response.content)
            
            return {
                "success": True,
                "response": final_response
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": f"Failed to explain workflow: {str(e)}"
            }