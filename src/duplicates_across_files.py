import streamlit as st
import pandas as pd

pd.set_option("styler.render.max_elements", 1451815)

st.title("🔍 Find Duplicates Across Files")
st.markdown("""
Upload multiple CSV files to identify duplicate entries that appear across any of the files.
This tool helps you find data that exists in multiple datasets.
""")

st.divider()

st.subheader("📤 Upload Files")
st.caption("Upload 2 or more CSV files to analyze")

multiple_csv_files = st.file_uploader(
    "Select CSV files",
    type=["csv"],
    accept_multiple_files=True,
    help="Upload the files you want to check for duplicates across"
)

if multiple_csv_files:
    if len(multiple_csv_files) < 2:
        st.warning("⚠️ Please upload at least 2 files to compare")
    else:
        # Concatenate all files into a single DataFrame
        all_dfs = []
        total_rows = 0

        with st.spinner("Loading files..."):
            for csv_file in multiple_csv_files:
                df = pd.read_csv(csv_file)
                df['source_file'] = csv_file.name
                all_dfs.append(df)
                total_rows += len(df)

        combined_df = pd.concat(all_dfs, ignore_index=True)

        # Show summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Files Uploaded", len(multiple_csv_files))
        with col2:
            st.metric("Total Rows", f"{total_rows:,}")
        with col3:
            st.metric("Total Columns", len(combined_df.columns) - 1)  # Exclude source_file

        # Display file previews in expander
        with st.expander("👁️ Preview Uploaded Files", expanded=False):
            for csv_file, df in zip(multiple_csv_files, all_dfs):
                st.markdown(f"**{csv_file.name}** ({len(df):,} rows)")
                st.dataframe(df.drop(columns=['source_file']).head(10), use_container_width=True)
                st.divider()

        st.divider()

        st.subheader("🎯 Select Comparison Columns")
        st.caption("Choose which columns to use for detecting duplicates")

        # Remove source_file from column selection
        available_columns = [col for col in combined_df.columns if col != 'source_file']

        selected_columns = st.multiselect(
            "Columns to compare",
            available_columns,
            help="Rows will be considered duplicates if ALL selected columns match"
        )

        if selected_columns:
            st.divider()

            # Identify duplicates across all files
            with st.spinner("Analyzing for duplicates..."):
                duplicated_df = combined_df[combined_df.duplicated(subset=selected_columns, keep=False)]

            if not duplicated_df.empty:
                st.success(f"✅ Found {len(duplicated_df):,} duplicate rows across all files")

                # Count duplicates and prepare the summary table
                duplicate_counts = duplicated_df.groupby(selected_columns).size().reset_index(name='Count')
                duplicate_counts_sorted = duplicate_counts.sort_values(by='Count', ascending=False)

                st.subheader("📈 Duplicate Summary (All Files Combined)")
                st.caption(f"Showing {len(duplicate_counts_sorted):,} unique duplicate values")

                # Filters for summary
                filtered_df = duplicate_counts_sorted.copy()

                with st.expander("🔍 Filter Results", expanded=False):
                    filter_cols = st.columns(min(len(selected_columns), 3))
                    for idx, col in enumerate(selected_columns):
                        with filter_cols[idx % len(filter_cols)]:
                            filter_value = st.text_input(
                                f"Filter {col}",
                                "",
                                key=f"summary_filter_{col}",
                                help="Case-insensitive text search"
                            )
                            if filter_value:
                                filtered_df = filtered_df[
                                    filtered_df[col].astype(str).str.contains(
                                        filter_value, na=False, case=False
                                    )
                                ]

                st.dataframe(filtered_df, use_container_width=True, hide_index=True)

                # Download option
                csv_summary = filtered_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Summary as CSV",
                    data=csv_summary,
                    file_name="duplicates_summary_all_files.csv",
                    mime="text/csv"
                )

                st.divider()

                # Per-file breakdown
                st.subheader("📂 Duplicate Breakdown by File")
                st.caption("Shows which files contain each duplicate value")

                file_duplicate_counts = duplicated_df.groupby(['source_file'] + selected_columns).size().reset_index(name='Count')
                file_duplicate_counts_sorted = file_duplicate_counts.sort_values(
                    by=['source_file', 'Count'],
                    ascending=[True, False]
                )

                filtered_file_df = file_duplicate_counts_sorted.copy()

                # Filters for per-file breakdown
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
                                key=f"file_filter_{col}",
                                help="Case-insensitive search"
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
                    file_name="duplicates_by_file.csv",
                    mime="text/csv"
                )
            else:
                st.success("✅ No duplicates found! All rows are unique across the uploaded files.")
        else:
            st.info("👆 Select at least one column to check for duplicates")
else:
    st.info("👆 Upload CSV files above to get started")
