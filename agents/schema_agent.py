"""Schema Agent for retrieving relevant schema information."""
import re
from typing import Dict, Any, List
from graph.state import GraphState
from database.schema_cache import schema_cache
from utils.logger import setup_logger

logger = setup_logger(__name__)

def _tokenize(text: str) -> set[str]:
    text = (text or "").lower()
    tokens = set(re.findall(r"[a-z0-9_]+", text))
    stopwords = {"show", "list", "get", "find", "all", "the", "me", "for", "with", "in", "of", "and", "top"}
    return tokens - stopwords

class SchemaAgent:
    """Schema Introspection and Retrieval Agent - conservative, no hallucination."""
    
    def get_relevant_schema(self, state: GraphState) -> GraphState:
        """Get schema information relevant to the query. Abstain if no confident match."""
        logger.info("Retrieving relevant schema information (conservative mode)")
        
        try:
            # Get full schema
            schema = schema_cache.get_schema()
            tables = schema.get("tables", {}) or {}
            
            # Tokenize user query
            user_query = (state.get("user_query") or "") 
            q_tokens = _tokenize(user_query)
            
            matched_tables: dict[str, int] = {}
            matched_columns: dict[str, List[Dict[str, Any]]] = {}
            
            # Score tables/columns conservatively based on token overlap
            for tname, tinfo in tables.items():
                t_tokens = _tokenize(tname)
                cols = tinfo.get("columns", []) or []
                
                # compute column token matches
                col_matches: List[Dict[str, Any]] = []
                for col in cols:
                    # support both dict and simple string column entries
                    if isinstance(col, dict):
                        cname = col.get("column_name") or col.get("name") or ""
                    else:
                        cname = str(col)
                    c_tokens = _tokenize(cname)
                    if q_tokens & c_tokens:
                        col_matches.append(col if isinstance(col, dict) else {"column_name": cname})
                
                # table-level match if table name tokens overlap or some columns matched
                score = len(q_tokens & t_tokens) + len(col_matches)
                if score > 0:
                    matched_tables[tname] = score
                    matched_columns[tname] = col_matches
            
            # sort and select top tables (conservative limit)
            selected_tables = [t for t, _ in sorted(matched_tables.items(), key=lambda x: x[1], reverse=True)][:5]
            
            if not selected_tables:
                # No confident schema identified — mark and explain, do NOT invent schema
                state["relevant_tables"] = []
                state["schema_context"] = ""
                state["no_schema_found"] = True
                state.setdefault("messages", []).append(
                    "No matching tables or columns found in schema cache for the user's question. Aborting SQL generation to avoid hallucination."
                )
                state["step"] = "schema_abstain"
                logger.info("Schema agent: no relevant schema identified for query. Abstaining.")
                return state
            
            # Build minimal schema context exposing only matched columns per table (if any)
            schema_parts: List[str] = []
            for tbl in selected_tables:
                schema_parts.append(f"### Table: {tbl}")
                cols = matched_columns.get(tbl, [])
                if cols:
                    schema_parts.append("Columns:")
                    for col in cols:
                        # preserve column attributes if available
                        if isinstance(col, dict):
                            cname = col.get("column_name") or col.get("name")
                            dtype = col.get("data_type", "unknown")
                            nullable = col.get("is_nullable", "")
                            null_text = "NULL" if nullable == "YES" else ("NOT NULL" if nullable else "")
                            schema_parts.append(f"  - {cname} ({dtype}) {null_text}".rstrip())
                        else:
                            schema_parts.append(f"  - {col}")
                else:
                    # do not invent columns; explicitly mark that no confident columns were matched
                    schema_parts.append("Columns: (no confidently matched columns)")
            
            state["relevant_tables"] = selected_tables
            state["schema_context"] = "\n".join(schema_parts)
            state["no_schema_found"] = False
            state["step"] = "schema_retrieved"
            state.setdefault("messages", []).append(f"Schema agent selected tables: {', '.join(selected_tables)}")
            
            logger.info(f"Schema context built for tables: {selected_tables}")
            
        except Exception as e:
            logger.error(f"Schema retrieval error: {str(e)}")
            state["error"] = f"Schema retrieval failed: {str(e)}"
            state["step"] = "error"
        
        return state

schema_agent = SchemaAgent()