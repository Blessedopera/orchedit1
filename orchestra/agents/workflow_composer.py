#!/usr/bin/env python3
"""
Orchestra Workflow Composer Agent - Advanced LangChain powered intelligent workflow creation
Handles ANY combination of nodes with intelligent assembly logic
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
        """Initialize the Advanced Workflow Composer Agent"""
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
            temperature=0.1,  # Lower temperature for more consistent logic
            max_tokens=3000   # Increased for complex workflows
        )

        # Initialize conversation history
        self.conversation_history = []

        # Initialize tools
        self.tools = self._create_tools()

        # Workflow memory for reuse
        self.workflow_memory = {}

        # Node capability analysis cache
        self.node_capabilities_cache = {}

    def _create_tools(self) -> List[Tool]:
        """Create comprehensive LangChain tools for the agent"""
        tools = [
            Tool(
                name="discover_all_nodes",
                func=self._discover_all_nodes,
                description="Discover ALL available Orchestra nodes with complete capability analysis including input/output schemas, dependencies, and functional purpose"
            ),
            Tool(
                name="analyze_node_compatibility",
                func=self._analyze_node_compatibility,
                description="Analyze compatibility between two nodes for chaining. Input: source_node|target_node"
            ),
            Tool(
                name="generate_assembly_logic",
                func=self._generate_assembly_logic,
                description="Generate intelligent assembly logic between nodes. Input: source_node|target_node|user_intent"
            ),
            Tool(
                name="validate_workflow_structure",
                func=self._validate_workflow_structure,
                description="Validate complete workflow JSON structure and logic flow"
            ),
            Tool(
                name="optimize_node_sequence",
                func=self._optimize_node_sequence,
                description="Optimize the sequence of nodes for maximum efficiency. Input: node_list|user_goal"
            ),
            Tool(
                name="analyze_user_requirements",
                func=self._analyze_user_requirements,
                description="Deep analysis of user requirements to determine needed capabilities and data flow"
            ),
            Tool(
                name="save_workflow_file",
                func=self._save_workflow_file,
                description="Save workflow JSON to file. Input: filename|workflow_json"
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

    def _process_agent_response(self, response: str, max_iterations: int = 8) -> str:
        """Process agent response and handle tool calls with increased iterations"""
        iteration = 0
        current_response = response

        while iteration < max_iterations:
            if "Action:" in current_response and "Action Input:" in current_response:
                try:
                    lines = current_response.split('\n')
                    action_line = None
                    input_line = None

                    for i, line in enumerate(lines):
                        if line.strip().startswith("Action:"):
                            action_line = line.strip().replace("Action:", "").strip()
                        elif line.strip().startswith("Action Input:"):
                            input_text = line.strip().replace("Action Input:", "").strip()
                            if not input_text and i + 1 < len(lines):
                                input_text = lines[i + 1].strip()
                            input_line = input_text
                            break

                    if action_line and input_line:
                        tool_result = self._call_tool(action_line, input_line)

                        follow_up_prompt = f"""
Previous analysis: {current_response}

Tool Result from {action_line}: {tool_result}

Based on this tool result, continue your comprehensive analysis. If you need more information, use additional tools. When you have enough information, provide the complete workflow JSON that perfectly matches the user's requirements.

Remember: You must create a workflow that uses the BEST available nodes for the user's specific request, with intelligent assembly steps that properly transform data between nodes.
"""

                        messages = [
                            SystemMessage(content=self._get_advanced_system_prompt()),
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
                break

        return current_response

    def _get_advanced_system_prompt(self) -> str:
        """Get the comprehensive system prompt for general-purpose workflow creation"""
        return """You are an EXPERT Orchestra Workflow Composer Agent with deep understanding of automation, data flow, and intelligent node orchestration.

CORE MISSION: Create perfect workflows for ANY user request using ANY available nodes, with intelligent assembly logic that ensures proper data flow.

CRITICAL CAPABILITIES:
1. **Universal Node Understanding**: Analyze ANY node's capabilities, inputs, outputs, and purpose
2. **Intelligent Node Selection**: Choose the OPTIMAL nodes for any user requirement
3. **Smart Assembly Logic**: Create perfect data transformations between ANY nodes
4. **Workflow Optimization**: Order nodes for maximum efficiency and logical flow
5. **Requirement Analysis**: Extract precise technical requirements from natural language

WORKFLOW CREATION PROCESS:
1. **Deep Requirement Analysis**: 
   - Extract user's core goal and sub-requirements
   - Identify needed data sources, processing steps, and outputs
   - Determine quality criteria and success metrics

