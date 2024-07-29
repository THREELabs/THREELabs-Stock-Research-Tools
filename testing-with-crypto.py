#pip install pandas tqdm tabulate requests matplotlib
import yfinance as yf
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import time
import random
import requests
from tabulate import tabulate

def get_tickers(num_stocks, crypto=False):
    if crypto:
        base_url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&sparkline=true"
        headers = {"Accept": "application/json"}
    else:
        base_url = "https://api.nasdaq.com/api/screener/stocks?tableonly=true&limit=7754&download=true"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.3takan/537.36"
        }

    try:
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()
        data = response.json()

        if crypto:
            tickers = [entry['id'] for entry in data]
        else:
            if 'data' not in data or 'rows' not in data['data']:
                raise ValueError("Unexpected data format from NASDAQ API")
            tickers = [row['symbol'] for row in data['data']['rows']]

        if len(tickers) < num_stocks:
            print(f"Warning: Only {len(tickers)} {['stocks', 'cryptocurrencies'][crypto]} available. Using all of them.")
        else:
            random.shuffle(tickers)
            tickers = tickers[:num_stocks]

        return tickers
    except Exception as e:
        print(f"Error fetching tickers: {str(e)}")
        return []

def get_stock_data(ticker, period="3mo"):
    try:
        if ticker.isupper():
            data = yf.Ticker(ticker).history(period=period)
        else:
            data = yf.Ticker(f"crypto/{ticker}").history(period=period)

        if data.empty:
            print(f"Warning: No data available for {ticker} in the specified period.")
            return None, None
        return ticker, data
    except Exception as e:
        print(f"Error fetching data for {ticker}: {str(e)}")
        return None, None

def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def analyze_weekly_change(history):
    weekly_changes = history['Close'].resample('W').last().pct_change()
    return weekly_changes.mean()

def get_recommendations(history, avg_weekly_change):
    current_price = history['Close'].iloc[-1]

    # Calculate buy price: Use a larger discount for negative weekly changes
    discount = max(0.05, abs(avg_weekly_change)) if avg_weekly_change < 0 else 0.05
    buy_price = current_price * (1 - discount)

    # Calculate sell price: Ensure it's always higher than the current price
    sell_multiplier = 1 + max(0.05, avg_weekly_change)
    sell_price = current_price * sell_multiplier

    return buy_price, sell_price

def find_repetitive_dips(history, threshold=10):
    close_prices = history['Close']
    repetitive_dips = []
    dip_found = False

    for i in range(len(close_prices) - 1):
        price_change = (close_prices[i + 1] / close_prices[i] - 1) * 100
        if price_change < -threshold:  # Price dropped by more than the threshold
            if not dip_found:
                dip_start_index = i
            dip_found = True
        elif price_change > 0:  # Price started going up
            if dip_found:
                dip_end_index = i
                dip_duration = dip_end_index - dip_start_index
                if dip_duration >= 2:  # Ensure the dip lasted for at least 2 periods
                    repetitive_dips.append((dip_start_index, dip_end_index))
                dip_found = False

    return repetitive_dips

def analyze_stock(ticker, drop_threshold=10):
    ticker, history = get_stock_data(ticker)
    if ticker is None or history is None or history.empty or len(history) < 20:
        return None

    history['RSI'] = calculate_rsi(history)
    history['SMA_50'] = history['Close'].rolling(window=50).mean()
    history['SMA_200'] = history['Close'].rolling(window=200).mean()

    current_price = history['Close'].iloc[-1]
    current_rsi = history['RSI'].iloc[-1]
    sma_50 = history['SMA_50'].iloc[-1]
    sma_200 = history['SMA_200'].iloc[-1]

    repetitive_dips = find_repetitive_dips(history, threshold=drop_threshold)

    if repetitive_dips:
        return {
            'ticker': ticker,
            'current_price': current_price,
            'rsi': current_rsi,
            'repetitive_dips': repetitive_dips
        }

    return None

def find_promising_stocks(tickers, crypto=False, max_workers=10, drop_threshold=10):
    promising_stocks = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(analyze_stock, ticker, drop_threshold): ticker for ticker in tickers}
        for future in tqdm(as_completed(futures), total=len(tickers), desc="Analyzing stocks"):
            result = future.result()
            if result:
                promising_stocks.append(result)

    return sorted(promising_stocks, key=lambda x: x['current_price'], reverse=True)

def display_stock_info(ticker):
    ticker, history = get_stock_data(ticker, period="1y")

    if ticker is None or history is None or history.empty:
        print(f"Unable to fetch data for {ticker}")
        return

    if ticker.isupper():
        info = yf.Ticker(ticker).info
    else:
        info = yf.Ticker(f"crypto/{ticker}").info

    current_price = history['Close'].iloc[-1]

    data = [
        ["Current Price", f"${current_price:.2f}"],
        ["52 Week High", f"${info.get('fiftyTwoWeekHigh', 'N/A')}"],
        ["52 Week Low", f"${info.get('fiftyTwoWeekLow', 'N/A')}"],
        ["Market Cap", f"${info.get('marketCap', 0) / 1e9:.2f}B"],
        ["P/E Ratio", f"{info.get('trailingPE', 'N/A')}"],
        ["Dividend Yield", f"{info.get('dividendYield', 0) * 100:.2f}%"],
    ]

    print(f"\n{['Stock', 'Cryptocurrency'][ticker.islower()]} Information for {ticker}:")
    print(tabulate(data, headers=["Metric", "Value"], tablefmt="grid"))

    avg_weekly_change = analyze_weekly_change(history)
    print(f"\nAverage Weekly Change: {avg_weekly_change:.2%}")

    last_week = history.last('1w')
    weekly_low = last_week['Low'].min()
    weekly_high = last_week['High'].max()
    weekly_change = (last_week['Close'].iloc[-1] / last_week['Open'].iloc[0] - 1)

    weekly_data = [
        ["Last Week's Low", f"${weekly_low:.2f}"],
        ["Last Week's High", f"${weekly_high:.2f}"],
        ["Last Week's Change", f"{weekly_change:.2%}"],
    ]

    print("\nLast Week's Performance:")
    print(tabulate(weekly_data, headers=["Metric", "Value"], tablefmt="grid"))

    buy_price, sell_price = get_recommendations(history, avg_weekly_change)

    recommendation_data = [
        ["Recommended Buy Price", f"${buy_price:.2f}"],
        ["Recommended Sell Price", f"${sell_price:.2f}"],
    ]

    print("\nRecommendations:")
    print(tabulate(recommendation_data, headers=["Action", "Price"], tablefmt="grid"))

