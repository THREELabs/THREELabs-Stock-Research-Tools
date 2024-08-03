import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import requests
import io

# Configurable Parameters
ANALYSIS_TYPE = 'crypto'  # Choose to analyze 'crypto', 'stocks', or 'both'
MIN_FLUCTUATION = 2  # Minimum percentage fluctuation to consider
MAX_FLUCTUATION = 10  # Maximum percentage fluctuation to consider
CONSECUTIVE_WEEKS = 3  # Number of consecutive weeks to check for fluctuation pattern
LOOKBACK_WEEKS = 12  # Number of weeks to look back for analysis
MAX_INSTRUMENTS_TO_ANALYZE = 20  # Maximum number of instruments to analyze. Set to None for no limit.
VERBOSE = True  # Set to True for detailed output during analysis
MANUAL_SYMBOLS = ['AAPL', 'GOOGL', 'BTC-USD']  # Add your manual stock or crypto symbols here

def get_crypto_symbols():
    """
    Fetch a list of cryptocurrency symbols using CoinGecko API.
    Returns an empty list on failure.
    """
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 250,
            "page": 1,
            "sparkline": False
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        symbols = [f"{coin['symbol'].upper()}-USD" for coin in data]
        return symbols[:MAX_INSTRUMENTS_TO_ANALYZE]
    except Exception as e:
        if VERBOSE:
            print(f"Error fetching crypto symbols: {str(e)}")
        return []

def get_stock_symbols():
    """
    Fetch stock symbols from predefined lists and a comprehensive CSV file.
    Returns an empty list on failure.
    """
    symbols = set()

    # Predefined lists of major indices
    sp500 = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'FB', 'TSLA', 'BRK.B', 'JPM', 'JNJ', 'V', 'PG', 'UNH', 'HD', 'MA', 'NVDA']
    dow30 = ['AAPL', 'AMGN', 'AXP', 'BA', 'CAT', 'CRM', 'CSCO', 'CVX', 'DIS', 'DOW', 'GS', 'HD', 'HON', 'IBM', 'INTC']
    nasdaq100 = ['AAPL', 'MSFT', 'AMZN', 'TSLA', 'GOOGL', 'GOOG', 'FB', 'NVDA', 'PYPL', 'ADBE', 'NFLX', 'CMCSA', 'CSCO', 'PEP', 'AVGO']

    symbols.update(sp500)
    symbols.update(dow30)
    symbols.update(nasdaq100)

    if VERBOSE:
        print(f"Fetched {len(symbols)} symbols from predefined lists")

    # Fetch additional symbols from a comprehensive CSV file
    try:
        url = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/all/all_tickers.txt"
        response = requests.get(url)
        response.raise_for_status()
        csv_data = io.StringIO(response.text)
        df = pd.read_csv(csv_data, header=None, names=['Symbol'])
        additional_symbols = df['Symbol'].tolist()
        symbols.update(additional_symbols)
        if VERBOSE:
            print(f"Fetched {len(additional_symbols)} additional symbols from CSV")
    except Exception as e:
        if VERBOSE:
            print(f"Error fetching additional symbols: {str(e)}")

    return list(symbols)[:MAX_INSTRUMENTS_TO_ANALYZE]

def get_financial_data(symbol, start_date, end_date):
    """
    Fetch financial data (open, high, low, close) for a given symbol and date range using yfinance.
    Returns an empty DataFrame on failure.
    """
    try:
        data = yf.download(symbol, start=start_date, end=end_date)
        if data.empty:
            if VERBOSE:
                print(f"No data available for {symbol}")
            return pd.DataFrame()
        return data[['Open', 'High', 'Low', 'Close']]
    except Exception as e:
        if VERBOSE:
            print(f"Error fetching data for {symbol}: {str(e)}")
        return pd.DataFrame()

def calculate_weekly_fluctuation(data):
    """
    Calculate weekly price fluctuations as a percentage.
    """
    weekly_data = data.resample('W').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last'
    })
    return ((weekly_data['High'] - weekly_data['Low']) / weekly_data['Open']) * 100

