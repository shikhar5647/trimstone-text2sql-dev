"""NLU Intent Agent for understanding user queries."""
import google.generativeai as genai
from typing import Dict, Any
from config.secrets import secrets_manager
from config.settings import settings
from graph.state import GraphState
from utils.logger import setup_logger

logger = setup_logger(__name__)

class NLUAgent:
    """Natural Language Understanding Agent."""
    
    def __init__(self):
        genai.configure(api_key=secrets_manager.get_gemini_api_key())
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
    
    def analyze_intent(self, state: GraphState) -> GraphState:
        """Analyze user intent and extract entities."""
        user_query = state["user_query"]
        logger.info(f"Analyzing intent for query: {user_query}")
        
        prompt = f"""Analyze the following database query and extract:
1. The intent (what the user wants to do - e.g., "get data", "aggregate", "filter", "join")
2. Key entities mentioned (table names, column names, filters, etc.)

User Query: {user_query}

Respond in the following format:
Intent: <intent>
Entities: <comma-separated list of entities>
Tables Likely Needed: <comma-separated list of table names from: client, contacts, project>
"""
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text
            
            # Parse response
            intent = "unknown"
            entities = []
            tables = []
            
            for line in result_text.split('\n'):
                if line.startswith('Intent:'):
                    intent = line.replace('Intent:', '').strip()
                elif line.startswith('Entities:'):
                    entities_str = line.replace('Entities:', '').strip()
                    entities = [e.strip() for e in entities_str.split(',') if e.strip()]
                elif line.startswith('Tables Likely Needed:'):
                    tables_str = line.replace('Tables Likely Needed:', '').strip()
                    tables = [t.strip() for t in tables_str.split(',') if t.strip()]
            
            state["intent"] = intent
            state["entities"] = entities
            state["relevant_tables"] = tables
            state["step"] = "nlu_complete"
            
            logger.info(f"Intent: {intent}, Entities: {entities}, Tables: {tables}")
            
        except Exception as e:
            logger.error(f"NLU error: {str(e)}")
            state["error"] = f"Intent analysis failed: {str(e)}"
            state["step"] = "error"
        
        return state

nlu_agent = NLUAgent()