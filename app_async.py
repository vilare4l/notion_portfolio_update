import asyncio
import aiohttp
import pandas as pd
from notion_client import AsyncClient
import os
from dotenv import load_dotenv
import time
import json

# Load environment variables
load_dotenv()
api_key = os.getenv("NOTION_API_KEY")
database_id = os.getenv("NOTION_DATABASE_ID")

# Initialize Notion client
notion = AsyncClient(auth=api_key)

async def get_full_table(database_id):
    """
    Retrieve all entries from the specified Notion database without filtering.
    Save the results to a file for reference.
    """
    try:
        all_results = []
        next_cursor = None

        # Fetch all entries with pagination
        while True:
            response = await notion.databases.query(database_id=database_id, start_cursor=next_cursor)
            all_results.extend(response["results"])

            # Check if there are more pages to retrieve
            if not response.get("has_more"):
                break
            next_cursor = response.get("next_cursor")

        # Save results to a file for reference
        with open("full_table_results.json", "w") as f:
            json.dump(all_results, f, indent=4)

        print(f"Total entries retrieved: {len(all_results)}")
        return all_results

    except Exception as e:
        # Handle and log exceptions
        print(f"Error in get_full_table: {e}")
        return []

def filter_for_coingecko(full_table):
    """
    Filter entries for CoinGecko API calls.
    - The 'Watchlist General' checkbox must be checked.
    - The 'ID API Coingecko' field must contain a value.
    Save the filtered results to a file for reference.
    """
    coingecko_list = []
    try:
        for entry in full_table:
            # Check if the entry meets the filtering criteria
            watchlist_flag = (
                entry["properties"].get("Watchlist General", {}).get("formula", {}).get("boolean", "true") and
                entry["properties"].get("ID API Coingecko", {}).get("rich_text", [{}])[0].get("text", {}).get("content", None) is not None
            )

            if watchlist_flag:
                coingecko_list.append({
                    "id": entry["id"],
                    "symbol": entry["properties"].get("Symbol", {}).get("title", [{}])[0].get("text", {}).get("content", None),
                    "coingecko_id": entry["properties"].get("ID API Coingecko", {}).get("rich_text", [{}])[0].get("text", {}).get("content", None)
                })
    except Exception as e:
        # Log any error during the filtering process
        print(f"Error processing entry for CoinGecko: {e}")

    # Save the filtered results to a file
    try:
        with open("filtered_coingecko_list.json", "w") as f:
            json.dump(coingecko_list, f, indent=4)
    except Exception as e:
        # Log any error during the file-saving process
        print(f"Error saving filtered results to file: {e}")

    print(f"Total entries for CoinGecko: {len(coingecko_list)}")
    return coingecko_list

def filter_for_binance(full_table):
    """
    Filter entries for Binance API calls.
    - The 'Watchlist OHLC' checkbox must be checked.
    - The 'ID API Binance' field must contain a value.
    Save the filtered results to a file for reference.
    """
    binance_list = []
    try:
        for entry in full_table:
            # Check if the entry meets the filtering criteria
            watchlist_flag = (
                entry["properties"].get("Watchlist OHLC", {}).get("formula", {}).get("boolean", "true") and
                entry["properties"].get("ID API Binance", {}).get("rich_text", [{}])[0].get("text", {}).get("content", None) is not None
            )

            if watchlist_flag:
                binance_list.append({
                    "id": entry["id"],
                    "symbol": entry["properties"].get("Symbol", {}).get("title", [{}])[0].get("text", {}).get("content", None),
                    "binance_id": entry["properties"].get("ID API Binance", {}).get("rich_text", [{}])[0].get("text", {}).get("content", None)
                })
    except Exception as e:
        # Log any error during the filtering process
        print(f"Error processing entry for Binance: {e}")

    # Save the filtered results to a file
    try:
        with open("filtered_binance_list.json", "w") as f:
            json.dump(binance_list, f, indent=4)
    except Exception as e:
        # Log any error during the file-saving process
        print(f"Error saving filtered results to file: {e}")

    print(f"Total entries for Binance: {len(binance_list)}")
    return binance_list

