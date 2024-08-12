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
                # Create a global filter field for all source files
                global_filters = {}
                for col in selected_columns:
                    global_filters[col] = st.text_input(f"Global Filter for {col} across all source files", "")
                
                for csv_file in multiple_csv_files:
                    df = pd.read_csv(csv_file)
                    df['source_file'] = csv_file.name  # Add a column to track the source file
                    
                    # Apply global filter fields to each file
                    filtered_df = df.copy()
                    for col in selected_columns:
                        filter_value = global_filters[col]
                        if filter_value:
                            filtered_df = filtered_df[filtered_df[col].astype(str).str.contains(filter_value, na=False, case=False)]

                    # Display the filtered content of each file
                    st.subheader(f"Content of {csv_file.name} (Filtered by Selected Properties)")
                    st.write(filtered_df)
                    
                    duplicates = df.merge(single_df[selected_columns], on=selected_columns, how='inner')
                    if not duplicates.empty:
                        duplicate_rows = pd.concat([duplicate_rows, duplicates], ignore_index=True)

                if not duplicate_rows.empty:
                    # Count duplicates by selected properties
                    duplicate_counts = duplicate_rows.groupby(selected_columns).size().reset_index(name='Duplicate Count')
                    duplicate_counts_sorted = duplicate_counts.sort_values(by='Duplicate Count', ascending=False)

                    # Add filter fields for each property in the summary
                    filtered_summary_df = duplicate_counts_sorted.copy()
                    for col in selected_columns:
                        filter_value = st.text_input(f"Filter {col} (Summary)", "")
                        if filter_value:
                            filtered_summary_df = filtered_summary_df[filtered_summary_df[col].astype(str).str.contains(filter_value, na=False, case=False)]

                    st.subheader("Duplicate Counts by Selected Properties")
                    st.write(filtered_summary_df)

                    # Summary table by filename and property
                    st.subheader("Duplicate Counts by Filename and Selected Properties")
                    file_duplicate_counts = duplicate_rows.groupby(['source_file'] + selected_columns).size().reset_index(name='Duplicate Count')
                    file_duplicate_counts_sorted = file_duplicate_counts.sort_values(by=['source_file', 'Duplicate Count'], ascending=[True, False])

                    # Add filter fields for the filename and each property
                    filtered_file_df = file_duplicate_counts_sorted.copy()
                    filter_value_source = st.text_input("Filter source_file (Summary)", "")
                    if filter_value_source:
                        filtered_file_df = filtered_file_df[filtered_file_df['source_file'].astype(str).str.contains(filter_value_source, na=False, case=False)]

                    for col in selected_columns:
                        filter_value = st.text_input(f"Filter {col} (Per File Summary)", "")
                        if filter_value:
                            filtered_file_df = filtered_file_df[filtered_file_df[col].astype(str).str.contains(filter_value, na=False, case=False)]

                    st.write(filtered_file_df)
                else:
                    st.write("No duplicates found in the uploaded files.")
            else:
                st.subheader("Primary File")
                st.dataframe(single_df[selected_columns])