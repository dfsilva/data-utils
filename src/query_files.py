import streamlit as st
import pandas as pd
import duckdb

try:
    from code_editor import code_editor
    HAS_CODE_EDITOR = True
except ImportError:
    HAS_CODE_EDITOR = False

# Initialize DuckDB connection
con = duckdb.connect()

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

    # Show available columns prominently
    st.info(f"**Available columns:** {', '.join([f'`{col}`' for col in combined_df.columns.tolist()])}")

    # Show file list and table structure
    col_a, col_b = st.columns(2)

    with col_a:
        with st.expander("📁 Uploaded Files", expanded=False):
            for file in uploaded_files:
                file_rows = len([df for df in [combined_df[combined_df['source_file'] == file.name]]][0])
                st.markdown(f"- **{file.name}** ({file_rows:,} rows)")

    with col_b:
        with st.expander("📋 Table Structure", expanded=False):
            structure_df = con.execute("DESCRIBE files").fetchdf()
            st.dataframe(structure_df, use_container_width=True, hide_index=True)

    st.divider()

    # Step 2: Query input
    st.subheader("💻 Write SQL Query")
    st.caption("Query the 'files' table using SQL. Use autocomplete (Ctrl+Space) for suggestions.")

    # Sample queries in tabs for better organization
    with st.expander("📝 Example Queries - Click to Copy", expanded=False):
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
    if HAS_CODE_EDITOR:
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

        response_dict = code_editor(
            code="SELECT * FROM files LIMIT 10",
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
                    "tabSize": 2}
        )

        query = response_dict['text'] if response_dict else ""
        run_query = response_dict.get('type') == 'submit' if response_dict else False
    else:
        # Fallback to text_area if code_editor is not available
        st.warning("💡 Install `streamlit-code-editor` for enhanced SQL editing with autocomplete: `pip install streamlit-code-editor`")
        query = st.text_area(
            "Enter your SQL query",
            value="SELECT * FROM files LIMIT 10",
            height=150,
            help="Write your SQL query here"
        )
        run_query = st.button("▶️ Run Query", type="primary")

    if run_query and query:
        st.divider()

        try:
            with st.spinner("Executing query..."):
                # Execute the query using DuckDB
                result_df = con.execute(query).fetchdf()

            # Display the result
            st.success(f"✅ Query executed successfully! Returned {len(result_df):,} row(s)")

            # Show result metrics
            if len(result_df) > 0:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Rows Returned", f"{len(result_df):,}")
                with col2:
                    st.metric("Columns", len(result_df.columns))

            st.subheader("📊 Query Results")
            st.dataframe(result_df, use_container_width=True)

            if len(result_df) > 0:
                # Download option
                csv_export = result_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Results as CSV",
                    data=csv_export,
                    file_name="query_results.csv",
                    mime="text/csv"
                )
            else:
                st.info("Query returned no results")

        except Exception as e:
            st.error(f"❌ Query Error: {str(e)}")
            with st.expander("💡 Tips for Fixing Query Errors"):
                st.markdown("""
                - Check that column names are spelled correctly and match case
                - Ensure the table name is `files`
                - Verify SQL syntax (missing commas, unclosed quotes, etc.)
                - Use quotes around text values: `WHERE column = 'value'`
                - Check the table structure in the expander above
                """)

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

        ### SQL Tips
        - Use `SELECT * FROM files LIMIT 10` to preview data
        - Filter by file: `WHERE source_file = 'filename.csv'`
        - Count rows: `SELECT COUNT(*) FROM files`
        - Group data: `GROUP BY column_name`
        """)
