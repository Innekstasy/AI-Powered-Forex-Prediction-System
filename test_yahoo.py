import yfinance as yf
from datetime import datetime, timezone
import time

def test_yahoo_fetch():
    """Test Yahoo Finance data fetching for EUR/USD"""
    print("🔍 Testing Yahoo Finance EUR/USD data fetching...")
    
    # Symbol for EUR/USD in Yahoo Finance
    symbol = "EURUSD=X"
    
    while True:
        try:
            # Get ticker
            ticker = yf.Ticker(symbol)
            
            # Get current timestamp in UTC
            now = datetime.now(timezone.utc)
            
            # Fetch latest data
            data = ticker.history(period="1d", interval="1m")
            
            if not data.empty:
                last_price = data['Close'].iloc[-1]
                last_timestamp = data.index[-1].tz_convert(timezone.utc)
                latency = (now - last_timestamp).total_seconds() / 60
                
                print("\n📊 Yahoo Finance Data:")
                print(f"Timestamp: {last_timestamp}")
                print(f"Current Time (UTC): {now}")
                print(f"Latency: {latency:.2f} minutes")
                print(f"Last Price: {last_price:.5f}")
                print("-" * 50)
            else:
                print("⚠️ No data received")
            
            # Wait 5 seconds before next fetch
            time.sleep(5)
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            time.sleep(5)

if __name__ == "__main__":
    test_yahoo_fetch()