def check_consecutive_fluctuations(fluctuations):
    """
    Check if there are 'CONSECUTIVE_WEEKS' of fluctuations between 'MIN_FLUCTUATION' and 'MAX_FLUCTUATION'.
    """
    count = 0
    for fluctuation in fluctuations:
        if MIN_FLUCTUATION <= fluctuation <= MAX_FLUCTUATION:
            count += 1
            if count == CONSECUTIVE_WEEKS:
                return True
        else:
            count = 0
    return False

def analyze_instrument(symbol):
    """
    Analyze a single financial instrument for the desired fluctuation pattern.
    Returns a dictionary with analysis results or None if no data is available.
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(weeks=LOOKBACK_WEEKS)

    data = get_financial_data(symbol, start_date, end_date)
    if data.empty:
        return None

    fluctuations = calculate_weekly_fluctuation(data)
    last_close = data['Close'].iloc[-1]
    last_fluctuation = fluctuations.iloc[-1]
    average_fluctuation = fluctuations.mean()
    
    return {
        'symbol': symbol,
        'last_close': last_close,
        'last_fluctuation': last_fluctuation,
        'average_fluctuation': average_fluctuation,
        'meets_criteria': check_consecutive_fluctuations(fluctuations)
    }

def analyze_instruments(instruments, instrument_type):
    """
    Analyze a list of financial instruments for the desired fluctuation pattern.
    Prints analysis summary and returns a list of dictionaries containing analysis results.
    """
    print(f"\nAnalyzing {instrument_type}...")
    print(f"Checking for {CONSECUTIVE_WEEKS} consecutive weeks of fluctuations "
          f"between {MIN_FLUCTUATION}% and {MAX_FLUCTUATION}%")

    results = []

    for i, instrument in enumerate(instruments, 1):
        result = analyze_instrument(instrument)
        if result:
            results.append(result)
        if VERBOSE:
            print(f"Processed {i}/{len(instruments)} {instrument_type}", end='\r')

    print(f"\n\nSummary for {instrument_type.capitalize()}:")
    print(f"Total {instrument_type} analyzed: {len(instruments)}")
    print(f"{instrument_type.capitalize()} meeting criteria: {len([r for r in results if r['meets_criteria']])}")

    if results:
        print(f"\nList of {instrument_type} meeting criteria:")
        for result in results:
            if result['meets_criteria']:
                print(f"Symbol: {result['symbol']}")
                print(f"  Last Close: ${result['last_close']:.2f}")
                print(f"  Last Week's Fluctuation: {result['last_fluctuation']:.2f}%")
                print(f"  Average Weekly Fluctuation: {result['average_fluctuation']:.2f}%")
                print()
    else:
        print(f"\nNo {instrument_type} met the fluctuation criteria.")

    return results

def main():
    """
    Main function to run the analysis based on the configured parameters.
    """
    all_results = []

    # Analyze manual symbols first
    if MANUAL_SYMBOLS:
        print("\nAnalyzing manually added symbols...")
        manual_results = analyze_instruments(MANUAL_SYMBOLS, "manual symbols")
        all_results.extend(manual_results)

    if ANALYSIS_TYPE in ['crypto', 'both']:
        crypto_list = get_crypto_symbols()
        if crypto_list:
            crypto_results = analyze_instruments(crypto_list, "cryptocurrencies")
            all_results.extend(crypto_results)
        else:
            print("Failed to fetch cryptocurrency list. Please check your internet connection or try again later.")

    if ANALYSIS_TYPE in ['stocks', 'both']:
        stock_list = get_stock_symbols()
        if stock_list:
            stock_results = analyze_instruments(stock_list, "stocks")
            all_results.extend(stock_results)
        else:
            print("Failed to fetch stock list. Please check your internet connection or try again later.")

    if all_results:
        print("\nTop opportunities based on recent weekly fluctuations:")
        sorted_results = sorted(all_results, key=lambda x: x['last_fluctuation'], reverse=True)
        for result in sorted_results[:10]:  # Display top 10 opportunities
            print(f"Symbol: {result['symbol']}")
            print(f"  Last Close: ${result['last_close']:.2f}")
            print(f"  Last Week's Fluctuation: {result['last_fluctuation']:.2f}%")
            print(f"  Average Weekly Fluctuation: {result['average_fluctuation']:.2f}%")
            print(f"  Meets Criteria: {'Yes' if result['meets_criteria'] else 'No'}")
            print()
    else:
        print("No results found. Please check your internet connection and try again.")

if __name__ == "__main__":
    main()