async def fetch_general_data_coingecko(crypto_list, vs_currency="usd"):
    """
    Fetch general data for a list of cryptocurrencies from CoinGecko.
    Save the fetched data to a primary file for reference.
    """
    if not crypto_list:
        print("Crypto list is empty. Nothing to fetch.")
        return {}

    # API endpoint and parameters for the request
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": vs_currency,
        "ids": ",".join(crypto_list),
        "order": "market_cap_desc",
        "per_page": len(crypto_list),
        "page": 1,
        "price_change_percentage": "7d,30d"
    }

    async with aiohttp.ClientSession() as session:
        try:
            # Fetch data from CoinGecko API
            async with session.get(url, params=params) as response:
                response.raise_for_status()  # Raise an exception for HTTP errors
                data = await response.json()

            # Save fetched data to a primary file
            with open("coingecko_general_data.json", "w") as file:
                json.dump(data, file, indent=4)
            print("Data saved to 'coingecko_general_data.json'")

            # Transform the data into a dictionary with the crypto ID as the key
            general_data = {item["id"]: {
                "current_price": item["current_price"],
                "market_cap": item["market_cap"],
                "fully_diluted_valuation": item.get("fully_diluted_valuation"),
                "total_volume": item["total_volume"],
                "price_change_percentage_24h": item["price_change_percentage_24h"],
                "price_change_percentage_7d_in_currency": item.get("price_change_percentage_7d_in_currency"),
                "price_change_percentage_30d_in_currency": item.get("price_change_percentage_30d_in_currency")
            } for item in data}

            # Return the transformed data
            return general_data

        except aiohttp.ClientError as e:
            # Handle any errors during the API request
            print(f"Error fetching general data from CoinGecko: {e}")
            return {}

async def fetch_ohlc_binance(session, symbol, interval="1h", days=100):
    """
    Fetch OHLC (Open, High, Low, Close) data for a single symbol from Binance.
    """
    BASE_URL = "https://api.binance.com/api/v3/klines"
    print(f"Fetching data for {symbol}...")
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1000  # The limit of data per request
    }
    symbol_data = []
    end_time = None

    try:
        # Loop to fetch data for the given number of days
        for _ in range(days * 24 // 1000 + 1):  # Adjust to the number of requests needed
            if end_time:
                params["endTime"] = end_time  # Set the end time for the next request
            async with session.get(BASE_URL, params=params) as response:
                if response.status == 429:  # Handle rate limit exceeded
                    print("Rate limit exceeded. Waiting 60 seconds...")
                    await asyncio.sleep(60)
                    continue
                response.raise_for_status()  # Raise an error for bad HTTP responses
                data = await response.json()
                if not data:  # If no data is returned, stop fetching
                    break
                symbol_data.extend(data)  # Add the fetched data to the list
                end_time = data[0][0]  # Set the end time for the next batch
        return symbol, symbol_data

    except aiohttp.ClientError as e:
        # Log any error that occurs during the data fetch process
        print(f"Error fetching data for {symbol}: {e}")
        return symbol, []  # If there's an error, store an empty list for this symbol

async def fetch_ohlc_binance_multi(symbols, interval="1h", days=100):
    """
    Fetch OHLC (Open, High, Low, Close) data for multiple symbols from Binance concurrently.
    Returns a dictionary with the symbol as the key and the raw data as the value.
    """
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_ohlc_binance(session, symbol, interval, days) for symbol in symbols]
        results = await asyncio.gather(*tasks)
    
    all_data = {symbol: data for symbol, data in results}
    return all_data


