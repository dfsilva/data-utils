import streamlit as st

st.set_page_config(
    page_title="Data Utils Tool",
    page_icon="🔧"
)

st.logo("src/logo.png")

# Define your pages with better icons
p1 = st.Page(
    "duplicates_for_one_file.py",
    title="Check Duplicates",
    icon="🗂️"  # Folder icon to represent file operations
)

p2 = st.Page(
    "duplicates_across_files.py",
    title="Check Duplicates Across Files",
    icon="🔍"  # Magnifying glass to represent search or inspection
)

p3 = st.Page(
    "compare_across_files.py",
    title="Compare CSV Files",
    icon="📊"  # Bar chart to represent comparison or analytics
)

p4 = st.Page(
    "query_files.py",
    title="SQL Query Files",
    icon="🧮"  # Abacus to represent SQL queries and calculations
)

pg = st.navigation([p1, p2, p3, p4])
pg.run()