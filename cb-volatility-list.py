import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
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
        df['Daily Change %'] = (df['close'] - df['open']) / df['open'] * 100
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
    for col in ['low', 'high', 'open', 'close']:
        formatted_df[col] = formatted_df[col].round(4)
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
            
            annualized_volatility = calculate_volatility(df)
            if not np.isnan(annualized_volatility):
                daily_volatility = annualized_volatility / np.sqrt(365)
                avg_daily_change = df['Daily Change %'].abs().mean()
                volatilities.append((currency, annualized_volatility, daily_volatility, avg_daily_change))
                
                print(f"\nData for {currency}:")
                formatted_df = format_dataframe(df)
                print(formatted_df[['low', 'high', 'open', 'close', 'volume', 'Daily Change %']].head().to_string())
                print(f"\nNumber of rows: {len(df)}")
                print(f"Annualized Volatility: {annualized_volatility:.2%}")
                print(f"Estimated Daily Volatility: {daily_volatility:.2%}")
                print(f"Average Daily Change: {avg_daily_change:.2%}")
                print("\nNote: Annualized volatility does not mean the price changes by this percentage each day.")
                print("Daily changes are typically much smaller, as shown in the 'Daily Change %' column.")
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
    
    # Sort by annualized volatility and get top 10
    top_10 = sorted(volatilities, key=lambda x: x[1], reverse=True)[:10]
    
    print("\n" + "="*50)
    print("TOP 10 MOST VOLATILE CRYPTOCURRENCIES ON COINBASE")
    print("="*50)
    print(f"{'Currency':<10} {'Ann. Volatility':<20} {'Est. Daily Vol.':<20} {'Avg. Daily Change':<20}")
    print("-"*70)
    for currency, ann_vol, daily_vol, avg_change in top_10:
        print(f"{currency:<10} {ann_vol:18.2%} {daily_vol:18.2%} {avg_change:18.2%}")

if __name__ == "__main__":
    main()  