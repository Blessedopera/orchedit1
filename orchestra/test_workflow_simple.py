#!/usr/bin/env python3
"""
Simple workflow test script to debug loading issues
"""
import json
import sys
from pathlib import Path

def test_workflow_loading():
    """Test loading the workflow file directly"""
    
    # Get the workflow file path
    current_dir = Path(__file__).parent
    workflow_path = current_dir / "workflows" / "test_workflow.json"
    
    print(f"Testing workflow file: {workflow_path}")
    print(f"File exists: {workflow_path.exists()}")
    
    if not workflow_path.exists():
        print("❌ Workflow file not found!")
        return False
    
    try:
        with open(workflow_path, 'r') as f:
            workflow_data = json.load(f)
        
        print("✅ JSON loaded successfully")
        print(f"Workflow keys: {list(workflow_data.keys())}")
        
        if 'steps' in workflow_data:
            print(f"Number of steps: {len(workflow_data['steps'])}")
            for i, step in enumerate(workflow_data['steps']):
                step_type = "NODE" if "node" in step else "ASSEMBLY" if "assembly" in step else "UNKNOWN"
                step_name = step.get("node", step.get("name", f"step_{i+1}"))
                print(f"  Step {i+1}: {step_type} - {step_name}")
        else:
            print("❌ No 'steps' key found in workflow")
            
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error loading workflow: {e}")
        return False

if __name__ == "__main__":
    test_workflow_loading()