import requests
import pandas as pd
import pandas_ta as ta
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
        df.sort_index(inplace=True)  # Sort by date in ascending order
        df['Daily Change %'] = (df['close'] - df['open']) / df['open'] * 100
        return df
    else:
        print(f"Error fetching data for {currency_pair}: {response.status_code} - {response.text}")
        return pd.DataFrame()

def calculate_metrics(df):
    if len(df) < 14:  # Require at least 14 days of data for RSI
        return np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan

    # Calculate returns
    df['returns'] = df['close'].pct_change()

    # Volatility (annualized)
    volatility = df['returns'].std() * np.sqrt(365)

    # Sharpe Ratio (assuming risk-free rate of 0 for simplicity)
    sharpe_ratio = (df['returns'].mean() * 365) / volatility

    # Simple Moving Average (20-day)
    df['SMA_20'] = ta.sma(df['close'], length=20)

    # Relative Strength Index (14-day)
    df.ta.rsi(length=14, append=True)

    # Bollinger Bands
    df.ta.bbands(length=20, append=True)

    # MACD
    df.ta.macd(append=True)

    # Average Daily Volume (last 30 days)
    avg_volume = df['volume'].rolling(window=30).mean().iloc[-1]

    # Volume-Weighted Average Price (VWAP)
    df.ta.vwap(append=True)

    current_rsi = df['RSI_14'].iloc[-1] if 'RSI_14' in df.columns else np.nan
    current_bb_position = ((df['close'].iloc[-1] - df['BBL_20_2.0'].iloc[-1]) / 
                           (df['BBU_20_2.0'].iloc[-1] - df['BBL_20_2.0'].iloc[-1])) if 'BBL_20_2.0' in df.columns else np.nan
    current_macd = df['MACD_12_26_9'].iloc[-1] if 'MACD_12_26_9' in df.columns else np.nan
    current_macd_signal = df['MACDs_12_26_9'].iloc[-1] if 'MACDs_12_26_9' in df.columns else np.nan

    return volatility, sharpe_ratio, df['SMA_20'].iloc[-1], current_rsi, current_bb_position, current_macd, current_macd_signal, avg_volume

def calculate_relative_strength(df, benchmark_df):
    if len(df) != len(benchmark_df):
        return np.nan

    asset_returns = df['close'].pct_change()
    benchmark_returns = benchmark_df['close'].pct_change()

    relative_strength = (1 + asset_returns).cumprod().iloc[-1] / (1 + benchmark_returns).cumprod().iloc[-1]
    return relative_strength

def select_investment_options(results, trend, n=3):
    def score_currency(currency_data):
        _, volatility, sharpe_ratio, _, _, rsi, _, _, price_change_7d, bb_position, _, _, _, relative_strength = currency_data
        
        # Normalize RSI (50 is neutral, so we'll score based on distance from 50)
        rsi_score = 1 - abs(rsi - 50) / 50
        
        # Normalize volatility (lower is better)
        volatility_score = 1 - min(volatility, 1)  # Cap at 100% volatility
        
        # Sharpe ratio (higher is better)
        sharpe_score = min(max(sharpe_ratio, 0), 3) / 3  # Cap between 0 and 3
        
        # Recent performance
        performance_score = (price_change_7d + 10) / 20  # Normalize to 0-1 range, assuming -10% to +10% range
        
        # Relative strength (higher is better)
        strength_score = min(relative_strength, 2) / 2  # Cap at 2
        
        # Calculate total score (you can adjust weights as needed)
        total_score = (rsi_score * 0.2 + volatility_score * 0.2 + sharpe_score * 0.2 + 
                       performance_score * 0.2 + strength_score * 0.2)
        
        return total_score

    filtered_results = [r for r in results if r[7] == trend]
    scored_results = [(r, score_currency(r)) for r in filtered_results]
    sorted_results = sorted(scored_results, key=lambda x: x[1], reverse=True)
    
    return [r[0] for r in sorted_results[:n]]

