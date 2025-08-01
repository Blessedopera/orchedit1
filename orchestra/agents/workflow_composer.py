#!/usr/bin/env python3
"""
Orchestra Workflow Composer Agent - Enhanced LangChain agent for intelligent workflow creation
"""
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import re

class WorkflowComposerAgent:
    """LangChain-powered agent for creating intelligent workflows"""
    
    def __init__(self, api_key: str):
        """Initialize the workflow composer agent"""
        self.api_key = api_key
        self.client = None
        self.available_nodes = {}
        self.node_schemas = {}
        
        # Initialize OpenRouter client
        self._init_client()
        
        # Load available nodes and their schemas
        self._load_available_nodes()
    
    def _init_client(self):
        """Initialize OpenRouter client"""
        try:
            from openai import OpenAI
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.api_key,
            )
        except ImportError:
            raise ImportError("openai package required for OpenRouter API")
    
    def _load_available_nodes(self):
        """Load all available nodes and their configurations"""
        try:
            # Import the glue runner to get available nodes
            current_dir = Path(__file__).parent
            backend_dir = current_dir.parent / "backend"
            sys.path.insert(0, str(backend_dir))
            
            from glue_runner import OrchestraGlueRunner
            runner = OrchestraGlueRunner()
            nodes = runner.list_available_nodes()
            
            for node in nodes:
                node_name = node['node_name']
                self.available_nodes[node_name] = node
                
                # Load detailed schema with example inputs for data type understanding
                self.node_schemas[node_name] = self._load_detailed_node_schema(node_name, node)
            
            print(f"Loaded {len(self.available_nodes)} available nodes: {list(self.available_nodes.keys())}")
            
        except Exception as e:
            print(f"Warning: Could not load available nodes: {e}")
            # Fallback to known nodes if loading fails
            self.available_nodes = {
                'google-news-scraper': {'node_name': 'google-news-scraper'},
                'article-page-scraper': {'node_name': 'article-page-scraper'},
                'article-processor': {'node_name': 'article-processor'}
            }
    
    def _load_detailed_node_schema(self, node_name: str, node_config: Dict[str, Any]) -> Dict[str, Any]:
        """Load detailed schema including example inputs to understand data types"""
        schema = {
            'name': node_config.get('name', node_name),
            'description': node_config.get('description', ''),
            'input_schema': node_config.get('input_schema', {}),
            'output_schema': node_config.get('output_schema', []),
            'type': node_config.get('type', 'unknown'),
            'dependencies': node_config.get('dependencies', [])
        }
        
        # Load example input to understand exact data types
        try:
            current_dir = Path(__file__).parent
            example_path = current_dir.parent / "nodes" / node_name / "example_input.json"
            
            if example_path.exists():
                with open(example_path, 'r') as f:
                    example_input = json.load(f)
                    schema['example_input'] = example_input
                    schema['field_types'] = self._analyze_field_types(example_input)
        except Exception as e:
            print(f"Warning: Could not load example input for {node_name}: {e}")
            schema['example_input'] = {}
            schema['field_types'] = {}
        
        return schema
    
    def _analyze_field_types(self, example_input: Dict[str, Any]) -> Dict[str, str]:
        """Analyze field types from example input"""
        field_types = {}
        
        for field, value in example_input.items():
            if isinstance(value, list):
                if value and isinstance(value[0], str):
                    field_types[field] = "array_of_strings"
                elif value and isinstance(value[0], dict):
                    field_types[field] = "array_of_objects"
                else:
                    field_types[field] = "array"
            elif isinstance(value, dict):
                field_types[field] = "object"
            elif isinstance(value, str):
                field_types[field] = "string"
            elif isinstance(value, int):
                field_types[field] = "integer"
            elif isinstance(value, float):
                field_types[field] = "number"
            elif isinstance(value, bool):
                field_types[field] = "boolean"
            else:
                field_types[field] = "unknown"
        
        return field_types
    
    def _call_openrouter(self, messages: List[Dict[str, str]], max_tokens: int = 2000) -> str:
        """Call OpenRouter API"""
        try:
            completion = self.client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "https://orchestra-ai.com",
                    "X-Title": "Orchestra Workflow Composer",
                },
                model="qwen/qwen3-coder:free",
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.3
            )
            return completion.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenRouter API call failed: {str(e)}")
    
    def create_workflow(self, user_request: str) -> Dict[str, Any]:
        """Create a workflow based on user request using only available nodes"""
        
        # Step 1: Analyze available nodes and create detailed node information
        node_info = self._create_detailed_node_info()
        
        # Step 2: Create the workflow using available nodes
        workflow_prompt = f"""
You are an expert workflow architect for the Orchestra automation system. Your job is to create a PERFECT workflow JSON that uses ONLY the available nodes to fulfill the user's request.

## CRITICAL VARIABLE SUBSTITUTION RULES:
1. **ASSEMBLY STEP NAMES MUST MATCH VARIABLE REFERENCES**
   - If you create assembly step named "article_selector", variables must use "{{article_selector.field_name}}"
   - If you create output field "selected_url", reference it as "{{step_name.selected_url}}"
   - NEVER create variables that don't match actual step names and output fields

2. **ASSEMBLY OUTPUT FIELDS MUST BE USED CORRECTLY**
   - Assembly step creates: {{"selected_url": {{"action": "select_index", "from": "articles", "extract": "url"}}}}
   - Next step references: "{{assembly_step_name.selected_url}}"
   - The field name after the dot MUST match the assembly output field name

3. **VALIDATE EVERY VARIABLE REFERENCE**
   - Before using "{{step_name.field}}", ensure step_name exists and produces field
   - Check that assembly steps create the exact fields referenced later
   - Trace data flow: Node Output → Assembly Transform → Next Node Input

## CRITICAL REQUIREMENTS:
1. **ONLY USE AVAILABLE NODES** - Never invent nodes that don't exist
2. **USE EXACT INPUT FIELD NAMES AND DATA TYPES** - Match the input_schema exactly with correct data types
3. **FOLLOW EXAMPLE INPUT FORMATS** - Use the exact same data structure as shown in examples
4. **CHAIN OUTPUTS TO INPUTS CORRECTLY** - Use proper variable substitution with EXACT step names
5. **CREATE SMART ASSEMBLY LOGIC** - Transform data between nodes intelligently
6. **VALIDATE VARIABLE CHAINS** - Ensure every {{variable}} reference actually exists

## DATA TYPE REQUIREMENTS:
- If example shows `"keywords": ["AI", "tech"]` → ALWAYS use array format: `["keyword1", "keyword2"]`
- If example shows `"max_news": 5` → ALWAYS use integer: `5` (not string "5")
- If example shows `"headless": true` → ALWAYS use boolean: `true` (not string "true")
- If example shows `"api_token": "your-token"` → Use string format

## CRITICAL: MATCH EXACT DATA TYPES FROM EXAMPLES!

## VARIABLE SUBSTITUTION EXAMPLES (CORRECT):
```json
// Step 1: Node produces output
{{"node": "google-news-scraper", "inputs": {{...}}}}
// This creates: google-news-scraper.articles (array of article objects)

// Step 2: Assembly transforms data  
{{
  "assembly": {{
    "selected_article_url": {{
      "action": "select_index",
      "from": "articles", 
      "extract": "url",
      "index": 0
    }}
  }},
  "source": "google-news-scraper",
  "name": "article_selector"
}}
// This creates: article_selector.selected_article_url (string URL)

// Step 3: Next node uses the data
{{
  "node": "article-page-scraper",
  "inputs": {{
    "url": "{{article_selector.selected_article_url}}"  // CORRECT REFERENCE
  }}
}}
```

## VARIABLE SUBSTITUTION EXAMPLES (WRONG - DON'T DO THIS):
```json
// ❌ WRONG: Creating variable that doesn't exist
"url": "{{url_extractor.selected_url}}"  // No step named "url_extractor"

// ❌ WRONG: Field name doesn't match assembly output
"url": "{{article_selector.url}}"  // Assembly creates "selected_article_url", not "url"

// ❌ WRONG: Using node output directly without assembly
"article_text": "{{google-news-scraper.articles}}"  // articles is array, need single article
```

## AVAILABLE NODES AND THEIR EXACT SCHEMAS:
{node_info}

## USER REQUEST:
"{user_request}"

## YOUR TASK:
Create a complete workflow JSON that:
1. Uses ONLY the available nodes listed above
2. Uses the EXACT input field names from each node's schema
3. Creates proper assembly steps with CORRECT variable references
4. Fulfills the user's request completely
5. VALIDATES that every {{variable}} reference actually exists

## ASSEMBLY ACTIONS AVAILABLE:
- `select_random`: Pick random item from array
- `select_index`: Pick specific index (0 = first, 1 = second, etc.)
- `extract`: Copy field directly
- `intelligent_select`: Pick best item based on criteria (for future AI enhancement)

## ASSEMBLY STEP NAMING RULES:
- Use descriptive names: "article_selector", "text_extractor", "data_processor"
- Assembly step name becomes the variable prefix: {{step_name.output_field}}
- Output field names should be clear: "selected_url", "clean_text", "processed_data"

## WORKFLOW JSON FORMAT:
```json
{{
  "name": "Descriptive Workflow Name",
  "description": "What this workflow accomplishes",
  "version": "1.0.0",
  "created_by": "Orchestra AI Agent",
  "user_request": "{user_request}",
  "steps": [
    {{
      "node": "exact-node-name-from-available-list",
      "inputs": {{
        "exact_field_name": "CORRECT_DATA_TYPE_value_or_{{previous_step.output_field}}"
      }}
    }},
    {{
      "assembly": {{
        "output_field_name": {{
          "action": "select_random|select_index|extract",
          "from": "source_field_name",
          "extract": "field_to_extract_if_needed",
          "index": 0
        }}
      }},
      "source": "previous_step_node_name",
      "name": "descriptive_assembly_name",
      "description": "What this assembly step does"
    }}
  ]
}}
```

## CRITICAL VALIDATION CHECKLIST:
Before finalizing the workflow, verify:
1. ✅ Every node name exists in available nodes list
2. ✅ Every input field matches the node's exact schema
3. ✅ Every {{variable}} reference has a matching step name and output field
4. ✅ Data types match examples (arrays, integers, booleans, strings)
5. ✅ Assembly steps create the exact fields referenced in next steps
6. ✅ Variable chain flows logically: Node → Assembly → Next Node

## CRITICAL DATA TYPE EXAMPLES:
- google-news-scraper keywords: `["AI", "finance"]` (ARRAY, not string)
- google-news-scraper max_news: `10` (INTEGER, not string)
- article-page-scraper headless: `true` (BOOLEAN, not string)
- article-processor temperature: `0.3` (NUMBER, not string)

## WORKING VARIABLE SUBSTITUTION EXAMPLES:
- `{{google-news-scraper.articles}}` - Array of articles from google-news-scraper node
- `{{article_selector.selected_article_url}}` - URL from assembly step named "article_selector" 
- `{{article-page-scraper.article_text}}` - Text from article-page-scraper node
- `{{text_processor.clean_content}}` - Content from assembly step named "text_processor"

Create the workflow JSON now. Be precise with:
1. Field names AND data types
2. Variable references that actually exist
3. Assembly step names that match variable prefixes
4. Data flow that works with available nodes

REMEMBER: 
- Look at EXAMPLE USAGE for exact data formats
- Validate EVERY {{variable}} reference
- Ensure assembly output fields match variable references
- Test the data flow logic before finalizing
"""

        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert workflow architect. Create precise, working workflows using only available nodes with correct schemas."
                },
                {
                    "role": "user", 
                    "content": workflow_prompt
                }
            ]
            
            response = self._call_openrouter(messages, max_tokens=3000)
            
            # Extract JSON from response
            workflow_json = self._extract_json_from_response(response)
            
            # Ensure proper JSON formatting
            if workflow_json:
                workflow_json = self._ensure_proper_json_format(workflow_json)
                
                # Validate JSON syntax
                if not self._validate_json_syntax(workflow_json):
                    return {
                        "success": False,
                        "error": "Generated workflow contains invalid JSON syntax",
                        "response": response
                    }
            
            if workflow_json:
                # Validate the workflow
                validation_result = self._validate_workflow(workflow_json)
                
                return {
                    "success": True,
                    "response": response,
                    "workflow_json": workflow_json,
                    "validation": validation_result
                }
            else:
                return {
                    "success": False,
                    "error": "Could not extract valid JSON from agent response",
                    "response": response
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_detailed_node_info(self) -> str:
        """Create detailed information about available nodes"""
        node_details = []
        
        for node_name, schema in self.node_schemas.items():
            # Create detailed schema with exact data types and examples
            input_details = self._format_input_schema_with_types(schema)
            output_details = self._format_output_schema(schema)
            
            detail = f"""
### NODE: {node_name}
- **Name**: {schema['name']}
- **Description**: {schema['description']}
- **Type**: {schema['type']}

**EXACT INPUT SCHEMA WITH DATA TYPES:**
{input_details}

**OUTPUT SCHEMA:**
{output_details}

**EXAMPLE USAGE:**
{self._get_example_usage(node_name, schema)}
"""
            node_details.append(detail)
        
        return "\n".join(node_details)
    
    def _format_input_schema_with_types(self, schema: Dict[str, Any]) -> str:
        """Format input schema with exact data types and examples"""
        input_schema = schema.get('input_schema', {})
        field_types = schema.get('field_types', {})
        example_input = schema.get('example_input', {})
        
        required_fields = input_schema.get('required', [])
        optional_fields = input_schema.get('optional', [])
        
        details = []
        
        if required_fields:
            details.append("**REQUIRED FIELDS:**")
            for field in required_fields:
                field_type = field_types.get(field, 'unknown')
                example_value = example_input.get(field, 'N/A')
                details.append(f"  - `{field}` ({field_type}): Example = {json.dumps(example_value)}")
        
        if optional_fields:
            details.append("**OPTIONAL FIELDS:**")
            for field in optional_fields:
                field_type = field_types.get(field, 'unknown')
                example_value = example_input.get(field, 'N/A')
                details.append(f"  - `{field}` ({field_type}): Example = {json.dumps(example_value)}")
        
        return "\n".join(details) if details else "No input schema available"
    
    def _format_output_schema(self, schema: Dict[str, Any]) -> str:
        """Format output schema information"""
        output_schema = schema.get('output_schema', [])
        if isinstance(output_schema, list):
            return "Fields: " + ", ".join(output_schema)
        else:
            return str(output_schema)
    
    def _get_example_usage(self, node_name: str, schema: Dict[str, Any]) -> str:
        """Get example usage for the node"""
        example_input = schema.get('example_input', {})
        
        if example_input:
            # Create a clean example without sensitive data
            clean_example = {}
            for key, value in example_input.items():
                if 'key' in key.lower() or 'token' in key.lower():
                    clean_example[key] = f"your-{key.replace('_', '-')}-here"
                else:
                    clean_example[key] = value
            
            return f"""```json
{{
  "node": "{node_name}",
  "inputs": {json.dumps(clean_example, indent=4)}
}}
```"""
        else:
            return "No example available"
    
    def _get_node_use_case(self, node_name: str, schema: Dict[str, Any]) -> str:
        """Get specific use case information for each node"""
        use_cases = {
            'google-news-scraper': 'Fetches news articles from Google News. Outputs: articles array with url, title, source, publishedAt fields',
            'article-page-scraper': 'Scrapes full article content from a URL. Takes url input, outputs: article_text, html_file, success',
            'article-processor': 'Processes article text using AI. Takes article_text and openrouter_api_key, outputs: summary, original_text, success'
        }
        
        return use_cases.get(node_name, f"General {schema.get('type', 'processing')} node")
    
    def _extract_json_from_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Extract JSON workflow from agent response"""
        try:
            # Look for JSON code blocks
            json_pattern = r'```json\s*(.*?)\s*```'
            matches = re.findall(json_pattern, response, re.DOTALL)
            
            if matches:
                json_str = matches[0]
            else:
                # Try to find JSON without code blocks
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = response[json_start:json_end]
                else:
                    return None
            
            # Parse JSON
            workflow = json.loads(json_str)
            return workflow
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            return None
        except Exception as e:
            print(f"Error extracting JSON: {e}")
            return None
    
    def _ensure_proper_json_format(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure workflow has proper JSON formatting for copy-paste"""
        # Fix any formatting issues that might cause JSON parsing problems
        
        # Ensure all variable references use double curly braces
        workflow_str = json.dumps(workflow, indent=2)
        
        # Fix single curly braces to double curly braces for variables
        import re
        workflow_str = re.sub(r'(?<!\{)\{([^{}]+)\}(?!\})', r'{{\1}}', workflow_str)
        
        # Parse back to ensure it's valid JSON
        try:
            return json.loads(workflow_str)
        except json.JSONDecodeError:
            return workflow
    
    def _validate_workflow(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Validate workflow structure and node usage"""
        validation = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check required fields
        required_fields = ['name', 'description', 'steps']
        for field in required_fields:
            if field not in workflow:
                validation["errors"].append(f"Missing required field: {field}")
                validation["valid"] = False
        
        # Validate variable substitution chains
        variable_validation = self._validate_variable_chains(workflow)
        validation["errors"].extend(variable_validation["errors"])
        validation["warnings"].extend(variable_validation["warnings"])
        if not variable_validation["valid"]:
            validation["valid"] = False
        
        # Validate steps
        if 'steps' in workflow:
            for i, step in enumerate(workflow['steps']):
                step_validation = self._validate_step(step, i)
                validation["errors"].extend(step_validation["errors"])
                validation["warnings"].extend(step_validation["warnings"])
                if not step_validation["valid"]:
                    validation["valid"] = False
        
        return validation
    
    def _validate_variable_chains(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that all variable references actually exist in the workflow"""
        validation = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        if 'steps' not in workflow:
            return validation
        
        # Track available outputs from each step
        available_outputs = {}
        
        for i, step in enumerate(workflow['steps']):
            step_name = None
            
            if 'node' in step:
                # Node step - track its outputs
                node_name = step['node']
                step_name = node_name
                
                # Add known outputs for this node type
                if node_name in self.node_schemas:
                    output_schema = self.node_schemas[node_name].get('output_schema', [])
                    for output_field in output_schema:
                        available_outputs[f"{step_name}.{output_field}"] = True
            
            elif 'assembly' in step:
                # Assembly step - track its outputs
                step_name = step.get('name', f'assembly_{i}')
                assembly_config = step.get('assembly', {})
                
                # Add assembly outputs
                for output_field in assembly_config.keys():
                    available_outputs[f"{step_name}.{output_field}"] = True
            
            # Check variable references in this step's inputs
            if 'inputs' in step:
                self._check_variable_references_in_inputs(
                    step['inputs'], available_outputs, i, validation
                )
        
        return validation
    
    def _check_variable_references_in_inputs(self, inputs: Dict[str, Any], 
                                           available_outputs: Dict[str, bool], 
                                           step_index: int, validation: Dict[str, Any]):
        """Check variable references in step inputs"""
        import re
        
        for field_name, field_value in inputs.items():
            if isinstance(field_value, str):
                # Find variable references like {{step.field}}
                pattern = r'\{\{([^}]+)\}\}'
                matches = re.findall(pattern, field_value)
                
                for match in matches:
                    variable_ref = match.strip()
                    
                    if variable_ref not in available_outputs:
                        validation["errors"].append(
                            f"Step {step_index}: Variable reference '{{{{{{variable_ref}}}}}}' not found. "
                            f"Available outputs: {list(available_outputs.keys())}"
                        )
                        validation["valid"] = False
    
    def _validate_step(self, step: Dict[str, Any], step_index: int) -> Dict[str, Any]:
        """Validate individual workflow step"""
        validation = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        if 'node' in step:
            # Validate node step
            node_name = step['node']
            
            # Check if node exists
            if node_name not in self.available_nodes:
                validation["errors"].append(f"Step {step_index}: Node '{node_name}' not available. Available nodes: {list(self.available_nodes.keys())}")
                validation["valid"] = False
            else:
                # Validate inputs against schema
                if 'inputs' in step and node_name in self.node_schemas:
                    schema = self.node_schemas[node_name]
                    required_inputs = schema['input_schema'].get('required', [])
                    provided_inputs = list(step['inputs'].keys())
                    
                    # Check required inputs
                    for required_input in required_inputs:
                        if required_input not in provided_inputs:
                            validation["warnings"].append(f"Step {step_index}: Missing required input '{required_input}' for node '{node_name}'")
        
        elif 'assembly' in step:
            # Validate assembly step
            if 'source' not in step:
                validation["errors"].append(f"Step {step_index}: Assembly step missing 'source' field")
                validation["valid"] = False
        
        else:
            validation["errors"].append(f"Step {step_index}: Step must contain either 'node' or 'assembly'")
            validation["valid"] = False
        
        return validation
    
    def analyze_workflow_compatibility(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze workflow for node compatibility and optimization opportunities"""
        analysis = {
            "compatibility_score": 0.0,
            "optimization_suggestions": [],
            "potential_issues": [],
            "data_flow_analysis": []
        }
        
        if 'steps' not in workflow:
            return analysis
        
        steps = workflow['steps']
        compatibility_scores = []
        
        # Analyze each step and its compatibility with the next
        for i in range(len(steps) - 1):
            current_step = steps[i]
            next_step = steps[i + 1]
            
            score = self._calculate_step_compatibility(current_step, next_step)
            compatibility_scores.append(score)
            
            if score < 0.7:
                analysis["potential_issues"].append(f"Low compatibility between step {i+1} and {i+2}")
        
        # Calculate overall compatibility
        if compatibility_scores:
            analysis["compatibility_score"] = sum(compatibility_scores) / len(compatibility_scores)
        
        return analysis
    
    def _calculate_step_compatibility(self, step1: Dict[str, Any], step2: Dict[str, Any]) -> float:
        """Calculate compatibility score between two workflow steps"""
        # Simple compatibility scoring based on data flow
        # This could be enhanced with more sophisticated analysis
        
        if 'node' in step1 and 'node' in step2:
            # Both are node steps - check if outputs can feed inputs
            return 0.8  # Assume good compatibility for now
        elif 'assembly' in step2:
            # Assembly step can usually handle any input
            return 0.9
        else:
            return 0.7  # Default compatibility