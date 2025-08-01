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
                        


    def _create_fallback_workflow(self, user_request: str, keywords: List[str]) -> Dict[str, Any]:
        """Create a simple, guaranteed-valid workflow as fallback"""
        return {
            "name": "Fallback AI Workflow",
            "description": f"Simple workflow for: {user_request[:50]}...",
            "version": "1.0.0", 
            "created_by": "Orchestra AI Agent (Fallback)",
            "user_request": user_request,
            "steps": [
                {
                    "node": "google-news-scraper",
                    "inputs": {
                        "api_token": "your-apify-token-here",
                        "keywords": keywords[:3],  # Limit to 3 keywords
                        "max_news": 5,
                        "time_period": "Last 24 hours",
                        "region_code": "United States (English)"
                    }
                },
                {
                    "assembly": {
                        "selected_url": {
                            "action": "select_index",
                            "from": "articles", 
                            "index": 0,
                            "extract": "url"
                        }
                    },
                    "source": "google-news-scraper",
                    "name": "simple_selector"
                },
                {
                    "node": "article-page-scraper",
                    "inputs": {
                        "url": "{{simple_selector.selected_url}}"
                    }
                }
            ]
        }

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
        """Extract comprehensive keywords from ANY user request using intelligent analysis"""
        return self._extract_all_relevant_keywords(user_request)
    
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
            
            # Step 2: Intelligent Article Selection with Error Recovery
            selection_criteria = analysis["selection_criteria"]
            workflow["steps"].append({
                "assembly": {
                    "selected_article_url": {
                        "action": "intelligent_select",
                        "from": "articles",
                        "criteria": analysis["keyword_filters"],
                        "fallback_strategy": "try_multiple",
                        "extract": "url",
                        "description": selection_criteria
                    },
                    "selected_article_title": {
                        "action": "intelligent_select", 
                        "from": "articles",
                        "criteria": analysis["keyword_filters"],
                        "fallback_strategy": "try_multiple",
                        "extract": "title",
                        "description": selection_criteria
                    },
                    "backup_urls": {
                        "action": "extract_all",
                        "from": "articles",
                        "extract": "url",
                        "limit": 5
                    }
                },
                "source": "google-news-scraper",
                "name": "intelligent_article_selector",
                "description": f"🤖 AI ASSEMBLY: {selection_criteria} with fallback strategy"
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
            
            # Step 4: Content Processing Assembly with Error Recovery
            workflow["steps"].append({
                "assembly": {
                    "clean_article_text": {
                        "primary": "article_text",
                        "fallback_action": "try_next_url",
                        "backup_urls": "{{intelligent_article_selector.backup_urls}}",
                        "min_content_length": 100,
                        "error_handling": "auto_retry"
                    },
                    "source_url": "url",
                    "article_title": "{{intelligent_article_selector.selected_article_title}}",
                    "content_quality_check": {
                        "action": "validate_content",
                        "min_words": 50,
                        "paywall_detection": True,
                        "retry_on_failure": True
                    }
                },
                "source": "article-page-scraper",
                "name": "content_processor",
                "description": "🤖 AI ASSEMBLY: Extracts content with intelligent error recovery and paywall detection"
            })
            
            # Step 5: AI Processing with Enhanced Instructions
            processing_instructions = analysis["processing_instructions"]
            workflow["steps"].append({
                "node": "article-processor",
                "inputs": {
                    "article_text": "{{content_processor.clean_article_text}}",
                    "openrouter_api_key": "your-openrouter-key-here", 
                    "model": "qwen/qwen3-coder:free",
                    "custom_instructions": processing_instructions,
                    "output_format": analysis["output_format"],
                    "keyword_focus": analysis["keyword_filters"],
                    "quality_requirements": {
                        "min_summary_length": 200,
                        "include_key_points": True,
                        "highlight_relevance": True
                    }
                }
            })
            
            # Validate JSON structure before returning
            import json
            try:
                json.dumps(workflow)  # Test if it's valid JSON
                return workflow
            except (TypeError, ValueError) as e:
                print(f"JSON validation error: {e}")
                # Return a simpler fallback workflow if complex one fails
                return self._create_fallback_workflow(user_request, keywords)
            
        except Exception as e:
            print(f"Error creating workflow: {e}")
            return None
    
    def _analyze_user_requirements(self, user_request: str) -> Dict[str, Any]:
        """Intelligently analyze ANY user request to determine workflow requirements"""
        request_lower = user_request.lower()
        
        # Extract ALL keywords and concepts from the request
        import re
        words = re.findall(r'\b\w+\b', request_lower)
        
        # Dynamic analysis based on content
        analysis = {
            "workflow_name": self._generate_workflow_name(user_request),
            "description": f"AI-generated workflow: {user_request[:100]}...",
            "max_articles": self._determine_article_count(user_request),
            "time_period": self._determine_time_period(user_request),
            "selection_criteria": self._generate_selection_criteria(user_request),
            "processing_instructions": self._generate_processing_instructions(user_request),
            "keyword_filters": self._extract_all_relevant_keywords(user_request),
            "output_format": self._determine_output_format(user_request)
        }
        
        return analysis
    
    def _generate_workflow_name(self, request: str) -> str:
        """Generate intelligent workflow name from ANY request"""
        request_lower = request.lower()
        
        # Extract main action verbs and nouns
        action_words = ["monitor", "track", "analyze", "summarize", "collect", "process", "generate", "create"]
        subject_words = ["news", "articles", "data", "content", "information", "reports", "summaries"]
        
        found_actions = [word for word in action_words if word in request_lower]
        found_subjects = [word for word in subject_words if word in request_lower]
        
        if found_actions and found_subjects:
            return f"AI {found_actions[0].title()} {found_subjects[0].title()} Workflow"
        else:
            return "Custom AI Automation Workflow"
    
    def _determine_article_count(self, request: str) -> int:
        """Intelligently determine how many articles to process"""
        request_lower = request.lower()
        
        # Look for quantity indicators
        if any(word in request_lower for word in ["few", "couple", "2", "3"]):
            return 3
        elif any(word in request_lower for word in ["many", "several", "bunch", "10", "lots"]):
            return 10
        elif any(word in request_lower for word in ["comprehensive", "extensive", "thorough"]):
            return 15
        else:
            return 5  # Default
    
    def _determine_time_period(self, request: str) -> str:
        """Intelligently determine time period from request"""
        request_lower = request.lower()
        
        if any(word in request_lower for word in ["today", "recent", "latest", "current"]):
            return "Last 24 hours"
        elif any(word in request_lower for word in ["week", "weekly", "7 days"]):
            return "Last 7 days"
        elif any(word in request_lower for word in ["month", "monthly", "30 days"]):
            return "Last 30 days"
        else:
            return "Last 24 hours"  # Default
    
    def _generate_selection_criteria(self, request: str) -> str:
        """Generate intelligent selection criteria for ANY request"""
        keywords = self._extract_all_relevant_keywords(request)
        
        if len(keywords) > 0:
            return f"Select articles most relevant to: {', '.join(keywords[:3])}"
        else:
            return "Select the most relevant and high-quality articles"
    
    def _generate_processing_instructions(self, request: str) -> str:
        """Generate processing instructions based on user intent"""
        request_lower = request.lower()
        
        if any(word in request_lower for word in ["summary", "summarize", "brief"]):
            return "Create concise, informative summaries highlighting key points"
        elif any(word in request_lower for word in ["analysis", "analyze", "insights"]):
            return "Perform deep analysis and extract valuable insights"
        elif any(word in request_lower for word in ["newsletter", "email", "report"]):
            return "Format content for newsletter/report distribution"
        elif any(word in request_lower for word in ["research", "investigate"]):
            return "Conduct thorough research analysis and compile findings"
        else:
            return "Process content according to user requirements and extract valuable information"
    
    def _extract_all_relevant_keywords(self, request: str) -> List[str]:
        """Extract ALL relevant keywords from ANY request"""
        request_lower = request.lower()
        keywords = []
        
        # Technology keywords
        tech_keywords = ["AI", "artificial intelligence", "machine learning", "technology", "tech", "digital", "automation", "robotics", "data science"]
        keywords.extend([kw for kw in tech_keywords if kw.lower() in request_lower])
        
        # Industry keywords
        industry_keywords = ["healthcare", "finance", "education", "retail", "manufacturing", "automotive", "energy", "agriculture"]
        keywords.extend([kw for kw in industry_keywords if kw.lower() in request_lower])
        
        # Business keywords
        business_keywords = ["startup", "funding", "investment", "company", "business", "enterprise", "innovation", "market"]
        keywords.extend([kw for kw in business_keywords if kw.lower() in request_lower])
        
        # Extract any quoted phrases or specific terms
        import re
        quoted_terms = re.findall(r'"([^"]*)"', request)
        keywords.extend(quoted_terms)
        
        # If no specific keywords found, use general terms
        if not keywords:
            keywords = ["technology", "innovation", "business"]
        
        return list(set(keywords))  # Remove duplicates
    
    def _determine_output_format(self, request: str) -> str:
        """Determine desired output format"""
        request_lower = request.lower()
        
        if any(word in request_lower for word in ["json", "structured", "data"]):
            return "structured_json"
        elif any(word in request_lower for word in ["markdown", "formatted"]):
            return "markdown"
        elif any(word in request_lower for word in ["plain", "simple", "text"]):
            return "plain_text"
        else:
            return "formatted_summary"
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