def main():
    currencies = get_coinbase_currencies()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)  # Get data for the last 90 days

    # Get Bitcoin data as benchmark
    btc_df = get_historical_data("BTC-USD", start_date, end_date)

    results = []

    for currency in currencies:
        try:
            df = get_historical_data(f"{currency}-USD", start_date, end_date)
            if df.empty:
                print(f"No data available for {currency}-USD")
                continue

            print(f"\nAnalyzing {currency}:")
            print(f"DataFrame for {df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}:")
            print(df.head())
            print(df.tail())
            print(f"DataFrame shape: {df.shape}")

            volatility, sharpe_ratio, sma_20, rsi, bb_position, macd, macd_signal, avg_volume = calculate_metrics(df)
            
            if not (np.isnan(volatility) or np.isnan(rsi) or np.isnan(bb_position) or np.isnan(macd) or np.isnan(macd_signal)):
                current_price = df['close'].iloc[-1]
                avg_daily_change = df['Daily Change %'].abs().mean()
                trend = 'uptrend' if current_price > sma_20 else 'downtrend'

                # Calculate 7-day price change
                price_change_7d = (df['close'].iloc[-1] - df['close'].iloc[-7]) / df['close'].iloc[-7] * 100

                # Calculate relative strength
                relative_strength = calculate_relative_strength(df, btc_df)

                results.append((currency, volatility, sharpe_ratio, current_price, sma_20, rsi, avg_daily_change, trend, price_change_7d, bb_position, macd, macd_signal, avg_volume, relative_strength))
            else:
                print(f"Insufficient data for complete analysis of {currency}")

            time.sleep(0.5)  # Add a delay to avoid rate limiting
        except Exception as e:
            print(f"Failed to get data for {currency}: {str(e)}")

    # Sort by 7-day price change and get top 10 uptrend (Momentum Movers)
    momentum_movers = sorted([r for r in results if r[7] == 'uptrend'], key=lambda x: x[8], reverse=True)[:10]

    # Sort by 7-day price change and get top 10 downtrend
    top_10_downtrend = sorted([r for r in results if r[7] == 'downtrend'], key=lambda x: x[8])[:10]

    print("\n" + "="*180)
    print("TOP 10 MOMENTUM MOVERS (UPTRENDING CRYPTOCURRENCIES) ON COINBASE")
    print("="*180)
    print(f"{'Currency':<10} {'Volatility':<12} {'Sharpe Ratio':<15} {'Price':<10} {'SMA(20)':<10} {'RSI':<10} {'Avg Daily Change':<18} {'7d Change':<12} {'BB Position':<12} {'MACD':<10} {'MACD Signal':<12} {'Avg Volume':<12} {'Relative Strength':<18}")
    print("-"*180)
    for currency, vol, sharpe, price, sma, rsi, avg_change, trend, price_change_7d, bb_position, macd, macd_signal, avg_volume, relative_strength in momentum_movers:
        print(f"{currency:<10} {vol:10.2%} {sharpe:13.2f} ${price:<8.2f} ${sma:<8.2f} {rsi:<8.2f} {avg_change:16.2%} {price_change_7d:10.2f}% {bb_position:10.2f} {macd:8.2f} {macd_signal:10.2f} {avg_volume:10.2f} {relative_strength:16.2f}")

    print("\n" + "="*180)
    print("TOP 10 DOWNTRENDING CRYPTOCURRENCIES ON COINBASE")
    print("="*180)
    print(f"{'Currency':<10} {'Volatility':<12} {'Sharpe Ratio':<15} {'Price':<10} {'SMA(20)':<10} {'RSI':<10} {'Avg Daily Change':<18} {'7d Change':<12} {'BB Position':<12} {'MACD':<10} {'MACD Signal':<12} {'Avg Volume':<12} {'Relative Strength':<18}")
    print("-"*180)
    for currency, vol, sharpe, price, sma, rsi, avg_change, trend, price_change_7d, bb_position, macd, macd_signal, avg_volume, relative_strength in top_10_downtrend:
        print(f"{currency:<10} {vol:10.2%} {sharpe:13.2f} ${price:<8.2f} ${sma:<8.2f} {rsi:<8.2f} {avg_change:16.2%} {price_change_7d:10.2f}% {bb_position:10.2f} {macd:8.2f} {macd_signal:10.2f} {avg_volume:10.2f} {relative_strength:16.2f}")

    # Select top 3 investment options for uptrend and downtrend
    uptrend_options = select_investment_options(results, 'uptrend', 3)
    downtrend_options = select_investment_options(results, 'downtrend', 3)

    print("\n" + "="*180)
    print("TOP 3 INVESTMENT OPTIONS (UPTREND)")
    print("="*180)
    print(f"{'Currency':<10} {'Volatility':<12} {'Sharpe Ratio':<15} {'Price':<10} {'RSI':<10} {'7d Change':<12} {'BB Position':<12} {'Relative Strength':<18}")
    print("-"*180)
    for currency, vol, sharpe, price, _, rsi, _, _, price_change_7d, bb_position, _, _, _, relative_strength in uptrend_options:
        print(f"{currency:<10} {vol:10.2%} {sharpe:13.2f} ${price:<8.2f} {rsi:<8.2f} {price_change_7d:10.2f}% {bb_position:10.2f} {relative_strength:16.2f}")

    print("\n" + "="*180)
    print("TOP 3 INVESTMENT OPTIONS (DOWNTREND)")
    print("="*180)
    print(f"{'Currency':<10} {'Volatility':<12} {'Sharpe Ratio':<15} {'Price':<10} {'RSI':<10} {'7d Change':<12} {'BB Position':<12} {'Relative Strength':<18}")
    print("-"*180)
    for currency, vol, sharpe, price, _, rsi, _, _, price_change_7d, bb_position, _, _, _, relative_strength in downtrend_options:
        print(f"{currency:<10} {vol:10.2%} {sharpe:13.2f} ${price:<8.2f} {rsi:<8.2f} {price_change_7d:10.2f}% {bb_position:10.2f} {relative_strength:16.2f}")

    print("\nInvestment Options Interpretation Guide:")
    print("- Uptrend options: These cryptocurrencies are showing positive momentum and could be considered for long positions or momentum trading strategies.")
    print("- Downtrend options: These cryptocurrencies are currently in a downtrend but may present potential value or reversal opportunities. Exercise caution and consider your risk tolerance.")
    print("- The selection is based on a combination of factors including RSI, volatility, Sharpe ratio, recent performance, and relative strength compared to Bitcoin.")
    print("\nRemember: This analysis is based on historical data and should not be considered as financial advice. Always conduct thorough research and consider your risk tolerance before investing.")

if __name__ == "__main__":
    main()