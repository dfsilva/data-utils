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
        st.dataframe(df.head(20), use_container_width=True)

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

        # Generate report for each selected column
        with st.spinner("Generating duplicate analysis report..."):
            report_data = []

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

        # Create and display report DataFrame
        report_df = pd.DataFrame(report_data)

        st.subheader("📊 Duplicate Count Report")
        st.caption(f"Analysis of {len(selected_columns)} column(s)")

        # Highlight columns with duplicates
        def highlight_duplicates(row):
            if row['Duplicate Values'] > 0:
                return ['background-color: #fff3cd'] * len(row)
            return [''] * len(row)

        styled_report = report_df.style.apply(highlight_duplicates, axis=1)
        st.dataframe(styled_report, use_container_width=True, hide_index=True)

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
                    use_container_width=True,
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

    else:
        st.info("👆 Select at least one column to generate the duplicate analysis report")
else:
    st.info("👆 Upload a CSV file above to get started")