def transform_and_save_multi(data, filename_prefix="ohlc_data"):
    """
    Transform and save OHLC data for multiple cryptocurrencies into CSV files.
    The function generates hourly, daily, and weekly data and saves them to separate files.
    Returns the DataFrames for in-memory usage.
    """
    if not data:
        print("No data to transform.")
        return None, None, None

    try:
        all_dfs = []  # List to store individual DataFrames for each symbol

        for symbol, raw_data in data.items():
            if not raw_data:
                print(f"No data for {symbol}. Skipping...")
                continue

            # Convert raw OHLC data to a DataFrame
            try:
                df = pd.DataFrame(raw_data, columns=["timestamp", "open", "high", "low", "close", "volume",
                                                     "close_time", "quote_asset_volume", "number_of_trades",
                                                     "taker_buy_base_volume", "taker_buy_quote_volume", "ignore"])
                # Keep only the relevant columns
                df = df[["timestamp", "open", "high", "low", "close", "volume"]]
                df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")  # Convert timestamps to datetime
                df["symbol"] = symbol  # Add the crypto symbol as a column

                # Convert numeric columns to appropriate types
                for col in ["open", "high", "low", "close", "volume"]:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

                # Drop rows with NaN values in critical columns
                df.dropna(subset=["open", "high", "low", "close", "volume"], inplace=True)
                all_dfs.append(df)
            except Exception as e:
                print(f"Error processing data for {symbol}: {e}")

        if not all_dfs:
            print("No valid data to combine. Exiting transformation.")
            return None, None, None

        # Combine all individual DataFrames into one
        combined_df = pd.concat(all_dfs)
        if combined_df.empty:
            print("Combined DataFrame is empty. Exiting transformation.")
            return None, None, None

        combined_df.set_index("timestamp", inplace=True)

        # Reorder columns for the hourly CSV file
        combined_df = combined_df[["symbol", "open", "high", "low", "close", "volume"]]

        # Save hourly data to a CSV file
        hourly_df = combined_df.reset_index()
        hourly_df.to_csv(f"{filename_prefix}_hourly.csv", index=False)
        print(f"Hourly data saved to {filename_prefix}_hourly.csv")

        # Aggregate data to daily intervals
        try:
            daily_df = combined_df.groupby("symbol").resample("1D").agg({
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum"
            }).reset_index()

            daily_df = daily_df[["timestamp", "symbol", "open", "high", "low", "close", "volume"]]
            daily_df.to_csv(f"{filename_prefix}_daily.csv", index=False)
            print(f"Daily data saved to {filename_prefix}_daily.csv")
        except Exception as e:
            print(f"Error aggregating daily data: {e}")
            daily_df = None

        # Aggregate data to weekly intervals
        try:
            weekly_df = combined_df.groupby("symbol").resample("1W").agg({
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum"
            }).reset_index()

            weekly_df = weekly_df[["timestamp", "symbol", "open", "high", "low", "close", "volume"]]
            weekly_df.to_csv(f"{filename_prefix}_weekly.csv", index=False)
            print(f"Weekly data saved to {filename_prefix}_weekly.csv")
        except Exception as e:
            print(f"Error aggregating weekly data: {e}")
            weekly_df = None

        return hourly_df, daily_df, weekly_df

    except Exception as e:
        # Log any error during the transformation or saving process
        print(f"Error during transformation or saving: {e}")
        return None, None, None

def analyze_trend(ohlc_data):
    """
    Analyze the market trend (Bullish, Bearish, or Range) using moving averages.
    The function compares a short-term moving average (10-period) with a long-term
    moving average (50-period) to determine the trend.
    """
    try:
        # Calculate the 10-period moving average
        short_ma = ohlc_data["close"].rolling(window=10).mean()
        # Calculate the 50-period moving average
        long_ma = ohlc_data["close"].rolling(window=50).mean()

        # Compare the latest values of the moving averages
        if short_ma.iloc[-1] > long_ma.iloc[-1]:  # Short MA above Long MA indicates a Bullish trend
            return {"trend": "Bullish"}
        elif short_ma.iloc[-1] < long_ma.iloc[-1]:  # Short MA below Long MA indicates a Bearish trend
            return {"trend": "Bearish"}
        else:  # If the moving averages are equal, the market is in a Range
            return {"trend": "Range"}
    except Exception as e:
        # Handle errors (e.g., insufficient data points)
        print(f"Error analyzing trend: {e}")
        return {"trend": "Unknown"}

