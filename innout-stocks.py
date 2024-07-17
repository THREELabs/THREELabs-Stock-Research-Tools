#pip install pandas tqdm tabulate requests matplotlib yfinance

import yfinance as yf
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import time
import random
import requests
from tabulate import tabulate

def get_tickers(num_stocks):
    base_url = "https://api.nasdaq.com/api/screener/stocks?tableonly=true&limit=7754&download=true"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()
        data = response.json()

        if 'data' not in data or 'rows' not in data['data']:
            raise ValueError("Unexpected data format from NASDAQ API")

        tickers = [row['symbol'] for row in data['data']['rows']]

        if len(tickers) < num_stocks:
            print(f"Warning: Only {len(tickers)} stocks available. Using all of them.")
        else:
            random.shuffle(tickers)
            tickers = tickers[:num_stocks]

        return tickers
    except Exception as e:
        print(f"Error fetching tickers: {str(e)}")
        return []

def get_crypto_tickers(num_cryptos):
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": num_cryptos,
        "page": 1,
        "sparkline": False
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return [f"{crypto['symbol']}-USD" for crypto in data]  # Format for yfinance
    except Exception as e:
        print(f"Error fetching crypto tickers: {str(e)}")
        return []

def get_stock_data(ticker, period="3mo"):
    try:
        stock = yf.Ticker(ticker)
        history = stock.history(period=period)
        if history.empty:
            print(f"Warning: No data available for {ticker} in the specified period.")
            return None, None
        return stock, history
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

def get_recommendations(history, avg_weekly_change, is_crypto=False):
    current_price = history['Close'].iloc[-1]
    
    if is_crypto:
        # More aggressive strategy for cryptocurrencies
        buy_discount = max(0.05, abs(avg_weekly_change))
        sell_premium = max(0.07, 1.5 * abs(avg_weekly_change))
    else:
        # Conservative strategy for stocks
        buy_discount = max(0.02, abs(avg_weekly_change))
        sell_premium = max(0.03, abs(avg_weekly_change))
    
    buy_price = current_price * (1 - buy_discount)
    sell_price = current_price * (1 + sell_premium)
    
    return buy_price, sell_price

def analyze_asset(ticker, is_crypto=False):
    stock, history = get_stock_data(ticker)
    if history is None or history.empty or len(history) < 14:
        return None

    history['RSI'] = calculate_rsi(history)
    history['SMA_50'] = history['Close'].rolling(window=50).mean()
    history['SMA_200'] = history['Close'].rolling(window=200).mean()

    current_price = history['Close'].iloc[-1]
    current_rsi = history['RSI'].iloc[-1]
    sma_50 = history['SMA_50'].iloc[-1]
    sma_200 = history['SMA_200'].iloc[-1]

    # Adjust criteria for cryptocurrencies
    if is_crypto:
        if current_rsi < 50:  # More lenient RSI criterion for crypto
            avg_weekly_change = analyze_weekly_change(history)
            buy_price, sell_price = get_recommendations(history, avg_weekly_change, is_crypto=True)

            potential_gain_percentage = ((sell_price / buy_price) - 1) * 100
            potential_gain_dollars = (sell_price - buy_price)

            return {
                'ticker': ticker,
                'current_price': current_price,
                'rsi': current_rsi,
                'buy_price': buy_price,
                'sell_price': sell_price,
                'potential_gain_percentage': potential_gain_percentage,
                'potential_gain_dollars': potential_gain_dollars
            }
    else:
        if current_rsi < 40 and current_price > sma_50 * 0.95:
            avg_weekly_change = analyze_weekly_change(history)
            buy_price, sell_price = get_recommendations(history, avg_weekly_change)

            potential_gain_percentage = ((sell_price / buy_price) - 1) * 100
            potential_gain_dollars = (sell_price - buy_price)

            return {
                'ticker': ticker,
                'current_price': current_price,
                'rsi': current_rsi,
                'buy_price': buy_price,
                'sell_price': sell_price,
                'potential_gain_percentage': potential_gain_percentage,
                'potential_gain_dollars': potential_gain_dollars
            }

    return None

def find_promising_assets(tickers, max_workers=10, is_crypto=False):
    promising_assets = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(analyze_asset, ticker, is_crypto): ticker for ticker in tickers}
        for future in tqdm(as_completed(futures), total=len(tickers), desc="Analyzing assets"):
            result = future.result()
            if result:
                promising_assets.append(result)

    return sorted(promising_assets, key=lambda x: x['potential_gain_percentage'], reverse=True)

