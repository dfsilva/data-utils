import streamlit as st

st.set_page_config(
    page_title="Data Utils - CSV Analysis Tools",
    page_icon="🔧",
    initial_sidebar_state="expanded",
    layout="wide"
)

st.logo("src/logo.png")

# Define pages organized by category
duplicate_tools = [
    st.Page(
        "duplicates_for_one_file.py",
        title="Compare Against Primary File",
        icon="🗂️"
    ),
    st.Page(
        "duplicates_across_files.py",
        title="Find Duplicates Across Files",
        icon="🔍"
    ),
    st.Page(
        "duplicate_report_by_column.py",
        title="Duplicate Analysis Report",
        icon="📋"
    ),
]

analysis_tools = [
    st.Page(
        "compare_across_files.py",
        title="Compare Files (Unique Rows)",
        icon="📊"
    ),
    st.Page(
        "query_files.py",
        title="SQL Query Builder",
        icon="🧮"
    ),
]

pg = st.navigation(
    {
        "🔍 Duplicate Detection": duplicate_tools,
        "📊 Data Analysis": analysis_tools,
    },
    position="sidebar"
)
pg.run()