#!/usr/bin/env python3
"""
Enhanced Orchestra Glue Runner with LangChain Agent Integration
"""
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Import the original glue runner
from glue_runner import OrchestraGlueRunner

class EnhancedOrchestraGlueRunner(OrchestraGlueRunner):
    """Enhanced glue runner with AI agent capabilities"""
    
    def __init__(self, nodes_dir: str = None, agent: Optional[Any] = None):
        """Initialize enhanced runner with optional AI agent"""
        super().__init__(nodes_dir)
        self.agent = agent
        self.execution_history = []
    
    def run_workflow_with_agent_assistance(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Run workflow with AI agent assistance for error handling and optimization"""
        try:
            # First, try normal execution
            result = self.run_workflow(workflow)
            
            # Record successful execution
            self.execution_history.append({
                "workflow": workflow,
                "result": result,
                "success": True,
                "timestamp": self._get_timestamp()
            })
            
            return result
            
        except Exception as e:
            # If execution fails and agent is available, try to get help
            if self.agent:
                return self._handle_execution_error_with_agent(workflow, str(e))
            else:
                # Fallback to original error handling
                raise e
    
    def _handle_execution_error_with_agent(self, workflow: Dict[str, Any], error_message: str) -> Dict[str, Any]:
        """Use AI agent to analyze and potentially fix workflow errors"""
        try:
            # Create a prompt for the agent to analyze the error
            error_analysis_prompt = f"""
            A workflow execution failed with this error:
            {error_message}
            
            Workflow that failed:
            {json.dumps(workflow, indent=2)}
            
            Please analyze the error and suggest fixes. Use your tools to:
            1. Check if all referenced nodes exist
            2. Validate the workflow structure
            3. Identify potential issues with variable substitution
            4. Suggest corrections
            
            Provide specific, actionable recommendations to fix this workflow.
            """
            
            agent_response = self.agent.run(error_analysis_prompt)
            
            # Record failed execution with agent analysis
            self.execution_history.append({
                "workflow": workflow,
                "error": error_message,
                "agent_analysis": agent_response,
                "success": False,
                "timestamp": self._get_timestamp()
            })
            
            return {
                "status": "failed_with_analysis",
                "error": error_message,
                "agent_analysis": agent_response,
                "suggestions": "Check the agent analysis for specific recommendations"
            }
            
        except Exception as agent_error:
            # If agent also fails, return original error
            return {
                "status": "failed",
                "error": error_message,
                "agent_error": str(agent_error)
            }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get execution history"""
        return self.execution_history
    
    def get_success_rate(self) -> float:
        """Calculate success rate from execution history"""
        if not self.execution_history:
            return 0.0
        
        successful = len([h for h in self.execution_history if h["success"]])
        return successful / len(self.execution_history)

def main():
    """CLI interface for enhanced glue runner"""
    if len(sys.argv) < 2:
        print("Usage: python enhanced_glue_runner.py <workflow.json> [openrouter_api_key]")
        sys.exit(1)
    
    workflow_file = sys.argv[1]
    api_key = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        with open(workflow_file, 'r') as f:
            workflow = json.load(f)
        
        # Initialize agent if API key provided
        agent = None
        if api_key:
            try:
                sys.path.append(str(Path(__file__).parent.parent / "agents"))
                from workflow_composer import WorkflowComposerAgent
                agent = WorkflowComposerAgent(api_key)
                print("🤖 AI Agent initialized for error assistance")
            except Exception as e:
                print(f"⚠️ Could not initialize AI agent: {e}")
        
        # Run workflow
        runner = EnhancedOrchestraGlueRunner(agent=agent)
        result = runner.run_workflow_with_agent_assistance(workflow)
        
        print("\n" + "="*60)
        print("🎯 EXECUTION RESULTS")
        print("="*60)
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"❌ Execution failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()