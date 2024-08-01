#checking for crypto that are dipping 10% for 3 weeks in a row
#libaries required !pip install yfinance pandas requests

import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
import requests

# Configurable Parameters
FLUCTUATION_THRESHOLD = 1  # Percentage
WEEKS_TO_CHECK = 3
MAX_CRYPTOS_TO_ANALYZE = 100  # Set to None for no limit
VERBOSE = True  # Set to False for less detailed output

def get_all_crypto_symbols():
    url = "https://finance.yahoo.com/cryptocurrencies/?count=100&offset=0"
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    
    tables = pd.read_html(response.text)
    if tables:
        crypto_df = tables[0]
        return crypto_df['Symbol'].tolist()[:MAX_CRYPTOS_TO_ANALYZE]
    return []

def get_crypto_data(symbol, start_date, end_date):
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
        prices = get_crypto_data(symbol, start_date, end_date)
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

def main():
    print(f"Fetching list of cryptocurrencies (max {MAX_CRYPTOS_TO_ANALYZE if MAX_CRYPTOS_TO_ANALYZE else 'all'})...")
    crypto_list = get_all_crypto_symbols()
    
    if not crypto_list:
        print("Failed to fetch cryptocurrency list. Please check your internet connection or try again later.")
        return

    print(f"Analyzing fluctuations for {len(crypto_list)} cryptocurrencies...")
    print(f"Checking for fluctuations of {FLUCTUATION_THRESHOLD}% or more every week for the last {WEEKS_TO_CHECK} weeks.")
    
    fluctuating_cryptos = []

    for i, crypto in enumerate(crypto_list, 1):
        if check_fluctuation(crypto):
            fluctuating_cryptos.append(crypto)
            if VERBOSE:
                print(f"{crypto} has been fluctuating {FLUCTUATION_THRESHOLD}% or more every week for the last {WEEKS_TO_CHECK} weeks.")
        if VERBOSE:
            print(f"Processed {i}/{len(crypto_list)} cryptocurrencies", end='\r')

    print("\n\nSummary:")
    print(f"Total cryptocurrencies analyzed: {len(crypto_list)}")
    print(f"Cryptocurrencies with significant fluctuations: {len(fluctuating_cryptos)}")
    
    if fluctuating_cryptos:
        print("\nList of cryptocurrencies with significant fluctuations:")
        for crypto in fluctuating_cryptos:
            print(crypto)
    else:
        print("\nNo cryptocurrencies met the fluctuation criteria.")

if __name__ == "__main__":
    main()
