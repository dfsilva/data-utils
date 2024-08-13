import streamlit as st
import pandas as pd

def app():
    pd.set_option("styler.render.max_elements", 1451815)
    
    st.title("File Comparison Based on Selected Columns")
    
    st.header("Upload Files to Compare")
    multiple_csv_files = st.file_uploader("Upload CSV files to compare", type=["csv"], accept_multiple_files=True)

    if multiple_csv_files:
        # Initialize a list to store DataFrames without the global filter
        all_dfs = []

        for csv_file in multiple_csv_files:
            df = pd.read_csv(csv_file)
            df['source_file'] = csv_file.name  # Add a column to track the source file
            all_dfs.append(df)  # Store the unfiltered DataFrame for comparison

            # Apply the global filter to the view of the individual file if a filter value is provided
            display_df = df.copy()
            global_filter_value = st.text_input(f"Global Filter for {csv_file.name}", "")
            if global_filter_value:
                condition = pd.Series([True] * len(display_df))
                for col in display_df.columns:
                    if col in df.select_dtypes(include=['object', 'string']).columns:
                        condition &= display_df[col].astype(str).str.contains(global_filter_value, na=False, case=False)
                display_df = display_df[condition]

            # Display the content of each file after applying the global filter for view only
            st.subheader(f"Content of {csv_file.name} (Filtered View)")
            st.write(display_df)
        
        # Concatenate all files into a single DataFrame for comparison (without the global view filter)
        combined_df = pd.concat(all_dfs, ignore_index=True)
        
        # Update the columns list with the concatenated DataFrame's columns
        columns = combined_df.columns.tolist()

        st.subheader("Select Columns to Compare")
        selected_columns = st.multiselect("Choose columns to compare", columns)

        if selected_columns:
            # Apply the global filter again to the combined DataFrame based on selected columns
            if global_filter_value:
                condition = pd.Series([True] * len(combined_df))
                for col in selected_columns:
                    condition &= combined_df[col].astype(str).str.contains(global_filter_value, na=False, case=False)
                combined_df = combined_df[condition]

            # Find rows with the same values in the selected columns but different across files
            grouped = combined_df.groupby(selected_columns)

            differences = []
            for _, group in grouped:
                if len(group['source_file'].unique()) > 1:
                    differences.append(group)
            
            if differences:
                differences_df = pd.concat(differences)

                st.subheader("Differences Found Across Files")
                filtered_diff_df = differences_df.copy()

                # Add individual filter fields for each selected column
                for col in selected_columns:
                    filter_value = st.text_input(f"Filter {col}", "")
                    if filter_value:
                        filtered_diff_df = filtered_diff_df[filtered_diff_df[col].astype(str).str.contains(filter_value, na=False, case=False)]
                
                st.write(filtered_diff_df)

                # Prepare the summary table for differences per file
                file_diff_counts = differences_df.groupby(['source_file'] + selected_columns).size().reset_index(name='Difference Count')
                file_diff_counts_sorted = file_diff_counts.sort_values(by=['source_file', 'Difference Count'], ascending=[True, False])

                st.subheader("Summary of Differences Found Per File")
                filtered_file_diff_df = file_diff_counts_sorted.copy()

                # Apply the global filter to the summary table as well
                if global_filter_value:
                    condition = pd.Series([True] * len(filtered_file_diff_df))
                    for col in selected_columns:
                        condition &= filtered_file_diff_df[col].astype(str).str.contains(global_filter_value, na=False, case=False)
                    filtered_file_diff_df = filtered_file_diff_df[condition]

                # Add individual filter fields for the source file and each selected column in the per-file summary
                filter_value_source = st.text_input("Filter source_file", "")
                if filter_value_source:
                    filtered_file_diff_df = filtered_file_diff_df[filtered_file_diff_df['source_file'].astype(str).str.contains(filter_value_source, na=False, case=False)]
                
                for col in selected_columns:
                    filter_value = st.text_input(f"Filter {col} (Per File)", "")
                    if filter_value:
                        filtered_file_diff_df = filtered_file_diff_df[filtered_file_diff_df[col].astype(str).str.contains(filter_value, na=False, case=False)]

                st.write(filtered_file_diff_df)
            else:
                st.write("No differences found across the uploaded files.")
        else:
            st.write("Please select columns to compare.")

if __name__ == "__main__":
    app()