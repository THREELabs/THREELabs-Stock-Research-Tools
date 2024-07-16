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

def get_recommendations(history, avg_weekly_change):
    current_price = history['Close'].iloc[-1]
    
    # Calculate buy price: Use a larger discount for negative weekly changes
    discount = max(0.02, abs(avg_weekly_change)) if avg_weekly_change < 0 else 0.02
    buy_price = current_price * (1 - discount)
    
    # Calculate sell price: Ensure it's always higher than the current price
    sell_price = current_price * (1 + max(0.02, avg_weekly_change))
    
    return buy_price, sell_price

def analyze_stock(ticker):
    stock, history = get_stock_data(ticker)
    if stock is None or history is None or history.empty or len(history) < 14:  # Minimum data for RSI calculation
        return None

    history['RSI'] = calculate_rsi(history)
    history['SMA_50'] = history['Close'].rolling(window=50).mean()
    history['SMA_200'] = history['Close'].rolling(window=200).mean()

    current_price = history['Close'].iloc[-1]
    current_rsi = history['RSI'].iloc[-1]
    sma_50 = history['SMA_50'].iloc[-1]
    sma_200 = history['SMA_200'].iloc[-1]

    # Relaxed criteria for promising stocks
    if (current_rsi < 40 and current_price > sma_50 * 0.95):  # Relaxed RSI and price condition
        avg_weekly_change = analyze_weekly_change(history)
        buy_price, sell_price = get_recommendations(history, avg_weekly_change)

        return {
            'ticker': ticker,
            'current_price': current_price,
            'rsi': current_rsi,
            'buy_price': buy_price,
            'sell_price': sell_price,
            'potential_gain': (sell_price / buy_price - 1) * 100
        }

    return None

def find_promising_stocks(tickers, max_workers=10):
    promising_stocks = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(analyze_stock, ticker): ticker for ticker in tickers}
        for future in tqdm(as_completed(futures), total=len(tickers), desc="Analyzing stocks"):
            result = future.result()
            if result:
                promising_stocks.append(result)

    return sorted(promising_stocks, key=lambda x: x['potential_gain'], reverse=True)

def display_stock_info(ticker):
    stock, history = get_stock_data(ticker, period="1y")

    if stock is None or history is None or history.empty:
        print(f"Unable to fetch data for {ticker}")
        return

    info = stock.info
    current_price = history['Close'].iloc[-1]

    data = [
        ["Current Price", f"${current_price:.2f}"],
        ["52 Week High", f"${info.get('fiftyTwoWeekHigh', 'N/A')}"],
        ["52 Week Low", f"${info.get('fiftyTwoWeekLow', 'N/A')}"],
        ["Market Cap", f"${info.get('marketCap', 0) / 1e9:.2f}B"],
        ["P/E Ratio", f"{info.get('trailingPE', 'N/A')}"],
        ["Dividend Yield", f"{info.get('dividendYield', 0) * 100:.2f}%"],
    ]

    print(f"\nStock Information for {ticker}:")
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

def display_glossary():
    glossary = {
        "Stock": "A share in the ownership of a company, representing a claim on the company's assets and earnings.",
        "Bull Market": "A market condition in which stock prices are rising or are expected to rise.",
        "Bear Market": "A market condition in which stock prices are falling or are expected to fall.",
        "Dividend": "A portion of a company's earnings paid out to shareholders.",
        "P/E Ratio": "Price-to-Earnings Ratio, a valuation ratio of a company's current share price compared to its per-share earnings.",
        "Market Cap": "The total dollar market value of a company's outstanding shares.",
        "Volume": "The number of shares traded during a given time period.",
        "Yield": "The income return on an investment, such as the interest or dividends received from holding a particular security.",
        "IPO": "Initial Public Offering, the first sale of stock by a private company to the public.",
        "Volatility": "A statistical measure of the dispersion of returns for a given security or market index.",
        "Blue Chip": "Stock of a large, well-established and financially sound company that has operated for many years.",
        "RSI": "Relative Strength Index, a momentum indicator that measures the magnitude of recent price changes to evaluate overbought or oversold conditions.",
        "SMA": "Simple Moving Average, an arithmetic moving average calculated by adding recent prices and then dividing that by the number of time periods in the calculation average.",
        "Broker": "An individual or firm that charges a fee or commission for executing buy and sell orders submitted by an investor.",
        "Exchange": "A marketplace in which securities, commodities, derivatives and other financial instruments are traded.",
        "NASDAQ": "National Association of Securities Dealers Automated Quotations, a global electronic marketplace for buying and selling securities.",
        "NYSE": "New York Stock Exchange, the world's largest securities exchange by market capitalization.",
        "SEC": "Securities and Exchange Commission, a U.S. government agency responsible for enforcing federal securities laws and regulating the securities industry.",
        "Portfolio": "A grouping of financial assets such as stocks, bonds, commodities, currencies and cash equivalents.",
        "Diversification": "A risk management strategy that mixes a wide variety of investments within a portfolio."
    }

    print("\nStock Market Glossary:")
    for term, definition in glossary.items():
        print(f"\n{term}:")
        print(f"  {definition}")

def main():
    while True:
        print("\nStock Analysis Tool")
        print("1. Analyze a single stock")
        print("2. Search for promising stocks")
        print("3. View Stock Market Glossary")
        print("4. Exit")

        choice = input("Enter your choice (1-4): ").strip()

        if choice == '1':
            ticker = input("Enter the stock ticker symbol: ").strip().upper()
            display_stock_info(ticker)

        elif choice == '2':
            while True:
                try:
                    num_stocks = int(input("Enter the number of stocks to search and analyze (recommended: 100 to 1000): "))
                    if num_stocks > 0:
                        break
                    else:
                        print("Please enter a positive number.")
                except ValueError:
                    print("Please enter a valid integer.")

            print(f"Fetching {num_stocks} stock tickers...")
            tickers_to_analyze = get_tickers(num_stocks)

            if not tickers_to_analyze:
                print("No tickers found. Please try again later.")
                continue

            print(f"Retrieved {len(tickers_to_analyze)} tickers.")

            start_time = time.time()
            promising_stocks = find_promising_stocks(tickers_to_analyze)
            end_time = time.time()

            print(f"\nAnalysis completed in {end_time - start_time:.2f} seconds.")
            print(f"Found {len(promising_stocks)} promising stocks.")

            if not promising_stocks:
                print("No promising stocks found based on the current criteria.")
                continue

            while True:
                try:
                    top_n = int(input("Enter the number of top stocks to display: "))
                    if top_n > 0:
                        break
                    else:
                        print("Please enter a positive number.")
                except ValueError:
                    print("Please enter a valid integer.")

            print(f"\nTop {min(top_n, len(promising_stocks))} Promising Stocks:")
            for i, stock in enumerate(promising_stocks[:top_n], 1):
                print(f"{i}. {stock['ticker']}:")
                print(f"   Current Price: ${stock['current_price']:.2f}")
                print(f"   RSI: {stock['rsi']:.2f}")
                print(f"   Recommended Buy Price: ${stock['buy_price']:.2f}")
                print(f"   Recommended Sell Price: ${stock['sell_price']:.2f}")
                print(f"   Potential Gain: {stock['potential_gain']:.2%}\n")

        elif choice == '3':
            display_glossary()

        elif choice == '4':
            print("Thank you for using the Stock Analysis Tool. Goodbye!")
            break

        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")

if __name__ == "__main__":
    main()