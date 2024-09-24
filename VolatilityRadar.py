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

def format_dataframe(df):
    formatted_df = df.copy()
    for col in ['low', 'high', 'open', 'close']:
        formatted_df[col] = formatted_df[col].round(4)
    formatted_df['volume'] = formatted_df['volume'].round(2)
    formatted_df['Daily Change %'] = formatted_df['Daily Change %'].round(2)
    return formatted_df

def calculate_metrics(df):
    if len(df) < 14:  # Require at least 14 days of data for RSI
        return np.nan, np.nan, np.nan, np.nan
    
    # Calculate returns
    df['returns'] = df['close'].pct_change()
    
    # Volatility (annualized)
    volatility = df['returns'].std() * np.sqrt(365)
    
    # Sharpe Ratio (assuming risk-free rate of 0 for simplicity)
    sharpe_ratio = (df['returns'].mean() * 365) / volatility
    
    # Simple Moving Average (20-day)
    df['SMA_20'] = df['close'].rolling(window=20).mean()
    
    # Relative Strength Index (14-day)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    current_rsi = df['RSI'].iloc[-1]
    
    return volatility, sharpe_ratio, df['SMA_20'].iloc[-1], current_rsi

def main():
    currencies = get_coinbase_currencies()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)  # Get data for the last 90 days
    
    results = []
    
    for currency in currencies:
        try:
            df = get_historical_data(f"{currency}-USD", start_date, end_date)
            if df.empty:
                print(f"No data available for {currency}-USD")
                continue
            
            volatility, sharpe_ratio, sma_20, rsi = calculate_metrics(df)
            if not np.isnan(volatility):
                current_price = df['close'].iloc[-1]
                avg_daily_change = df['Daily Change %'].abs().mean()
                results.append((currency, volatility, sharpe_ratio, current_price, sma_20, rsi, avg_daily_change))
                
                print(f"\nData for {currency}:")
                formatted_df = format_dataframe(df)
                print(formatted_df[['low', 'high', 'open', 'close', 'volume', 'Daily Change %']].tail().to_string())
                print(f"\nNumber of rows: {len(df)}")
                print(f"Annualized Volatility: {volatility:.2%}")
                print(f"Sharpe Ratio: {sharpe_ratio:.2f}")
                print(f"Current Price: ${current_price:.2f}")
                print(f"20-day SMA: ${sma_20:.2f}")
                print(f"RSI: {rsi:.2f}")
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
    
    # Sort by volatility and get top 10
    top_10 = sorted(results, key=lambda x: x[1], reverse=True)[:10]
    
    print("\n" + "="*100)
    print("TOP 10 MOST VOLATILE CRYPTOCURRENCIES ON COINBASE WITH METRICS")
    print("="*100)
    print(f"{'Currency':<10} {'Volatility':<12} {'Sharpe Ratio':<15} {'Price':<10} {'SMA(20)':<10} {'RSI':<10} {'Avg Daily Change':<18}")
    print("-"*100)
    for currency, vol, sharpe, price, sma, rsi, avg_change in top_10:
        print(f"{currency:<10} {vol:10.2%} {sharpe:13.2f} ${price:<8.2f} ${sma:<8.2f} {rsi:<8.2f} {avg_change:16.2%}")

    print("\nInterpretation Guide:")
    print("- Volatility: Higher values indicate higher risk and potential for larger price swings.")
    print("- Sharpe Ratio: Higher values suggest better risk-adjusted returns historically.")
    print("- Price vs SMA: Price above SMA might indicate an uptrend, below might indicate a downtrend.")
    print("- RSI: Values above 70 may indicate overbought conditions, below 30 may indicate oversold.")
    print("- Avg Daily Change: Gives an idea of the typical daily price movement.")
    print("\nRemember: Past performance does not guarantee future results. Always consider your risk tolerance.")

if __name__ == "__main__":
    main()