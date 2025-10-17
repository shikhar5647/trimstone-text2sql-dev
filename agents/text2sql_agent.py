"""Text to SQL Agent for generating SQL queries."""
import google.generativeai as genai
from typing import Dict, Any
from config.secrets import secrets_manager
from config.settings import settings
from graph.state import GraphState
from utils.logger import setup_logger
from utils.helpers import sanitize_sql, ensure_top_limit

logger = setup_logger(__name__)

class Text2SQLAgent:
    """SQL Generation Agent."""
    
    def __init__(self):
        genai.configure(api_key=secrets_manager.get_gemini_api_key())
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
    
    def generate_sql(self, state: GraphState) -> GraphState:
        """Generate SQL query from natural language."""
        user_query = state["user_query"]
        schema_context = state.get("schema_context", "")
        
        logger.info(f"Generating SQL for: {user_query}")
        
        prompt = f"""You are a senior data engineer generating safe, production-quality T-SQL for Microsoft SQL Server.

You will receive the user request and the available schema. Your job is to write a single, safe SELECT statement.

STRICT RULES:
- Output only the SQL, no commentary or markdown fences.
- Only SELECT is allowed. Never use INSERT/UPDATE/DELETE/CREATE/ALTER/DROP/EXEC.
- Prefer explicit JOINs with ON clauses over implicit joins.
- Qualify columns with table aliases when joining.
- Use ISNULL for null-safe display where appropriate.
- Use meaningful column aliases for readability.
- Use WHERE filters for user constraints; avoid returning entire tables.
- Use TOP 100 by default if the user didn't specify a limit.
- For text search, use LIKE with wildcards and proper quoting.
- Prefer COUNT(*) for counts; use GROUP BY for aggregations.
- For date filters, use BETWEEN or >= <= and proper CAST/CONVERT if needed.

SCHEMA (authoritative):
{schema_context}

USER REQUEST:
{user_query}

Return only the final SQL (no code fences, no explanation)."""
        
        try:
            response = self.model.generate_content(prompt)
            sql_query = response.text.strip()
            
            # Extract SQL from markdown code blocks if present
            if "```sql" in sql_query:
                sql_query = sql_query.split("```sql")[1].split("```")[0].strip()
            elif "```" in sql_query:
                sql_query = sql_query.split("```")[1].split("```")[0].strip()
            
            # Sanitize and format
            sql_query = sanitize_sql(sql_query)
            sql_query = ensure_top_limit(sql_query, limit=100)
            
            state["generated_sql"] = sql_query
            state["step"] = "sql_generated"
            
            logger.info(f"Generated SQL: {sql_query}")
            
        except Exception as e:
            logger.error(f"SQL generation error: {str(e)}")
            state["error"] = f"SQL generation failed: {str(e)}"
            state["step"] = "error"
        
        return state

text2sql_agent = Text2SQLAgent()