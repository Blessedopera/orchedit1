#!/usr/bin/env python3
"""
Orchestra Agent Dashboard - Enhanced Streamlit GUI with LangChain AI agents
"""
import streamlit as st
import json
import sys
import os
import time
from pathlib import Path
import traceback
from typing import Dict, Any, List

# Add the backend and agents directories to Python path
current_dir = Path(__file__).parent
backend_dir = current_dir.parent / "backend"
agents_dir = current_dir.parent / "agents"
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(agents_dir))

from glue_runner import OrchestraGlueRunner
from orchestra.agents.workflow_composer import WorkflowComposerAgent
from workflow_memory import WorkflowMemory
from workflow_templates import WorkflowTemplates

def initialize_session_state():
    """Initialize Streamlit session state"""
    if 'agent' not in st.session_state:
        st.session_state.agent = None
    if 'workflow_memory' not in st.session_state:
        st.session_state.workflow_memory = WorkflowMemory()
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'show_json_editor' not in st.session_state:
        st.session_state.show_json_editor = False

def setup_agent(api_key: str):
    """Setup the LangChain agent"""
    try:
        if api_key:
            st.session_state.agent = WorkflowComposerAgent(api_key)
            return True
        return False
    except Exception as e:
        st.error(f"Failed to initialize agent: {str(e)}")
        return False

def main():
    st.set_page_config(
        page_title="Orchestra v2 - AI Agent Dashboard",
        page_icon="🎼",
        layout="wide"
    )
    
    # Initialize session state
    initialize_session_state()
    
    st.title("🎼 Orchestra v2 - AI Agent Dashboard")
    st.markdown("**Intelligent Workflow Automation** - Powered by LangChain & Qwen3 Coder")
    
    # Sidebar for API key and navigation
    with st.sidebar:
        st.header("🔑 Configuration")
        
        # API Key input
        api_key = st.text_input(
            "OpenRouter API Key",
            type="password",
            help="Enter your OpenRouter API key to enable AI agent features"
        )
        
        if api_key and not st.session_state.agent:
            if setup_agent(api_key):
                st.success("✅ AI Agent initialized!")
            else:
                st.error("❌ Failed to initialize agent")
        
        st.divider()
        
        # Navigation
        st.header("📋 Navigation")
        page = st.selectbox(
            "Choose a page:",
            [
                "🏠 Overview", 
                "🤖 AI Workflow Creator", 
                "📦 Node Explorer", 
                "🔧 Manual Node Test", 
                "🚀 Execute Workflows",
                "🧠 Workflow Memory",
                "📊 Analytics"
            ]
        )
    
    # Main content based on selected page
    if page == "🏠 Overview":
        show_overview_page()
    elif page == "🤖 AI Workflow Creator":
        show_ai_workflow_creator()
    elif page == "📦 Node Explorer":
        show_node_explorer()
    elif page == "🔧 Manual Node Test":
        show_manual_node_test()
    elif page == "🚀 Execute Workflows":
        show_workflow_execution()
    elif page == "🧠 Workflow Memory":
        show_workflow_memory()
    elif page == "📊 Analytics":
        show_analytics()

def show_overview_page():
    """Show system overview"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("🎯 Orchestra v2 Features")
        
        st.info("""
        **New in v2:**
        - 🤖 **AI Workflow Creation** - Describe what you want, get a working workflow
        - 🧠 **Intelligent Assembly** - AI decides how to connect node outputs to inputs
        - 💾 **Workflow Memory** - System remembers successful workflows
        - 🔄 **Iterative Improvement** - Refine workflows based on feedback
        - 📊 **Analytics** - Track workflow performance and success rates
        """)
        
        # System status
        runner = OrchestraGlueRunner()
        nodes = runner.list_available_nodes()
        
        st.metric("Available Nodes", len(nodes))
        
        if st.session_state.agent:
            st.metric("AI Agent Status", "🟢 Active")
        else:
            st.metric("AI Agent Status", "🔴 Inactive")
        
        # Workflow memory stats
        if st.session_state.workflow_memory:
            stats = st.session_state.workflow_memory.get_workflow_stats()
            st.metric("Stored Workflows", stats["total_workflows"])
            st.metric("Success Rate", f"{stats['success_rate']:.1%}")
    
    with col2:
        st.header("🏗️ Architecture v2")
        
        st.code("""