2. **Comprehensive Node Discovery**:
   - Analyze ALL available nodes and their capabilities
   - Map node functions to user requirements
   - Identify optimal node combinations

3. **Intelligent Node Selection**:
   - Choose nodes that BEST match user needs (not just available ones)
   - Consider data flow compatibility
   - Optimize for efficiency and reliability

4. **Advanced Assembly Logic**:
   - Create intelligent data transformations between nodes
   - Handle data type conversions and filtering
   - Implement conditional logic and error handling
   - Ensure perfect data flow from input to final output

5. **Workflow Optimization**:
   - Order nodes for logical data flow
   - Minimize unnecessary steps
   - Maximize parallel processing where possible
   - Ensure robust error handling

ASSEMBLY LOGIC INTELLIGENCE:
- **Smart Selection**: Choose best items from arrays based on relevance, quality, or user criteria
- **Data Transformation**: Convert data formats, extract specific fields, combine data sources
- **Conditional Logic**: Make decisions based on data content or user preferences
- **Quality Filtering**: Remove low-quality or irrelevant data
- **Context Awareness**: Use user intent to guide data processing decisions

WORKFLOW JSON STRUCTURE:
```json
{
  "name": "Descriptive Workflow Name",
  "description": "Clear description of what this workflow accomplishes",
  "version": "1.0.0",
  "created_by": "Orchestra AI Agent",
  "user_request": "Original user request",
  "steps": [
    {
      "node": "node-name",
      "inputs": {
        "field": "value or {{previous_step.field}}"
      }
    },
    {
      "assembly": {
        "output_field": {
          "action": "intelligent_select|extract|transform|filter",
          "from": "source_field",
          "criteria": "selection criteria based on user intent",
          "extract": "specific_field_to_extract",
          "fallback": "fallback_strategy"
        }
      },
      "source": "previous_step_name",
      "name": "descriptive_assembly_name",
      "description": "What this assembly accomplishes"
    }
  ]
}
```

ADVANCED ASSEMBLY ACTIONS:
- **intelligent_select**: Choose best item based on relevance, quality, or user criteria
- **extract**: Pull specific data fields from complex structures
- **transform**: Convert data formats or combine multiple sources
- **filter**: Remove items that don't meet criteria
- **aggregate**: Combine multiple items into summaries or collections
- **conditional**: Make decisions based on data content

CRITICAL REQUIREMENTS:
1. **Perfect Data Flow**: Every input must have a valid source
2. **User Intent Alignment**: Assembly logic must serve the user's specific goal
3. **Error Resilience**: Include fallback strategies for data processing
4. **Efficiency**: Minimize unnecessary steps while maximizing output quality
5. **Flexibility**: Work with ANY combination of available nodes

