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

def simulate_trading_strategy(df, buy_dip_percentage=5, sell_rise_percentage=5):
    df = df.copy()
    df['buy_signal'] = df['close'] <= df['close'].shift(1) * (1 - buy_dip_percentage/100)
    df['sell_signal'] = df['close'] >= df['close'].shift(1) * (1 + sell_rise_percentage/100)

    position = 0
    entry_price = 0
    trades = []

    for i, row in df.iterrows():
        if position == 0 and row['buy_signal']:
            position = 1
            entry_price = row['close']
            trades.append(('buy', i, entry_price))
        elif position == 1 and row['sell_signal']:
            position = 0
            exit_price = row['close']
            trades.append(('sell', i, exit_price))

    if position == 1:
        trades.append(('sell', df.index[-1], df['close'].iloc[-1]))

    return trades

def calculate_strategy_performance(trades):
    if len(trades) < 2:
        return 0, 0

    total_return = 1
    num_trades = len(trades) // 2

    for i in range(0, len(trades) - 1, 2):
        buy_price = trades[i][2]
        sell_price = trades[i+1][2]
        trade_return = sell_price / buy_price
        total_return *= trade_return

    total_return_percentage = (total_return - 1) * 100
    avg_return_per_trade = (total_return ** (1/num_trades) - 1) * 100

    return total_return_percentage, avg_return_per_trade

def calculate_trend(df, window=14):
    df['SMA'] = df['close'].rolling(window=window).mean()
    df['trend'] = np.where(df['close'] > df['SMA'], 'uptrend', 'downtrend')
    return df['trend'].iloc[-1]

def select_top_picks(crypto_list, num_picks=2):
    # Sort by a combination of factors: 7-day change, Sharpe ratio, and RSI
    sorted_list = sorted(crypto_list, key=lambda x: (x[10], x[2], 70 - abs(x[5] - 50)), reverse=True)
    return sorted_list[:num_picks]

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
                trend = calculate_trend(df)

                # Calculate 7-day price change
                price_change_7d = (df['close'].iloc[-1] - df['close'].iloc[-8]) / df['close'].iloc[-8] * 100

                # Simulate trading strategy
                trades = simulate_trading_strategy(df)
                total_return, avg_return_per_trade = calculate_strategy_performance(trades)

                results.append((currency, volatility, sharpe_ratio, current_price, sma_20, rsi, avg_daily_change, total_return, avg_return_per_trade, trend, price_change_7d))

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
                print(f"Strategy Total Return: {total_return:.2%}")
                print(f"Strategy Average Return per Trade: {avg_return_per_trade:.2%}")
                print(f"Current Trend: {trend}")
                print(f"7-day Price Change: {price_change_7d:.2f}%")
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

    # Sort by 7-day price change and get top 10 uptrend (Momentum Movers)
    momentum_movers = sorted([r for r in results if r[9] == 'uptrend'], key=lambda x: x[10], reverse=True)[:10]

    # Sort by 7-day price change and get top 10 downtrend
    top_10_downtrend = sorted([r for r in results if r[9] == 'downtrend'], key=lambda x: x[10])[:10]

    # Select top picks
    uptrend_picks = select_top_picks([r for r in results if r[9] == 'uptrend'])
    downtrend_picks = select_top_picks([r for r in results if r[9] == 'downtrend'])

    print("\n" + "="*140)
    print("TOP 10 MOMENTUM MOVERS (UPTRENDING CRYPTOCURRENCIES) ON COINBASE")
    print("="*140)
    print(f"{'Currency':<10} {'Volatility':<12} {'Sharpe Ratio':<15} {'Price':<10} {'SMA(20)':<10} {'RSI':<10} {'Avg Daily Change':<18} {'Strategy Return':<18} {'Avg Trade Return':<18} {'7d Change':<10}")
    print("-"*140)
    for currency, vol, sharpe, price, sma, rsi, avg_change, total_return, avg_return_per_trade, trend, price_change_7d in momentum_movers:
        print(f"{currency:<10} {vol:10.2%} {sharpe:13.2f} ${price:<8.2f} ${sma:<8.2f} {rsi:<8.2f} {avg_change:16.2%} {total_return:16.2%} {avg_return_per_trade:16.2%} {price_change_7d:8.2f}%")

    print("\n" + "="*140)
    print("TOP 10 DOWNTRENDING CRYPTOCURRENCIES ON COINBASE")
    print("="*140)
    print(f"{'Currency':<10} {'Volatility':<12} {'Sharpe Ratio':<15} {'Price':<10} {'SMA(20)':<10} {'RSI':<10} {'Avg Daily Change':<18} {'Strategy Return':<18} {'Avg Trade Return':<18} {'7d Change':<10}")
    print("-"*140)
    for currency, vol, sharpe, price, sma, rsi, avg_change, total_return, avg_return_per_trade, trend, price_change_7d in top_10_downtrend:
        print(f"{currency:<10} {vol:10.2%} {sharpe:13.2f} ${price:<8.2f} ${sma:<8.2f} {rsi:<8.2f} {avg_change:16.2%} {total_return:16.2%} {avg_return_per_trade:16.2%} {price_change_7d:8.2f}%")

    print("\n" + "="*140)
    print("TOP PICKS FOR POTENTIAL INVESTMENT")
    print("="*140)
    print("Uptrending Picks:")
    for currency, vol, sharpe, price, sma, rsi, avg_change, total_return, avg_return_per_trade, trend, price_change_7d in uptrend_picks:
        print(f"{currency:<10} Price: ${price:<8.2f} RSI: {rsi:<8.2f} 7d Change: {price_change_7d:8.2f}% Sharpe Ratio: {sharpe:8.2f}")
    print("\nDowntrending Picks:")
    for currency, vol, sharpe, price, sma, rsi, avg_change, total_return, avg_return_per_trade, trend, price_change_7d in downtrend_picks:
        print(f"{currency:<10} Price: ${price:<8.2f} RSI: {rsi:<8.2f} 7d Change: {price_change_7d:8.2f}% Sharpe Ratio: {sharpe:8.2f}")

    print("\nInterpretation Guide:")
    print("- Momentum Movers: Cryptocurrencies in an uptrend, sorted by 7-day price change. These might be good candidates for momentum trading strategies.")
    print("- Top Picks: Selected based on a combination of recent performance, risk-adjusted returns, and technical indicators.")
    print("  - Uptrending Picks: May be suitable for momentum strategies or long-term investment if fundamentals are strong.")
    print("  - Downtrending Picks: May present potential value investments or reversal opportunities, but carry higher risk.")
    print("- Volatility: Higher values indicate higher risk and potential for larger price swings.")
    print("- Sharpe Ratio: Higher values suggest better risk-adjusted returns historically.")
    print("- RSI: Values above 70 may indicate overbought conditions, below 30 may indicate oversold.")
    print("- 7d Change: Percentage price change over the last 7 days.")
    print("\nRemember: Past performance does not guarantee future results. Always conduct thorough research and consider your risk tolerance before investing.")
    print("This analysis is based on historical data and should not be considered as financial advice.")

if __name__ == "__main__":
    main()