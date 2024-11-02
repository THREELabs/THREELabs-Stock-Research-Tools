import pandas as pd
import yfinance as yf

def analyze_stock():
    # Get user input for stock symbol
    while True:
        stock_symbol = input("\nEnter the stock ticker symbol (e.g., AAPL, GOOGL, AMC): ").upper()
        try:
            # Quick validation check
            test_data = yf.download(stock_symbol, period='1d')
            if not test_data.empty:
                break
            else:
                print(f"Could not find data for {stock_symbol}. Please try again.")
        except Exception as e:
            print(f"Error: Invalid ticker symbol. Please try again.")

    # Define multiple periods for analysis
    periods = {
        '1mo': 'Last Month',
        '3mo': 'Last 3 Months',
        '6mo': 'Last 6 Months',
        '1y': 'Last Year',
        '2y': 'Last 2 Years',
        '5y': 'Last 5 Years'
    }

    # Get the current price using the most recent data
    current_data = yf.download(stock_symbol, period='1d')
    current_price = current_data['Close'].iloc[-1]

    # Initialize dictionary to store analysis results
    analysis_results = {}

    # Analyze each time period
    for period, period_name in periods.items():
        try:
            # Fetch historical stock data for this period
            data = yf.download(stock_symbol, period=period)
            
            # Calculate daily price range as a percentage
            data['Daily Range (%)'] = ((data['High'] - data['Low']) / data['Low']) * 100
            
            # Calculate metrics for this period
            average_daily_range = data['Daily Range (%)'].mean()
            historical_high = data['High'].max()
            historical_low = data['Low'].min()
            avg_price = data['Close'].mean()
            
            analysis_results[period] = {
                'avg_daily_range': average_daily_range,
                'hist_high': historical_high,
                'hist_low': historical_low,
                'avg_price': avg_price
            }
        except Exception as e:
            print(f"Could not analyze {period_name} due to: {str(e)}")

    # Calculate buy limit based on recent (1mo) price movements
    recent_range = analysis_results['1mo']['avg_daily_range']
    limit_buy_price = current_price * (1 - (recent_range / 2) / 100)

    # Print comprehensive analysis
    print(f"\nAnalysis for {stock_symbol}")
    print(f"Current Price: ${current_price:.2f}")
    print(f"Recommended Buy Price: ${limit_buy_price:.2f}")
    print(f"Potential entry discount: {((current_price - limit_buy_price) / current_price * 100):.2f}%")

    print("\nSELL TARGETS BASED ON HISTORICAL DATA:")
    print("-" * 80)

    # For each time period, show relevant price levels
    for period, period_name in periods.items():
        if period in analysis_results:
            results = analysis_results[period]
            print(f"\n{period_name} Price Levels:")
            print(f"Average Price: ${results['avg_price']:.2f}")
            print(f"Highest Price: ${results['hist_high']:.2f}")
            print(f"Average Daily Range: {results['avg_daily_range']:.2f}%")
            
            # Calculate and show potential profit if sold at average price
            profit_at_avg = ((results['avg_price'] - limit_buy_price) / limit_buy_price * 100)
            print(f"Potential return at average price: {profit_at_avg:.2f}%")

    print("\nRECOMMENDED SELL STRATEGY:")
    print("-" * 80)
    print("Based on the historical data, here are three price-based sell targets:")

    # Sell Target 1: Based on 3-month average price
    sell_target_1 = analysis_results['3mo']['avg_price']
    profit_1 = ((sell_target_1 - limit_buy_price) / limit_buy_price * 100)
    print(f"\n1. Three Month Average Price Target:")
    print(f"   Sell at: ${sell_target_1:.2f}")
    print(f"   Potential return: {profit_1:.2f}%")

    # Sell Target 2: Based on 1-year average price
    sell_target_2 = analysis_results['1y']['avg_price']
    profit_2 = ((sell_target_2 - limit_buy_price) / limit_buy_price * 100)
    print(f"\n2. One Year Average Price Target:")
    print(f"   Sell at: ${sell_target_2:.2f}")
    print(f"   Potential return: {profit_2:.2f}%")

    # Sell Target 3: Based on 2-year high
    sell_target_3 = analysis_results['2y']['hist_high']
    profit_3 = ((sell_target_3 - limit_buy_price) / limit_buy_price * 100)
    print(f"\n3. Two Year High Price Target:")
    print(f"   Sell at: ${sell_target_3:.2f}")
    print(f"   Potential return: {profit_3:.2f}%")

    print("\nSTRATEGY EXPLANATION:")
    print("-" * 80)
    print("1. Entry Strategy:")
    print(f"   - Buy at ${limit_buy_price:.2f} (based on recent daily price movements)")

    print("\n2. Exit Strategy Options:")
    print(f"   - First Target: 3-month average price ${sell_target_1:.2f}")
    print(f"   - Second Target: 1-year average price ${sell_target_2:.2f}")
    print(f"   - Third Target: 2-year high ${sell_target_3:.2f}")

    print("\n3. Suggested Approach:")
    print("   - Consider splitting your position into three parts")
    print("   - Sell portions at each target price")
    print("   - This helps capture profits while maintaining upside potential")

    # Ask if user wants to analyze another stock
    another = input("\nWould you like to analyze another stock? (yes/no): ").lower()
    if another.startswith('y'):
        analyze_stock()

# Start the program
if __name__ == "__main__":
    print("Stock Analysis Tool")
    print("This tool will help you determine optimal buy and sell prices based on historical data.")
    analyze_stock()