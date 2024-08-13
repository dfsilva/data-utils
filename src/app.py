import streamlit as st
from duplicates_for_one_file import app as duplicates_one_file
from duplicates_across_files import app as duplicates_across_files
from compare_across_files import app as compare_across_files

PAGES = {
    "Check Duplicates": duplicates_one_file,
    "Check Duplicates Across Files": duplicates_across_files,
    "Compare CSV Files": compare_across_files
}

st.sidebar.title('Navigation')
selection = st.sidebar.radio("Go to", list(PAGES.keys()))

page = PAGES[selection]
page()