import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import requests
import io
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue

# Configurable Parameters
ANALYSIS_TYPE = 'both'  # Choose to analyze 'crypto', 'stocks', or 'both'
MIN_FLUCTUATION = 2  # Minimum percentage fluctuation to consider
MAX_FLUCTUATION = 10  # Maximum percentage fluctuation to consider
CONSECUTIVE_WEEKS = 3  # Number of consecutive weeks to check for fluctuation pattern
LOOKBACK_WEEKS = 13  # Number of weeks to look back for analysis (approximately 3 months)
MAX_INSTRUMENTS_TO_ANALYZE = 20  # Maximum number of instruments to analyze. Set to None for no limit.
VERBOSE = True  # Set to True for detailed output during analysis
MANUAL_SYMBOLS = ['AAPL', 'GOOGL', 'BTC-USD']  # Add your manual stock or crypto symbols here

def get_crypto_symbols():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 250,
        "page": 1,
        "sparkline": False
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        return [coin['symbol'].upper() + '-USD' for coin in data]
    else:
        print(f"Failed to fetch cryptocurrency list. Status code: {response.status_code}")
        return []

def get_stock_symbols():
    url = "https://pkgstore.datahub.io/core/s-and-p-500-companies/constituents_csv/data/64dd3e9582b936b0352fdd826ecd3c95/constituents_csv.csv"
    response = requests.get(url)
    if response.status_code == 200:
        df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))
        return df['Symbol'].tolist()
    else:
        print(f"Failed to fetch stock list. Status code: {response.status_code}")
        return []

def analyze_instruments(symbols, instrument_type):
    results = []
    for symbol in symbols[:MAX_INSTRUMENTS_TO_ANALYZE]:
        try:
            ticker = yf.Ticker(symbol)
            
            # Use '3mo' instead of '12wk' for broader compatibility
            hist = ticker.history(period='3mo')
            
            if hist.empty:
                if VERBOSE:
                    print(f"No data available for {symbol}")
                continue
            
            # Resample to weekly data
            weekly_data = hist['Close'].resample('W').last()
            
            # Calculate returns and fluctuations
            weekly_returns = weekly_data.pct_change()
            weekly_fluctuations = weekly_returns.abs() * 100
            
            # Check if we have enough data points
            if len(weekly_fluctuations) < CONSECUTIVE_WEEKS:
                if VERBOSE:
                    print(f"Not enough data points for {symbol}")
                continue
            
            meets_criteria = False
            for i in range(len(weekly_fluctuations) - CONSECUTIVE_WEEKS + 1):
                if all(MIN_FLUCTUATION <= fluctuation <= MAX_FLUCTUATION for fluctuation in weekly_fluctuations[i:i+CONSECUTIVE_WEEKS]):
                    meets_criteria = True
                    break
            
            last_close = hist['Close'].iloc[-1]
            last_fluctuation = weekly_fluctuations.iloc[-1]
            average_fluctuation = weekly_fluctuations.mean()
            
            # Calculate overall growth and determine if it's "HOT"
            overall_growth = (last_close - hist['Close'].iloc[0]) / hist['Close'].iloc[0] * 100
            is_hot = meets_criteria and overall_growth > 0 and last_fluctuation > average_fluctuation
            
            results.append({
                'symbol': symbol,
                'last_close': last_close,
                'last_fluctuation': last_fluctuation,
                'average_fluctuation': average_fluctuation,
                'meets_criteria': meets_criteria,
                'overall_growth': overall_growth,
                'is_hot': is_hot
            })
            
            if VERBOSE:
                print(f"Analyzed {symbol}")
        
        except Exception as e:
            if VERBOSE:
                print(f"Error analyzing {symbol}: {str(e)}")
    
    return results

