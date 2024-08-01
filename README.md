# Stock Analysis Tools

This Python program is a comprehensive stock analysis tool that provides users with the ability to analyze individual stocks and search for promising investment opportunities across a large number of stocks. The tool leverages financial data from Yahoo Finance and the NASDAQ API to perform various analyses and provide investment recommendations.

## Key Features:

1. **Single Stock Analysis**: 
   - Fetches detailed information about a specific stock, including current price, 52-week high/low, market cap, P/E ratio, and dividend yield.
   - Calculates and displays average weekly change and last week's performance.
   - Provides recommended buy and sell prices based on current market trends.

2. **Promising Stock Search**:
   - Allows users to specify the number of stocks to analyze (recommended: 100 to 1000).
   - Fetches a random selection of stock tickers from the NASDAQ API.
   - Analyzes each stock using multiple technical indicators:
     - Relative Strength Index (RSI)
     - Simple Moving Averages (50-day and 200-day)
     - Weekly price changes
   - Identifies promising stocks based on predefined criteria:
     - RSI below 40 (potentially oversold)
     - Current price above 95% of the 50-day moving average
   - Calculates potential gain percentages and dollar amounts for each promising stock.
   - Ranks and displays the top promising stocks based on potential gains.

3. **Technical Analysis**:
   - Calculates RSI (Relative Strength Index) to identify overbought or oversold conditions.
   - Computes 50-day and 200-day Simple Moving Averages (SMA) for trend analysis.
   - Analyzes weekly price changes to gauge stock volatility and momentum.

4. **Multithreading**:
   - Utilizes concurrent processing to analyze multiple stocks simultaneously, significantly reducing overall analysis time.

5. **User-Friendly Interface**:
   - Offers a simple command-line interface for easy interaction.
   - Provides clear options for single stock analysis or bulk stock search.
   - Displays results in a formatted, easy-to-read table format.

6. **Data Visualization** (commented out in the current version):
   - Includes commented code for potential integration of matplotlib for graphical representation of stock data.

## Technical Details:

- Written in Python
- Uses libraries such as yfinance, pandas, numpy, requests, and tabulate
- Implements error handling for API requests and data processing
- Employs multithreading for efficient processing of large datasets

This Stock Analysis Tool is designed to assist investors in making informed decisions by providing comprehensive stock data, technical analysis, and potential investment recommendations. It's important to note that all investment decisions should be made with careful consideration and additional research.
