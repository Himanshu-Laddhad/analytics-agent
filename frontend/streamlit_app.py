import streamlit as st
import requests
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import json
import io

# Page config
st.set_page_config(
    page_title="Analytics Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS (keep existing)
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
    .data-source-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #1f77b4;
    }
    .insight-box {
        background-color: #e7f3ff;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #0066cc;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
API_URL = "http://backend:8000"

# Initialize session state
if 'query_history' not in st.session_state:
    st.session_state.query_history = []
if 'favorite_queries' not in st.session_state:
    st.session_state.favorite_queries = []
if 'data_sources' not in st.session_state:
    st.session_state.data_sources = []

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
    
    # Data Sources Section
    st.header("📁 Data Sources")
    
    # Refresh data sources
    try:
        sources_response = requests.get(f"{API_URL}/data-sources", timeout=5)
        if sources_response.status_code == 200:
            st.session_state.data_sources = sources_response.json().get('sources', [])
    except:
        pass
    
    # Upload CSV
    with st.expander("➕ Upload New CSV", expanded=False):
        uploaded_file = st.file_uploader("Choose a CSV file", type=['csv'])
        table_name = st.text_input("Table name (optional)", placeholder="my_data")
        description = st.text_area("Description (optional)", placeholder="Sales data from Q4 2024")
        
        if st.button("Upload", type="primary", use_container_width=True):
            if uploaded_file:
                with st.spinner("Uploading..."):
                    try:
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
                        params = {}
                        if table_name:
                            params["table_name"] = table_name
                        if description:
                            params["description"] = description
                        
                        response = requests.post(
                            f"{API_URL}/upload-csv",
                            files=files,
                            params=params,
                            timeout=60
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.success(f"✅ {result['message']}")
                            st.info(f"Table: `{result['table_name']}`\nRows: {result['rows']}")
                            st.rerun()
                        else:
                            st.error(f"Upload failed: {response.text}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    
    # Show available data sources
    if st.session_state.data_sources:
        st.caption(f"**{len(st.session_state.data_sources)} data source(s) available**")
        
        for source in st.session_state.data_sources:
            with st.expander(f"📊 {source['name']}", expanded=False):
                st.caption(f"**Table:** `{source['table_name']}`")
                st.caption(f"**Rows:** {source['row_count']:,}")
                st.caption(f"**Columns:** {source['column_count']}")
                if source.get('description'):
                    st.caption(f"**Description:** {source['description']}")
                st.caption(f"**Uploaded:** {source.get('uploaded_at', 'N/A')[:10]}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("👁️ View", key=f"view_{source['table_name']}", use_container_width=True):
                        try:
                            info = requests.get(f"{API_URL}/data-sources/{source['table_name']}", timeout=5).json()
                            st.session_state.viewing_table = info
                            st.rerun()
                        except:
                            st.error("Failed to load table info")
                
                with col2:
                    if st.button("🗑️ Delete", key=f"del_{source['table_name']}", use_container_width=True):
                        try:
                            response = requests.delete(f"{API_URL}/data-sources/{source['table_name']}", timeout=5)
                            if response.status_code == 200:
                                st.success("Deleted!")
                                st.rerun()
                            else:
                                st.error("Delete failed")
                        except:
                            st.error("Error deleting")
    else:
        st.info("No data sources yet. Upload a CSV to get started!")
    
    st.divider()
    
    # Saved Queries
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
        st.info("No saved queries yet")
    
    st.divider()
    
    # Query History
    st.header("📜 Query History")
    if st.session_state.query_history:
        total_queries = len(st.session_state.query_history)
        cached_queries = sum(1 for q in st.session_state.query_history if q.get('result', {}).get('cached'))
        
        col1, col2 = st.columns(2)
        col1.metric("Total", total_queries)
        col2.metric("Cached", cached_queries)
        
        for i, hist in enumerate(reversed(st.session_state.query_history[-10:])):
            with st.expander(f"🕐 {hist['timestamp']}", expanded=False):
                st.text(hist['query'])
                if hist.get('result', {}).get('cached'):
                    st.caption("⚡ Served from cache")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("▶️ Rerun", key=f"rerun_{i}", use_container_width=True):
                        st.session_state.current_query = hist['query']
                        st.rerun()
                with col2:
                    is_saved = any(fav['query'] == hist['query'] for fav in st.session_state.favorite_queries)
                    if not is_saved:
                        if st.button("⭐ Save", key=f"save_{i}", use_container_width=True):
                            st.session_state.favorite_queries.append({
                                'query': hist['query'],
                                'saved_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            })
                            st.rerun()
        
        if st.button("🗑️ Clear History", type="secondary", use_container_width=True):
            st.session_state.query_history = []
            st.rerun()
    else:
        st.info("No queries yet")

# Main content area
# Show table viewer if requested
if 'viewing_table' in st.session_state:
    info = st.session_state.viewing_table
    
    st.header(f"📊 {info['table_name']}")
    st.caption(f"**{info['row_count']:,} rows** | **{len(info['columns'])} columns**")
    
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("✖️ Close"):
            del st.session_state.viewing_table
            st.rerun()
    
    # Column info
    st.subheader("Columns")
    col_df = pd.DataFrame(info['columns'])
    st.dataframe(col_df, use_container_width=True)
    
    # Sample data
    st.subheader("Sample Data (first 5 rows)")
    sample_df = pd.DataFrame(info['sample_data'])
    st.dataframe(sample_df, use_container_width=True)
    
    st.divider()

# Query input
query_input = st.text_input(
    "🔍 Ask your question:",
    value=st.session_state.get('current_query', ''),
    placeholder="e.g., What are the top products by revenue?",
    key="query_input"
)

col1, col2, col3 = st.columns([1, 1, 4])
with col1:
    ask_button = st.button("🚀 Ask Question", type="primary", use_container_width=True)
with col2:
    use_cache = st.checkbox("⚡ Use Cache", value=True)

# Process query (keep existing query processing code)
if ask_button and query_input:
    with st.spinner("🤔 Thinking..."):
        try:
            response = requests.post(
                f"{API_URL}/query",
                json={"query": query_input, "use_cache": use_cache},
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            st.session_state.query_history.append({
                'query': query_input,
                'timestamp': datetime.now().strftime("%H:%M:%S"),
                'result': result
            })
            
            if 'current_query' in st.session_state:
                del st.session_state.current_query
            
            st.success("✅ Query executed successfully!")
            
            # Metrics
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
            
            # Save button
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
            
            # Visualization
            st.markdown("### 📊 Visualization")
            
            if result.get('visualization_code') and result['visualization_code'] != "# No visualization generated":
                try:
                    data_summary = result.get('data_summary', {})
                    
                    if 'data' in data_summary and data_summary['data']:
                        data = pd.DataFrame(data_summary['data'])
                        
                        for col in data.columns:
                            try:
                                data[col] = pd.to_numeric(data[col], errors='ignore')
                            except:
                                pass
                        
                        if not data.empty:
                            local_vars = {'df': data, 'go': go, 'pd': pd}
                            try:
                                exec(result['visualization_code'], {}, local_vars)
                                fig = local_vars.get('fig')
                                
                                if fig:
                                    st.plotly_chart(fig, use_container_width=True)
                                else:
                                    st.warning("Visualization code didn't produce a figure")
                            except Exception as viz_error:
                                st.error(f"Error rendering visualization: {str(viz_error)}")
                                with st.expander("🔍 Debug Info"):
                                    st.write("**Error:**", str(viz_error))
                                    st.code(result['visualization_code'], language='python')
                        else:
                            st.info("No data to visualize")
                    else:
                        st.info("No data available for visualization")
                except Exception as e:
                    st.error(f"Visualization error: {str(e)}")
            else:
                st.info("No visualization generated for this query")
            
            # SQL Query
            with st.expander("🔍 View SQL Query", expanded=False):
                st.code(result.get('sql', ''), language='sql')
            
            # Raw data
            with st.expander("📄 View Raw Data", expanded=False):
                data_summary = result.get('data_summary', {})
                if 'data' in data_summary and data_summary['data']:
                    df = pd.DataFrame(data_summary['data'])
                    st.dataframe(df, use_container_width=True)
                    
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
            with st.expander("Error Details"):
                st.code(e.response.text)
        except Exception as e:
            st.error(f"❌ Unexpected error: {str(e)}")

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    Built with LangGraph 🦜 | Powered by Groq ⚡ | Visualized with Plotly 📊
</div>
""", unsafe_allow_html=True)