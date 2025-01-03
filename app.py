from flask import Flask, render_template
import yfinance as yf
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler

# Initialize Flask app
app = Flask(__name__)

# List of 15 Indian stocks (Yahoo Finance tickers for NSE)
STOCKS = [
    "TCS.NS", "RELIANCE.NS", "INFY.NS", "HDFC.NS", "ICICIBANK.NS",
    "AXISBANK.NS", "SBIN.NS", "HDFCBANK.NS", "LT.NS", "BAJFINANCE.NS",
    "ITC.NS", "ONGC.NS", "TATASTEEL.NS", "BHARTIARTL.NS", "WIPRO.NS"
]

# Function to fetch and analyze stock data
def fetch_and_analyze():
    try:
        print("Fetching stock data...")
        stock_data = []
        for stock in STOCKS:
            ticker = yf.Ticker(stock)
            history = ticker.history(period="6mo")  # Fetch 6 months of data for SMA and RSI

            if not history.empty:
                # Extract data for the latest day
                current_data = history.iloc[-1]
                open_price = current_data['Open']
                close_price = current_data['Close']
                change_percent = ((close_price - open_price) / open_price) * 100

                # Calculate SMAs with error handling for insufficient data
                sma_50 = history['Close'].rolling(window=50).mean().iloc[-1] if len(history) >= 50 else "Insufficient Data"
                sma_100 = history['Close'].rolling(window=100).mean().iloc[-1] if len(history) >= 100 else "Insufficient Data"
                sma_200 = history['Close'].rolling(window=200).mean().iloc[-1] if len(history) >= 200 else "Insufficient Data"

                # Determine Buy/Sell Signal based on Golden Crossover
                signal = "Data Not Available"
                if isinstance(sma_50, float) and isinstance(sma_100, float):
                    if sma_50 > sma_100:
                        signal = "Buy"
                    elif sma_50 < sma_100:
                        signal = "Sell"

                # Calculate RSI
                delta = history['Close'].diff()
                gain = delta.where(delta > 0, 0).rolling(window=14).mean()
                loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs.iloc[-1])) if rs.iloc[-1] > 0 else "Insufficient Data"

                # Append data
                stock_data.append({
                    "Stock": stock.replace(".NS", ""),  # Remove ".NS" for display
                    "Current Price": f"₹{close_price:.2f}",
                    "% Change": f"{change_percent:.2f}%",
                    "RSI": f"{rsi:.2f}" if isinstance(rsi, float) else rsi,
                    "SMA(50)": f"₹{sma_50:.2f}" if isinstance(sma_50, float) else sma_50,
                    "SMA(100)": f"₹{sma_100:.2f}" if isinstance(sma_100, float) else sma_100,
                    "SMA(200)": f"₹{sma_200:.2f}" if isinstance(sma_200, float) else sma_200,
                    "Signal": signal
                })
            else:
                stock_data.append({
                    "Stock": stock.replace(".NS", ""),
                    "Current Price": "Data Not Available",
                    "% Change": "Data Not Available",
                    "RSI": "Data Not Available",
                    "SMA(50)": "Data Not Available",
                    "SMA(100)": "Data Not Available",
                    "SMA(200)": "Data Not Available",
                    "Signal": "Data Not Available"
                })

        # Create DataFrame
        df = pd.DataFrame(stock_data)

        # Save DataFrame to an HTML file
        df.to_html("templates/stock_data.html", index=False, classes="table table-striped")
        print("Stock data updated successfully!")

    except Exception as e:
        print(f"Error fetching stock data: {e}")

# Schedule the function to run daily at 8:50 PM
def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_and_analyze, "cron", hour=20, minute=50)
    scheduler.start()
    print("Scheduler started!")

# Flask route to display stock updates
@app.route("/")
def index():
    return render_template("stock_data.html")

# Run the app
if __name__ == "__main__":
    print("Starting Optimist.Trader...")
    fetch_and_analyze()  # Initial fetch to ensure data exists on first load
    start_scheduler()    # Start the scheduler
    app.run(debug=True, port=5000)  # Start the Flask app
