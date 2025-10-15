"""Reusable Streamlit UI components."""
import streamlit as st
import pandas as pd
from typing import List, Dict, Any

def display_schema_info(schema: Dict[str, Any]):
    """Display database schema information."""
    st.subheader("📋 Database Schema")
    
    tables = schema.get('tables', {})
    
    for table_name, table_info in tables.items():
        with st.expander(f"Table: {table_name}", expanded=False):
            columns_data = []
            for col in table_info['columns']:
                columns_data.append({
                    'Column': col['column_name'],
                    'Type': col['data_type'],
                    'Nullable': col['is_nullable']
                })
            df = pd.DataFrame(columns_data)
            st.dataframe(df, use_container_width=True)

def display_sql_query(sql: str, title: str = "Generated SQL"):
    """Display SQL query in a formatted code block."""
    st.subheader(f"⚡ {title}")
    st.code(sql, language="sql")

def display_results_table(results: List[Dict[str, Any]]):
    """Display query results in a table."""
    if not results:
        st.info("No results found.")
        return
    
    df = pd.DataFrame(results)
    st.subheader(f"📊 Results ({len(results)} rows)")
    st.dataframe(df, use_container_width=True)
    
    # Download button
    csv = df.to_csv(index=False)
    st.download_button(
        label="⬇️ Download as CSV",
        data=csv,
        file_name="query_results.csv",
        mime="text/csv"
    )

def display_workflow_status(state: Dict[str, Any]):
    """Display workflow execution status."""
    st.subheader("🔄 Workflow Status")
    
    steps = [
        ("NLU Analysis", "nlu_complete"),
        ("Schema Retrieval", "schema_retrieved"),
        ("SQL Generation", "sql_generated"),
        ("Validation", "validated"),
        ("Execution", "executed"),
        ("Formatting", "complete")
    ]
    
    current_step = state.get("step", "")
    
    cols = st.columns(len(steps))
    for idx, (step_name, step_key) in enumerate(steps):
        with cols[idx]:
            if step_key == current_step:
                st.markdown(f"**🔵 {step_name}**")
            elif steps.index((step_name, step_key)) < steps.index(
                next((s for s in steps if s[1] == current_step), steps[0])
            ):
                st.markdown(f"✅ {step_name}")
            else:
                st.markdown(f"⚪ {step_name}")

def display_validation_result(is_valid: bool, message: str):
    """Display validation results."""
    if is_valid:
        st.success(f"✅ Validation Passed: {message}")
    else:
        st.error(f"❌ Validation Failed: {message}")