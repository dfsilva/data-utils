import streamlit as st
import pandas as pd

def app():
    pd.set_option("styler.render.max_elements", 1451815)
    
    st.title("File Comparison Based on Selected Columns")
    
    st.header("Upload Files to Compare")
    multiple_csv_files = st.file_uploader("Upload CSV files to compare", type=["csv"], accept_multiple_files=True)

    if multiple_csv_files:
        # Initialize a dictionary to store DataFrames
        file_dfs = {}

        for csv_file in multiple_csv_files:
            df = pd.read_csv(csv_file)
            file_dfs[csv_file.name] = df

            # Display the content of each file along with the row count
            st.subheader(f"Content of {csv_file.name} (Total Rows: {len(df)})")
            st.write(df)
        
        # Ask the user to select columns for comparison
        combined_df = pd.concat(file_dfs.values(), ignore_index=True)
        columns = combined_df.columns.tolist()

        st.subheader("Select Columns to Compare")
        selected_columns = st.multiselect("Choose columns to compare", columns)

        if selected_columns:
            st.subheader("Rows Present in One File But Not in Others")

            # Find the unique rows for each file based on selected columns
            for file_name, df in file_dfs.items():
                df_subset = df[selected_columns].drop_duplicates()
                other_dfs = [file_dfs[other_file][selected_columns].drop_duplicates() 
                             for other_file in file_dfs if other_file != file_name]
                
                combined_other_df = pd.concat(other_dfs).drop_duplicates()
                
                # Identify rows in the current file that are not in the combined set of other files
                diff_df = df_subset.merge(combined_other_df, on=selected_columns, how='left', indicator=True)
                unique_rows = df[df[selected_columns].isin(diff_df[diff_df['_merge'] == 'left_only'][selected_columns].to_dict('list')).all(axis=1)]

                unique_count = len(unique_rows)

                if unique_count > 0:
                    st.subheader(f"{unique_count} Unique Rows in {file_name}")
                    st.write(unique_rows)
                else:
                    st.write(f"No unique rows found in {file_name} based on selected columns.")
        else:
            st.write("Please select columns to compare.")