Remember: You are creating workflows for a GENERAL-PURPOSE automation system. The current nodes are just examples. Your job is to create perfect workflows using WHATEVER nodes are available to achieve the user's goal."""

    def _discover_all_nodes(self, query: str = "") -> str:
        """Comprehensive discovery of all available nodes with detailed capability analysis"""
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

                            # Enhanced node analysis
                            node_info = {
                                "node_name": node_dir.name,
                                "display_name": config.get("name", node_dir.name),
                                "description": config.get("description", "No description"),
                                "input_schema": config.get("input_schema", {}),
                                "output_schema": config.get("output_schema", []),
                                "node_type": config.get("type", "unknown"),
                                "language": config.get("language", "unknown"),
                                "dependencies": config.get("dependencies", []),
                                "capabilities": self._analyze_node_capabilities(config, node_dir.name),
                                "data_flow": self._analyze_data_flow(config),
                                "use_cases": self._identify_use_cases(config),
                                "compatibility": self._assess_compatibility(config)
                            }
                            nodes_info.append(node_info)
                        except Exception as e:
                            nodes_info.append({
                                "node_name": node_dir.name,
                                "error": f"Could not load config: {str(e)}"
                            })

            # Add comprehensive analysis summary
            analysis_summary = {
                "total_nodes": len(nodes_info),
                "node_types": list(set([n.get("node_type", "unknown") for n in nodes_info if "error" not in n])),
                "capabilities_overview": self._summarize_system_capabilities(nodes_info),
                "workflow_patterns": self._identify_workflow_patterns(nodes_info)
            }

            return json.dumps({
                "nodes": nodes_info,
                "system_analysis": analysis_summary
            }, indent=2)

        except Exception as e:
            return f"Error discovering nodes: {str(e)}"

    def _analyze_node_capabilities(self, config: Dict[str, Any], node_name: str) -> Dict[str, Any]:
        """Deep analysis of what a node can do"""
        capabilities = {
            "primary_function": "unknown",
            "data_sources": [],
            "processing_types": [],
            "output_formats": [],
            "special_features": []
        }

        description = config.get("description", "").lower()
        node_type = config.get("type", "").lower()
        
        # Analyze primary function
        if "scrape" in description or "scraper" in node_type:
            capabilities["primary_function"] = "data_extraction"
            capabilities["data_sources"].append("web")
        elif "process" in description or "processor" in node_type:
            capabilities["primary_function"] = "data_processing"
        elif "api" in description:
            capabilities["primary_function"] = "api_integration"
        elif "database" in description:
            capabilities["primary_function"] = "data_storage"

        # Analyze input/output capabilities
        input_schema = config.get("input_schema", {})
        output_schema = config.get("output_schema", [])

        # Determine data processing types
        if any("text" in field.lower() for field in output_schema):
            capabilities["processing_types"].append("text_processing")
        if any("html" in field.lower() for field in output_schema):
            capabilities["processing_types"].append("html_processing")
        if any("json" in field.lower() for field in output_schema):
            capabilities["processing_types"].append("structured_data")

        return capabilities

    def _analyze_data_flow(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze how data flows through this node"""
        input_schema = config.get("input_schema", {})
        output_schema = config.get("output_schema", [])
        
        return {
            "required_inputs": input_schema.get("required", []),
            "optional_inputs": input_schema.get("optional", []),
            "outputs": output_schema,
            "data_transformation": self._infer_transformation_type(input_schema, output_schema)
        }

    def _infer_transformation_type(self, inputs: Dict, outputs: List) -> str:
        """Infer what type of data transformation this node performs"""
        if not inputs or not outputs:
            return "unknown"
        
        input_fields = inputs.get("required", []) + inputs.get("optional", [])
        
        if "url" in input_fields and any("content" in out.lower() for out in outputs):
            return "web_content_extraction"
        elif any("text" in inp.lower() for inp in input_fields) and any("summary" in out.lower() for out in outputs):
            return "text_summarization"
        elif "keywords" in input_fields and "articles" in outputs:
            return "content_search"
        else:
            return "data_processing"

    def _identify_use_cases(self, config: Dict[str, Any]) -> List[str]:
        """Identify common use cases for this node"""
        use_cases = []
        description = config.get("description", "").lower()
        node_type = config.get("type", "").lower()
        
        if "news" in description:
            use_cases.extend(["news_monitoring", "content_research", "trend_analysis"])
        if "scrape" in description:
            use_cases.extend(["data_collection", "web_research", "content_extraction"])
        if "ai" in description or "llm" in description:
            use_cases.extend(["content_analysis", "text_processing", "summarization"])
        if "api" in description:
            use_cases.extend(["data_integration", "service_connection", "automation"])
            
        return use_cases

    def _assess_compatibility(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Assess compatibility with other node types"""
        output_schema = config.get("output_schema", [])
        
        compatibility = {
            "can_feed_to": [],
            "common_outputs": output_schema,
            "chaining_potential": "medium"
        }
        
        # Determine what types of nodes this can feed data to
        if "url" in output_schema:
            compatibility["can_feed_to"].append("web_scrapers")
        if any("text" in out.lower() for out in output_schema):
            compatibility["can_feed_to"].append("text_processors")
        if any("html" in out.lower() for out in output_schema):
            compatibility["can_feed_to"].append("html_processors")
            
        return compatibility

    def _summarize_system_capabilities(self, nodes_info: List[Dict]) -> Dict[str, Any]:
        """Summarize overall system capabilities"""
        capabilities = {
            "data_sources": set(),
            "processing_types": set(),
            "output_formats": set(),
            "workflow_types": set()
        }
        
        for node in nodes_info:
            if "error" not in node and "capabilities" in node:
                caps = node["capabilities"]
                capabilities["data_sources"].update(caps.get("data_sources", []))
                capabilities["processing_types"].update(caps.get("processing_types", []))
                capabilities["output_formats"].update(caps.get("output_formats", []))
        
        return {k: list(v) for k, v in capabilities.items()}

    def _identify_workflow_patterns(self, nodes_info: List[Dict]) -> List[str]:
        """Identify common workflow patterns possible with available nodes"""
        patterns = []
        
        node_types = [n.get("node_type", "") for n in nodes_info if "error" not in n]
        
        if "scraper" in node_types and "processor" in node_types:
            patterns.append("web_scraping_to_analysis")
        if any("news" in n.get("description", "").lower() for n in nodes_info):
            patterns.append("news_monitoring_pipeline")
        if any("ai" in n.get("description", "").lower() for n in nodes_info):
            patterns.append("ai_content_processing")
            
        return patterns

    def _analyze_node_compatibility(self, input_data: str) -> str:
        """Analyze compatibility between two specific nodes"""
        try:
            parts = input_data.split("|")
            if len(parts) != 2:
                return "Input format should be: source_node|target_node"

            source_node, target_node = parts

            # Load node configurations
            source_config_path = self.nodes_dir / source_node / "config.json"
            target_config_path = self.nodes_dir / target_node / "config.json"

            if not source_config_path.exists():
                return f"Source node '{source_node}' config not found"
            if not target_config_path.exists():
                return f"Target node '{target_node}' config not found"

            with open(source_config_path, 'r') as f:
                source_config = json.load(f)
            with open(target_config_path, 'r') as f:
                target_config = json.load(f)

            # Comprehensive compatibility analysis
            analysis = {
                "source_node": source_node,
                "target_node": target_node,
                "compatibility_score": 0,
                "direct_matches": [],
                "possible_transformations": [],
                "assembly_requirements": [],
                "data_flow_analysis": {},
                "recommendations": []
            }

            source_outputs = source_config.get("output_schema", [])
            target_inputs = target_config.get("input_schema", {})
            target_required = target_inputs.get("required", [])
            target_optional = target_inputs.get("optional", [])

            # Check direct field matches
            for output_field in source_outputs:
                if output_field in target_required:
                    analysis["direct_matches"].append(output_field)
                    analysis["compatibility_score"] += 10
                elif output_field in target_optional:
                    analysis["direct_matches"].append(f"{output_field} (optional)")
                    analysis["compatibility_score"] += 5

            # Analyze possible transformations
            for required_field in target_required:
                if required_field not in source_outputs:
                    # Look for semantic matches
                    possible_sources = self._find_semantic_matches(required_field, source_outputs)
                    if possible_sources:
                        analysis["possible_transformations"].append({
                            "target_field": required_field,
                            "possible_sources": possible_sources,
                            "transformation_type": "semantic_mapping"
                        })
                        analysis["compatibility_score"] += 3

            # Generate assembly requirements
            for required_field in target_required:
                if required_field not in [m.split(" ")[0] for m in analysis["direct_matches"]]:
                    analysis["assembly_requirements"].append({
                        "field": required_field,
                        "requirement": "Must be provided via assembly step or default value"
                    })

            # Generate recommendations
            if analysis["compatibility_score"] >= 20:
                analysis["recommendations"].append("High compatibility - direct chaining recommended")
            elif analysis["compatibility_score"] >= 10:
                analysis["recommendations"].append("Medium compatibility - assembly step recommended")
            else:
                analysis["recommendations"].append("Low compatibility - consider intermediate processing node")

            return json.dumps(analysis, indent=2)

        except Exception as e:
            return f"Error analyzing compatibility: {str(e)}"

    def _find_semantic_matches(self, target_field: str, source_fields: List[str]) -> List[str]:
        """Find semantically similar fields between source and target"""
        matches = []
        target_lower = target_field.lower()
        
        # Define semantic mappings
        semantic_groups = {
            "url": ["link", "href", "address", "location"],
            "text": ["content", "body", "article", "description"],
            "title": ["name", "heading", "subject"],
            "content": ["text", "body", "article", "data"],
            "data": ["content", "information", "result"]
        }
        
        for source_field in source_fields:
            source_lower = source_field.lower()
            
            # Direct substring match
            if target_lower in source_lower or source_lower in target_lower:
                matches.append(source_field)
                continue
                
            # Semantic group matching
            for key, synonyms in semantic_groups.items():
                if key in target_lower and any(syn in source_lower for syn in synonyms):
                    matches.append(source_field)
                elif key in source_lower and any(syn in target_lower for syn in synonyms):
                    matches.append(source_field)
        
        return matches

    def _generate_assembly_logic(self, input_data: str) -> str:
        """Generate intelligent assembly logic between nodes"""
        try:
            parts = input_data.split("|")
            if len(parts) != 3:
                return "Input format should be: source_node|target_node|user_intent"

            source_node, target_node, user_intent = parts

            # Load configurations
            source_config_path = self.nodes_dir / source_node / "config.json"
            target_config_path = self.nodes_dir / target_node / "config.json"

            with open(source_config_path, 'r') as f:
                source_config = json.load(f)
            with open(target_config_path, 'r') as f:
                target_config = json.load(f)

            source_outputs = source_config.get("output_schema", [])
            target_inputs = target_config.get("input_schema", {})
            target_required = target_inputs.get("required", [])

            assembly_logic = {}

            # Generate intelligent assembly based on user intent
            intent_lower = user_intent.lower()

            for required_field in target_required:
                if required_field in source_outputs:
                    # Direct mapping
                    assembly_logic[f"mapped_{required_field}"] = required_field
                else:
                    # Intelligent transformation based on intent
                    if "best" in intent_lower or "relevant" in intent_lower:
                        if "articles" in source_outputs and "url" in required_field:
                            assembly_logic[f"selected_{required_field}"] = {
                                "action": "intelligent_select",
                                "from": "articles",
                                "criteria": f"most relevant to: {user_intent}",
                                "extract": required_field,
                                "fallback": "select_index",
                                "fallback_index": 0
                            }
                    elif "first" in intent_lower or "latest" in intent_lower:
                        if "articles" in source_outputs:
                            assembly_logic[f"selected_{required_field}"] = {
                                "action": "select_index",
                                "from": "articles",
                                "index": 0,
                                "extract": required_field
                            }
                    elif "random" in intent_lower:
                        if "articles" in source_outputs:
                            assembly_logic[f"selected_{required_field}"] = {
                                "action": "select_random",
                                "from": "articles",
                                "extract": required_field
                            }

            return json.dumps({
                "assembly_logic": assembly_logic,
                "user_intent": user_intent,
                "transformation_strategy": self._determine_transformation_strategy(user_intent),
                "quality_checks": self._generate_quality_checks(user_intent)
            }, indent=2)

        except Exception as e:
            return f"Error generating assembly logic: {str(e)}"

    def _determine_transformation_strategy(self, user_intent: str) -> str:
        """Determine the best transformation strategy based on user intent"""
        intent_lower = user_intent.lower()
        
        if any(word in intent_lower for word in ["best", "relevant", "important", "interesting"]):
            return "quality_based_selection"
        elif any(word in intent_lower for word in ["first", "latest", "recent", "new"]):
            return "chronological_selection"
        elif any(word in intent_lower for word in ["random", "any", "sample"]):
            return "random_selection"
        elif any(word in intent_lower for word in ["all", "every", "complete"]):
            return "comprehensive_processing"
        else:
            return "intelligent_selection"

    def _generate_quality_checks(self, user_intent: str) -> List[str]:
        """Generate quality checks based on user intent"""
        checks = ["validate_data_exists", "check_required_fields"]
        
        intent_lower = user_intent.lower()
        
        if "quality" in intent_lower or "best" in intent_lower:
            checks.extend(["content_length_check", "relevance_scoring"])
        if "accurate" in intent_lower or "reliable" in intent_lower:
            checks.extend(["source_validation", "data_consistency_check"])
        if "complete" in intent_lower:
            checks.extend(["completeness_validation", "missing_data_handling"])
            
        return checks

    def _validate_workflow_structure(self, workflow_json: str) -> str:
        """Comprehensive workflow validation"""
        try:
            workflow = json.loads(workflow_json)
            
            validation_results = {
                "structure_valid": True,
                "errors": [],
                "warnings": [],
                "optimization_suggestions": [],
                "data_flow_analysis": {}
            }

            # Basic structure validation
            required_fields = ["name", "steps"]
            for field in required_fields:
                if field not in workflow:
                    validation_results["errors"].append(f"Missing required field: {field}")
                    validation_results["structure_valid"] = False

            if "steps" in workflow:
                steps = workflow["steps"]
                if not isinstance(steps, list):
                    validation_results["errors"].append("'steps' must be an array")
                    validation_results["structure_valid"] = False
                else:
                    # Validate each step
                    for i, step in enumerate(steps):
                        step_errors = self._validate_step(step, i)
                        validation_results["errors"].extend(step_errors)

                    # Analyze data flow
                    flow_analysis = self._analyze_workflow_data_flow(steps)
                    validation_results["data_flow_analysis"] = flow_analysis

            return json.dumps(validation_results, indent=2)

        except json.JSONDecodeError as e:
            return f"Invalid JSON: {str(e)}"
        except Exception as e:
            return f"Validation error: {str(e)}"

    def _validate_step(self, step: Dict[str, Any], step_index: int) -> List[str]:
        """Validate individual workflow step"""
        errors = []
        
        if "node" in step:
            # Node step validation
            node_name = step["node"]
            if "inputs" not in step:
                errors.append(f"Step {step_index + 1}: Missing 'inputs' field")
            
            # Check if node exists
            node_path = self.nodes_dir / node_name
            if not node_path.exists():
                errors.append(f"Step {step_index + 1}: Node '{node_name}' does not exist")
                
        elif "assembly" in step:
            # Assembly step validation
            if "source" not in step:
                errors.append(f"Step {step_index + 1}: Assembly step missing 'source' field")
            if "name" not in step:
                errors.append(f"Step {step_index + 1}: Assembly step missing 'name' field")
                
        else:
            errors.append(f"Step {step_index + 1}: Must contain either 'node' or 'assembly' field")
            
        return errors

    def _analyze_workflow_data_flow(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze data flow through the workflow"""
        flow_analysis = {
            "step_dependencies": {},
            "data_transformations": [],
            "potential_bottlenecks": [],
            "optimization_opportunities": []
        }
        
        available_data = {}
        
        for i, step in enumerate(steps):
            step_name = f"step_{i}"
            
            if "node" in step:
                node_name = step["node"]
                step_name = node_name
                
                # Analyze inputs
                inputs = step.get("inputs", {})
                dependencies = []
                
                for input_field, input_value in inputs.items():
                    if isinstance(input_value, str) and "{{" in input_value:
                        # Extract dependency
                        import re
                        matches = re.findall(r'\{\{([^}]+)\}\}', input_value)
                        dependencies.extend(matches)
                
                flow_analysis["step_dependencies"][step_name] = dependencies
                
                # Add outputs to available data (simplified)
                available_data[step_name] = ["output_data"]
                
            elif "assembly" in step:
                assembly_name = step.get("name", f"assembly_{i}")
                source = step.get("source", "")
                
                flow_analysis["step_dependencies"][assembly_name] = [source] if source else []
                flow_analysis["data_transformations"].append({
                    "step": assembly_name,
                    "type": "assembly",
                    "source": source
                })
                
                available_data[assembly_name] = ["transformed_data"]
        
        return flow_analysis

    def _optimize_node_sequence(self, input_data: str) -> str:
        """Optimize the sequence of nodes for maximum efficiency"""
        try:
            parts = input_data.split("|")
            if len(parts) != 2:
                return "Input format should be: node_list|user_goal"

            node_list_str, user_goal = parts
            node_list = json.loads(node_list_str)

            optimization_result = {
                "original_sequence": node_list,
                "optimized_sequence": [],
                "optimization_rationale": [],
                "efficiency_improvements": []
            }

            # Analyze node dependencies and capabilities
            node_analysis = {}
            for node_name in node_list:
                config_path = self.nodes_dir / node_name / "config.json"
                if config_path.exists():
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                    node_analysis[node_name] = {
                        "inputs": config.get("input_schema", {}),
                        "outputs": config.get("output_schema", []),
                        "type": config.get("type", "unknown")
                    }

            # Optimize sequence based on data flow
            optimized = self._create_optimal_sequence(node_analysis, user_goal)
            optimization_result["optimized_sequence"] = optimized["sequence"]
            optimization_result["optimization_rationale"] = optimized["rationale"]

            return json.dumps(optimization_result, indent=2)

        except Exception as e:
            return f"Error optimizing sequence: {str(e)}"

    def _create_optimal_sequence(self, node_analysis: Dict[str, Any], user_goal: str) -> Dict[str, Any]:
        """Create optimal node sequence based on data flow analysis"""
        sequence = []
        rationale = []
        remaining_nodes = list(node_analysis.keys())
        
        # Start with data source nodes (nodes that don't require external inputs)
        source_nodes = []
        for node_name, analysis in node_analysis.items():
            required_inputs = analysis["inputs"].get("required", [])
            if not required_inputs or all(self._is_external_input(inp) for inp in required_inputs):
                source_nodes.append(node_name)
        
        if source_nodes:
            # Choose best source node based on user goal
            best_source = self._select_best_source_node(source_nodes, node_analysis, user_goal)
            sequence.append(best_source)
            remaining_nodes.remove(best_source)
            rationale.append(f"Started with {best_source} as primary data source")
        
        # Add remaining nodes based on data flow dependencies
        while remaining_nodes:
            next_node = self._find_next_compatible_node(sequence, remaining_nodes, node_analysis)
            if next_node:
                sequence.append(next_node)
                remaining_nodes.remove(next_node)
                rationale.append(f"Added {next_node} to process data from previous steps")
            else:
                # Add remaining nodes in original order if no clear dependencies
                sequence.extend(remaining_nodes)
                rationale.append("Added remaining nodes in original order")
                break
        
        return {"sequence": sequence, "rationale": rationale}

    def _is_external_input(self, input_field: str) -> bool:
        """Check if input field is typically provided externally (API keys, URLs, etc.)"""
        external_indicators = ["api", "key", "token", "url", "endpoint", "credentials"]
        return any(indicator in input_field.lower() for indicator in external_indicators)

    def _select_best_source_node(self, source_nodes: List[str], node_analysis: Dict, user_goal: str) -> str:
        """Select the best source node based on user goal"""
        goal_lower = user_goal.lower()
        
        for node_name in source_nodes:
            node_type = node_analysis[node_name].get("type", "").lower()
            if "scraper" in node_type and any(word in goal_lower for word in ["scrape", "collect", "gather"]):
                return node_name
            if "api" in node_type and "api" in goal_lower:
                return node_name
        
        return source_nodes[0]  # Default to first available

    def _find_next_compatible_node(self, current_sequence: List[str], remaining_nodes: List[str], node_analysis: Dict) -> Optional[str]:
        """Find the next node that can process data from current sequence"""
        if not current_sequence:
            return None
            
        last_node = current_sequence[-1]
        last_outputs = node_analysis.get(last_node, {}).get("outputs", [])
        
        for node_name in remaining_nodes:
            required_inputs = node_analysis[node_name]["inputs"].get("required", [])
            
            # Check if any required input can be satisfied by previous outputs
            for required_input in required_inputs:
                if required_input in last_outputs or self._is_external_input(required_input):
                    return node_name
        
        return None

    def _analyze_user_requirements(self, user_request: str) -> str:
        """Deep analysis of user requirements"""
        analysis = {
            "primary_goal": "",
            "data_sources_needed": [],
            "processing_requirements": [],
            "output_requirements": [],
            "quality_criteria": [],
            "workflow_complexity": "medium",
            "estimated_steps": 0,
            "key_entities": [],
            "action_verbs": [],
            "success_metrics": []
        }

        request_lower = user_request.lower()
        words = request_lower.split()

        # Extract action verbs
        action_verbs = ["find", "get", "collect", "gather", "scrape", "analyze", "process", "summarize", "create", "generate", "monitor", "track"]
        analysis["action_verbs"] = [verb for verb in action_verbs if verb in words]

        # Determine primary goal
        if any(verb in words for verb in ["find", "search", "collect", "gather"]):
            analysis["primary_goal"] = "data_collection"
        elif any(verb in words for verb in ["analyze", "process", "summarize"]):
            analysis["primary_goal"] = "data_processing"
        elif any(verb in words for verb in ["create", "generate", "build"]):
            analysis["primary_goal"] = "content_creation"
        elif any(verb in words for verb in ["monitor", "track", "watch"]):
            analysis["primary_goal"] = "monitoring"

        # Identify data sources
        if any(word in request_lower for word in ["news", "articles", "web", "website"]):
            analysis["data_sources_needed"].append("web_content")
        if any(word in request_lower for word in ["api", "service", "database"]):
            analysis["data_sources_needed"].append("api_data")
        if any(word in request_lower for word in ["social", "twitter", "facebook"]):
            analysis["data_sources_needed"].append("social_media")

        # Identify processing requirements
        if any(word in request_lower for word in ["summarize", "summary", "brief"]):
            analysis["processing_requirements"].append("text_summarization")
        if any(word in request_lower for word in ["analyze", "analysis", "insights"]):
            analysis["processing_requirements"].append("data_analysis")
        if any(word in request_lower for word in ["filter", "select", "choose"]):
            analysis["processing_requirements"].append("data_filtering")

        # Determine quality criteria
        if any(word in request_lower for word in ["best", "top", "highest", "quality"]):
            analysis["quality_criteria"].append("high_quality_selection")
        if any(word in request_lower for word in ["relevant", "related", "matching"]):
            analysis["quality_criteria"].append("relevance_filtering")
        if any(word in request_lower for word in ["recent", "latest", "new"]):
            analysis["quality_criteria"].append("recency_priority")

        # Estimate workflow complexity
        complexity_indicators = len(analysis["action_verbs"]) + len(analysis["processing_requirements"])
        if complexity_indicators <= 2:
            analysis["workflow_complexity"] = "simple"
            analysis["estimated_steps"] = 2-3
        elif complexity_indicators <= 4:
            analysis["workflow_complexity"] = "medium"
            analysis["estimated_steps"] = 3-5
        else:
            analysis["workflow_complexity"] = "complex"
            analysis["estimated_steps"] = 5-8

        return json.dumps(analysis, indent=2)

    def _save_workflow_file(self, input_data: str) -> str:
        """Save workflow to file"""
        try:
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

    def create_workflow(self, user_request: str) -> Dict[str, Any]:
        """Advanced workflow creation with comprehensive analysis"""
        try:
            self.conversation_history.append({"role": "user", "content": user_request})

            # Create comprehensive system message
            system_message = self._get_advanced_system_prompt()

            # Create detailed user message with analysis instructions
            user_message = f"""
USER REQUEST: "{user_request}"

TASK: Create a perfect workflow that accomplishes this user's goal using the available Orchestra nodes.

PROCESS:
1. Use discover_all_nodes to understand ALL available nodes and their capabilities
2. Use analyze_user_requirements to deeply understand what the user needs
3. Select the OPTIMAL nodes for this specific request (not just the example nodes)
4. Use analyze_node_compatibility to ensure proper data flow between selected nodes
5. Use generate_assembly_logic to create intelligent data transformations
6. Create the complete workflow JSON with perfect assembly logic
7. Use validate_workflow_structure to ensure everything is correct

CRITICAL REQUIREMENTS:
- The workflow must use the BEST available nodes for this specific request
- Assembly steps must intelligently transform data based on user intent
- Every input must have a valid data source
- The final output must perfectly match what the user requested

Create a workflow that would work with ANY available nodes, not just the current examples.
"""

            messages = [
                SystemMessage(content=system_message),
                HumanMessage(content=user_message)
            ]

            initial_response = self.llm.invoke(messages)
            final_response = self._process_agent_response(initial_response.content)

            # Extract workflow JSON from response
            workflow_json = self._extract_workflow_json(final_response)

            if workflow_json:
                self.conversation_history.append({
                    "role": "assistant", 
                    "content": final_response
                })

                return {
                    "success": True,
                    "response": final_response,
                    "workflow_json": workflow_json,
                    "conversation_history": self.conversation_history
                }
            else:
                return {
                    "success": False,
                    "error": "Could not extract valid workflow JSON from response",
                    "response": final_response,
                    "conversation_history": self.conversation_history
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": f"Failed to create workflow: {str(e)}",
                "conversation_history": self.conversation_history
            }

    def _extract_workflow_json(self, response: str) -> Optional[Dict[str, Any]]:
        """Extract workflow JSON from agent response"""
        try:
            # Look for JSON blocks in the response
            import re
            
            # Try to find JSON between ```json and ``` or { and }
            json_patterns = [
                r'```json\s*(\{.*?\})\s*```',
                r'```\s*(\{.*?\})\s*```',
                r'(\{[^{}]*"steps"[^{}]*\[.*?\][^{}]*\})'
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, response, re.DOTALL)
                for match in matches:
                    try:
                        workflow = json.loads(match)
                        if "steps" in workflow:
                            return workflow
                    except json.JSONDecodeError:
                        continue
            
            # If no JSON blocks found, try to extract the largest JSON-like structure
            brace_count = 0
            start_idx = -1
            
            for i, char in enumerate(response):
                if char == '{':
                    if brace_count == 0:
                        start_idx = i
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0 and start_idx != -1:
                        try:
                            potential_json = response[start_idx:i+1]
                            workflow = json.loads(potential_json)
                            if "steps" in workflow:
                                return workflow
                        except json.JSONDecodeError:
                            continue
            
            return None
            
        except Exception as e:
            print(f"Error extracting workflow JSON: {e}")
            return None

    def improve_workflow(self, workflow_json: str, feedback: str) -> Dict[str, Any]:
        """Improve workflow based on feedback"""
        try:
            system_message = self._get_advanced_system_prompt()

            user_message = f"""
CURRENT WORKFLOW: {workflow_json}

USER FEEDBACK: "{feedback}"

TASK: Improve this workflow based on the user's feedback.

PROCESS:
1. Analyze the current workflow structure and logic
2. Understand what the user wants changed/improved
3. Use your tools to analyze better node combinations if needed
4. Create improved assembly logic based on feedback
5. Validate the improved workflow
6. Provide the updated workflow JSON

Focus on making the workflow more intelligent and better aligned with user expectations.
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
            system_message = self._get_advanced_system_prompt()

            user_message = f"""
WORKFLOW TO EXPLAIN: {workflow_json}

TASK: Provide a comprehensive explanation of this workflow.

Use your tools to:
1. Analyze each node used in the workflow
2. Understand the data flow between steps
3. Explain the assembly logic and transformations
4. Describe what the final output will be

Provide a clear explanation that both technical and non-technical users can understand.
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