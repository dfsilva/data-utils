import streamlit as st
import pandas as pd
import duckdb
import json
from datetime import datetime
import time

try:
    from code_editor import code_editor
    HAS_CODE_EDITOR = True
except ImportError:
    HAS_CODE_EDITOR = False

try:
    from streamlit_js_eval import streamlit_js_eval
    HAS_JS_EVAL = True
except ImportError:
    HAS_JS_EVAL = False

# Initialize DuckDB connection
con = duckdb.connect()

# Initialize session state for query history if not exists
if 'query_history' not in st.session_state:
    st.session_state.query_history = []

# Query history management functions
def load_query_history():
    """Load query history from session state"""
    # Using session state only to avoid infinite loops with streamlit-js-eval
    # History persists during the session but not across browser restarts
    return st.session_state.query_history

def save_query_history(history):
    """Save query history to localStorage and session state"""
    # Always save to session state
    st.session_state.query_history = history

    # Note: localStorage sync is disabled to prevent infinite loops
    # History will persist during the session but not across browser restarts
    # To enable localStorage, uncomment the code below and ensure streamlit-js-eval
    # doesn't cause reruns in your environment

    # if not HAS_JS_EVAL:
    #     return

    # try:
    #     # Save to localStorage
    #     history_json = json.dumps(history)
    #     streamlit_js_eval(
    #         js_expressions=f'localStorage.setItem("sql_query_history", {json.dumps(history_json)})',
    #         key=f"save_history_{datetime.now().timestamp()}"
    #     )
    # except Exception as e:
    #     pass

def add_query_to_history(query, success, error_msg=None, rows_returned=None):
    """Add a query to the history with metadata"""
    # Get current history
    history = st.session_state.query_history.copy() if st.session_state.query_history else []

    # Create history entry
    entry = {
        'query': query.strip(),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'success': success,
        'error_msg': error_msg,
        'rows_returned': rows_returned
    }

    # Add to beginning of list
    history.insert(0, entry)

    # Keep only last 50 queries
    history = history[:50]

    # Save back to session state
    save_query_history(history)

def clear_query_history():
    """Clear all query history"""
    # Clear session state
    st.session_state.query_history = []

def export_query_history_to_sql():
    """Export query history to SQL format"""
    history = st.session_state.query_history
    sql_content = "-- SQL Query History Export\n"
    sql_content += f"-- Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    sql_content += f"-- Total queries: {len(history)}\n"
    sql_content += "--" + "="*70 + "\n\n"

    for idx, entry in enumerate(history, 1):
        sql_content += f"-- Query #{idx}\n"
        sql_content += f"-- Timestamp: {entry['timestamp']}\n"
        sql_content += f"-- Status: {'SUCCESS' if entry['success'] else 'FAILED'}\n"

        if entry['success'] and entry.get('rows_returned') is not None:
            sql_content += f"-- Rows returned: {entry['rows_returned']:,}\n"

        if not entry['success'] and entry.get('error_msg'):
            sql_content += f"-- Error: {entry['error_msg']}\n"

        sql_content += "--" + "-"*70 + "\n"
        sql_content += entry['query'].strip() + ";\n\n"
        sql_content += "--" + "="*70 + "\n\n"

    return sql_content

st.title("🧮 SQL Query Builder")
st.markdown("""
Upload CSV files and query them using SQL. All files are combined into a single table with a `source_file` column.
Perfect for advanced data analysis and filtering using the full power of SQL.
""")

st.divider()

# Step 1: Upload multiple CSV files
st.subheader("📤 Upload Files")
st.caption("Upload one or more CSV files to query with SQL")

uploaded_files = st.file_uploader(
    "Select CSV files",
    accept_multiple_files=True,
    type="csv",
    help="All files will be combined into a single queryable table"
)

