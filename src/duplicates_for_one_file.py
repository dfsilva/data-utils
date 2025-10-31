import streamlit as st
import pandas as pd

pd.set_option("styler.render.max_elements", 1451815)

st.title("🗂️ Compare Against Primary File")
st.markdown("""
Compare a primary (reference) file against multiple other files to identify duplicate entries.
This tool is useful when you have a master dataset and want to check if any values appear in other files.
""")

st.divider()

# Step 1: Upload primary file
st.subheader("📤 Step 1: Upload Primary File")
st.caption("This is your reference file that will be compared against other files")

single_csv_file = st.file_uploader(
    "Upload your primary CSV file",
    type=["csv"],
    help="The primary file serves as your reference dataset",
    key="primary_file"
)
selected_columns = []

if single_csv_file is not None:
    single_df = pd.read_csv(single_csv_file)

    # Show file info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("File Name", single_csv_file.name)
    with col2:
        st.metric("Total Rows", f"{len(single_df):,}")
    with col3:
        st.metric("Total Columns", len(single_df.columns))

    # Preview in expander
    with st.expander("👁️ Preview Primary File Data", expanded=False):
        st.dataframe(single_df.head(20), use_container_width=True)

    st.divider()

    # Column selection
    st.subheader("🎯 Step 2: Select Comparison Columns")
    st.caption("Choose which columns to use for detecting duplicates")

    selected_columns = st.multiselect(
        "Columns to compare",
        single_df.columns.tolist(),
        default=single_df.columns.tolist(),
        help="Rows will be considered duplicates if ALL selected columns match"
    )

    if selected_columns:
        st.divider()
        st.subheader("📂 Step 3: Upload Files to Check")
        st.caption("Upload one or more files to compare against your primary file")

        multiple_csv_files = st.file_uploader(
            "Upload CSV files to check for duplicates",
            type=["csv"],
            accept_multiple_files=True,
            help="These files will be checked for rows that match your primary file",
            key="comparison_files"
        )
        
        duplicate_rows = pd.DataFrame()
        if multiple_csv_files:
            st.divider()

            # Optional global filters
            with st.expander("🔍 Apply Filters (Optional)", expanded=False):
                st.caption("Filter the data before displaying results")
                global_filters = {}
                filter_cols = st.columns(min(len(selected_columns), 3))
                for idx, col in enumerate(selected_columns):
                    with filter_cols[idx % len(filter_cols)]:
                        global_filters[col] = st.text_input(
                            f"Filter by {col}",
                            "",
                            key=f"global_filter_{col}",
                            help="Case-insensitive text search"
                        )

            # Process files
            st.subheader("📊 Results")

            with st.spinner("Analyzing files for duplicates..."):
                for csv_file in multiple_csv_files:
                    df = pd.read_csv(csv_file)
                    df['source_file'] = csv_file.name

                    # Apply global filters
                    filtered_df = df.copy()
                    for col in selected_columns:
                        if col in df.columns and global_filters.get(col):
                            filtered_df = filtered_df[filtered_df[col].astype(str).str.contains(
                                global_filters[col], na=False, case=False
                            )]

                    # Show uploaded files in expander
                    with st.expander(f"📄 {csv_file.name} ({len(filtered_df):,} rows)", expanded=False):
                        st.dataframe(filtered_df, use_container_width=True)

                    # Find duplicates
                    duplicates = df.merge(single_df[selected_columns], on=selected_columns, how='inner')
                    if not duplicates.empty:
                        duplicate_rows = pd.concat([duplicate_rows, duplicates], ignore_index=True)

            st.divider()

            if not duplicate_rows.empty:
                # Summary statistics
                st.success(f"✅ Found {len(duplicate_rows):,} duplicate rows across {len(multiple_csv_files)} file(s)")

                # Count duplicates by selected properties
                duplicate_counts = duplicate_rows.groupby(selected_columns).size().reset_index(name='Count')
                duplicate_counts_sorted = duplicate_counts.sort_values(by='Count', ascending=False)

                # Summary filters
                st.subheader("📈 Duplicate Summary by Values")
                st.caption("Shows how many times each unique combination appears")

                filtered_summary_df = duplicate_counts_sorted.copy()

                with st.expander("🔍 Filter Summary Results", expanded=False):
                    summary_filter_cols = st.columns(min(len(selected_columns), 3))
                    for idx, col in enumerate(selected_columns):
                        with summary_filter_cols[idx % len(summary_filter_cols)]:
                            filter_value = st.text_input(
                                f"Filter {col}",
                                "",
                                key=f"summary_filter_{col}",
                                help="Case-insensitive search"
                            )
                            if filter_value:
                                filtered_summary_df = filtered_summary_df[
                                    filtered_summary_df[col].astype(str).str.contains(
                                        filter_value, na=False, case=False
                                    )
                                ]

                st.dataframe(filtered_summary_df, use_container_width=True, hide_index=True)

                # Download option
                csv_summary = filtered_summary_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Summary as CSV",
                    data=csv_summary,
                    file_name="duplicate_summary.csv",
                    mime="text/csv"
                )

                st.divider()

                # Per-file breakdown
                st.subheader("📂 Duplicate Breakdown by File")
                st.caption("Shows duplicate counts for each file")

                file_duplicate_counts = duplicate_rows.groupby(['source_file'] + selected_columns).size().reset_index(name='Count')
                file_duplicate_counts_sorted = file_duplicate_counts.sort_values(by=['source_file', 'Count'], ascending=[True, False])

                filtered_file_df = file_duplicate_counts_sorted.copy()

                with st.expander("🔍 Filter File Breakdown", expanded=False):
                    filter_value_source = st.text_input(
                        "Filter by file name",
                        "",
                        key="file_filter",
                        help="Filter by source file name"
                    )
                    if filter_value_source:
                        filtered_file_df = filtered_file_df[
                            filtered_file_df['source_file'].astype(str).str.contains(
                                filter_value_source, na=False, case=False
                            )
                        ]

                    file_filter_cols = st.columns(min(len(selected_columns), 3))
                    for idx, col in enumerate(selected_columns):
                        with file_filter_cols[idx % len(file_filter_cols)]:
                            filter_value = st.text_input(
                                f"Filter {col}",
                                "",
                                key=f"file_breakdown_filter_{col}"
                            )
                            if filter_value:
                                filtered_file_df = filtered_file_df[
                                    filtered_file_df[col].astype(str).str.contains(
                                        filter_value, na=False, case=False
                                    )
                                ]

                st.dataframe(filtered_file_df, use_container_width=True, hide_index=True)

                # Download option
                csv_file_breakdown = filtered_file_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download File Breakdown as CSV",
                    data=csv_file_breakdown,
                    file_name="duplicate_file_breakdown.csv",
                    mime="text/csv"
                )
            else:
                st.success("✅ No duplicates found! None of the uploaded files contain rows that match the primary file.")
        else:
            st.info("👆 Upload one or more CSV files above to check for duplicates")
    else:
        st.info("👆 Select at least one column to continue")