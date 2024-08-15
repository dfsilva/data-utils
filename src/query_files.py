import streamlit as st
import pandas as pd
import duckdb
from io import StringIO

def app():
   # Initialize DuckDB connection
    con = duckdb.connect()

    st.title("CSV File Uploader and Query with SQL")

    # Step 1: Upload multiple CSV files
    uploaded_files = st.file_uploader("Upload CSV files", accept_multiple_files=True, type="csv")

    if uploaded_files:
        combined_df = pd.DataFrame()  # Initialize an empty DataFrame
        
        for file in uploaded_files:
            # Read each CSV file into a DataFrame
            df = pd.read_csv(file)
            
            # Add a column with the file name
            df['source_file'] = file.name
            
            # Combine into a single DataFrame
            combined_df = pd.concat([combined_df, df], ignore_index=True)
            
            st.write(f"File '{file.name}' loaded and combined into the table.")

        # Register the combined DataFrame as a table in DuckDB
        con.register('files', combined_df)
        st.write("All files loaded into DuckDB as a single table 'files'")

    # Step 2: Query input
    if uploaded_files:
        query = st.text_area("Enter your SQL query")

        if st.button("Run Query"):
            try:
                # Execute the query using DuckDB
                result_df = con.execute(query).fetchdf()
                
                # Display the result
                st.write("Query Result:")
                st.dataframe(result_df)
            except Exception as e:
                st.error(f"An error occurred: {e}")

    # Optional: Show the table structure
    if st.checkbox("Show table structure"):
        st.write("Combined Table Structure:")
        st.dataframe(con.execute("DESCRIBE files").fetchdf())