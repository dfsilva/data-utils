import streamlit as st
import pandas as pd

pd.set_option("styler.render.max_elements", 1451815)

st.title("📊 Compare Files (Unique Rows)")
st.markdown("""
Compare multiple CSV files to identify unique rows that exist in one file but not in others.
This tool helps you find data discrepancies between datasets.
""")

st.divider()

st.subheader("📤 Upload Files to Compare")
st.caption("Upload 2 or more CSV files to analyze")

multiple_csv_files = st.file_uploader(
    "Select CSV files",
    type=["csv"],
    accept_multiple_files=True,
    help="Upload files you want to compare for unique entries"
)

if multiple_csv_files:
    if len(multiple_csv_files) < 2:
        st.warning("⚠️ Please upload at least 2 files to compare")
    else:
        # Initialize a dictionary to store DataFrames
        file_dfs = {}
        total_rows = 0

        with st.spinner("Loading files..."):
            for csv_file in multiple_csv_files:
                df = pd.read_csv(csv_file)
                file_dfs[csv_file.name] = df
                total_rows += len(df)

        # Show summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Files Uploaded", len(multiple_csv_files))
        with col2:
            st.metric("Total Rows", f"{total_rows:,}")
        with col3:
            # Get all unique columns across files
            all_columns = set()
            for df in file_dfs.values():
                all_columns.update(df.columns)
            st.metric("Unique Columns", len(all_columns))

        # Display file previews in expander
        with st.expander("👁️ Preview Uploaded Files", expanded=False):
            for file_name, df in file_dfs.items():
                st.markdown(f"**{file_name}** ({len(df):,} rows, {len(df.columns)} columns)")
                st.dataframe(df.head(10), use_container_width=True)
                st.divider()

        st.divider()

        # Ask the user to select columns for comparison
        combined_df = pd.concat(file_dfs.values(), ignore_index=True)
        columns = combined_df.columns.tolist()

        st.subheader("🎯 Select Comparison Columns")
        st.caption("Choose which columns to use for finding unique rows")

        selected_columns = st.multiselect(
            "Columns to compare",
            columns,
            help="Rows will be considered unique if the combination of these columns doesn't exist in other files"
        )

        if selected_columns:
            st.divider()
            st.subheader("📊 Unique Rows Analysis")
            st.caption("Shows rows present in one file but not in others")

            # Track if any unique rows were found
            found_any_unique = False

            # Find the unique rows for each file based on selected columns
            for file_name, df in file_dfs.items():
                with st.spinner(f"Analyzing {file_name}..."):
                    df_subset = df[selected_columns].drop_duplicates()
                    other_dfs = [
                        file_dfs[other_file][selected_columns].drop_duplicates()
                        for other_file in file_dfs if other_file != file_name
                    ]

                    combined_other_df = pd.concat(other_dfs).drop_duplicates()

                    # Identify rows in the current file that are not in the combined set of other files
                    diff_df = df_subset.merge(
                        combined_other_df,
                        on=selected_columns,
                        how='left',
                        indicator=True
                    )
                    unique_rows = df[
                        df[selected_columns].isin(
                            diff_df[diff_df['_merge'] == 'left_only'][selected_columns].to_dict('list')
                        ).all(axis=1)
                    ]

                    unique_count = len(unique_rows)

                    if unique_count > 0:
                        found_any_unique = True
                        with st.expander(f"📄 {file_name} - {unique_count:,} unique row(s)", expanded=True):
                            st.info(f"These {unique_count:,} rows exist in **{file_name}** but not in any other uploaded file.")
                            st.dataframe(unique_rows, use_container_width=True, hide_index=True)

                            # Download option
                            csv_unique = unique_rows.to_csv(index=False)
                            st.download_button(
                                label=f"📥 Download Unique Rows from {file_name}",
                                data=csv_unique,
                                file_name=f"unique_rows_{file_name}",
                                mime="text/csv",
                                key=f"download_{file_name}"
                            )
                    else:
                        with st.expander(f"✅ {file_name} - No unique rows", expanded=False):
                            st.success(f"All rows in **{file_name}** also exist in other files (based on selected columns).")

            if not found_any_unique:
                st.success("✅ No unique rows found! All rows exist across multiple files (based on selected columns).")

        else:
            st.info("👆 Select at least one column to compare")
else:
    st.info("👆 Upload CSV files above to get started")