def display_asset_info(ticker, is_crypto=False):
    stock, history = get_stock_data(ticker, period="1y")

    if history is None or history.empty:
        print(f"Unable to fetch data for {ticker}")
        return

    current_price = history['Close'].iloc[-1]

    asset_type = "Cryptocurrency" if is_crypto else "Stock"

    data = [
        ["Current Price", f"${current_price:.2f}"],
        ["52 Week High", f"${history['Close'].max():.2f}"],
        ["52 Week Low", f"${history['Close'].min():.2f}"],
    ]

    if stock is not None:
        info = stock.info
        data.extend([
            ["Market Cap", f"${info.get('marketCap', 0) / 1e9:.2f}B"],
            ["Volume", f"{info.get('volume', 'N/A')}"],
        ])
        if not is_crypto:
            data.extend([
                ["P/E Ratio", f"{info.get('trailingPE', 'N/A')}"],
                ["Dividend Yield", f"{info.get('dividendYield', 0) * 100:.2f}%"],
            ])

    print(f"\n{asset_type} Information for {ticker}:")
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

    buy_price, sell_price = get_recommendations(history, avg_weekly_change, is_crypto)

    recommendation_data = [
        ["Recommended Buy Price", f"${buy_price:.2f}"],
        ["Recommended Sell Price", f"${sell_price:.2f}"],
    ]

    print("\nRecommendations:")
    print(tabulate(recommendation_data, headers=["Action", "Price"], tablefmt="grid"))

def main():
    while True:
        print("\nStock and Cryptocurrency Analysis Tool")
        print("1. Analyze a single stock")
        print("2. Analyze a single cryptocurrency")
        print("3. Search for promising stocks")
        print("4. Search for promising cryptocurrencies")
        print("5. Exit")

        choice = input("Enter your choice (1-5): ").strip()

        if choice in ['1', '2']:
            ticker = input("Enter the ticker symbol: ").strip().upper()
            if choice == '2':
                ticker = f"{ticker}-USD"
            display_asset_info(ticker, is_crypto=(choice == '2'))

        elif choice in ['3', '4']:
            while True:
                try:
                    num_assets = int(input("Enter the number of assets to search and analyze (recommended: 100 to 1000): "))
                    if num_assets > 0:
                        break
                    else:
                        print("Please enter a positive number.")
                except ValueError:
                    print("Please enter a valid integer.")

            is_crypto = (choice == '4')
            asset_type = "cryptocurrencies" if is_crypto else "stocks"
            print(f"Fetching {num_assets} {asset_type} tickers...")
            
            if is_crypto:
                tickers_to_analyze = get_crypto_tickers(num_assets)
            else:
                tickers_to_analyze = get_tickers(num_assets)

            if not tickers_to_analyze:
                print(f"No {asset_type} tickers found. Please try again later.")
                continue

            print(f"Retrieved {len(tickers_to_analyze)} tickers.")

            start_time = time.time()
            promising_assets = find_promising_assets(tickers_to_analyze, is_crypto=is_crypto)
            end_time = time.time()

            print(f"\nAnalysis completed in {end_time - start_time:.2f} seconds.")
            print(f"Found {len(promising_assets)} promising {asset_type}.")

            if not promising_assets:
                print(f"No promising {asset_type} found based on the current criteria.")
                continue

            while True:
                try:
                    top_n = int(input("Enter the number of top assets to display: "))
                    if top_n > 0:
                        break
                    else:
                        print("Please enter a positive number.")
                except ValueError:
                    print("Please enter a valid integer.")

            print(f"\nTop {min(top_n, len(promising_assets))} Promising {asset_type.capitalize()}:")
            for i, asset in enumerate(promising_assets[:top_n], 1):
                print(f"{i}. {asset['ticker']}:")
                print(f"   Current Price: ${asset['current_price']:.2f}")
                print(f"   RSI: {asset['rsi']:.2f}")
                print(f"   Recommended Buy Price: ${asset['buy_price']:.2f}")
                print(f"   Recommended Sell Price: ${asset['sell_price']:.2f}")
                print(f"   Potential Gain (%): {asset['potential_gain_percentage']:.2f} (${asset['potential_gain_dollars']:.2f})\n")

        elif choice == '5':
            print("Thank you for using the Stock and Cryptocurrency Analysis Tool. Goodbye!")
            break

        else:
            print("Invalid choice. Please enter 1, 2, 3, 4, or 5.")

if __name__ == "__main__":
    main()