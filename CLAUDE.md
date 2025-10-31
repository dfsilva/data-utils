# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Streamlit-based data utilities application for CSV file analysis. It provides five main tools organized into two categories for comparing, analyzing, and querying CSV data files through a modern web interface.

## Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Streamlit app
streamlit run src/app.py
```

The app will be available at `http://localhost:8501`

## Project Structure

The application uses Streamlit's categorized multi-page navigation system with two main categories:

### 🔍 Duplicate Detection Tools

- **`src/duplicates_for_one_file.py`**: Compare Against Primary File - Compares a reference file against multiple other files to find matching entries
- **`src/duplicates_across_files.py`**: Find Duplicates Across Files - Identifies duplicate entries that appear across any uploaded files
- **`src/duplicate_report_by_column.py`**: Duplicate Analysis Report - Generates comprehensive statistics showing duplicate counts for each column

### 📊 Data Analysis Tools

- **`src/compare_across_files.py`**: Compare Files (Unique Rows) - Identifies unique rows that exist in one file but not in others
- **`src/query_files.py`**: SQL Query Builder - Advanced SQL interface using DuckDB to query combined CSV data with autocomplete

### Main Navigation

- **`src/app.py`**: Main entry point that configures the Streamlit app with categorized navigation, wide layout, and expanded sidebar

## Architecture Notes

### Data Processing Pattern

All tools follow a similar pattern:
1. Upload CSV file(s) via `st.file_uploader()`
2. Read files into pandas DataFrames
3. Add `source_file` column to track which file each row came from
4. Allow column selection via `st.multiselect()`
5. Perform analysis and display results

### Key Dependencies

- **Streamlit**: Web UI framework
- **Pandas**: Data manipulation and analysis
- **DuckDB**: Used in `query_files.py` for SQL querying across CSV files

### Important Configuration

`pd.set_option("styler.render.max_elements", 1451815)` is set in multiple files to handle large datasets in the UI.

### DuckDB Integration

In `query_files.py`, all uploaded CSV files are combined into a single DataFrame and registered as a table called `files` in DuckDB. Users can then query this table with standard SQL. The table automatically includes a `source_file` column.

### SQL Query Editor with Autocomplete

The SQL query tool uses `streamlit-code-editor` to provide:
- **SQL syntax highlighting** for better readability
- **Autocomplete for SQL keywords** (SELECT, WHERE, GROUP BY, etc.)
- **Autocomplete for column names** from uploaded CSV files
- **Autocomplete for SQL functions** (COUNT, SUM, AVG, etc.)
- **Example queries** in an expandable section
- **VS Code-style shortcuts** for familiar editing experience

The editor has a "Run Query" button built-in and gracefully falls back to a text area if the code editor component is not installed.

## UX Design Patterns

All pages follow consistent UX patterns for better usability:

### Visual Hierarchy
- **Title with icon** and descriptive subtitle
- **Dividers** (`st.divider()`) to separate sections
- **Metrics** displayed in columns for key statistics
- **Captions** (`st.caption()`) to provide context for each section

### User Guidance
- **Help text** on file uploaders and inputs
- **Info boxes** showing available columns and key information
- **Expandable sections** for previews and optional features
- **Loading spinners** for all data processing operations
- **Clear success/error messages** with emojis for visual feedback

### Data Display
- **Collapsible previews** of uploaded files (not expanded by default)
- **Formatted numbers** with thousand separators (e.g., 1,234)
- **Download buttons** for all result tables
- **Filter options** in expanders to keep UI clean
- **Hide index** on dataframes for cleaner presentation

### Filtering
- Filters organized in **column layouts** (max 3 columns)
- **Unique keys** for all widgets to prevent conflicts
- **Case-insensitive** text search across all filters
- Filters placed in **expandable sections** to reduce clutter

### Navigation
- Pages organized by **category** in sidebar
- **Descriptive titles** that explain what each tool does
- **Consistent icons** across similar features

## Development Notes

- All Python source files are in the `src/` directory
- The app uses `src/logo.png` for branding
- Layout set to `"wide"` for better use of screen space
- Filter functionality uses case-insensitive string matching with `str.contains()`
- All pages use `st.divider()`, metrics, captions, and expanders for consistent UX
