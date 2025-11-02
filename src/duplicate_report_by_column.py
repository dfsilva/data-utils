import streamlit as st
import pandas as pd

pd.set_option("styler.render.max_elements", 1451815)

st.title("📋 Duplicate Analysis Report")
st.markdown("""
Generate a comprehensive report showing duplicate statistics for each column in your CSV file.
This tool provides an overview of data quality and identifies columns with duplicate values.
""")

st.divider()

st.subheader("📤 Upload File to Analyze")
st.caption("Upload a single CSV file to generate a duplicate analysis report")

csv_file = st.file_uploader(
    "Select a CSV file",
    type=["csv"],
    help="Upload the file you want to analyze for duplicates"
)

if csv_file is not None:
    df = pd.read_csv(csv_file)

    # Show file info with metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("File Name", csv_file.name)
    with col2:
        st.metric("Total Rows", f"{len(df):,}")
    with col3:
        st.metric("Total Columns", len(df.columns))

    # Preview in expandable section
    with st.expander("👁️ Preview File Data", expanded=False):
        st.dataframe(df.head(20), width="stretch")

    st.divider()

    # Column selection
    st.subheader("🎯 Select Columns to Analyze")
    st.caption("Choose which columns to include in the duplicate analysis report")

    selected_columns = st.multiselect(
        "Columns to analyze",
        df.columns.tolist(),
        help="Select one or more columns to check for duplicate values"
    )

    if selected_columns:
        st.divider()

        # Analysis mode selection
        st.subheader("🔧 Analysis Mode")
        analysis_mode = st.radio(
            "Choose analysis type",
            ["Individual Columns", "Combined Columns (Multi-column duplicates)"],
            help="Individual: Analyze each column separately. Combined: Find duplicates based on combination of selected columns"
        )

        st.divider()

        # Generate report based on mode
        with st.spinner("Generating duplicate analysis report..."):
            report_data = []

            if analysis_mode == "Individual Columns":
                # Original behavior - analyze each column separately
                for column in selected_columns:
                    # Count total values
                    total_values = len(df[column])

                    # Count unique values
                    unique_values = df[column].nunique()

                    # Count duplicate values (values that appear more than once)
                    value_counts = df[column].value_counts()
                    duplicated_values = value_counts[value_counts > 1]
                    num_duplicate_values = len(duplicated_values)

                    # Count total rows with duplicate values
                    total_duplicate_rows = duplicated_values.sum() if len(duplicated_values) > 0 else 0

                    # Count rows that have duplicates (excluding first occurrence)
                    duplicate_rows_excluding_first = total_duplicate_rows - num_duplicate_values if num_duplicate_values > 0 else 0

                    # Calculate duplicate percentage
                    duplicate_percentage = (num_duplicate_values / unique_values * 100) if unique_values > 0 else 0

                    report_data.append({
                        'Column': column,
                        'Total Rows': total_values,
                        'Unique Values': unique_values,
                        'Duplicate Values': num_duplicate_values,
                        'Duplicate %': f"{duplicate_percentage:.1f}%",
                        'Total Duplicate Rows': total_duplicate_rows,
                        'Duplicate Rows (excl. first)': duplicate_rows_excluding_first
                    })

            else:  # Combined Columns mode
                # Analyze duplicates based on combination of selected columns
                column_combo_name = " + ".join(selected_columns)

                # Count total rows
                total_values = len(df)

                # Count unique combinations
                unique_combinations = df[selected_columns].drop_duplicates()
                unique_values = len(unique_combinations)

                # Find duplicate combinations
                duplicate_mask = df.duplicated(subset=selected_columns, keep=False)
                total_duplicate_rows = duplicate_mask.sum()

                # Count unique duplicate combinations (values that appear more than once)
                combination_counts = df.groupby(selected_columns).size()
                duplicated_combinations = combination_counts[combination_counts > 1]
                num_duplicate_values = len(duplicated_combinations)

                # Count duplicate rows excluding first occurrence
                duplicate_mask_excl_first = df.duplicated(subset=selected_columns, keep='first')
                duplicate_rows_excluding_first = duplicate_mask_excl_first.sum()

                # Calculate duplicate percentage
                duplicate_percentage = (num_duplicate_values / unique_values * 100) if unique_values > 0 else 0

                report_data.append({
                    'Column': column_combo_name,
                    'Total Rows': total_values,
                    'Unique Values': unique_values,
                    'Duplicate Values': num_duplicate_values,
                    'Duplicate %': f"{duplicate_percentage:.1f}%",
                    'Total Duplicate Rows': total_duplicate_rows,
                    'Duplicate Rows (excl. first)': duplicate_rows_excluding_first
                })

        # Create and display report DataFrame
        report_df = pd.DataFrame(report_data)

        st.subheader("📊 Duplicate Count Report")
        st.caption(f"Analysis of {len(selected_columns)} column(s)")

        # Highlight columns with duplicates
        def highlight_duplicates(row):
            if row['Duplicate Values'] > 0:
                return ['background-color: #fff3cd; color: #000000'] * len(row)
            return ['color: #000000'] * len(row)

        styled_report = report_df.style.apply(highlight_duplicates, axis=1)
        st.dataframe(styled_report, width="stretch", hide_index=True)

        # Download report
        csv_report = report_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Report as CSV",
            data=csv_report,
            file_name=f"duplicate_report_{csv_file.name}",
            mime="text/csv"
        )

        # Explanation
        with st.expander("ℹ️ Understanding the Report", expanded=False):
            st.markdown("""
            **Column Definitions:**
            - **Column**: The name of the analyzed column
            - **Total Rows**: Total number of rows in the column
            - **Unique Values**: Number of distinct/unique values
            - **Duplicate Values**: Number of values that appear more than once
            - **Duplicate %**: Percentage of unique values that are duplicates
            - **Total Duplicate Rows**: Total count of all rows with duplicate values (including all occurrences)
            - **Duplicate Rows (excl. first)**: Count of duplicate rows excluding the first occurrence of each value

            **Color Coding:**
            - 🟨 Yellow highlighted rows indicate columns containing duplicate values
            """)

        st.divider()

        # Detailed view section
        st.subheader("🔍 Detailed Duplicate Analysis")

        if analysis_mode == "Individual Columns":
            st.caption("Drill down into specific columns to see which values are duplicated")

            selected_column_detail = st.selectbox(
                "Select a column to view detailed duplicate values",
                selected_columns,
                help="View all duplicate values and their counts for this column"
            )

            if selected_column_detail:
                value_counts = df[selected_column_detail].value_counts()
                duplicated_values = value_counts[value_counts > 1].reset_index()
                duplicated_values.columns = ['Value', 'Count']

                if len(duplicated_values) > 0:
                    # Summary metrics for this column
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Unique Duplicate Values", f"{len(duplicated_values):,}")
                    with col2:
                        st.metric("Total Duplicate Rows", f"{duplicated_values['Count'].sum():,}")
                    with col3:
                        st.metric("Most Common Count", f"{duplicated_values['Count'].max():,}")

                    # Filter option
                    filter_value = ""
                    with st.expander("🔍 Filter Duplicate Values", expanded=False):
                        filter_value = st.text_input(
                            f"Search in '{selected_column_detail}'",
                            "",
                            help="Enter text to filter the duplicate values (case-insensitive)"
                        )

                    if filter_value:
                        duplicated_values = duplicated_values[
                            duplicated_values['Value'].astype(str).str.contains(
                                filter_value,
                                na=False,
                                case=False
                            )
                        ]
                        st.caption(f"Showing {len(duplicated_values):,} filtered duplicate value(s)")
                    else:
                        st.caption(f"Showing all {len(duplicated_values):,} duplicate value(s)")

                    st.dataframe(
                        duplicated_values.sort_values('Count', ascending=False),
                        width="stretch",
                        hide_index=True
                    )

                    # Download detailed report
                    csv_detail = duplicated_values.to_csv(index=False)
                    st.download_button(
                        label=f"📥 Download Detailed Report for '{selected_column_detail}'",
                        data=csv_detail,
                        file_name=f"duplicate_detail_{selected_column_detail}.csv",
                        mime="text/csv",
                        key="download_detail"
                    )
                else:
                    st.success(f"✅ No duplicate values found in '{selected_column_detail}' - All values are unique!")

        else:  # Combined Columns mode
            st.caption("View the specific combinations of values that appear multiple times")

            # Get duplicate combinations
            combination_counts = df.groupby(selected_columns).size().reset_index(name='Count')
            duplicated_combinations = combination_counts[combination_counts['Count'] > 1].copy()

            if len(duplicated_combinations) > 0:
                # Summary metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Unique Duplicate Combinations", f"{len(duplicated_combinations):,}")
                with col2:
                    st.metric("Total Duplicate Rows", f"{duplicated_combinations['Count'].sum():,}")
                with col3:
                    st.metric("Most Common Count", f"{duplicated_combinations['Count'].max():,}")

                # Filter option
                filter_value = ""
                with st.expander("🔍 Filter Duplicate Combinations", expanded=False):
                    filter_value = st.text_input(
                        "Search in duplicate combinations",
                        "",
                        help="Enter text to filter the duplicate combinations (case-insensitive)",
                        key="filter_combined"
                    )

                if filter_value:
                    # Filter across all selected columns
                    mask = duplicated_combinations[selected_columns].astype(str).apply(
                        lambda row: row.str.contains(filter_value, na=False, case=False).any(),
                        axis=1
                    )
                    duplicated_combinations = duplicated_combinations[mask]
                    st.caption(f"Showing {len(duplicated_combinations):,} filtered duplicate combination(s)")
                else:
                    st.caption(f"Showing all {len(duplicated_combinations):,} duplicate combination(s)")

                # Sort by count descending
                duplicated_combinations = duplicated_combinations.sort_values('Count', ascending=False)

                st.dataframe(
                    duplicated_combinations,
                    width="stretch",
                    hide_index=True
                )

                # Download detailed report
                csv_detail = duplicated_combinations.to_csv(index=False)
                column_names = "_".join(selected_columns)
                st.download_button(
                    label=f"📥 Download Detailed Report for Combined Columns",
                    data=csv_detail,
                    file_name=f"duplicate_detail_combined_{column_names}.csv",
                    mime="text/csv",
                    key="download_detail_combined"
                )
            else:
                st.success(f"✅ No duplicate combinations found - All combinations of {' + '.join(selected_columns)} are unique!")

    else:
        st.info("👆 Select at least one column to generate the duplicate analysis report")
else:
    st.info("👆 Upload a CSV file above to get started")