def analyze_momentum(ohlc_data):
    """
    Analyze momentum indicators (RSI and MACD) for the given OHLC data,
    and return a condensed overview with RSI and MACD trends.
    """
    try:
        # RSI (Relative Strength Index) calculation
        window_rsi = 14  # Standard RSI period
        delta = ohlc_data["close"].diff()  # Difference between consecutive closing prices
        gain = (delta.where(delta > 0, 0)).rolling(window=window_rsi).mean()  # Average gain over the window
        loss = (-delta.where(delta < 0, 0)).rolling(window=window_rsi).mean()  # Average loss over the window
        rs = gain / loss  # Relative Strength
        rsi = 100 - (100 / (1 + rs))  # RSI formula

        # MACD (Moving Average Convergence Divergence) calculation
        ema_12 = ohlc_data["close"].ewm(span=12, adjust=False).mean()  # 12-period EMA
        ema_26 = ohlc_data["close"].ewm(span=26, adjust=False).mean()  # 26-period EMA
        macd_line = ema_12 - ema_26  # MACD Line
        signal_line = macd_line.ewm(span=9, adjust=False).mean()  # Signal Line (9-period EMA of MACD Line)

        # Determine RSI trend
        if rsi.iloc[-1] > 70:
            rsi_trend = "Overbought"  # RSI above 70 indicates overbought conditions
        elif rsi.iloc[-1] < 30:
            rsi_trend = "Oversold"  # RSI below 30 indicates oversold conditions
        else:
            rsi_trend = "Neutral"  # RSI between 30 and 70 indicates neutral conditions

        # Determine MACD trend
        if macd_line.iloc[-1] > signal_line.iloc[-1]:
            macd_trend = "Bullish"  # MACD Line above Signal Line indicates bullish momentum
        elif macd_line.iloc[-1] < signal_line.iloc[-1]:
            macd_trend = "Bearish"  # MACD Line below Signal Line indicates bearish momentum
        else:
            macd_trend = "Neutral"  # MACD Line equal to Signal Line indicates neutral momentum

        # Create a condensed overview
        overview = f"RSI: {rsi_trend} MACD: {macd_trend}"

        # Return detailed results
        return {
            "overview": overview,
            "RSI": rsi.iloc[-1],
            "MACD Line": macd_line.iloc[-1],
            "Signal Line": signal_line.iloc[-1],
        }

    except Exception as e:
        # Handle and log exceptions
        print(f"Error in analyze_momentum: {e}")
        return {
            "overview": "Unknown",
            "RSI": None,
            "MACD Line": None,
            "Signal Line": None,
        }

async def update_security_entry(page_id, properties):
    """
    Update an entry in the security table with the given properties.

    Parameters:
    - page_id (str): The ID of the page to update in the Notion database.
    - properties (dict): A dictionary of properties to update, where keys are the property names
      and values are the new values for those properties.

    Behavior:
    - Uses the Notion API to update the page with the specified ID.
    - Prints a success message upon successful update.
    - Prints an error message if the update fails.
    """
    try:
        # Update the page in the Notion database with the provided properties
        await notion.pages.update(page_id=page_id, properties=properties)
        print(f"Updated page {page_id} successfully.")
    except Exception as e:
        # Handle and log any errors that occur during the update process
        print(f"Error updating page {page_id}: {e}")

