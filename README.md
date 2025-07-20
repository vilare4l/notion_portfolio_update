# Cryptocurrency Data Processor and Notion Integration
#### Video Demo: [Add Your Video URL Here]
#### Description:

This project is a comprehensive cryptocurrency data processor that integrates with the Notion API to manage and analyze cryptocurrency data. It provides tools for fetching, filtering, and transforming cryptocurrency data from external APIs such as CoinGecko and Binance, and updates entries in a Notion database with the processed information.

The project is designed to help cryptocurrency enthusiasts, traders, and analysts streamline their workflow by consolidating data processing and analysis into one automated pipeline.

---

## Features
- **Notion Integration**: Fetch and update entries in a Notion database using the Notion API.
- **Data Fetching**:
  - Retrieve general cryptocurrency data (e.g., prices, market cap) from CoinGecko.
  - Fetch OHLC (Open, High, Low, Close) data for multiple cryptocurrencies from Binance.
- **Data Transformation**: Process and save OHLC data into hourly, daily, and weekly intervals.
- **Technical Analysis**:
  - Analyze market trends using moving averages.
  - Calculate momentum indicators like RSI (Relative Strength Index) and MACD (Moving Average Convergence Divergence).
- **Error Handling**: Includes robust exception handling for API requests and data processing steps.

---

## Files and Their Functionality

1. **`project.py`**:
    This is the main file containing all the core functionality and entry point (`main()`) for the project. Below is an overview of the functions included in `project.py`:

    - **Notion Integration**:
        - `get_full_table(database_id)`: Retrieves all entries from the Notion database.
        - `update_security_entry(page_id, properties)`: Updates a Notion entry with computed data.

    - **Data Fetching**:
        - `filter_for_coingecko(full_table)`: Filters Notion entries for valid CoinGecko IDs.
        - `filter_for_binance(full_table)`: Filters Notion entries for valid Binance IDs.
        - `fetch_general_data_coingecko(crypto_list, vs_currency="usd")`: Fetches cryptocurrency market data from CoinGecko.
        - `fetch_ohlc_binance_multi(symbols, interval="1h", days=100)`: Fetches OHLC (Open, High, Low, Close) data from Binance.

    - **Data Processing**:
        - `transform_and_save_multi(data, filename_prefix="ohlc_data")`: Processes OHLC data into hourly, daily, and weekly formats, saving them to CSV files.

    - **Technical Analysis**:
        - `analyze_trend(ohlc_data)`: Determines the market trend (Bullish, Bearish, or Range) using moving averages.
        - `analyze_momentum(ohlc_data)`: Computes RSI and MACD to analyze cryptocurrency momentum.

    - **Main Functionality**:
        - The `main()` function orchestrates the workflow:
            1. Fetching data from Notion.
            2. Filtering data for CoinGecko and Binance.
            3. Performing data analysis.
            4. Updating Notion entries with computed results.

2. **`test_project.py`**:
   This file contains unit tests to ensure the robustness and accuracy of the project's core functions, written using the `pytest` framework.

   - **`test_analyze_trend()`**:
     - Identifies market trends (Bullish, Bearish, or Range) using moving averages.
       - **Test Cases**:
         1. **Bullish Trend**: Dataset with increasing moving averages.
         2. **Bearish Trend**: Dataset with decreasing moving averages.
         3. **Range Trend**: Dataset with constant values.

   - **`test_filter_for_coingecko()`**:
     - Filters Notion database entries compatible with the CoinGecko API.
       - **Test Cases**:
         1. Valid entries where one meets filtering criteria (checkbox enabled and API ID present).
         2. Empty list of entries to ensure no errors occur.

   - **`test_analyze_momentum()`**:
     - Calculates and interprets indicators like RSI and MACD for market data.
       - **Test Cases**:
         1. **Strong Upward Trend**: Dataset with increasing values, producing RSI > 70 and Bullish MACD.
         2. **Strong Downward Trend**: Dataset with decreasing values, producing RSI < 30 and Bearish MACD.
         3. **Constant Data with One Spike**: Verifies if RSI and MACD react correctly to a single outlier.


3. **`requirements.txt`**:
   - Lists all dependencies required to run the project, including `pandas`, `notion-client`, `requests`, and `python-dotenv`.

4. **`README.md`**:
   - Provides a comprehensive overview of the project, including its features, structure, and design choices.

5. **`.env`**:
   - Contains sensitive API keys for Notion

---

## Design Choices

### Notion Integration
- **Why Notion?**: Notion provides a flexible and user-friendly database system that integrates well with other tools. It was chosen for its ability to visually display and manage cryptocurrency data.
- **Database Structure**: The Notion database uses properties such as "Symbol", "Watchlist General", "ID API Coingecko", and "ID API Binance" to store and filter relevant information.

### API Selection
- **CoinGecko**: Selected for its extensive cryptocurrency market data, including price, market cap, and historical trends.
- **Binance**: Chosen for its reliable OHLC data, which is crucial for technical analysis.

### Data Analysis
- **RSI and MACD**: These indicators were chosen because they are widely used in technical analysis and provide valuable insights into market trends and momentum.

### File Storage
- The workflow implies several file storage for debugging and potential future updates
---
