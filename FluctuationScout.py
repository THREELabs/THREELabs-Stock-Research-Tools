import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import sys
import requests
import time

def get_coinbase_cryptos():
    url = "https://api.pro.coinbase.com/products"
    max_retries = 3
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raises an HTTPError for bad responses
            products = response.json()
            crypto_list = [f"{p['base_currency']}-USD" for p in products if p['quote_currency'] == 'USD']
            return crypto_list
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("Failed to fetch cryptocurrencies from Coinbase API after multiple attempts")
                return []

def calculate_fluctuations(ticker, days=30):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    for attempt in range(3):
        try:
            data = yf.Ticker(ticker).history(start=start_date, end=end_date)
            data['Daily_Fluctuation'] = ((data['High'] - data['Low']) / data['Low']) * 100
            return data['Daily_Fluctuation']
        except Exception as e:
            if attempt < 2:
                print(f"Attempt {attempt + 1} failed for {ticker}: {str(e)}. Retrying...")
                time.sleep(2)
            else:
                raise

def is_promising(fluctuations, min_percent=3, max_percent=5, frequency_threshold=0.5):
    in_range = ((fluctuations >= min_percent) & (fluctuations <= max_percent))
    frequency = in_range.mean()
    
    return frequency >= frequency_threshold

def scan_promising_cryptos(days=30, min_percent=3, max_percent=5, frequency_threshold=0.5):
    crypto_list = get_coinbase_cryptos()
    promising_cryptos = []
    
    total_cryptos = len(crypto_list)
    for index, crypto in enumerate(crypto_list, 1):
        try:
            print(f"Processing {crypto} ({index}/{total_cryptos})")
            fluctuations = calculate_fluctuations(crypto, days)
            if is_promising(fluctuations, min_percent, max_percent, frequency_threshold):
                promising_cryptos.append(crypto)
        except Exception as e:
            print(f"Error processing {crypto}: {str(e)}")
    
    return promising_cryptos

if __name__ == "__main__":
    print("Fetching list of cryptocurrencies from Coinbase...")
    
    days = int(input("Enter the number of days to analyze (default 30): ") or 30)
    min_percent = float(input("Enter the minimum fluctuation percentage (default 3): ") or 3)
    max_percent = float(input("Enter the maximum fluctuation percentage (default 5): ") or 5)
    frequency_threshold = float(input("Enter the frequency threshold (default 0.5): ") or 0.5)

    promising_list = scan_promising_cryptos(days, min_percent, max_percent, frequency_threshold)
    
    print(f"\nPromising cryptocurrencies ({len(promising_list)}):")
    for crypto in promising_list:
        print(crypto)
    
    # Save results to a file
    with open('promising_cryptos.txt', 'w') as f:
        for crypto in promising_list:
            f.write(f"{crypto}\n")
    
    print("Results saved to promising_cryptos.txt")