orchestra/
├── agents/                 # 🆕 AI Agents
│   ├── workflow_composer.py
│   ├── workflow_memory.py
│   └── workflow_templates.py
├── backend/
│   └── glue_runner.py     # Enhanced with agent integration
├── nodes/                 # Unchanged - pure & reusable
│   ├── google-news-scraper/
│   ├── article-page-scraper/
│   └── article-processor/
├── workflows/             # AI-generated workflows
├── dashboard/             # Enhanced with AI features
└── data/                  # 🆕 Workflow memory database
        """, language="text")
        
        st.header("🚀 How It Works")
        st.markdown("""
        1. **Describe** your automation need in natural language
        2. **AI Agent** analyzes available nodes and creates workflow
        3. **Intelligent Assembly** connects node outputs to inputs
        4. **Execute** the workflow with real-time monitoring
        5. **Learn** from results to improve future workflows
        """)

def show_ai_workflow_creator():
    """Show AI-powered workflow creation interface"""
    st.header("🤖 AI Workflow Creator")
    
    if not st.session_state.agent:
        st.warning("⚠️ Please enter your OpenRouter API key in the sidebar to enable AI features.")
        return
    
    # Workflow creation interface
    st.subheader("Describe Your Automation Need")
    
    # Example requests
    with st.expander("💡 Example Requests", expanded=False):
        st.markdown("""
        **Content Creation:**
        - "Monitor AI news and create weekly summaries"
        - "Find articles about machine learning and summarize the key points"
        
        **Data Processing:**
        - "Scrape product reviews and analyze sentiment"
        - "Collect social media mentions and generate reports"
        
        **Research Automation:**
        - "Track competitor news and highlight important developments"
        - "Monitor industry trends and create briefing documents"
        """)
    
    # User input
    user_request = st.text_area(
        "What automation workflow do you need?",
        height=100,
        placeholder="Example: I want to monitor AI startup news, pick the most relevant articles about healthcare, and create summaries for my newsletter..."
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 Create Workflow", type="primary", disabled=not user_request):
            create_workflow_with_agent(user_request)
    
    with col2:
        if st.button("🔍 Find Similar Workflows"):
            find_similar_workflows(user_request)
    
    with col3:
        if st.button("📋 Use Template"):
            show_workflow_templates()
    
    # Show conversation history
    if st.session_state.conversation_history:
        st.subheader("💬 Conversation History")
        for i, entry in enumerate(st.session_state.conversation_history):
            with st.expander(f"Request {i+1}: {entry['request'][:50]}...", expanded=i == len(st.session_state.conversation_history)-1):
                st.write("**Request:**", entry['request'])
                st.write("**Response:**", entry['response'])
                if 'workflow_json' in entry:
                    st.json(entry['workflow_json'])

def create_workflow_with_agent(user_request: str):
    """Create workflow using AI agent"""
    with st.spinner("🤖 AI Agent is creating your workflow..."):
        try:
            result = st.session_state.agent.create_workflow(user_request)
            
            if result["success"]:
                st.success("✅ Workflow created successfully!")
                
                # Display agent response
                st.subheader("🤖 Agent Response")
                st.write(result["response"])
                
                # Check if workflow was generated
                if "workflow_json" in result and result["workflow_json"]:
                    workflow_json = result["workflow_json"]
                    
                    st.subheader("📋 Generated Workflow JSON")
                    
                    # Create properly formatted JSON string
                    formatted_json = json.dumps(workflow_json, indent=2)
                    
                    # Display in copyable text area
                    st.text_area(
                        "Copy this JSON (Click in box, Ctrl+A, Ctrl+C):",
                        value=formatted_json,
                        height=400,
                        key=f"workflow_json_{len(st.session_state.conversation_history)}"
                    )
                    
                    # Also show as expandable JSON for reference
                    with st.expander("📋 View Formatted JSON", expanded=False):
                        st.json(workflow_json)
                    
                    # Save workflow option
                    col1, col2 = st.columns(2)
                    with col1:
                        default_filename = f"{workflow_json.get('name', 'workflow').lower().replace(' ', '_')}.json"
                        filename = st.text_input("Filename:", default_filename, key=f"filename_{len(st.session_state.conversation_history)}")
                    with col2:
                        if st.button("💾 Save Workflow"):
                            try:
                                # Get absolute path to workflows directory
                                import os
                                current_file_dir = os.path.dirname(os.path.abspath(__file__))
                                orchestra_root = os.path.dirname(current_file_dir)
                                workflows_dir = os.path.join(orchestra_root, "workflows")
                                
                                # Create directory if it doesn't exist
                                os.makedirs(workflows_dir, exist_ok=True)
                                
                                # Save workflow
                                workflow_path = os.path.join(workflows_dir, filename)
                                with open(workflow_path, 'w') as f:
                                    json.dump(workflow_json, f, indent=2)
                                
                                st.success(f"✅ Workflow saved to: {workflow_path}")
                                st.info("💡 **Next Steps:**\n1. Go to '🚀 Execute Workflows' tab\n2. Click 'Refresh Workflow List'\n3. Find your saved workflow\n4. Add API keys if needed\n5. Execute the workflow")
                                
                                # Clear all caches to force refresh
                                cache_keys = ['workflow_files_cache', 'workflows_dir_cache']
                                for key in cache_keys:
                                    if key in st.session_state:
                                        del st.session_state[key]
                                
                                # Force immediate refresh
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"❌ Save failed: {str(e)}")
                                st.code(f"Error details: {traceback.format_exc()}")
                            
                            # Store in memory
                            st.session_state.workflow_memory.store_workflow(
                                workflow_json.get('name', 'Unnamed Workflow'),
                                workflow_json.get('description', ''),
                                user_request,
                                json.dumps(workflow_json)
                            )
                    
                    # Store in conversation history
                    st.session_state.conversation_history.append({
                        'request': user_request,
                        'response': result["response"],
                        'workflow_json': workflow_json
                    })
                else:
                    st.warning("⚠️ No workflow JSON was generated. Please try rephrasing your request.")
                
            else:
                st.error(f"❌ Failed to create workflow: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.code(traceback.format_exc())

def find_similar_workflows(user_request: str):
    """Find and display similar workflows"""
    if not user_request:
        st.warning("Please enter a request to find similar workflows")
        return
    
    similar_workflows = st.session_state.workflow_memory.find_similar_workflows(user_request)
    
    if similar_workflows:
        st.subheader("🔍 Similar Workflows Found")
        for workflow in similar_workflows:
            with st.expander(f"📋 {workflow['name']} (Success: {workflow['success_count']})", expanded=False):
                st.write("**Description:**", workflow['description'])
                st.write("**Original Request:**", workflow['user_request'])
                st.write("**Success Rate:**", f"{workflow['success_count']} successes, {workflow['failure_count']} failures")
                
                if st.button(f"Use This Workflow", key=f"use_{workflow['id']}"):
                    st.json(json.loads(workflow['workflow_json']))
    else:
        st.info("No similar workflows found. This will be a new workflow!")

def show_workflow_templates():
    """Show available workflow templates"""
    st.subheader("📋 Workflow Templates")
    
    templates = WorkflowTemplates.get_all_templates()
    
    for template in templates:
        with st.expander(f"📋 {template['name']}", expanded=False):
            st.write("**Description:**", template['description'])
            st.write("**Category:**", template.get('category', 'general'))
            st.json(template)
            
            if st.button(f"Use Template: {template['name']}", key=f"template_{template['name']}"):
                st.session_state.selected_template = template
                st.rerun()

def show_node_explorer():
    """Show available nodes (unchanged from v1)"""
    st.header("📦 Available Nodes")
    
    runner = OrchestraGlueRunner()
    nodes = runner.list_available_nodes()
    
    if not nodes:
        st.warning("No nodes found. Make sure nodes are properly configured.")
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

def show_manual_node_test():
    """Show manual node testing (unchanged from v1)"""
    st.header("🔧 Manual Node Testing")
    
    runner = OrchestraGlueRunner()
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
        try:
            example_path = current_dir.parent / "nodes" / selected_node / "example_input.json"
            with open(example_path, 'r') as f:
                example_input = json.load(f)
        except Exception:
            example_input = {"error": "Could not load example input"}
        
        # Input editor
        input_json = st.text_area(
            "Input JSON",
            value=json.dumps(example_input, indent=2),
            height=200
        )
        
        if st.button("🚀 Run Node", type="primary"):
            try:
                parsed_input = json.loads(input_json)
                
                with st.spinner(f"Executing {selected_node}..."):
                    result = runner.execute_node(selected_node, parsed_input)
                
                st.success("✅ Node executed successfully!")
                st.json(result)
                
            except json.JSONDecodeError:
                st.error("❌ Invalid JSON input")
            except Exception as e:
                st.error(f"❌ Execution failed: {str(e)}")

def show_workflow_execution():
    """Show workflow execution interface"""
    st.header("🚀 Workflow Execution")
    
    # List available workflows with absolute path
    import os
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    orchestra_root = os.path.dirname(current_file_dir)
    workflows_dir = os.path.join(orchestra_root, "workflows")
    
    if not os.path.exists(workflows_dir):
        st.warning("No workflows directory found.")
        st.info(f"Expected directory: {workflows_dir}")
        return
    
    # Cache workflow files to avoid constant file system checks
    if 'workflow_files_cache' not in st.session_state or st.button("🔄 Refresh Workflow List"):
        import glob
        workflow_pattern = os.path.join(workflows_dir, "*.json")
        workflow_files = glob.glob(workflow_pattern)
        st.session_state.workflow_files_cache = workflow_files
        st.session_state.workflows_dir_cache = workflows_dir
    else:
        workflow_files = st.session_state.workflow_files_cache
        workflows_dir = st.session_state.workflows_dir_cache
    
    if not workflow_files:
        st.warning("No workflow files found. Create one using the AI Workflow Creator first.")
        if st.button("🔄 Refresh List"):
            if 'workflow_files_cache' in st.session_state:
                del st.session_state['workflow_files_cache']
            st.rerun()
        return
    
    # Workflow selection
    workflow_names = [os.path.basename(f) for f in workflow_files]
    if not workflow_names:
        st.warning("No workflow files found. Create one using the AI Workflow Creator first.")
        if st.button("🔄 Refresh List"):
            if 'workflow_files_cache' in st.session_state:
                del st.session_state['workflow_files_cache']
            st.rerun()
        return
    
    selected_workflow = st.selectbox("Select workflow to execute:", workflow_names)
    
    if selected_workflow:
        try:
            workflow_path = os.path.join(workflows_dir, selected_workflow)
            with open(workflow_path, 'r') as f:
                workflow_data = json.load(f)
            
            st.subheader(f"Workflow: {workflow_data.get('name', selected_workflow)}")
            st.write("**Description:**", workflow_data.get('description', 'No description'))
            
            # Show workflow steps
            with st.expander("📋 Workflow Steps", expanded=True):
                for i, step in enumerate(workflow_data.get('steps', [])):
                    if 'node' in step:
                        st.write(f"**Step {i+1}: NODE** - {step['node']}")
                        
                        # Show inputs with API key highlighting
                        inputs = step.get('inputs', {})
                        for key, value in inputs.items():
                            if 'api' in key.lower() or 'key' in key.lower() or 'token' in key.lower():
                                if isinstance(value, str) and ('your-' in value or 'api-key' in value or 'token-here' in value):
                                    st.warning(f"🔑 **{key}**: {value} ← **NEEDS YOUR API KEY**")
                                else:
                                    st.write(f"• **{key}**: {value}")
                            else:
                                st.write(f"• **{key}**: {value}")
                    elif 'assembly' in step:
                        step_name = step.get('name', f'assembly_{i+1}')
                        st.write(f"**Step {i+1}: ASSEMBLY** - {step_name}")
                        st.write(f"*{step.get('description', 'No description')}*")
                        assembly_config = step.get('assembly', {})
                        for key, config in assembly_config.items():
                            st.write(f"• **{key}**: {config}")
            
            # API Key Management Section
            api_keys_needed = []
            for step in workflow_data.get('steps', []):
                if 'node' in step:
                    inputs = step.get('inputs', {})
                    for key, value in inputs.items():
                        if 'api' in key.lower() or 'key' in key.lower() or 'token' in key.lower():
                            if isinstance(value, str) and ('your-' in value or 'api-key' in value or 'token-here' in value):
                                api_keys_needed.append({
                                    'step': step['node'],
                                    'field': key,
                                    'placeholder': value
                                })
            
            if api_keys_needed:
                st.subheader("🔑 API Keys Required")
                st.warning("This workflow requires API keys. You can either:")
                st.write("**Option 1:** Edit the JSON file directly after saving")
                st.write("**Option 2:** Update keys here before execution")
                
                # Create form for API key input
                with st.form("api_keys_form"):
                    updated_keys = {}
                    for api_key in api_keys_needed:
                        key_input = st.text_input(
                            f"{api_key['step']} - {api_key['field']}:",
                            placeholder=api_key['placeholder'],
                            type="password",
                            key=f"api_{api_key['step']}_{api_key['field']}"
                        )
                        if key_input:
                            updated_keys[f"{api_key['step']}.{api_key['field']}"] = key_input
                    
                    if st.form_submit_button("🔄 Update API Keys"):
                        if updated_keys:
                            # Update workflow with API keys
                            for step in workflow_data['steps']:
                                if 'node' in step:
                                    for key, value in step.get('inputs', {}).items():
                                        lookup_key = f"{step['node']}.{key}"
                                        if lookup_key in updated_keys:
                                            step['inputs'][key] = updated_keys[lookup_key]
                            
                            st.success("✅ API keys updated in workflow!")
                            st.rerun()
            
            # Execution
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🚀 Execute Workflow", type="primary"):
                    execute_workflow(workflow_data, selected_workflow)
            
            with col2:
                if st.button("📝 Edit Workflow JSON"):
                    st.session_state.show_json_editor = True
                    st.rerun()
            
            # JSON Editor
            if st.session_state.get('show_json_editor', False):
                st.subheader("📝 Edit Workflow JSON")
                st.info("💡 **Tip**: You can manually add your API keys here by replacing placeholder values")
                
                edited_json = st.text_area(
                    "Workflow JSON:",
                    value=json.dumps(workflow_data, indent=2),
                    height=400,
                    key="json_editor"
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 Save Changes"):
                        try:
                            updated_workflow = json.loads(edited_json)
                            workflow_path = workflows_dir / selected_workflow
                            with open(workflow_path, 'w') as f:
                                json.dump(updated_workflow, f, indent=2)
                            st.success("✅ Workflow updated!")
                            st.session_state.show_json_editor = False
                            st.rerun()
                        except json.JSONDecodeError:
                            st.error("❌ Invalid JSON")
                        except Exception as e:
                            st.error(f"❌ Save failed: {str(e)}")
                
                with col2:
                    if st.button("❌ Cancel"):
                        st.session_state.show_json_editor = False
                        st.rerun()
                    
        except Exception as e:
            st.error(f"❌ Could not load workflow: {str(e)}")

def execute_workflow(workflow_data: Dict[str, Any], workflow_name: str):
    """Execute a workflow and record results with detailed error handling"""
    try:
        st.info("🔍 **Pre-execution checks...**")
        
        # Check for missing API keys before execution
        missing_keys = []
        for step in workflow_data.get('steps', []):
            if 'node' in step:
                inputs = step.get('inputs', {})
                for key, value in inputs.items():
                    if 'api' in key.lower() or 'key' in key.lower() or 'token' in key.lower():
                        if isinstance(value, str) and ('your-' in value or 'api-key' in value or 'token-here' in value):
                            missing_keys.append(f"{step['node']}.{key}")
        
        if missing_keys:
            st.error("❌ **Cannot execute workflow - API keys missing:**")
            for key in missing_keys:
                st.write(f"• {key}")
            st.info("💡 **To fix**: Use the '📝 Edit Workflow JSON' button above to add your API keys")
            return
        
        st.success("✅ Pre-execution checks passed!")
        
        # Initialize runner
        runner = OrchestraGlueRunner()
        
        # Validate workflow structure
        st.info("🔍 **Validating workflow structure...**")
        
        # Check if all nodes exist
        for step in workflow_data.get('steps', []):
            if 'node' in step:
                node_name = step['node']
                available_nodes = runner.list_available_nodes()
                node_exists = any(n['node_name'] == node_name for n in available_nodes)
                if not node_exists:
                    st.error(f"❌ Node '{node_name}' not found!")
                    st.write("Available nodes:", [n['node_name'] for n in available_nodes])
                    return
        
        st.success("✅ All nodes validated!")
        
        start_time = time.time()
        
        with st.spinner("Executing workflow..."):
            # Show step-by-step execution
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            total_steps = len(workflow_data.get('steps', []))
            
            for i, step in enumerate(workflow_data.get('steps', [])):
                progress = (i + 1) / total_steps
                progress_bar.progress(progress)
                
                if 'node' in step:
                    status_text.text(f"Executing step {i+1}/{total_steps}: {step['node']}")
                else:
                    status_text.text(f"Processing step {i+1}/{total_steps}: Assembly")
                
                time.sleep(0.5)  # Visual feedback
            
            # Execute the workflow
            result = runner.run_workflow(workflow_data)
            
            progress_bar.progress(1.0)
            status_text.text("✅ Workflow completed!")
        
        execution_time = time.time() - start_time
        
        st.success(f"✅ Workflow completed successfully in {execution_time:.2f} seconds!")
        
        # Show results
        st.subheader("📊 Execution Results")
        
        if isinstance(result, dict):
            # Show step-by-step results
            for step_name, step_result in result.items():
                with st.expander(f"📋 Step: {step_name}", expanded=False):
                    st.json(step_result)
        else:
            st.json(result)
        
        # Record execution in memory
        try:
            st.session_state.workflow_memory.record_execution(
                workflow_id=hash(workflow_name),  # Simple hash for demo
                success=True,
                execution_time=execution_time
            )
        except Exception as memory_error:
            st.warning(f"Could not record execution in memory: {memory_error}")
        
    except Exception as e:
        st.error(f"❌ Workflow execution failed: {str(e)}")
        
        # Detailed error information
        with st.expander("🔧 Error Details", expanded=True):
            st.code(traceback.format_exc())
            
            # Suggest fixes
            error_str = str(e).lower()
            if "connection" in error_str or "api" in error_str:
                st.info("💡 **Possible fixes:**\n- Check your API keys\n- Verify internet connection\n- Check API service status")
            elif "file" in error_str or "path" in error_str:
                st.info("💡 **Possible fixes:**\n- Check file paths in workflow\n- Verify node directories exist\n- Check permissions")
            elif "json" in error_str:
                st.info("💡 **Possible fixes:**\n- Validate workflow JSON format\n- Check for syntax errors\n- Verify assembly step configuration")
        
        # Record failed execution
        try:
            st.session_state.workflow_memory.record_execution(
                workflow_id=hash(workflow_name),
                success=False,
                error_message=str(e)
            )
        except Exception as memory_error:
            st.warning(f"Could not record failed execution: {memory_error}")

def show_workflow_memory():
    """Show workflow memory and learning capabilities"""
    st.header("🧠 Workflow Memory")
    
    # Memory statistics
    stats = st.session_state.workflow_memory.get_workflow_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Workflows", stats["total_workflows"])
    with col2:
        st.metric("Successful Executions", stats["successful_executions"])
    with col3:
        st.metric("Failed Executions", stats["failed_executions"])
    with col4:
        st.metric("Success Rate", f"{stats['success_rate']:.1%}")
    
    # Top performing workflows
    if stats["top_workflows"]:
        st.subheader("🏆 Top Performing Workflows")
        for workflow in stats["top_workflows"]:
            st.write(f"**{workflow['name']}** - {workflow['success_count']} successes")
    
    # Search workflows
    st.subheader("🔍 Search Workflow Memory")
    search_query = st.text_input("Search for workflows:")
    
    if search_query:
        similar_workflows = st.session_state.workflow_memory.find_similar_workflows(search_query, limit=10)
        
        for workflow in similar_workflows:
            with st.expander(f"📋 {workflow['name']}", expanded=False):
                st.write("**Description:**", workflow['description'])
                st.write("**Original Request:**", workflow['user_request'])
                st.write("**Performance:**", f"{workflow['success_count']} successes, {workflow['failure_count']} failures")
                st.write("**Created:**", workflow['created_at'])
                st.write("**Last Used:**", workflow['last_used'])
                
                if st.button(f"View Workflow JSON", key=f"view_{workflow['id']}"):
                    st.json(json.loads(workflow['workflow_json']))

def show_analytics():
    """Show workflow analytics and performance metrics"""
    st.header("📊 Workflow Analytics")
    
    stats = st.session_state.workflow_memory.get_workflow_stats()
    
    # Performance overview
    st.subheader("📈 Performance Overview")
    
    if stats["total_workflows"] > 0:
        # Success rate chart
        success_data = {
            "Successful": stats["successful_executions"],
            "Failed": stats["failed_executions"]
        }
        
        st.bar_chart(success_data)
        
        # Top workflows
        st.subheader("🏆 Most Successful Workflows")
        if stats["top_workflows"]:
            for i, workflow in enumerate(stats["top_workflows"], 1):
                st.write(f"{i}. **{workflow['name']}** - {workflow['success_count']} successes")
        
    else:
        st.info("No workflow data available yet. Create and execute some workflows to see analytics!")
    
    # System health
    st.subheader("🔧 System Health")
    
    runner = OrchestraGlueRunner()
    nodes = runner.list_available_nodes()
    
    healthy_nodes = len([n for n in nodes if 'error' not in n.get('description', '')])
    total_nodes = len(nodes)
    
    st.metric("Healthy Nodes", f"{healthy_nodes}/{total_nodes}")
    
    if st.session_state.agent:
        st.metric("AI Agent", "🟢 Active")
    else:
        st.metric("AI Agent", "🔴 Inactive")

if __name__ == "__main__":
    main()