async def main():
    """
    Main function to orchestrate the program.
    This includes fetching data from Notion, filtering data for CoinGecko and Binance,
    retrieving and processing market data, and updating Notion entries with the results.
    """
    try:
        # Step 1: Fetch the full table from Notion
        print("Fetching data from Notion...")
        full_table = await get_full_table(database_id)
        if not full_table:
            print("No entries retrieved from the database.")
            return
        print("Data fetched from Notion successfully.")

        # Step 2: Filter data for CoinGecko and Binance
        print("Filtering data for CoinGecko and Binance...")
        coingecko_list = filter_for_coingecko(full_table)
        binance_list = filter_for_binance(full_table)
        print(f"CoinGecko entries: {len(coingecko_list)}")
        print(f"Binance entries: {len(binance_list)}")

        # Step 3: Fetch general data from CoinGecko
        coingecko_ids = [entry["coingecko_id"] for entry in coingecko_list]
        if coingecko_ids:
            print("Fetching general data from CoinGecko...")
            general_data = await fetch_general_data_coingecko(coingecko_ids)
            print("CoinGecko data fetched successfully.")
        else:
            print("No CoinGecko IDs found. Skipping CoinGecko step.")
            general_data = {}

        # Step 4: Fetch and transform Binance OHLC data
        binance_symbols = [entry["binance_id"] for entry in binance_list]
        if not binance_symbols:
            print("No Binance symbols available to fetch.")
            return

        print("Fetching OHLC data from Binance...")
        ohlc_data = await fetch_ohlc_binance_multi(binance_symbols, interval="1h", days=365)
        print("Transforming and saving OHLC data...")
        hourly_df, daily_df, weekly_df = transform_and_save_multi(ohlc_data, filename_prefix="crypto_ohlc")
        print("Transformation completed. DataFrames created.")

        # Validate transformation results
        if hourly_df is None or daily_df is None or weekly_df is None:
            print("Transformation failed or data is incomplete. Exiting.")
            return

        if hourly_df.empty or daily_df.empty or weekly_df.empty:
            print("One or more DataFrames are empty. Exiting.")
            return

        # Step 5: Process each Notion entry
        print("Processing Notion entries...")
        update_tasks = []
        for entry in full_table:
            page_id = entry["id"]

            coingecko_id = None
            binance_id = None

            # Validation of ID API Coingecko
            coingecko_property = entry["properties"].get("ID API Coingecko", {})
            if "rich_text" in coingecko_property and coingecko_property["rich_text"]:
                coingecko_id = coingecko_property["rich_text"][0].get("text", {}).get("content")

            # Validation of ID API Binance
            binance_property = entry["properties"].get("ID API Binance", {})
            if "rich_text" in binance_property and binance_property["rich_text"]:
                binance_id = binance_property["rich_text"][0].get("text", {}).get("content")

            updated_properties = {}

            # Add CoinGecko data
            if coingecko_id and coingecko_id in general_data:

                data = general_data[coingecko_id]
                if data:  # Vérifie que des données existent
                    print(f"Updating CoinGecko data for {coingecko_id}: {data}")
                    updated_properties.update({
                        "Price": {"number": data.get("current_price")},
                        "Market Cap": {"number": data.get("market_cap")},
                        "FDV": {"number": data.get("fully_diluted_valuation")},
                        "Volume 24h": {"number": data.get("total_volume")},
                        "24h Change %": {"number": data.get("price_change_percentage_24h")},
                        "7d Change %": {"number": data.get("price_change_percentage_7d_in_currency")},
                        "30d Change %": {"number": data.get("price_change_percentage_30d_in_currency")},
                    })
                else:
                    print(f"No data found for {coingecko_id}. Skipping...")
            else:
                print(f"CoinGecko ID {coingecko_id} not in general_data. Skipping...")

            # Add Binance analysis
            if binance_id:
                print(f"Fetching Binance trends and momentum for {binance_id}...")
                hourly_data_filtered = hourly_df[hourly_df["symbol"] == binance_id]
                daily_data_filtered = daily_df[daily_df["symbol"] == binance_id]
                weekly_data_filtered = weekly_df[weekly_df["symbol"] == binance_id]

                if hourly_data_filtered.empty or daily_data_filtered.empty or weekly_data_filtered.empty:
                    print(f"No OHLC data available for {binance_id}. Skipping...")
                    continue

                short_trend = analyze_trend(hourly_data_filtered)
                medium_trend = analyze_trend(daily_data_filtered)
                long_trend = analyze_trend(weekly_data_filtered)

                short_momentum = analyze_momentum(hourly_data_filtered)
                medium_momentum = analyze_momentum(daily_data_filtered)
                long_momentum = analyze_momentum(weekly_data_filtered)

                updated_properties.update({
                    "Short Term Trend": {"select": {"name": short_trend["trend"]}},
                    "Medium Term Trend": {"select": {"name": medium_trend["trend"]}},
                    "Long Term Trend": {"select": {"name": long_trend["trend"]}},
                    "Short Term Momentum": {"select": {"name": short_momentum["overview"]}},
                    "Medium Term Momentum": {"select": {"name": medium_momentum["overview"]}},
                    "Long Term Momentum": {"select": {"name": long_momentum["overview"]}},
                })

            # Update Notion entry if there are changes
            if updated_properties:
                print(f"Updating Notion entry {page_id} with properties: {updated_properties}")
                update_tasks.append(update_security_entry(page_id, updated_properties))
            else:
                print(f"No updates needed for page {page_id}.")
        
        await asyncio.gather(*update_tasks)
        print("Workflow completed successfully!")

    except Exception as e:
        print(f"An error occurred in the main function: {e}")


if __name__ == "__main__":
    asyncio.run(main())