if uploaded_files:
    combined_df = pd.DataFrame()
    total_rows = 0

    with st.spinner("Loading and combining files..."):
        for file in uploaded_files:
            df = pd.read_csv(file)
            df['source_file'] = file.name
            combined_df = pd.concat([combined_df, df], ignore_index=True)
            total_rows += len(df)

    # Register the combined DataFrame as a table in DuckDB
    con.register('files', combined_df)

    # Show summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Files Loaded", len(uploaded_files))
    with col2:
        st.metric("Total Rows", f"{total_rows:,}")
    with col3:
        st.metric("Total Columns", len(combined_df.columns))

    st.success(f"✅ All files loaded into DuckDB table: **'files'**")

    # Data preview section
    with st.expander("👀 Data Preview (First 5 Rows)", expanded=False):
        preview_df = combined_df.head(5)
        st.dataframe(preview_df, width='stretch', hide_index=True)
        st.caption(f"Showing 5 of {len(combined_df):,} total rows")

    # Show available columns in a more user-friendly way
    st.subheader("📋 Available Columns")
    st.caption("Click on any column name to copy it")

    # Group columns for better display (3 columns layout)
    cols_per_row = 3
    columns_list = [col for col in combined_df.columns.tolist() if col != 'source_file']

    # Display columns in a grid
    for i in range(0, len(columns_list), cols_per_row):
        cols = st.columns(cols_per_row)
        for idx, col_name in enumerate(columns_list[i:i+cols_per_row]):
            with cols[idx]:
                st.code(col_name, language=None)

    # Show source_file column separately
    st.caption("**System column:** `source_file` (automatically added to track file origin)")

    # Show file list and table structure
    col_a, col_b = st.columns(2)

    with col_a:
        with st.expander("📁 Uploaded Files Details", expanded=False):
            for file in uploaded_files:
                file_rows = len([df for df in [combined_df[combined_df['source_file'] == file.name]]][0])
                st.markdown(f"- **{file.name}** ({file_rows:,} rows)")

    with col_b:
        with st.expander("🔍 Table Structure & Data Types", expanded=False):
            structure_df = con.execute("DESCRIBE files").fetchdf()
            st.dataframe(structure_df, width='stretch', hide_index=True)

    st.divider()

    # Recent successful queries quick access
    history = load_query_history()
    recent_successful = [q for q in history if q['success']][:5]

    if recent_successful:
        st.subheader("⚡ Recent Successful Queries")
        st.caption("Quick access to your recently executed queries")

        for idx, query_entry in enumerate(recent_successful):
            col1, col2 = st.columns([4, 1])
            with col1:
                # Truncate query for display
                query_preview = query_entry['query'][:80] + "..." if len(query_entry['query']) > 80 else query_entry['query']
                st.caption(f"`{query_preview}`")
            with col2:
                if st.button(f"▶️ Run", key=f"rerun_{idx}", width='stretch'):
                    st.session_state['loaded_query'] = query_entry['query']
                    st.session_state['auto_run_query'] = True
                    st.rerun()

        st.divider()

    # Step 2: Query input
    st.subheader("💻 Write SQL Query")

    # Add option to load SQL file
    col_caption, col_upload = st.columns([3, 1])
    with col_caption:
        st.caption("Query the 'files' table using SQL. Use autocomplete (Ctrl+Space) for suggestions.")
    with col_upload:
        uploaded_sql = st.file_uploader(
            "📂 Load .sql file",
            type=["sql", "txt"],
            key="sql_uploader",
            help="Upload a .sql or .txt file to load into the editor",
            label_visibility="visible"
        )

        # Process uploaded file only once
        if uploaded_sql is not None:
            # Create a unique identifier for this upload
            upload_id = f"{uploaded_sql.name}_{uploaded_sql.size}"
            last_upload_id = st.session_state.get('last_sql_upload_id', None)

            # Only process if this is a new upload
            if upload_id != last_upload_id:
                try:
                    sql_content = uploaded_sql.read().decode('utf-8')
                    st.session_state['loaded_query'] = sql_content
                    st.session_state['loaded_query_filename'] = uploaded_sql.name
                    st.session_state['last_sql_upload_id'] = upload_id
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error reading file: {str(e)}")

    # Quick query buttons for common operations
    st.markdown("**🚀 Quick Queries:**")
    qcol1, qcol2, qcol3, qcol4 = st.columns(4)

    with qcol1:
        if st.button("📋 Preview All Data", width='stretch'):
            st.session_state['loaded_query'] = "SELECT * FROM files LIMIT 100"
            st.rerun()

    with qcol2:
        if st.button("📊 Count Rows by File", width='stretch'):
            st.session_state['loaded_query'] = "SELECT source_file, COUNT(*) as row_count\nFROM files\nGROUP BY source_file\nORDER BY row_count DESC"
            st.rerun()

    with qcol3:
        if st.button("📁 List Files", width='stretch'):
            st.session_state['loaded_query'] = "SELECT DISTINCT source_file FROM files"
            st.rerun()

    with qcol4:
        if st.button("🔢 Count Total Rows", width='stretch'):
            st.session_state['loaded_query'] = "SELECT COUNT(*) as total_rows FROM files"
            st.rerun()

    st.markdown("")  # Add spacing

    # Sample queries in tabs for better organization
    with st.expander("📝 More Example Queries", expanded=False):
        tab1, tab2, tab3, tab4 = st.tabs(["Basic", "Filtering", "Aggregation", "Advanced"])

        with tab1:
            st.code("SELECT * FROM files LIMIT 10", language="sql")
            st.caption("Retrieve first 10 rows")

            st.code("SELECT DISTINCT source_file FROM files", language="sql")
            st.caption("List all source files")

        with tab2:
            st.code("SELECT * FROM files WHERE source_file = 'your_file.csv'", language="sql")
            st.caption("Filter by specific file")

            st.code("SELECT * FROM files WHERE column_name LIKE '%search_term%'", language="sql")
            st.caption("Search for text in a column")

        with tab3:
            st.code("SELECT COUNT(*) as total_rows FROM files", language="sql")
            st.caption("Count total rows")

            st.code("SELECT source_file, COUNT(*) as row_count\nFROM files\nGROUP BY source_file", language="sql")
            st.caption("Count rows per file")

        with tab4:
            st.code("SELECT source_file, column_name, COUNT(*) as occurrences\nFROM files\nGROUP BY source_file, column_name\nORDER BY occurrences DESC", language="sql")
            st.caption("Find most common values by file")

    # Use code editor if available, otherwise fallback to text_area
    # Initialize editor_key counter if not exists
    if 'editor_key_counter' not in st.session_state:
        st.session_state.editor_key_counter = 0

    # Initialize current query in session state if not exists
    if 'current_editor_query' not in st.session_state:
        st.session_state.current_editor_query = "SELECT * FROM files LIMIT 10"

    # Check if a query was loaded from history or quick queries
    query_was_loaded = False
    auto_run = st.session_state.get('auto_run_query', False)
    loaded_filename = None

    if 'loaded_query' in st.session_state:
        # New query loaded - update the editor
        st.session_state.current_editor_query = st.session_state['loaded_query']
        query_was_loaded = True

        # Check if this was from a file upload
        if 'loaded_query_filename' in st.session_state:
            loaded_filename = st.session_state['loaded_query_filename']
            del st.session_state['loaded_query_filename']

        del st.session_state['loaded_query']
        # Increment key to force editor refresh with new query
        st.session_state.editor_key_counter += 1

    default_query = st.session_state.current_editor_query

    if query_was_loaded:
        if loaded_filename:
            st.success(f"✅ Loaded query from {loaded_filename}")
            # Show preview of loaded query
            with st.expander("📄 Preview of loaded query", expanded=False):
                st.code(default_query[:200] + "..." if len(default_query) > 200 else default_query, language="sql")
        else:
            st.success("✅ Query loaded!")

    # Clear the auto_run flag immediately to prevent repeated execution
    if auto_run and 'auto_run_query' in st.session_state:
        del st.session_state['auto_run_query']

    # Try to use code editor, fallback to text area if it fails
    use_code_editor = HAS_CODE_EDITOR
    editor_error = False

    if use_code_editor:
        try:
            # Configure code editor with SQL autocomplete
            editor_buttons = [{
                "name": "Run Query",
                "feather": "Play",
                "primary": True,
                "hasText": True,
                "showWithIcon": True,
                "commands": ["submit"],
                "style": {"bottom": "0.44rem", "right": "0.4rem"}
            }]

            # Get column names for autocomplete
            column_completions = [{"caption": col, "value": col, "meta": "column"}
                                 for col in combined_df.columns.tolist()]

            # SQL keywords for autocomplete
            sql_keywords = [
                {"caption": "SELECT", "value": "SELECT", "meta": "keyword"},
                {"caption": "FROM", "value": "FROM", "meta": "keyword"},
                {"caption": "WHERE", "value": "WHERE", "meta": "keyword"},
                {"caption": "GROUP BY", "value": "GROUP BY", "meta": "keyword"},
                {"caption": "ORDER BY", "value": "ORDER BY", "meta": "keyword"},
                {"caption": "HAVING", "value": "HAVING", "meta": "keyword"},
                {"caption": "LIMIT", "value": "LIMIT", "meta": "keyword"},
                {"caption": "OFFSET", "value": "OFFSET", "meta": "keyword"},
                {"caption": "JOIN", "value": "JOIN", "meta": "keyword"},
                {"caption": "LEFT JOIN", "value": "LEFT JOIN", "meta": "keyword"},
                {"caption": "INNER JOIN", "value": "INNER JOIN", "meta": "keyword"},
                {"caption": "COUNT", "value": "COUNT", "meta": "function"},
                {"caption": "SUM", "value": "SUM", "meta": "function"},
                {"caption": "AVG", "value": "AVG", "meta": "function"},
                {"caption": "MIN", "value": "MIN", "meta": "function"},
                {"caption": "MAX", "value": "MAX", "meta": "function"},
                {"caption": "DISTINCT", "value": "DISTINCT", "meta": "keyword"},
                {"caption": "AS", "value": "AS", "meta": "keyword"},
                {"caption": "AND", "value": "AND", "meta": "operator"},
                {"caption": "OR", "value": "OR", "meta": "operator"},
                {"caption": "LIKE", "value": "LIKE", "meta": "operator"},
                {"caption": "IN", "value": "IN", "meta": "operator"},
                {"caption": "files", "value": "files", "meta": "table"}
            ]

            completions = sql_keywords + column_completions

            # Use a unique key to force refresh only when loading a new query
            editor_key = f"sql_editor_{st.session_state.editor_key_counter}"

            response_dict = code_editor(
                code=default_query,
                lang="sql",
                height=[10, 20],
                theme="contrast",
                shortcuts="vscode",
                focus=False,
                buttons=editor_buttons,
                completions=completions,
                options={"enableBasicAutocompletion": True,
                        "enableLiveAutocompletion": True,
                        "enableSnippets": True,
                        "showLineNumbers": True,
                        "tabSize": 2,
                        "readOnly": False},
                key=editor_key
            )

            # Handle editor response safely
            if response_dict and isinstance(response_dict, dict):
                # Get text from editor, fallback to default if empty
                query_text = response_dict.get('text', '')
                query = query_text if query_text else default_query
                run_query = response_dict.get('type') == 'submit'
            else:
                # If no response, use the default query
                query = default_query
                run_query = False

            # Ensure query is never None or empty
            if not query:
                query = default_query

        except Exception as e:
            # Code editor failed, fall back to text area
            st.warning(f"⚠️ Code editor encountered an error. Using simple text editor instead.")
            editor_error = True
            use_code_editor = False

    if not use_code_editor or editor_error:
        # Fallback to text_area if code_editor is not available or has error
        if not HAS_CODE_EDITOR:
            st.warning("💡 Install `streamlit-code-editor` for enhanced SQL editing with autocomplete: `pip install streamlit-code-editor`")

        query = st.text_area(
            "Enter your SQL query",
            value=default_query,
            height=150,
            help="Write your SQL query here",
            key=f"sql_textarea_{st.session_state.editor_key_counter}"
        )
        run_query = st.button("▶️ Run Query", type="primary")

    # Execute query (either manually or auto-run from quick queries)
    if (run_query or auto_run) and query:
        st.divider()

        try:
            # Track execution time
            start_time = time.time()

            with st.spinner("Executing query..."):
                # Execute the query using DuckDB
                result_df = con.execute(query).fetchdf()

            execution_time = time.time() - start_time

            # Save successful query to history
            add_query_to_history(query, success=True, rows_returned=len(result_df))

            # Display the result
            st.success(f"✅ Query executed successfully in {execution_time:.3f}s! Returned {len(result_df):,} row(s)")

            # Show result metrics
            if len(result_df) > 0:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Rows Returned", f"{len(result_df):,}")
                with col2:
                    st.metric("Columns", len(result_df.columns))
                with col3:
                    st.metric("Execution Time", f"{execution_time:.3f}s")

            st.subheader("📊 Query Results")

            if len(result_df) > 0:
                # Show dataframe with better options
                st.dataframe(result_df, width='stretch', hide_index=True)

                # Download and column info in columns
                col_download, col_info = st.columns([1, 1])

                with col_download:
                    csv_export = result_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Results as CSV",
                        data=csv_export,
                        file_name="query_results.csv",
                        mime="text/csv",
                        width='stretch'
                    )

                with col_info:
                    with st.expander("📋 Result Columns Info"):
                        for col in result_df.columns:
                            dtype = result_df[col].dtype
                            st.caption(f"**{col}**: `{dtype}`")
            else:
                st.info("✨ Query executed successfully but returned no results")

        except Exception as e:
            error_msg = str(e)

            # Save failed query to history
            add_query_to_history(query, success=False, error_msg=error_msg)

            st.error(f"❌ Query Error")

            # Show the actual error in an expander
            with st.expander("🔍 Error Details", expanded=True):
                st.code(error_msg, language=None)

            with st.expander("💡 Common Solutions & Tips"):
                st.markdown("""
                ### Common Fixes:
                - **Column name errors**: Check spelling and case sensitivity
                - **Table name**: Make sure you're querying the `files` table
                - **SQL syntax**: Look for missing commas, unclosed quotes, or parentheses
                - **Data types**: Use quotes around text values: `WHERE column = 'value'`
                - **Aggregations**: Remember to include all non-aggregated columns in GROUP BY

                ### Quick Checks:
                1. Review the **Available Columns** section above
                2. Check the **Table Structure & Data Types** expander
                3. Try one of the **Example Queries** to verify your connection
                4. Use **Quick Queries** buttons to test basic operations
                """)

    # Full Query History Section (shown after query execution)
    st.divider()

    full_history = load_query_history()

    # Always show the history section
    expander_title = f"📜 Full Query History ({len(full_history)} queries)" if full_history else "📜 Full Query History (Empty)"
    with st.expander(expander_title, expanded=False):
        st.caption("📝 Your recent SQL queries are saved during this session (history will be lost on refresh)")

        # Export section
        if full_history:
            st.markdown("**💾 Export Query History**")
            # Export history as SQL
            history_sql = export_query_history_to_sql()
            st.download_button(
                label="📥 Download All Queries as SQL",
                data=history_sql,
                file_name=f"query_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql",
                mime="text/plain",
                width='stretch',
                help="Download all your queries as a single SQL file with comments"
            )
            st.caption(f"💡 Export {len(full_history)} queries to a single .sql file")
            st.divider()
        else:
            st.info("💡 Run some queries to build history that you can export")
            st.divider()

        if full_history:
            # Control buttons
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                search_term = st.text_input(
                    "🔍 Search history",
                    placeholder="Filter queries...",
                    key="history_search",
                    label_visibility="collapsed"
                )
            with col2:
                show_only_successful = st.checkbox("✅ Only successful", key="filter_successful")
            with col3:
                if st.button("🗑️ Clear All", type="secondary", width='stretch'):
                    clear_query_history()
                    st.rerun()

            # Filter history based on search and success filter
            filtered_history = full_history
            if search_term:
                filtered_history = [
                    h for h in filtered_history
                    if search_term.lower() in h['query'].lower()
                ]
            if show_only_successful:
                filtered_history = [h for h in filtered_history if h['success']]

            if filtered_history:
                st.caption(f"📊 Showing {len(filtered_history)} of {len(full_history)} queries")
                st.divider()

                # Display each query in history with improved layout
                for idx, entry in enumerate(filtered_history):
                    status_icon = "✅" if entry['success'] else "❌"
                    timestamp = entry['timestamp']

                    # Header with timestamp and status
                    col_time, col_stat, col_action1, col_action2 = st.columns([3, 2, 1, 1])
                    with col_time:
                        st.caption(f"🕐 {timestamp}")
                    with col_stat:
                        if entry['success'] and entry.get('rows_returned') is not None:
                            st.caption(f"{status_icon} {entry['rows_returned']:,} rows")
                        else:
                            st.caption(f"{status_icon} Failed")
                    with col_action1:
                        if st.button(
                            "↻ Rerun",
                            key=f"load_query_{idx}",
                            width='stretch'
                        ):
                            st.session_state['loaded_query'] = entry['query']
                            st.session_state['auto_run_query'] = True
                            st.rerun()
                    with col_action2:
                        # Download individual query as .sql file
                        query_filename = f"query_{timestamp.replace(':', '-').replace(' ', '_')}.sql"
                        st.download_button(
                            label="💾",
                            data=entry['query'],
                            file_name=query_filename,
                            mime="text/plain",
                            key=f"download_query_{idx}",
                            width='stretch',
                            help="Download this query as .sql file"
                        )

                    # Display query in code block
                    st.code(entry['query'], language="sql")

                    # Show error if failed
                    if not entry['success'] and entry.get('error_msg'):
                        with st.expander("❌ Error Details"):
                            st.caption(entry['error_msg'])

                    if idx < len(filtered_history) - 1:
                        st.divider()
            else:
                st.info("🔍 No queries match your search criteria")
        else:
            st.info("📝 No queries in history yet. Run a query above to start building your history!")

