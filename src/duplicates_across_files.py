import streamlit as st
import pandas as pd

pd.set_option("styler.render.max_elements", 1451815)

st.title("Duplicate Values Checker Across Multiple Files")

st.header("Upload Files to Check for Duplicates")
multiple_csv_files = st.file_uploader("Upload CSV files to check for duplicates", type=["csv"], accept_multiple_files=True)

if multiple_csv_files:
    # Concatenate all files into a single DataFrame
    all_dfs = []
    for csv_file in multiple_csv_files:
        df = pd.read_csv(csv_file)
        df['source_file'] = csv_file.name  # Add a column to track the source file
        all_dfs.append(df)
        
        # Display the content of each file
        st.subheader(f"Content of {csv_file.name}")
        st.write(df)
    
    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    st.subheader("Select Columns to Check for Duplicates")
    selected_columns = st.multiselect("Choose columns to check for duplicates", combined_df.columns.tolist())
    
    if selected_columns:
        # Identify duplicates across all files
        duplicated_df = combined_df[combined_df.duplicated(subset=selected_columns, keep=False)]

        if not duplicated_df.empty:
            # Count duplicates and prepare the summary table for all files combined
            duplicate_counts = duplicated_df.groupby(selected_columns).size().reset_index(name='Duplicate Count')
            duplicate_counts_sorted = duplicate_counts.sort_values(by='Duplicate Count', ascending=False)
            
            st.subheader("Summary of Duplicates Found Across All Files")
            filtered_df = duplicate_counts_sorted.copy()

            # Add a filter field for each selected column
            for col in selected_columns:
                filter_value = st.text_input(f"Filter {col}", "")
                if filter_value:
                    filtered_df = filtered_df[filtered_df[col].astype(str).str.contains(filter_value, na=False, case=False)]
            
            st.write(filtered_df)

            # Prepare the summary table for each file
            file_duplicate_counts = duplicated_df.groupby(['source_file'] + selected_columns).size().reset_index(name='Duplicate Count')
            file_duplicate_counts_sorted = file_duplicate_counts.sort_values(by=['source_file', 'Duplicate Count'], ascending=[True, False])

            st.subheader("Summary of Duplicates Found Per File")
            filtered_file_df = file_duplicate_counts_sorted.copy()

            # Add a filter field for the source file and each selected column in the per-file summary
            filter_value_source = st.text_input("Filter source_file", "")
            if filter_value_source:
                filtered_file_df = filtered_file_df[filtered_file_df['source_file'].astype(str).str.contains(filter_value_source, na=False, case=False)]
            
            for col in selected_columns:
                filter_value = st.text_input(f"Filter {col} (Per File)", "")
                if filter_value:
                    filtered_file_df = filtered_file_df[filtered_file_df[col].astype(str).str.contains(filter_value, na=False, case=False)]

            st.write(filtered_file_df)
        else:
            st.write("No duplicates found across the uploaded files.")
    else:
        st.write("Please select columns to check for duplicates.")