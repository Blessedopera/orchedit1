#!/usr/bin/env python3
"""
Orchestra Workflow Memory System - Stores and retrieves successful workflows
"""
import json
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

class WorkflowMemory:
    def __init__(self, db_path: str = None):
        """Initialize workflow memory database"""
        if db_path is None:
            current_dir = Path(__file__).parent
            self.db_path = current_dir.parent / "data" / "workflow_memory.db"
        else:
            self.db_path = Path(db_path)
        
        # Ensure data directory exists
        self.db_path.parent.mkdir(exist_ok=True)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create workflows table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                user_request TEXT,
                workflow_json TEXT NOT NULL,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tags TEXT
            )
        """)
        
        # Create workflow executions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id INTEGER,
                success BOOLEAN,
                execution_time REAL,
                error_message TEXT,
                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (workflow_id) REFERENCES workflows (id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def store_workflow(self, name: str, description: str, user_request: str, 
                      workflow_json: str, tags: List[str] = None) -> int:
        """Store a successful workflow"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        tags_str = json.dumps(tags) if tags else None
        
        cursor.execute("""
            INSERT INTO workflows (name, description, user_request, workflow_json, tags)
            VALUES (?, ?, ?, ?, ?)
        """, (name, description, user_request, workflow_json, tags_str))
        
        workflow_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return workflow_id
    
    def find_similar_workflows(self, user_request: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find workflows similar to the user request"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Simple keyword matching for now - could be enhanced with embeddings
        keywords = user_request.lower().split()
        
        workflows = []
        cursor.execute("""
            SELECT id, name, description, user_request, workflow_json, success_count, 
                   failure_count, created_at, last_used
            FROM workflows
            ORDER BY success_count DESC, last_used DESC
            LIMIT ?
        """, (limit * 2,))  # Get more to filter
        
        for row in cursor.fetchall():
            workflow_data = {
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "user_request": row[3],
                "workflow_json": row[4],
                "success_count": row[5],
                "failure_count": row[6],
                "created_at": row[7],
                "last_used": row[8]
            }
            
            # Simple relevance scoring
            relevance_score = 0
            request_text = (row[3] + " " + row[2]).lower()
            
            for keyword in keywords:
                if keyword in request_text:
                    relevance_score += 1
            
            if relevance_score > 0 or len(workflows) < limit:
                workflow_data["relevance_score"] = relevance_score
                workflows.append(workflow_data)
        
        # Sort by relevance and success
        workflows.sort(key=lambda x: (x["relevance_score"], x["success_count"]), reverse=True)
        
        conn.close()
        return workflows[:limit]
    
    def record_execution(self, workflow_id: int, success: bool, 
                        execution_time: float = None, error_message: str = None):
        """Record a workflow execution result"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Record execution
        cursor.execute("""
            INSERT INTO workflow_executions (workflow_id, success, execution_time, error_message)
            VALUES (?, ?, ?, ?)
        """, (workflow_id, success, execution_time, error_message))
        
        # Update workflow success/failure counts
        if success:
            cursor.execute("""
                UPDATE workflows 
                SET success_count = success_count + 1, last_used = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (workflow_id,))
        else:
            cursor.execute("""
                UPDATE workflows 
                SET failure_count = failure_count + 1
                WHERE id = ?
            """, (workflow_id,))
        
        conn.commit()
        conn.close()
    
    def get_workflow_stats(self) -> Dict[str, Any]:
        """Get workflow memory statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM workflows")
        total_workflows = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM workflow_executions WHERE success = 1")
        successful_executions = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM workflow_executions WHERE success = 0")
        failed_executions = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT name, success_count FROM workflows 
            ORDER BY success_count DESC LIMIT 5
        """)
        top_workflows = cursor.fetchall()
        
        conn.close()
        
        return {
            "total_workflows": total_workflows,
            "successful_executions": successful_executions,
            "failed_executions": failed_executions,
            "success_rate": successful_executions / (successful_executions + failed_executions) if (successful_executions + failed_executions) > 0 else 0,
            "top_workflows": [{"name": row[0], "success_count": row[1]} for row in top_workflows]
        }