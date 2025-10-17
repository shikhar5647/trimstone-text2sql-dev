"""Main Streamlit application for Text-to-SQL."""
import streamlit as st
import pandas as pd
from typing import Dict, Any
from graph.workflow import text2sql_workflow
from graph.state import GraphState
from database.connection import db_connection
from database.schema_cache import schema_cache
from config.secrets import secrets_manager
from ui.components import (
    display_schema_info,
    display_sql_query,
    display_results_table,
    display_workflow_status,
    display_validation_result
)
from utils.logger import setup_logger
from config.settings import settings



logger = setup_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="Text-to-SQL Assistant",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stApp {
        max-width: 1400px;
        margin: 0 auto;
    }
    .sql-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize Streamlit session state."""
    if 'workflow_state' not in st.session_state:
        st.session_state.workflow_state = None
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    if 'execution_approved' not in st.session_state:
        st.session_state.execution_approved = False

def main():
    """Main application function."""
    initialize_session_state()
    
    # Title and description
    st.title("🔍 Text-to-SQL Assistant")
    st.markdown("Transform natural language into SQL queries using AI-powered agents")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Connection status
        st.subheader("Database Connection")
        st.info("Database connection not required to generate SQL. Use cached schema or test connection manually.")
        conn_test = st.button("🔎 Test DB Connection", use_container_width=True)
        if conn_test:
            with st.spinner("Testing database connection..."):
                if db_connection.test_connection():
                    st.success("✅ Connected to MS SQL Server")
                else:
                    st.error("❌ Database connection failed. Using cached schema for SQL generation.")
                    # do not stop — allow offline generation using schema cache
        
        # Schema information
        st.subheader("Database Schema")
        # Option to load schema from Excel
        with st.expander("Schema Source", expanded=False):
            st.caption("Choose how to build the schema context exposed to the LLM")
            col_a, col_b = st.columns([1,1])
            with col_a:
                if st.button("Load schema from DB", use_container_width=True):
                    with st.spinner("Refreshing schema from database..."):
                        schema_cache.refresh_schema()
                        st.success("Schema refreshed from DB!")
            with col_b:
                if st.button("Load schema from Excel", use_container_width=True):
                    with st.spinner("Loading schema from Excel..."):
                        try:
                            schema_cache.load_schema_from_excel()
                            st.success("Schema loaded from Excel!")
                        except Exception as e:
                            st.error(f"Failed to load Excel schema: {e}")
            if st.button("Load manual schema", use_container_width=True):
                with st.spinner("Loading manual schema..."):
                    try:
                        schema_cache.load_manual_schema()
                        st.success("Manual schema loaded!")
                    except Exception as e:
                        st.error(f"Failed to load manual schema: {e}")
        if st.button("🔄 Refresh Schema Cache"):
            with st.spinner("Refreshing schema cache..."):
                schema_cache.refresh_schema()
                st.success("Schema cache refreshed!")
        
        schema = schema_cache.get_schema()
        tables = list(schema.get('tables', {}).keys())
        st.info(f"📊 Tables: {len(tables)}")
        for table in tables:
            st.text(f"  • {table}")
        
        # View detailed schema
        if st.checkbox("Show Detailed Schema"):
            display_schema_info(schema)
        
        st.divider()
        
        # Query history
        st.subheader("📜 Query History")
        if st.session_state.query_history:
            for idx, query in enumerate(reversed(st.session_state.query_history[-5:])):
                if st.button(f"Query {len(st.session_state.query_history) - idx}", key=f"history_{idx}"):
                    st.session_state.user_input = query
                    st.rerun()
        else:
            st.text("No history yet")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("💬 Ask Your Question")
        
        # Example queries
        st.markdown("**Example queries:**")
        examples = [
            "Show me all clients from New York",
            "List projects with budget over 100000",
            "Get contact details for client 'Acme Corp'",
            "Show me the top 10 clients by number of projects"
        ]
        
        example_cols = st.columns(2)
        for idx, example in enumerate(examples):
            with example_cols[idx % 2]:
                if st.button(example, key=f"example_{idx}", use_container_width=True):
                    st.session_state.user_input = example
        
        # User input
        user_query = st.text_area(
            "Enter your question:",
            value=st.session_state.get('user_input', ''),
            height=100,
            placeholder="e.g., Show me all active projects for clients in the technology industry"
        )
        
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
        
        with col_btn1:
            submit_button = st.button("🚀 Generate SQL", type="primary", use_container_width=True)
        
        with col_btn2:
            clear_button = st.button("🗑️ Clear", use_container_width=True)
        
        if clear_button:
            st.session_state.workflow_state = None
            st.session_state.execution_approved = False
            st.session_state.user_input = ''
            st.rerun()
    
    with col2:
        st.header("ℹ️ Information")
        st.info("""
        **How it works:**
        1. Enter your question in natural language
        2. AI agents analyze and generate SQL
        3. Review and approve the query
        4. View results in a formatted table
        
        **Features:**
        - Natural language processing
        - Intelligent schema detection
        - SQL validation & safety checks
        - Human-in-the-loop approval
        """)
    
    # Process query
    if submit_button and user_query:
        st.session_state.query_history.append(user_query)
        
        with st.spinner("🤖 Processing your query..."):
            try:
                # Initialize state
                initial_state: GraphState = {
                    "user_query": user_query,
                    "intent": None,
                    "entities": [],
                    "relevant_tables": [],
                    "schema_context": "",
                    "generated_sql": None,
                    "is_valid": False,
                    "validation_message": "",
                    "safety_check": False,
                    "execution_approved": False,
                    "query_results": None,
                    "execution_error": None,
                    "formatted_response": None,
                    "messages": [],
                    "step": "start",
                    "error": None,
                    "requires_human_approval": False
                }
                
                # Run workflow
                result = text2sql_workflow.invoke(initial_state)
                st.session_state.workflow_state = result
                
            except Exception as e:
                st.error(f"❌ Error processing query: {str(e)}")
                logger.error(f"Workflow error: {str(e)}")
    
    # Display results
    if st.session_state.workflow_state:
        state = st.session_state.workflow_state
        
        st.divider()
        
        # Workflow status
        display_workflow_status(state)
        
        st.divider()
        
        # Intent and entities
        if state.get("intent"):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("🎯 Intent", state["intent"])
            with col2:
                st.metric("🏷️ Tables Identified", ", ".join(state.get("relevant_tables", [])))
        
        # Generated SQL
        if state.get("generated_sql"):
            display_sql_query(state["generated_sql"])
            
            # Validation results
            display_validation_result(
                state.get("is_valid", False),
                state.get("validation_message", "")
            )
            
            # Human approval
            if state.get("is_valid") and state.get("requires_human_approval"):
                st.warning("⚠️ Please review the SQL query before execution")
                
                col1, col2, col3 = st.columns([1, 1, 2])
                
                with col1:
                    if st.button("✅ Approve & Execute", type="primary"):
                        st.session_state.execution_approved = True
                        state["execution_approved"] = True
                        
                        with st.spinner("Executing query..."):
                            # Re-run workflow from executor
                            from agents.executor_agent import executor_agent
                            state = executor_agent.execute_sql(state)
                            
                            if state.get("query_results") is not None:
                                from agents.formatter_agent import formatter_agent
                                state = formatter_agent.format_results(state)
                            
                            st.session_state.workflow_state = state
                            st.rerun()
                
                with col2:
                    if st.button("❌ Reject"):
                        st.session_state.workflow_state = None
                        st.rerun()
        
        # Execution results
        if state.get("execution_error"):
            st.error(f"❌ Execution Error: {state['execution_error']}")
        
        if state.get("query_results") is not None:
            # Formatted response
            if state.get("formatted_response"):
                st.success(state["formatted_response"])
            
            # Results table
            display_results_table(state["query_results"])

if __name__ == "__main__":
    # Validate secrets on startup
    if not secrets_manager.validate_secrets():
        st.error("❌ Missing required configuration. Please check your .env file.")
        st.stop()
    
    main()