else:
    st.info("👆 Upload CSV files above to start querying with SQL")

    # Show helpful information when no files uploaded
    with st.expander("ℹ️ How to Use SQL Query Builder", expanded=True):
        st.markdown("""
        ### Getting Started
        1. **Upload Files**: Upload one or more CSV files
        2. **Write Query**: Use SQL to query the combined data in the 'files' table
        3. **Run Query**: Execute your query and view results
        4. **Download**: Export results as CSV

        ### Key Features
        - ✅ All files are combined into a single table called `files`
        - ✅ Each row includes a `source_file` column showing which file it came from
        - ✅ SQL autocomplete for keywords, functions, and column names
        - ✅ Example queries provided for common scenarios
        - ✅ Download query results as CSV
        - ✅ Save and load queries as .sql files
        - ✅ Export query history as a single SQL file
        - ✅ Quick query buttons for common operations

        ### SQL Tips
        - Use `SELECT * FROM files LIMIT 10` to preview data
        - Filter by file: `WHERE source_file = 'filename.csv'`
        - Count rows: `SELECT COUNT(*) FROM files`
        - Group data: `GROUP BY column_name`

        ### Save & Load Queries
        - **Save current query**: Use the "💾 Save Query" button below the editor
        - **Load SQL file**: Use the "📂 Load .sql file" uploader to import queries
        - **Export history**: Download all your queries as a single .sql file with comments
        - **Individual queries**: Each query in history has a 💾 button to download separately
        """)
