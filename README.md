# Financial Analysis Tool (drop-checker-GUI / drop-checker-CMD )

This Python program is a comprehensive financial analysis tool that helps identify potentially promising investment opportunities in both cryptocurrencies and stocks. It analyzes price fluctuations over time to find assets that meet specific criteria, potentially indicating favorable market conditions. Command line and GUI versions may have some slight differences.

## Features

- Analyzes both cryptocurrencies and stocks
- Fetches up-to-date lists of cryptocurrencies and S&P 500 stocks
- Allows for manual addition of specific symbols to analyze
- Configurable parameters for analysis criteria
- User-friendly GUI for easy configuration and result display
- Multithreaded analysis for improved performance
- Detailed output of top opportunities based on recent weekly fluctuations

## How It Works

1. The tool fetches lists of cryptocurrencies and stocks from online sources.
2. It then analyzes the price history of each asset over a specified period.
3. The analysis looks for patterns of consistent price fluctuations within a defined range.
4. Assets that meet the criteria are flagged as potential opportunities.
5. Results are sorted and displayed, with the most promising opportunities highlighted.

## Requirements

- Python 3.x
- Required libraries: yfinance, pandas, requests, tkinter

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/financial-analysis-tool.git
   ```
2. Install the required libraries:
   ```
   pip install yfinance pandas requests
   ```

## Usage

1. Run the script:
   ```
   python financial_analysis_tool.py
   ```
2. Use the GUI to configure analysis parameters:
   - Select analysis type (crypto, stocks, or both)
   - Set minimum and maximum fluctuation percentages
   - Specify the number of consecutive weeks for pattern recognition
   - Set the lookback period and maximum number of instruments to analyze
   - Add any manual symbols you want to include in the analysis
3. Click "Run Analysis" to start the process
4. View the results in the "Results" tab of the GUI

## Configuration Options

- **Analysis Type**: Choose to analyze cryptocurrencies, stocks, or both
- **Min/Max Fluctuation**: Set the range of weekly price fluctuations to look for
- **Consecutive Weeks**: Number of weeks the fluctuation pattern should persist
- **Lookback Weeks**: How far back to analyze (default is 13 weeks, about 3 months)
- **Max Instruments**: Limit the number of instruments to analyze for performance
- **Manual Symbols**: Add specific stock or crypto symbols to include in the analysis

## Disclaimer

This tool is for informational purposes only and should not be considered financial advice. Always do your own research and consult with a qualified financial advisor before making investment decisions.

## Contributing

Contributions, issues, and feature requests are welcome. Feel free to check [issues page](https://github.com/yourusername/financial-analysis-tool/issues) if you want to contribute.

