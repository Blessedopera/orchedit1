#!/usr/bin/env python3
"""
Orchestra Glue Runner - Core engine for chaining reusable nodes
"""
import json
import subprocess
import sys
import os
import re
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

class OrchestraGlueRunner:
    def __init__(self, nodes_dir: str = None):
        """Initialize the glue runner with nodes directory"""
        if nodes_dir is None:
            # Default to orchestra/nodes relative to this file
            current_dir = Path(__file__).parent
            self.nodes_dir = current_dir.parent / "nodes"
        else:
            self.nodes_dir = Path(nodes_dir)
        
        self.execution_memory = {}
        self.retry_attempts = {}
        self.max_retries = 3
        
    def load_node_config(self, node_name: str) -> Dict[str, Any]:
        """Load configuration for a specific node"""
        config_path = self.nodes_dir / node_name / "config.json"
        
        if not config_path.exists():
            raise FileNotFoundError(f"Node config not found: {config_path}")
            
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def substitute_variables(self, data: Any, memory: Dict[str, Any]) -> Any:
        """Recursively substitute {{node.field}} variables in data"""
        if isinstance(data, str):
            # Find all {{variable}} patterns
            pattern = r'\{\{([^}]+)\}\}'
            matches = re.findall(pattern, data)
            
            result = data
            for match in matches:
                # Parse node.field.subfield syntax
                parts = match.split('.')
                if len(parts) >= 2:
                    node_name = parts[0]
                    field_path = parts[1:]
                    
                    if node_name in memory:
                        value = memory[node_name]
                        # Navigate nested fields
                        for field in field_path:
                            if isinstance(value, dict) and field in value:
                                value = value[field]
                            elif isinstance(value, list) and field.startswith('[') and field.endswith(']'):
                                # Handle array indexing like [0]
                                try:
                                    index = int(field[1:-1])
                                    value = value[index]
                                except (ValueError, IndexError):
                                    value = None
                                    break
                            else:
                                value = None
                                break
                        
                        if value is not None:
                            result = result.replace(f"{{{{{match}}}}}", str(value))
            
            return result
        
        elif isinstance(data, dict):
            return {k: self.substitute_variables(v, memory) for k, v in data.items()}
        
        elif isinstance(data, list):
            return [self.substitute_variables(item, memory) for item in data]
        
        return data
    
    def apply_assembly_logic(self, node_name: str, node_output: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply workflow-specific assembly logic to extract/transform data"""
        # This method is now handled by process_assembly_step
        return node_output
    
    def process_assembly_step(self, assembly_config: Dict[str, Any], source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process assembly instructions to transform data between workflow steps"""
        import random
        
        result = {}
        
        for output_key, instruction in assembly_config.items():
            if isinstance(instruction, dict):
                action = instruction.get("action")
                source_field = instruction.get("from")
                
                if action == "select_random" and source_field in source_data:
                    # Select random item from array
                    items = source_data[source_field]
                    if isinstance(items, list) and items:
                        selected_item = random.choice(items)
                        extract_field = instruction.get("extract")
                        if extract_field and isinstance(selected_item, dict):
                            result[output_key] = selected_item.get(extract_field)
                        else:
                            result[output_key] = selected_item
                
                elif action == "select_index" and source_field in source_data:
                    # Select specific index from array
                    items = source_data[source_field]
                    index = instruction.get("index", 0)
                    if isinstance(items, list) and 0 <= index < len(items):
                        selected_item = items[index]
                        extract_field = instruction.get("extract")
                        if extract_field and isinstance(selected_item, dict):
                            result[output_key] = selected_item.get(extract_field)
                        else:
                            result[output_key] = selected_item
                
                elif action == "extract" and source_field in source_data:
                    # Simple field extraction
                    result[output_key] = source_data[source_field]
            
            elif isinstance(instruction, str):
                # Simple field copy
                if instruction in source_data:
                    result[output_key] = source_data[instruction]
        
        return result
    
    def _validate_node_output(self, node_name: str, output: Dict[str, Any]) -> Dict[str, Any]:
        """Validate node output and determine if it's usable"""
        validation = {
            "is_valid": True,
            "issues": [],
            "retry_recommended": False,
            "alternative_strategy": None
        }
        
        # Check for explicit error indicators
        if output.get("success") is False or "error" in output:
            validation["is_valid"] = False
            validation["issues"].append(f"Node {node_name} reported failure")
            validation["retry_recommended"] = True
        
        # Node-specific validation
        if node_name == "google-news-scraper":
            articles = output.get("articles", [])
            if not articles or len(articles) == 0:
                validation["is_valid"] = False
                validation["issues"].append("No articles found")
                validation["alternative_strategy"] = "try_different_keywords_or_time_period"
        
        elif node_name == "article-page-scraper":
            article_text = output.get("article_text", "")
            if not article_text or (isinstance(article_text, str) and len(article_text.strip()) < 100):
                validation["is_valid"] = False
                article_length = len(article_text) if article_text else 0
                validation["issues"].append(f"Insufficient article content: {article_length} characters")
                validation["retry_recommended"] = True
                validation["alternative_strategy"] = "try_different_article_url"
        
        elif node_name == "article-processor":
            summary = output.get("summary", "")
            if not summary or (isinstance(summary, str) and len(summary.strip()) < 50):
                validation["is_valid"] = False
                validation["issues"].append("Summary too short or missing")
                validation["retry_recommended"] = True
        
        return validation
    
    def _create_retry_strategy(self, node_name: str, original_inputs: Dict[str, Any], 
                             validation: Dict[str, Any], attempt: int) -> Dict[str, Any]:
        """Create intelligent retry strategy based on failure type"""
        retry_inputs = original_inputs.copy()
        
        if node_name == "google-news-scraper":
            if validation["alternative_strategy"] == "try_different_keywords_or_time_period":
                # Expand time period for more results
                current_period = retry_inputs.get("time_period", "Last 24 hours")
                if current_period == "Last 24 hours":
                    retry_inputs["time_period"] = "Last week"
                elif current_period == "Last week":
                    retry_inputs["time_period"] = "Last month"
                
                # Increase max_news for more options
                retry_inputs["max_news"] = min(retry_inputs.get("max_news", 10) * 2, 50)
        
        elif node_name == "article-page-scraper":
            if validation["alternative_strategy"] == "try_different_article_url":
                # This will be handled by assembly step retry
                pass
        
        return retry_inputs
    
    def _create_intelligent_assembly_retry(self, assembly_config: Dict[str, Any], 
                                         source_data: Dict[str, Any], attempt: int) -> Dict[str, Any]:
        """Create intelligent assembly retry strategy"""
        retry_config = assembly_config.copy()
        
        for output_key, instruction in retry_config.items():
            if isinstance(instruction, dict):
                action = instruction.get("action")
                
                if action == "select_index":
                    # Try next article in the list
                    current_index = instruction.get("index", 0)
                    new_index = current_index + attempt
                    source_field = instruction.get("from")
                    
                    if source_field in source_data:
                        items = source_data[source_field]
                        if isinstance(items, list) and new_index < len(items):
                            instruction["index"] = new_index
                            print(f"   🔄 Retry: Trying article at index {new_index}")
                
                elif action == "select_random":
                    # Random selection will naturally try different items
                    print(f"   🔄 Retry: Attempting different random selection")
        
        return retry_config
    
    def execute_node(self, node_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single node with given inputs"""
        node_dir = self.nodes_dir / node_name
        run_script = node_dir / "run.py"
        
        if not run_script.exists():
            raise FileNotFoundError(f"Node run script not found: {run_script}")
        
        # Prepare input JSON
        input_json = json.dumps(inputs)
        
        try:
            # Execute the node script
            result = subprocess.run(
                [sys.executable, str(run_script)],
                input=input_json,
                text=True,
                capture_output=True,
                cwd=str(node_dir),
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Node {node_name} failed with error: {result.stderr}")
            
            # Parse output JSON
            try:
                output = json.loads(result.stdout)
                return output
            except json.JSONDecodeError as e:
                raise RuntimeError(f"Node {node_name} returned invalid JSON: {result.stdout}")
                
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Node {node_name} timed out after 5 minutes")
        except Exception as e:
            raise RuntimeError(f"Failed to execute node {node_name}: {str(e)}")
    
    def execute_node_with_retry(self, node_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute node with intelligent retry logic"""
        retry_key = f"{node_name}_{hash(str(inputs))}"
        attempt = self.retry_attempts.get(retry_key, 0)
        
        while attempt < self.max_retries:
            try:
                print(f"   🔄 Attempt {attempt + 1}/{self.max_retries} for {node_name}")
                
                # Execute the node
                output = self.execute_node(node_name, inputs)
                
                # Validate output quality
                validation = self._validate_node_output(node_name, output)
                
                if validation["is_valid"]:
                    print(f"   ✅ {node_name} succeeded with valid output")
                    return output
                else:
                    print(f"   ⚠️ {node_name} output validation failed: {validation['issues']}")
                    
                    if not validation["retry_recommended"] or attempt >= self.max_retries - 1:
                        print(f"   ❌ No more retries for {node_name}")
                        return output  # Return even if not ideal
                    
                    # Create retry strategy
                    attempt += 1
                    self.retry_attempts[retry_key] = attempt
                    inputs = self._create_retry_strategy(node_name, inputs, validation, attempt)
                    print(f"   🔄 Retrying {node_name} with modified inputs")
                    time.sleep(2)  # Brief pause between retries
                    
            except Exception as e:
                attempt += 1
                self.retry_attempts[retry_key] = attempt
                
                if attempt >= self.max_retries:
                    raise e
                
                print(f"   ⚠️ {node_name} failed, retrying... ({e})")
                time.sleep(2)
        
        raise RuntimeError(f"Node {node_name} failed after {self.max_retries} attempts")
    
    def run_workflow(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a complete workflow"""
        if "steps" not in workflow:
            raise ValueError(f"Workflow must contain 'steps' array. Found keys: {list(workflow.keys())}")
        
        self.execution_memory = {}
        results = {}
        
        print("🚀 Starting Orchestra workflow execution...")
        
        for i, step in enumerate(workflow["steps"]):
            # Check if this is a node step or assembly step
            if "node" in step:
                # Regular node execution
                node_name = step["node"]
                step_inputs = step.get("inputs", {})
                
                print(f"\n📦 Executing step {i+1}: {node_name}")
                
                # Load node configuration for validation
                try:
                    config = self.load_node_config(node_name)
                    print(f"   📋 Loaded config: {config.get('name', node_name)}")
                except Exception as e:
                    print(f"   ⚠️  Warning: Could not load config: {e}")
                    config = {}
                
                # Substitute variables in inputs
                resolved_inputs = self.substitute_variables(step_inputs, self.execution_memory)
                print(f"   🔄 Resolved inputs: {list(resolved_inputs.keys())}")
                
                # Execute the node
                try:
                    node_output = self.execute_node_with_retry(node_name, resolved_inputs)
                    
                    # Store results in memory for future steps
                    self.execution_memory[node_name] = node_output
                    results[node_name] = node_output
                    
                    print(f"   ✅ Completed: {list(node_output.keys())}")
                    
                except Exception as e:
                    print(f"   ❌ Failed: {str(e)}")
                    raise
            
            elif "assembly" in step:
                # Assembly step
                assembly_name = step.get("name", f"assembly_{i+1}")
                assembly_config = step["assembly"]
                source_step = step.get("source")
                
                print(f"\n🔧 Executing assembly step {i+1}: {assembly_name}")
                
                if source_step and source_step in self.execution_memory:
                    source_data = self.execution_memory[source_step]
                    print(f"   📥 Source: {source_step}")
                    
                    # Process assembly instructions with retry logic
                    assembled_data = self.process_assembly_step_with_retry(
                        assembly_config, source_data, assembly_name
                    )
                    
                    # Store assembled results
                    self.execution_memory[assembly_name] = assembled_data
                    results[assembly_name] = assembled_data
                    
                    print(f"   🔧 Assembled: {list(assembled_data.keys())}")
                else:
                    available_sources = list(self.execution_memory.keys())
                    raise ValueError(f"Assembly step {i+1} missing valid source step: {source_step}. Available sources: {available_sources}")
            
            else:
                step_keys = list(step.keys())
                raise ValueError(f"Step {i+1} must contain either 'node' or 'assembly' field. Found keys: {step_keys}")
        
        print(f"\n🎉 Workflow completed successfully! Executed {len(workflow['steps'])} steps.")
        return {
            "status": "success",
            "results": results,
            "execution_memory": self.execution_memory
        }
    
    def process_assembly_step_with_retry(self, assembly_config: Dict[str, Any], 
                                       source_data: Dict[str, Any], assembly_name: str) -> Dict[str, Any]:
        """Process assembly step with intelligent retry for failed selections"""
        retry_key = f"{assembly_name}_{hash(str(assembly_config))}"
        attempt = self.retry_attempts.get(retry_key, 0)
        
        while attempt < self.max_retries:
            try:
                # Process assembly with current configuration
                result = self.process_assembly_step(assembly_config, source_data)
                
                # Validate assembly result
                if self._validate_assembly_output(result, assembly_config):
                    return result
                else:
                    print(f"   ⚠️ Assembly {assembly_name} produced invalid result, retrying...")
                    attempt += 1
                    self.retry_attempts[retry_key] = attempt
                    
                    if attempt >= self.max_retries:
                        print(f"   ❌ Assembly {assembly_name} failed after {self.max_retries} attempts")
                        return result
                    
                    # Create retry strategy
                    assembly_config = self._create_intelligent_assembly_retry(
                        assembly_config, source_data, attempt
                    )
                    
            except Exception as e:
                attempt += 1
                self.retry_attempts[retry_key] = attempt
                
                if attempt >= self.max_retries:
                    raise e
                
                print(f"   ⚠️ Assembly {assembly_name} failed, retrying...")
        
        return self.process_assembly_step(assembly_config, source_data)
    
    def _validate_assembly_output(self, result: Dict[str, Any], assembly_config: Dict[str, Any]) -> bool:
        """Validate that assembly output is usable"""
        for output_key in assembly_config.keys():
            if output_key not in result or not result[output_key]:
                return False
            
            # Check for URL validity
            if "url" in output_key.lower():
                url = result[output_key]
                if not isinstance(url, str) or not url.startswith(('http://', 'https://')):
                    return False
        
        return True
    
    def list_available_nodes(self) -> List[Dict[str, Any]]:
        """List all available nodes with their configurations"""
        nodes = []
        
        if not self.nodes_dir.exists():
            return nodes
        
        for node_dir in self.nodes_dir.iterdir():
            if node_dir.is_dir():
                try:
                    config = self.load_node_config(node_dir.name)
                    config["node_name"] = node_dir.name
                    nodes.append(config)
                except Exception as e:
                    # Add basic info even if config is missing
                    nodes.append({
                        "node_name": node_dir.name,
                        "name": node_dir.name.replace("-", " ").title(),
                        "description": f"Node configuration error: {str(e)}",
                        "status": "error"
                    })
        
        return nodes

def main():
    """CLI interface for the glue runner"""
    if len(sys.argv) != 2:
        print("Usage: python glue_runner.py <workflow.json>")
        sys.exit(1)
    
    workflow_file = sys.argv[1]
    
    try:
        with open(workflow_file, 'r') as f:
            workflow = json.load(f)
        
        runner = OrchestraGlueRunner()
        result = runner.run_workflow(workflow)
        
        print("\n" + "="*60)
        print("🎯 FINAL RESULTS")
        print("="*60)
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"❌ Workflow execution failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()