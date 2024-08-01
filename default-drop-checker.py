import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
import requests

# Configurable Parameters
ANALYSIS_TYPE = 'both'  # Options: 'crypto', 'stocks', 'both'
FLUCTUATION_THRESHOLD = 10  # Percentage
WEEKS_TO_CHECK = 3
MAX_INSTRUMENTS_TO_ANALYZE = 100  # Set to None for no limit
VERBOSE = True  # Set to False for less detailed output

def get_crypto_symbols():
    url = "https://finance.yahoo.com/cryptocurrencies/?count=100&offset=0"
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    
    tables = pd.read_html(response.text)
    if tables:
        crypto_df = tables[0]
        return crypto_df['Symbol'].tolist()[:MAX_INSTRUMENTS_TO_ANALYZE]
    return []

def get_stock_symbols():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    tables = pd.read_html(url)
    if tables:
        stocks_df = tables[0]
        return stocks_df['Symbol'].tolist()[:MAX_INSTRUMENTS_TO_ANALYZE]
    return []

def get_financial_data(symbol, start_date, end_date):
    ticker = yf.Ticker(symbol)
    data = ticker.history(start=start_date, end=end_date)
    return data['Close']

def calculate_weekly_fluctuation(prices):
    weekly_fluctuation = (prices.pct_change() * 100).abs()
    return weekly_fluctuation.resample('W').max()

def check_fluctuation(symbol):
    end_date = datetime.now()
    start_date = end_date - timedelta(weeks=WEEKS_TO_CHECK + 1)  # Extra week to ensure we have enough data

    try:
        prices = get_financial_data(symbol, start_date, end_date)
        if len(prices) < WEEKS_TO_CHECK:  # Ensure we have enough weeks of data
            return False
        weekly_fluctuation = calculate_weekly_fluctuation(prices)

        # Check if the last WEEKS_TO_CHECK weeks had fluctuations >= threshold
        last_weeks = weekly_fluctuation.tail(WEEKS_TO_CHECK)
        return all(last_weeks >= FLUCTUATION_THRESHOLD)
    except Exception as e:
        if VERBOSE:
            print(f"Error processing {symbol}: {str(e)}")
        return False

def analyze_instruments(instruments, instrument_type):
    print(f"\nAnalyzing {instrument_type}...")
    print(f"Checking for fluctuations of {FLUCTUATION_THRESHOLD}% or more every week for the last {WEEKS_TO_CHECK} weeks.")
    
    fluctuating_instruments = []

    for i, instrument in enumerate(instruments, 1):
        if check_fluctuation(instrument):
            fluctuating_instruments.append(instrument)
            if VERBOSE:
                print(f"{instrument} has been fluctuating {FLUCTUATION_THRESHOLD}% or more every week for the last {WEEKS_TO_CHECK} weeks.")
        if VERBOSE:
            print(f"Processed {i}/{len(instruments)} {instrument_type}", end='\r')

    print(f"\n\nSummary for {instrument_type}:")
    print(f"Total {instrument_type} analyzed: {len(instruments)}")
    print(f"{instrument_type.capitalize()} with significant fluctuations: {len(fluctuating_instruments)}")
    
    if fluctuating_instruments:
        print(f"\nList of {instrument_type} with significant fluctuations:")
        for instrument in fluctuating_instruments:
            print(instrument)
    else:
        print(f"\nNo {instrument_type} met the fluctuation criteria.")

def main():
    if ANALYSIS_TYPE in ['crypto', 'both']:
        crypto_list = get_crypto_symbols()
        if crypto_list:
            analyze_instruments(crypto_list, "cryptocurrencies")
        else:
            print("Failed to fetch cryptocurrency list. Please check your internet connection or try again later.")

    if ANALYSIS_TYPE in ['stocks', 'both']:
        stock_list = get_stock_symbols()
        if stock_list:
            analyze_instruments(stock_list, "stocks")
        else:
            print("Failed to fetch stock list. Please check your internet connection or try again later.")

if __name__ == "__main__":
    main()
