#!/usr/bin/env python3
"""
Orchestra Central Dashboard - Simple Streamlit GUI for testing nodes and workflows
"""
import streamlit as st
import json
import sys
import os
from pathlib import Path
import subprocess

# Add the backend directory to Python path
current_dir = Path(__file__).parent
backend_dir = current_dir.parent / "backend"
sys.path.insert(0, str(backend_dir))

from glue_runner import OrchestraGlueRunner

def load_example_input(node_name: str):
    """Load example input for a node"""
    try:
        example_path = current_dir.parent / "nodes" / node_name / "example_input.json"
        with open(example_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        return {"error": f"Could not load example: {str(e)}"}

def save_workflow(workflow_data: dict, filename: str):
    """Save workflow to file"""
    workflows_dir = current_dir.parent / "workflows"
    workflows_dir.mkdir(exist_ok=True)
    
    workflow_path = workflows_dir / filename
    with open(workflow_path, 'w') as f:
        json.dump(workflow_data, f, indent=2)
    
    return workflow_path

def load_workflow(filename: str):
    """Load workflow from file"""
    workflow_path = current_dir.parent / "workflows" / filename
    try:
        with open(workflow_path, 'r') as f:
            workflow_data = json.load(f)
        return workflow_data
    except Exception as e:
        st.error(f"Error loading workflow: {str(e)}")
        return None

def main():
    st.set_page_config(
        page_title="Orchestra Central Dashboard",
        page_icon="🎼",
        layout="wide"
    )
    
    st.title("🎼 Orchestra Central Dashboard")
    st.markdown("**Prototype System** - Testing Node Architecture & Glue Runner")
    
    # Initialize the glue runner
    runner = OrchestraGlueRunner()
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["🏠 Overview", "📦 Node Explorer", "🔧 Single Node Test", "🔗 Workflow Builder", "🚀 Run Workflow"]
    )
    
    if page == "🏠 Overview":
        st.header("System Overview")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 System Status")
            
            # Get available nodes
            nodes = runner.list_available_nodes()
            st.metric("Available Nodes", len(nodes))
            
            # Check workflows
            workflows_dir = current_dir.parent / "workflows"
            workflow_files = list(workflows_dir.glob("*.json")) if workflows_dir.exists() else []
            st.metric("Available Workflows", len(workflow_files))
            
            st.subheader("🎯 Current Test Nodes")
            st.info("""
            This prototype includes 3 example nodes to test the architecture:
            
            1. **Google News Scraper** - Fetches news articles via Apify API
            2. **Article Page Scraper** - Scrapes full content using Playwright  
            3. **Article Processor** - Summarizes content via OpenRouter API
            
            These demonstrate the plug-and-play node system that will support many more nodes in the future.
            """)
        
        with col2:
            st.subheader("🏗️ Architecture")
            st.code("""
orchestra/
├── backend/
│   └── glue_runner.py      # Core execution engine
├── nodes/                  # Plug-and-play nodes
│   ├── google-news-scraper/
│   ├── article-page-scraper/
│   └── article-processor/
├── workflows/              # JSON workflow definitions
├── dashboard/              # This GUI
└── utils/                  # Shared utilities
            """, language="text")
            
            st.subheader("🔄 How It Works")
            st.markdown("""
            1. **Nodes** are self-contained with config.json + run.py
            2. **Glue Runner** chains nodes using JSON workflows
            3. **Variable substitution** like `{{node.field}}` connects outputs to inputs
            4. **Dashboard** provides manual testing and workflow building
            """)
    
    elif page == "📦 Node Explorer":
        st.header("Available Nodes")
        
        nodes = runner.list_available_nodes()
        
        if not nodes:
            st.warning("No nodes found. Make sure nodes are properly configured in the orchestra/nodes/ directory.")
            return
        
        for node in nodes:
            with st.expander(f"📦 {node.get('name', node['node_name'])}", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Description:**", node.get('description', 'No description'))
                    st.write("**Type:**", node.get('type', 'Unknown'))
                    st.write("**Language:**", node.get('language', 'Unknown'))
                    
                    if 'dependencies' in node:
                        st.write("**Dependencies:**", ", ".join(node['dependencies']))
                
                with col2:
                    st.write("**Input Schema:**")
                    if 'input_schema' in node:
                        st.json(node['input_schema'])
                    
                    st.write("**Output Schema:**")
                    if 'output_schema' in node:
                        st.write(", ".join(node['output_schema']))
    
    elif page == "🔧 Single Node Test":
        st.header("Single Node Testing")
        
        nodes = runner.list_available_nodes()
        if not nodes:
            st.warning("No nodes available for testing.")
            return
        
        # Node selection
        node_names = [node['node_name'] for node in nodes]
        selected_node = st.selectbox("Select a node to test:", node_names)
        
        if selected_node:
            st.subheader(f"Testing: {selected_node}")
            
            # Load example input
            example_input = load_example_input(selected_node)
            
            # Input editor
            st.write("**Edit Input JSON:**")
            input_json = st.text_area(
                "Input JSON",
                value=json.dumps(example_input, indent=2),
                height=200,
                help="Modify the JSON input for testing"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🚀 Run Node", type="primary"):
                    try:
                        # Parse input
                        parsed_input = json.loads(input_json)
                        
                        # Execute node
                        with st.spinner(f"Executing {selected_node}..."):
                            result = runner.execute_node(selected_node, parsed_input)
                        
                        st.success("✅ Node executed successfully!")
                        st.subheader("Output:")
                        st.json(result)
                        
                    except json.JSONDecodeError:
                        st.error("❌ Invalid JSON input")
                    except Exception as e:
                        st.error(f"❌ Execution failed: {str(e)}")
            
            with col2:
                if st.button("📋 Reset to Example"):
                    st.rerun()
    
    elif page == "🔗 Workflow Builder":
        st.header("Workflow Builder")
        
        st.info("Build and save custom workflows by chaining nodes together.")
        
        # Workflow metadata
        col1, col2 = st.columns(2)
        with col1:
            workflow_name = st.text_input("Workflow Name", "My Custom Workflow")
        with col2:
            workflow_desc = st.text_input("Description", "Custom workflow description")
        
        # Available nodes
        nodes = runner.list_available_nodes()
        node_names = [node['node_name'] for node in nodes]
        
        # Workflow steps
        st.subheader("Workflow Steps")
        
        if 'workflow_steps' not in st.session_state:
            st.session_state.workflow_steps = []
        
        # Add step
        with st.expander("➕ Add New Step", expanded=len(st.session_state.workflow_steps) == 0):
            step_node = st.selectbox("Select Node:", node_names, key="new_step_node")
            step_inputs = st.text_area(
                "Step Inputs (JSON):",
                value='{\n  "example_key": "example_value"\n}',
                height=100,
                key="new_step_inputs"
            )
            
            if st.button("Add Step"):
                try:
                    parsed_inputs = json.loads(step_inputs)
                    st.session_state.workflow_steps.append({
                        "node": step_node,
                        "inputs": parsed_inputs
                    })
                    st.success(f"Added step: {step_node}")
                    st.rerun()
                except json.JSONDecodeError:
                    st.error("Invalid JSON in step inputs")
        
        # Display current steps
        if st.session_state.workflow_steps:
            st.subheader("Current Workflow Steps")
            
            for i, step in enumerate(st.session_state.workflow_steps):
                with st.expander(f"Step {i+1}: {step['node']}", expanded=False):
                    st.json(step)
                    if st.button(f"Remove Step {i+1}", key=f"remove_{i}"):
                        st.session_state.workflow_steps.pop(i)
                        st.rerun()
            
            # Save workflow
            col1, col2, col3 = st.columns(3)
            
            with col1:
                filename = st.text_input("Filename:", f"{workflow_name.lower().replace(' ', '_')}.json")
            
            with col2:
                if st.button("💾 Save Workflow"):
                    workflow_data = {
                        "name": workflow_name,
                        "description": workflow_desc,
                        "version": "1.0.0",
                        "steps": st.session_state.workflow_steps
                    }
                    
                    try:
                        saved_path = save_workflow(workflow_data, filename)
                        st.success(f"✅ Workflow saved to: {saved_path}")
                    except Exception as e:
                        st.error(f"❌ Save failed: {str(e)}")
            
            with col3:
                if st.button("🗑️ Clear All Steps"):
                    st.session_state.workflow_steps = []
                    st.rerun()
    
    elif page == "🚀 Run Workflow":
        st.header("Workflow Execution")
        
        # List available workflows
        workflows_dir = current_dir.parent / "workflows"
        if not workflows_dir.exists():
            st.warning("No workflows directory found.")
            return
        
        workflow_files = list(workflows_dir.glob("*.json"))
        
        if not workflow_files:
            st.warning("No workflow files found. Create one in the Workflow Builder first.")
            return
        
        # Workflow selection
        workflow_names = [f.name for f in workflow_files]
        selected_workflow = st.selectbox("Select workflow to run:", workflow_names)
        
        if selected_workflow:
            try:
                workflow_data = load_workflow(selected_workflow)
                
                if workflow_data is None:
                    st.error("Failed to load workflow data")
                    return
                
                st.subheader(f"Workflow: {workflow_data.get('name', selected_workflow)}")
                st.write("**Description:**", workflow_data.get('description', 'No description'))
                
                # Show workflow steps
                with st.expander("📋 Workflow Steps", expanded=True):
                    for i, step in enumerate(workflow_data.get('steps', [])):
                        if 'node' in step:
                            st.write(f"**Step {i+1}:** NODE - {step['node']}")
                            st.json(step.get('inputs', {}))
                        elif 'assembly' in step:
                            step_name = step.get('name', f'assembly_{i+1}')
                            st.write(f"**Step {i+1}:** ASSEMBLY - {step_name}")
                            st.write(f"*{step.get('description', 'No description')}*")
                            st.json(step.get('assembly', {}))
                        else:
                            st.write(f"**Step {i+1}:** UNKNOWN STEP TYPE")
                            st.json(step)
                
                # Execution
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🚀 Execute Workflow", type="primary"):
                        try:
                            # Validate workflow structure
                            if not workflow_data:
                                st.error("No workflow data loaded")
                                return
                            
                            if 'steps' not in workflow_data:
                                st.error("Workflow missing 'steps' field")
                                return
                            
                            if not isinstance(workflow_data['steps'], list):
                                st.error("Workflow 'steps' must be a list")
                                return
                                
                            with st.spinner("Executing workflow..."):
                                result = runner.run_workflow(workflow_data)
                            
                            st.success("✅ Workflow completed successfully!")
                            
                            # Show results
                            st.subheader("Execution Results")
                            st.json(result)
                            
                        except Exception as e:
                            st.error(f"❌ Workflow execution failed: {str(e)}")
                
                with col2:
                    # Edit workflow
                    if st.button("✏️ Edit Workflow JSON"):
                        st.subheader("Edit Workflow")
                        edited_json = st.text_area(
                            "Workflow JSON:",
                            value=json.dumps(workflow_data, indent=2),
                            height=400
                        )
                        
                        if st.button("💾 Save Changes"):
                            try:
                                updated_workflow = json.loads(edited_json)
                                save_workflow(updated_workflow, selected_workflow)
                                st.success("✅ Workflow updated!")
                                st.rerun()
                            except json.JSONDecodeError:
                                st.error("❌ Invalid JSON")
                            except Exception as e:
                                st.error(f"❌ Save failed: {str(e)}")
                
            except Exception as e:
                st.error(f"❌ Could not load workflow: {str(e)}")

if __name__ == "__main__":
    main()