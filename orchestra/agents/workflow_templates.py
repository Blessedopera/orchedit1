#!/usr/bin/env python3
"""
Orchestra Workflow Templates - Predefined templates for common workflow patterns
"""
import json
from typing import Dict, Any, List

class WorkflowTemplates:
    """Collection of workflow templates for common automation patterns"""
    
    @staticmethod
    def get_news_processing_template() -> Dict[str, Any]:
        """Template for news scraping and processing workflows"""
        return {
            "name": "News Processing Pipeline",
            "description": "Scrape news articles and process them with AI",
            "version": "1.0.0",
            "category": "content_processing",
            "steps": [
                {
                    "node": "google-news-scraper",
                    "inputs": {
                        "api_token": "{{USER_INPUT:apify_token}}",
                        "keywords": "{{USER_INPUT:keywords}}",
                        "max_news": "{{USER_INPUT:max_articles|5}}",
                        "time_period": "{{USER_INPUT:time_period|Last 24 hours}}",
                        "region_code": "{{USER_INPUT:region|United States (English)}}"
                    }
                },
                {
                    "assembly": {
                        "selected_article_url": {
                            "action": "{{USER_INPUT:selection_method|select_random}}",
                            "from": "articles",
                            "extract": "url"
                        }
                    },
                    "source": "google-news-scraper",
                    "name": "article_selector",
                    "description": "Select article for processing"
                },
                {
                    "node": "article-page-scraper",
                    "inputs": {
                        "url": "{{article_selector.selected_article_url}}",
                        "headless": True
                    }
                },
                {
                    "assembly": {
                        "clean_text": "article_text"
                    },
                    "source": "article-page-scraper",
                    "name": "text_extractor",
                    "description": "Extract clean text for processing"
                },
                {
                    "node": "article-processor",
                    "inputs": {
                        "article_text": "{{text_extractor.clean_text}}",
                        "openrouter_api_key": "{{USER_INPUT:openrouter_key}}",
                        "model": "{{USER_INPUT:model|qwen/qwen3-coder:free}}"
                    }
                }
            ]
        }
    
    @staticmethod
    def get_data_processing_template() -> Dict[str, Any]:
        """Template for general data processing workflows"""
        return {
            "name": "Data Processing Pipeline",
            "description": "Extract, transform, and process data",
            "version": "1.0.0",
            "category": "data_processing",
            "steps": [
                {
                    "node": "{{USER_INPUT:source_node}}",
                    "inputs": "{{USER_INPUT:source_inputs}}"
                },
                {
                    "assembly": {
                        "processed_data": "{{USER_INPUT:assembly_logic}}"
                    },
                    "source": "{{USER_INPUT:source_node}}",
                    "name": "data_transformer",
                    "description": "Transform data for next step"
                },
                {
                    "node": "{{USER_INPUT:target_node}}",
                    "inputs": {
                        "data": "{{data_transformer.processed_data}}"
                    }
                }
            ]
        }
    
    @staticmethod
    def get_all_templates() -> List[Dict[str, Any]]:
        """Get all available templates"""
        return [
            WorkflowTemplates.get_news_processing_template(),
            WorkflowTemplates.get_data_processing_template()
        ]
    
    @staticmethod
    def find_template_by_category(category: str) -> List[Dict[str, Any]]:
        """Find templates by category"""
        templates = WorkflowTemplates.get_all_templates()
        return [t for t in templates if t.get("category") == category]
    
    @staticmethod
    def customize_template(template: Dict[str, Any], user_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Customize a template with user inputs"""
        # Convert template to JSON string for easy replacement
        template_str = json.dumps(template, indent=2)
        
        # Replace user input placeholders
        for key, value in user_inputs.items():
            placeholder = f"{{{{USER_INPUT:{key}}}}}"
            template_str = template_str.replace(placeholder, str(value))
            
            # Handle default values
            placeholder_with_default = f"{{{{USER_INPUT:{key}|"
            if placeholder_with_default in template_str:
                # Find the default value and use it if user input not provided
                import re
                pattern = f"{{{{USER_INPUT:{key}\\|([^}}]+)}}}}"
                matches = re.findall(pattern, template_str)
                if matches:
                    default_value = matches[0]
                    full_placeholder = f"{{{{USER_INPUT:{key}|{default_value}}}}}"
                    template_str = template_str.replace(full_placeholder, str(value) if value else default_value)
        
        # Clean up any remaining placeholders
        import re
        template_str = re.sub(r'\{\{USER_INPUT:[^}]+\}\}', '""', template_str)
        
        return json.loads(template_str)