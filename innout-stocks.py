#pip install pandas numpy requests tabulate matplotlib scikit-learn textblob plotly beautifulsoup4 fredapi


import yfinance as yf
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import time
import random
import requests
from tabulate import tabulate
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from textblob import TextBlob
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from bs4 import BeautifulSoup
from fredapi import Fred

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

def calculate_macd(data, short_window=12, long_window=26, signal_window=9):
    short_ema = data['Close'].ewm(span=short_window, adjust=False).mean()
    long_ema = data['Close'].ewm(span=long_window, adjust=False).mean()
    macd = short_ema - long_ema
    signal = macd.ewm(span=signal_window, adjust=False).mean()
    return macd, signal

def calculate_bollinger_bands(data, window=20, num_std=2):
    rolling_mean = data['Close'].rolling(window=window).mean()
    rolling_std = data['Close'].rolling(window=window).std()
    upper_band = rolling_mean + (rolling_std * num_std)
    lower_band = rolling_mean - (rolling_std * num_std)
    return upper_band, lower_band

def calculate_fibonacci_retracements(data):
    high = data['High'].max()
    low = data['Low'].min()
    diff = high - low
    levels = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1]
    retracements = [high - (diff * level) for level in levels]
    return retracements

def calculate_position_size(account_size, risk_per_trade, entry_price, stop_loss):
    risk_amount = account_size * risk_per_trade
    position_size = risk_amount / (entry_price - stop_loss)
    return position_size

def backtest_strategy(data, strategy_function):
    results = strategy_function(data)
    return results

def get_real_time_data(ticker):
    stock = yf.Ticker(ticker)
    data = stock.history(period="1d", interval="1m")
    return data

def analyze_sentiment(ticker):
    url = f"https://finviz.com/quote.ashx?t={ticker}"
    resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(resp.text, 'html.parser')
    news_table = soup.find(id='news-table')
    news_rows = news_table.findAll('tr')
    
    parsed_news = []
    for row in news_rows:
        title = row.a.get_text()
        date_data = row.td.text.split(' ')
        if len(date_data) == 1:
            time = date_data[0]
        else:
            date = date_data[0]
            time = date_data[1]
        parsed_news.append([date, time, title])
    
    sentiment_scores = [TextBlob(article[2]).sentiment.polarity for article in parsed_news]
    return np.mean(sentiment_scores)

def plot_interactive_chart(data, ticker):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, subplot_titles=(f'{ticker} Stock Price', 'Volume'), 
                        row_width=[0.2, 0.7])

    fig.add_trace(go.Candlestick(x=data.index,
                                 open=data['Open'],
                                 high=data['High'],
                                 low=data['Low'],
                                 close=data['Close'],
                                 name='Price'),
                  row=1, col=1)

    fig.add_trace(go.Bar(x=data.index, y=data['Volume'], name='Volume'),
                  row=2, col=1)

    fig.update_layout(height=600, width=1000, title_text=f"{ticker} Stock Analysis")
    fig.show()

def analyze_portfolio(portfolio):
    total_value = sum(stock['value'] for stock in portfolio)
    weights = [stock['value'] / total_value for stock in portfolio]
    returns = [stock['return'] for stock in portfolio]
    
    portfolio_return = sum(w * r for w, r in zip(weights, returns))
    portfolio_risk = np.sqrt(sum((w * r)**2 for w, r in zip(weights, returns)))
    
    return portfolio_return, portfolio_risk

def get_economic_indicators():
    fred = Fred(api_key='d48823c5969661b080289ace4e0df569')
    gdp_growth = fred.get_series('GDP')
    unemployment_rate = fred.get_series('UNRATE')
    inflation_rate = fred.get_series('CPIAUCSL')
    
    return gdp_growth, unemployment_rate, inflation_rate

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
    if stock is None or history is None or history.empty or len(history) < 14:
        return None

    history['RSI'] = calculate_rsi(history)
    history['SMA_50'] = history['Close'].rolling(window=50).mean()
    history['SMA_200'] = history['Close'].rolling(window=200).mean()
    history['MACD'], history['Signal'] = calculate_macd(history)
    history['Upper_BB'], history['Lower_BB'] = calculate_bollinger_bands(history)

    current_price = history['Close'].iloc[-1]
    current_rsi = history['RSI'].iloc[-1]
    sma_50 = history['SMA_50'].iloc[-1]
    sma_200 = history['SMA_200'].iloc[-1]

    fib_levels = calculate_fibonacci_retracements(history)
    sentiment = analyze_sentiment(ticker)

    if (current_rsi < 40 and current_price > sma_50 * 0.95):
        avg_weekly_change = analyze_weekly_change(history)
        buy_price, sell_price = get_recommendations(history, avg_weekly_change)

        return {
            'ticker': ticker,
            'current_price': current_price,
            'rsi': current_rsi,
            'buy_price': buy_price,
            'sell_price': sell_price,
            'potential_gain': (sell_price / buy_price - 1) * 100,
            'fibonacci_levels': fib_levels,
            'sentiment': sentiment
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

    # Display technical indicators
    print("\nTechnical Indicators:")
    print(f"RSI: {calculate_rsi(history).iloc[-1]:.2f}")
    macd, signal = calculate_macd(history)
    print(f"MACD: {macd.iloc[-1]:.2f}")
    print(f"MACD Signal: {signal.iloc[-1]:.2f}")
    upper_bb, lower_bb = calculate_bollinger_bands(history)
    print(f"Bollinger Bands: Upper {upper_bb.iloc[-1]:.2f}, Lower {lower_bb.iloc[-1]:.2f}")

    # Display Fibonacci retracements
    fib_levels = calculate_fibonacci_retracements(history)
    print("\nFibonacci Retracement Levels:")
    for level, price in zip([0, 23.6, 38.2, 50, 61.8, 78.6, 100], fib_levels):
        print(f"{level}%: ${price:.2f}")

    # Display sentiment analysis
    sentiment = analyze_sentiment(ticker)
    print(f"\nNews Sentiment: {sentiment:.2f} (-1 to 1, where 1 is most positive)")

    # Plot interactive chart
    plot_interactive_chart(history, ticker)

