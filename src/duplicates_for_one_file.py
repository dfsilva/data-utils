import streamlit as st
import pandas as pd

def app():
    pd.set_option("styler.render.max_elements", 1451815)
    
    st.title("Duplicate Values Checker")
    st.header("Step 1: Upload the Primary File")
    single_csv_file = st.file_uploader("Upload a CSV file to check for duplicates", type=["csv"])
    selected_columns = []
    
    if single_csv_file is not None:
        single_df = pd.read_csv(single_csv_file)
        st.subheader("Preview of Primary File")
        selected_columns = st.multiselect("Choose columns to check for duplicates", single_df.columns.tolist(), default=single_df.columns.tolist())

        if selected_columns:
            st.subheader("Step 2: Upload Files for Duplicate Checking")
            multiple_csv_files = st.file_uploader("Upload one or more CSV files to check for duplicates", type=["csv"], accept_multiple_files=True)
            
            duplicate_rows = pd.DataFrame()
            if multiple_csv_files:
                for csv_file in multiple_csv_files:
                    df = pd.read_csv(csv_file)
                    duplicates = df.merge(single_df[selected_columns], on=selected_columns, how='inner')
                    if not duplicates.empty:
                        duplicate_rows = pd.concat([duplicate_rows, duplicates], ignore_index=True)
                        st.subheader(f"Duplicate Rows Found in {csv_file.name}")
                        st.write(duplicates)

                def highlight_rows(row):
                    is_duplicate = duplicate_rows[selected_columns].eq(row[selected_columns].values).all(axis=1).any()
                    return ['background-color: yellow' if is_duplicate else '' for _ in row.index]

                st.subheader("Highlighted Duplicates in Primary File")
                styled_df = single_df.style.apply(highlight_rows, axis=1)
                st.dataframe(styled_df)
            else:
                st.subheader("Primary File with No Duplicates Highlighted")
                st.dataframe(single_df[selected_columns])