# Strategic Plan: Streamlined Modernization of `spotify_history.py`

## 1. Understanding the Goal
The objective is to modernize the `spotify_history.py` application. The focus is on **readability** ("landmarking"), **simplicity**, and adherence to **Streamlit best practices**. The current "spaghetti chaos" must be resolved by organizing code logically, removing dead weight, and optimizing the execution flow, without over-engineering the solution.

## 2. Investigation & Analysis
My analysis of the codebase highlights several key areas for improvement:
*   **Performance Anti-Pattern:** Data cleaning and feature engineering (renaming columns, date conversions) occur in the **global scope** (lines 129-144). This forces the app to re-process the entire dataset on every single user interaction, bypassing Streamlit's caching mechanism.
*   **Dead Code:** The imports `calplot` and `numpy` appear to be unused, cluttering the dependencies.
*   **Mixed Concerns:** Visualization logic (verbose Altair code) is interleaved with data manipulation and UI layout calls, making the file hard to scroll through and understand.
*   **Lack of Structure:** The script runs top-to-bottom without a standard `main()` entry point.

## 3. Proposed Strategic Approach
I propose a **"Flat & Functional"** refactoring strategy. We will distribute the logic into three flat files residing in the root directory:

### Step 1: Clean Up & Organization
*   **Remove Unused Imports:** Delete `calplot` and `numpy`.
*   **Constants Extraction:** Move hardcoded lists (like `days_of_week`) and dictionaries (`change_cols`) to the top of the file or a config section.

### Step 2: Modularization (The 3-File Structure)
We will distribute the logic into three files residing in the root directory:

1.  **`data_processing.py`** (The Brain)
    *   **Consolidate Logic:** Create a single function `load_and_process_data(files)` that handles *both* loading JSONs and performing all pandas transformations (renaming, date parsing, filtering).
    *   **Apply Caching:** Decorate this function with `@st.cache_data`. This fixes the performance anti-pattern.
    *   **Type Hints:** Add Python type hints (e.g., `-> pd.DataFrame`) to improve developer experience.

2.  **`charts.py`** (The Visuals)
    *   **Encapsulate Charts:** Move all Altair chart definitions here. Functions like `get_artist_rank_chart(df)` or `get_heatmap_chart(df)` will accept data and return chart objects.
    *   **Simplify:** Remove the complexity from the main file, leaving only the "what" (display this chart), not the "how" (configure x/y axes).

3.  **`spotify_history.py`** (The Face)
    *   **Main Function:** Wrap the execution logic in a `main()` function and a `if __name__ == "__main__":` block.
    *   **Landmarking:** Use prominent comment blocks to divide the UI into logical sections (e.g., `Header`, `Data Loading`, `Top Artists Section`, `Heatmap Section`).
    *   **Declarative UI:** The code should read like a story: "Load data -> Show Header -> Show Top Artists".

### Step 3: Streamlit Best Practices
*   **State Management:** Ensure `st.session_state` is used cleanly for the clear-data functionality.
*   **Error Handling:** Wrap the file uploader logic in a `try-except` block to gracefully handle bad JSONs.
*   **Page Config:** Ensure `st.set_page_config` is the very first Streamlit command.

## 4. Verification Strategy
*   **Performance Check:** Verify that interacting with a widget (e.g., changing the heatmap artist) feels instant because the data processing doesn't re-run.
*   **Visual Regression:** Confirm the charts look identical to the original version using `example_data_2`.
*   **Readability Check:** A developer should be able to open `spotify_history.py` and immediately identify where the "Top Artists" UI code lives without scrolling past 50 lines of Altair configuration.

## 5. Anticipated Challenges & Considerations
*   **Global Variables:** The current script likely relies on implicit global variables (like `all_data`). The refactor must strictly pass dataframes as arguments to functions.
*   **Import Circularity:** By keeping the structure flat and hierarchical (Main imports Data/Charts; Data/Charts import nothing from Main), we avoid circular imports.
*   **Altair Complexity:** The `build_heatmap` function is complex. Moving it to `charts.py` requires carefully identifying all its inputs (e.g., `year_select`, `heatmap_artist`) to pass them as arguments.