import streamlit as st
import requests
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import json

# Page config
st.set_page_config(
    page_title="Analytics Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .sql-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
    }
    .insight-box {
        background-color: #e7f3ff;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #0066cc;
        margin: 1rem 0;
    }
    .success-badge {
        background-color: #d4edda;
        color: #155724;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-weight: bold;
    }
    .cache-badge {
        background-color: #fff3cd;
        color: #856404;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-weight: bold;
    }
    .history-item {
        padding: 0.5rem;
        margin: 0.25rem 0;
        border-radius: 0.25rem;
        background-color: #f8f9fa;
        cursor: pointer;
        transition: background-color 0.2s;
    }
    .history-item:hover {
        background-color: #e9ecef;
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
API_URL = "http://backend:8000"  # Docker service name
# For local testing outside Docker, use: "http://localhost:8000"

# Initialize session state
if 'query_history' not in st.session_state:
    st.session_state.query_history = []

if 'favorite_queries' not in st.session_state:
    st.session_state.favorite_queries = []

# Header
st.markdown('<div class="main-header">🤖 Analytics Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Ask questions about your data in natural language</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("📊 System Status")
    
    # Health check
    try:
        health_response = requests.get(f"{API_URL}/health", timeout=5)
        health_data = health_response.json()
        
        if health_data['status'] == 'healthy':
            st.success("✅ System Online")
            st.metric("Database", health_data['database'])
            st.metric("Cache", health_data['redis'])
        else:
            st.warning("⚠️ System Degraded")
    except:
        st.error("❌ System Offline")
    
    st.divider()
    
    # Saved Queries Section
    st.header("⭐ Saved Queries")
    
    if st.session_state.favorite_queries:
        for i, fav in enumerate(st.session_state.favorite_queries):
            col1, col2 = st.columns([5, 1])
            with col1:
                if st.button(fav['query'], key=f"fav_{i}", use_container_width=True):
                    st.session_state.current_query = fav['query']
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_fav_{i}"):
                    st.session_state.favorite_queries.pop(i)
                    st.rerun()
    else:
        st.info("No saved queries yet. Run a query and click '⭐ Save' to add it here!")
    
    st.divider()
    
    # Query History Section
    st.header("📜 Query History")
    
    if st.session_state.query_history:
        # Show statistics
        total_queries = len(st.session_state.query_history)
        cached_queries = sum(1 for q in st.session_state.query_history if q.get('result', {}).get('cached'))
        
        col1, col2 = st.columns(2)
        col1.metric("Total", total_queries)
        col2.metric("Cached", cached_queries)
        
        st.caption("Last 10 queries:")
        
        # Show recent queries
        for i, hist in enumerate(reversed(st.session_state.query_history[-10:])):
            with st.expander(f"🕐 {hist['timestamp']}", expanded=False):
                st.text(hist['query'])
                
                # Show if it was cached
                if hist.get('result', {}).get('cached'):
                    st.caption("⚡ Served from cache")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("▶️ Rerun", key=f"rerun_{i}", use_container_width=True):
                        st.session_state.current_query = hist['query']
                        st.rerun()
                with col2:
                    # Check if already saved
                    is_saved = any(fav['query'] == hist['query'] for fav in st.session_state.favorite_queries)
                    if not is_saved:
                        if st.button("⭐ Save", key=f"save_{i}", use_container_width=True):
                            st.session_state.favorite_queries.append({
                                'query': hist['query'],
                                'saved_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            })
                            st.rerun()
        
        # Clear history button
        if st.button("🗑️ Clear History", type="secondary", use_container_width=True):
            st.session_state.query_history = []
            st.rerun()
    else:
        st.info("No queries yet. Ask a question to get started!")
    
    st.divider()
    
    # Quick Tips
    with st.expander("💡 Tips & Examples"):
        st.markdown("""
        **Try questions like:**
        - What were the top 5 products by revenue?
        - Show me daily order trends
        - Which customer spent the most?
        - Compare sales by category
        - How many pending orders?
        - What's the average order value?
        
        **Pro tips:**
        - ⭐ Save frequently used queries
        - ⚡ Enable cache for faster results
        - 📥 Download data as CSV
        - 🔍 View generated SQL queries
        """)

# Main content area
query_input = st.text_input(
    "🔍 Ask your question:",
    value=st.session_state.get('current_query', ''),
    placeholder="e.g., What were the top products by revenue last month?",
    key="query_input"
)

col1, col2, col3 = st.columns([1, 1, 4])
with col1:
    ask_button = st.button("🚀 Ask Question", type="primary", use_container_width=True)
with col2:
    use_cache = st.checkbox("⚡ Use Cache", value=True)

# Process query
if ask_button and query_input:
    with st.spinner("🤔 Thinking..."):
        try:
            # Make API request
            response = requests.post(
                f"{API_URL}/query",
                json={"query": query_input, "use_cache": use_cache},
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            # Add to history
            st.session_state.query_history.append({
                'query': query_input,
                'timestamp': datetime.now().strftime("%H:%M:%S"),
                'result': result
            })
            
            # Clear current query
            if 'current_query' in st.session_state:
                del st.session_state.current_query
            
            # Display results
            st.success("✅ Query executed successfully!")
            
            # Performance metrics - FIXED VERSION
            col1, col2, col3 = st.columns(3)
            with col1:
                row_count = result.get('data_summary', {}).get('row_count', 0)
                st.metric("Rows Returned", row_count)
            with col2:
                cache_status = "🟢 Cache Hit" if result.get('cached') else "🔵 Fresh Query"
                st.metric("Cache Status", cache_status)
            with col3:
                data_type = result.get('data_summary', {}).get('type', 'unknown')
                st.metric("Data Type", data_type.title())
            
            # Save query button
            is_already_saved = any(fav['query'] == query_input for fav in st.session_state.favorite_queries)
            if not is_already_saved:
                if st.button("⭐ Save this query for later"):
                    st.session_state.favorite_queries.append({
                        'query': query_input,
                        'saved_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    st.success("Query saved!")
                    st.rerun()
            
            # Insight
            st.markdown("### 💡 Insight")
            st.markdown(f'<div class="insight-box">{result.get("insight", "No insight available")}</div>', unsafe_allow_html=True)
            
            # Visualization - FIXED VERSION
            st.markdown("### 📊 Visualization")
            
            if result.get('visualization_code') and result['visualization_code'] != "# No visualization generated":
                try:
                    # Get data from response - handle different response structures
                    data_summary = result.get('data_summary', {})
                    
                    # Try to get data from different possible locations
                    if 'data' in data_summary and data_summary['data']:
                        data = pd.DataFrame(data_summary['data'])
                    else:
                        # Fallback: check if columns exist and create empty DataFrame
                        columns = data_summary.get('columns', [])
                        if columns:
                            data = pd.DataFrame(columns=columns)
                        else:
                            data = pd.DataFrame()
                    
                    if not data.empty:
                        # Execute visualization code
                        local_vars = {'df': data, 'go': go, 'pd': pd}
                        try:
                            exec(result['visualization_code'], {}, local_vars)
                            fig = local_vars.get('fig')
                            
                            if fig:
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.warning("Visualization code didn't produce a figure")
                                st.code(result['visualization_code'], language='python')
                        except Exception as viz_error:
                            st.error(f"Error rendering visualization: {str(viz_error)}")
                            with st.expander("🔍 Debug Info"):
                                st.write("**Error:**", str(viz_error))
                                st.write("**Data shape:**", data.shape)
                                st.write("**Columns:**", data.columns.tolist())
                                st.write("**First few rows:**")
                                st.dataframe(data.head())
                                st.write("**Visualization code:**")
                                st.code(result['visualization_code'], language='python')
                    else:
                        st.info("No data to visualize")
                except Exception as e:
                    st.error(f"Visualization error: {str(e)}")
                    # Show debug information
                    with st.expander("🔍 Debug Information"):
                        st.write("**Error details:**", str(e))
                        st.write("**Data summary:**", data_summary)
                        if result.get('visualization_code'):
                            st.code(result['visualization_code'], language='python')
            else:
                st.info("No visualization generated for this query")
            
            # SQL Query (collapsible)
            with st.expander("🔍 View SQL Query", expanded=False):
                st.markdown(f'<div class="sql-box">{result.get("sql", "No SQL generated")}</div>', unsafe_allow_html=True)
                if st.button("📋 Copy SQL"):
                    st.code(result.get('sql', ''), language='sql')
            
            # Raw data (collapsible)
            with st.expander("📄 View Raw Data", expanded=False):
                data_summary = result.get('data_summary', {})
                if 'data' in data_summary and data_summary['data']:
                    df = pd.DataFrame(data_summary['data'])
                    st.dataframe(df, use_container_width=True)
                    
                    # Download button
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download as CSV",
                        data=csv,
                        file_name=f"query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("No data returned")
            
        except requests.exceptions.Timeout:
            st.error("⏱️ Request timeout. The query took too long to execute.")
        except requests.exceptions.ConnectionError:
            st.error("🔌 Cannot connect to backend. Make sure the API is running.")
        except requests.exceptions.HTTPError as e:
            st.error(f"❌ API Error: {e.response.status_code}")
            if e.response.text:
                with st.expander("Error Details"):
                    st.code(e.response.text)
        except Exception as e:
            st.error(f"❌ Unexpected error: {str(e)}")
            with st.expander("Error Details"):
                st.write(str(e))
                import traceback
                st.code(traceback.format_exc())

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    Built with LangGraph 🦜 | Powered by Groq ⚡ | Visualized with Plotly 📊
</div>
""", unsafe_allow_html=True)