class FinancialAnalysisGUI:
    def __init__(self, master):
        self.master = master
        master.title("Financial Analysis Tool")
        master.geometry("800x600")

        self.create_widgets()
        self.queue = queue.Queue()
        self.update_gui()

    def create_widgets(self):
        # Create tabs
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        # Configuration Tab
        self.config_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.config_frame, text='Configuration')

        # Analysis Type
        ttk.Label(self.config_frame, text="Analysis Type:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.analysis_type = tk.StringVar(value=ANALYSIS_TYPE)
        ttk.Combobox(self.config_frame, textvariable=self.analysis_type, values=['crypto', 'stocks', 'both']).grid(row=0, column=1, sticky='w', padx=5, pady=5)

        # Min Fluctuation
        ttk.Label(self.config_frame, text="Min Fluctuation (%):").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.min_fluctuation = tk.StringVar(value=str(MIN_FLUCTUATION))
        ttk.Entry(self.config_frame, textvariable=self.min_fluctuation).grid(row=1, column=1, sticky='w', padx=5, pady=5)

        # Max Fluctuation
        ttk.Label(self.config_frame, text="Max Fluctuation (%):").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.max_fluctuation = tk.StringVar(value=str(MAX_FLUCTUATION))
        ttk.Entry(self.config_frame, textvariable=self.max_fluctuation).grid(row=2, column=1, sticky='w', padx=5, pady=5)

        # Consecutive Weeks
        ttk.Label(self.config_frame, text="Consecutive Weeks:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
        self.consecutive_weeks = tk.StringVar(value=str(CONSECUTIVE_WEEKS))
        ttk.Entry(self.config_frame, textvariable=self.consecutive_weeks).grid(row=3, column=1, sticky='w', padx=5, pady=5)

        # Lookback Weeks
        ttk.Label(self.config_frame, text="Lookback Weeks:").grid(row=4, column=0, sticky='w', padx=5, pady=5)
        self.lookback_weeks = tk.StringVar(value=str(LOOKBACK_WEEKS))
        ttk.Entry(self.config_frame, textvariable=self.lookback_weeks).grid(row=4, column=1, sticky='w', padx=5, pady=5)

        # Max Instruments
        ttk.Label(self.config_frame, text="Max Instruments:").grid(row=5, column=0, sticky='w', padx=5, pady=5)
        self.max_instruments = tk.StringVar(value=str(MAX_INSTRUMENTS_TO_ANALYZE))
        ttk.Entry(self.config_frame, textvariable=self.max_instruments).grid(row=5, column=1, sticky='w', padx=5, pady=5)

        # Manual Symbols
        ttk.Label(self.config_frame, text="Manual Symbols:").grid(row=6, column=0, sticky='w', padx=5, pady=5)
        self.manual_symbols = tk.StringVar(value=','.join(MANUAL_SYMBOLS))
        ttk.Entry(self.config_frame, textvariable=self.manual_symbols).grid(row=6, column=1, sticky='w', padx=5, pady=5)

        # Run Analysis Button
        self.run_button = ttk.Button(self.config_frame, text="Run Analysis", command=self.run_analysis)
        self.run_button.grid(row=7, column=0, columnspan=2, pady=20)

        # Results Tab
        self.results_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.results_frame, text='Results')

        self.results_text = scrolledtext.ScrolledText(self.results_frame, wrap=tk.WORD)
        self.results_text.pack(expand=True, fill='both')

    def run_analysis(self):
        # Update global variables with GUI values
        global ANALYSIS_TYPE, MIN_FLUCTUATION, MAX_FLUCTUATION, CONSECUTIVE_WEEKS, LOOKBACK_WEEKS, MAX_INSTRUMENTS_TO_ANALYZE, MANUAL_SYMBOLS

        ANALYSIS_TYPE = self.analysis_type.get()
        MIN_FLUCTUATION = float(self.min_fluctuation.get())
        MAX_FLUCTUATION = float(self.max_fluctuation.get())
        CONSECUTIVE_WEEKS = int(self.consecutive_weeks.get())
        LOOKBACK_WEEKS = int(self.lookback_weeks.get())
        MAX_INSTRUMENTS_TO_ANALYZE = int(self.max_instruments.get())
        MANUAL_SYMBOLS = [symbol.strip() for symbol in self.manual_symbols.get().split(',')]

        # Clear previous results
        self.results_text.delete('1.0', tk.END)

        # Disable the run button
        self.run_button.config(state='disabled')

        # Run analysis in a separate thread
        threading.Thread(target=self.threaded_analysis, daemon=True).start()

    def threaded_analysis(self):
        # Redirect print statements to the GUI
        import sys
        class StdoutRedirector:
            def __init__(self, text_widget):
                self.text_widget = text_widget

            def write(self, string):
                self.text_widget.insert(tk.END, string)
                self.text_widget.see(tk.END)

            def flush(self):
                pass

        sys.stdout = StdoutRedirector(self.results_text)

        # Run the main analysis
        main()

        # Reset stdout
        sys.stdout = sys.__stdout__

        # Signal that the analysis is complete
        self.queue.put("Analysis Complete")

    def update_gui(self):
        try:
            message = self.queue.get(0)
            if message == "Analysis Complete":
                messagebox.showinfo("Analysis Complete", "The financial analysis has completed.")
                self.run_button.config(state='normal')
        except queue.Empty:
            pass
        finally:
            self.master.after(100, self.update_gui)

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
        sorted_results = sorted(all_results, key=lambda x: (x['is_hot'], x['last_fluctuation']), reverse=True)
        for result in sorted_results[:10]:  # Display top 10 opportunities
            hot_indicator = "🔥 HOT!" if result['is_hot'] else ""
            print(f"Symbol: {result['symbol']} {hot_indicator}")
            print(f"  Last Close: ${result['last_close']:.2f}")
            print(f"  Last Week's Fluctuation: {result['last_fluctuation']:.2f}%")
            print(f"  Average Weekly Fluctuation: {result['average_fluctuation']:.2f}%")
            print(f"  Overall Growth: {result['overall_growth']:.2f}%")
            print(f"  Meets Criteria: {'Yes' if result['meets_criteria'] else 'No'}")
            print()
    else:
        print("No results found. Please check your internet connection and try again.")

if __name__ == "__main__":
    root = tk.Tk()
    app = FinancialAnalysisGUI(root)
    root.mainloop()