def main():
    while True:
        print("\nInvestment Analysis Tool")
        print("1. Analyze a single stock or cryptocurrency")
        print("2. Search for promising stocks or cryptocurrencies")
        print("3. Search for stocks/cryptocurrencies with repetitive dips")
        print("4. Exit")

        choice = input("Enter your choice (1-4): ").strip()

        if choice == '1':
            ticker = input("Enter the stock or cryptocurrency ticker symbol: ").strip()
            display_stock_info(ticker)

        elif choice == '2':
            while True:
                try:
                    num_stocks = int(input("Enter the number of stocks/cryptocurrencies to search and analyze (recommended: 100 to 1000): "))
                    if num_stocks > 0:
                        break
                    else:
                        print("Please enter a positive number.")
                except ValueError:
                    print("Please enter a valid integer.")

            print("Do you want to search for stocks or cryptocurrencies?")
            search_type = input("Enter 'stocks' or 'crypto': ").strip().lower()

            if search_type == 'stocks':
                tickers_to_analyze = get_tickers(num_stocks)
            elif search_type == 'crypto':
                tickers_to_analyze = get_tickers(num_stocks, crypto=True)
            else:
                print("Invalid choice. Please enter 'stocks' or 'crypto'.")
                continue

            if not tickers_to_analyze:
                print(f"No tickers found. Please try again later.")
                continue

            print(f"Retrieved {len(tickers_to_analyze)} tickers.")

            start_time = time.time()
            promising_stocks = find_promising_stocks(tickers_to_analyze, crypto=search_type == 'crypto')
            end_time = time.time()

            print(f"\nAnalysis completed in {end_time - start_time:.2f} seconds.")
            print(f"Found {len(promising_stocks)} promising {['stocks', 'cryptocurrencies'][search_type == 'crypto']}.")

            if not promising_stocks:
                print("No promising stocks/cryptocurrencies found based on the current criteria.")
                continue

            while True:
                try:
                    top_n = int(input("Enter the number of top stocks/cryptocurrencies to display: "))
                    if top_n > 0:
                        break
                    else:
                        print("Please enter a positive number.")
                except ValueError:
                    print("Please enter a valid integer.")

            print(f"\nTop {min(top_n, len(promising_stocks))} Promising {['Stocks', 'Cryptocurrencies'][search_type == 'crypto']}:")
            for i, stock in enumerate(promising_stocks[:top_n], 1):
                print(f"{i}. {stock['ticker']}:")
                print(f"   Current Price: ${stock['current_price']:.2f}")
                print(f"   RSI: {stock['rsi']:.2f}")
                print(f"   Recommended Buy Price: ${stock['buy_price']:.2f}")
                print(f"   Recommended Sell Price: ${stock['sell_price']:.2f}")
                print(f"   Potential Gain (%): N/A (No weekly change data)\n")

        elif choice == '3':
            while True:
                try:
                    num_stocks = int(input("Enter the number of stocks/cryptocurrencies to search for repetitive dips: "))
                    if num_stocks > 0:
                        break
                    else:
                        print("Please enter a positive number.")
                except ValueError:
                    print("Please enter a valid integer.")

            drop_threshold = int(input("Enter the drop threshold percentage (e.g., 5 for 5%): "))

            print("Do you want to search for stocks or cryptocurrencies?")
            search_type = input("Enter 'stocks' or 'crypto': ").strip().lower()

            if search_type == 'stocks':
                tickers_to_analyze = get_tickers(num_stocks)
            elif search_type == 'crypto':
                tickers_to_analyze = get_tickers(num_stocks, crypto=True)
            else:
                print("Invalid choice. Please enter 'stocks' or 'crypto'.")
                continue

            if not tickers_to_analyze:
                print(f"No tickers found. Please try again later.")
                continue

            print(f"Retrieved {len(tickers_to_analyze)} tickers.")

            start_time = time.time()
            stocks_with_dips = find_promising_stocks(tickers_to_analyze, crypto=search_type == 'crypto', drop_threshold=drop_threshold)
            end_time = time.time()

            print(f"\nSearch completed in {end_time - start_time:.2f} seconds.")
            print(f"Found {len(stocks_with_dips)} {['stocks', 'cryptocurrencies'][search_type == 'crypto']} with repetitive dips.")

            if not stocks_with_dips:
                print("No stocks/cryptocurrencies found with repetitive dips based on the current criteria.")
                continue

            for stock in stocks_with_dips:
                print(f"{stock['ticker']}:")
                print("  Repetitive Dips:")
                for dip in stock['repetitive_dips']:
                    start_date = history.index[dip[0]]
                    end_date = history.index[dip[1]]
                    print(f"    From {start_date} to {end_date}")

        elif choice == '4':
            print("Thank you for using the Investment Analysis Tool. Goodbye!")
            break

        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")

if __name__ == "__main__":
    main()
