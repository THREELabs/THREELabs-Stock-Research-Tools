import requests
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import time

def get_coinbase_currencies():
    url = "https://api.exchange.coinbase.com/currencies"
    response = requests.get(url)
    return [currency['id'] for currency in response.json() if currency['details']['type'] == 'crypto']

def get_historical_data(currency_pair, start_date, end_date):
    url = f"https://api.exchange.coinbase.com/products/{currency_pair}/candles"
    params = {
        'start': start_date.isoformat(),
        'end': end_date.isoformat(),
        'granularity': 86400  # Daily candles
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        df = pd.DataFrame(response.json(), columns=['time', 'low', 'high', 'open', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        df['Daily Change %'] = (df['close'] - df['open']) / df['open'] * 100  # Calculate daily percentage change
        return df
    else:
        print(f"Error fetching data for {currency_pair}: {response.status_code} - {response.text}")
        return pd.DataFrame()

def calculate_volatility(df):
    if len(df) < 7:  # Require at least 7 days of data
        return np.nan
    
    log_returns = np.log(df['close'] / df['close'].shift(1))
    return log_returns.std() * np.sqrt(365)  # Annualized volatility

def format_dataframe(df):
    formatted_df = df.copy()
    formatted_df['low'] = formatted_df['low'].round(4)
    formatted_df['high'] = formatted_df['high'].round(4)
    formatted_df['open'] = formatted_df['open'].round(4)
    formatted_df['close'] = formatted_df['close'].round(4)
    formatted_df['volume'] = formatted_df['volume'].round(2)
    formatted_df['Daily Change %'] = formatted_df['Daily Change %'].round(2)
    return formatted_df

def main():
    currencies = get_coinbase_currencies()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)  # Get data for the last 90 days
    
    volatilities = []
    
    for currency in currencies:
        try:
            df = get_historical_data(f"{currency}-USD", start_date, end_date)
            if df.empty:
                print(f"No data available for {currency}-USD")
                continue
            
            volatility = calculate_volatility(df)
            if not np.isnan(volatility):
                volatilities.append((currency, volatility))
                print(f"\nData for {currency}:")
                formatted_df = format_dataframe(df)
                print(formatted_df[['low', 'high', 'open', 'close', 'volume', 'Daily Change %']].head().to_string())
                print(f"\nNumber of rows: {len(df)}")
                print(f"Volatility: {volatility:.2%}")
                print("---")
            else:
                print(f"Insufficient data for {currency}")
                print(f"Data for {currency}:")
                print(df)
                print(f"Number of rows: {len(df)}")
                print("---")
            
            time.sleep(0.5)  # Add a delay to avoid rate limiting
        except Exception as e:
            print(f"Failed to get data for {currency}: {str(e)}")
    
    # Sort by volatility and get top 10
    top_10 = sorted(volatilities, key=lambda x: x[1], reverse=True)[:10]
    
    print("\nTop 10 most volatile cryptocurrencies on Coinbase:")
    for currency, volatility in top_10:
        print(f"{currency}: {volatility:.2%} average daily volatility")

if __name__ == "__main__":
    main()