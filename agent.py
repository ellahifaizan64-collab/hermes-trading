import os
import time
import yaml
import json
import urllib.request

def load_goal():
    try:
        with open('state/goal.yaml', 'r') as f:
            return yaml.safe_load(f)
    except Exception:
        return {"asset": "BTCUSD", "target_return_30d": 0.05}

def get_alpaca_headers():
    api_key = os.environ.get("APCA_API_KEY_ID")
    api_secret = os.environ.get("APCA_API_SECRET_KEY")
    return {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": api_secret,
        "Content-Type": "application/json"
    }

def get_latest_price(symbol):
    # Format symbol for crypto data endpoint (e.g., BTCUSD -> BTC/USD)
    data_symbol = symbol
    if "BTC" in symbol and "/" not in symbol:
        data_symbol = "BTC/USD"
        
    url = f"https://data.alpaca.markets/v1beta3/crypto/us/latest/trades?symbols={data_symbol}"
    headers = get_alpaca_headers()
    
    try:
        req = urllib.request.Request(url, headers=headers, method='GET')
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            price = res_data["trades"][data_symbol]["p"]
            return float(price)
    except Exception as e:
        print(f"⚠️ Could not fetch live price for {data_symbol}: {e}")
        return None

def get_current_position(base_url, symbol):
    url = f"{base_url}/v2/positions/{symbol}"
    headers = get_alpaca_headers()
    try:
        req = urllib.request.Request(url, headers=headers, method='GET')
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return float(res_data["qty"])
    except Exception:
        # If it returns an error or 404, it means we don't own any shares/coins
        return 0.0

def place_alpaca_order(base_url, symbol, side, qty):
    url = f"{base_url}/v2/orders"
    headers = get_alpaca_headers()
    data = {
        "symbol": symbol,
        "qty": str(qty),
        "side": side,
        "type": "market",
        "time_in_force": "gtc"
    }
    try:
        req = urllib.request.Request(
            url, 
            data=json.dumps(data).encode('utf-8'), 
            headers=headers, 
            method='POST'
        )
        with urllib.request.urlopen(req) as response:
            print(f"✅ [TRADE EXECUTED] Successfully placed {side} order for {qty} {symbol}!")
            return True
    except Exception as e:
        print(f"❌ [ORDER ERROR] Failed to place {side} order: {e}")
        return False

def main():
    config = load_goal()
    asset = config.get('asset', 'BTCUSD').replace('/', '').replace('USDT', 'USD')
    base_url = os.environ.get("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")
    
    print(f"🚀 Real Automated Trading Agent Activated!")
    print(f"📊 Live Tracking Strategy for: {asset}")
    print("--------------------------------------------------")

    price_history = []
    
    while True:
        current_price = get_latest_price(asset)
        
        if current_price:
            price_history.append(current_price)
            # Maintain the moving window size of 10 periods
            if len(price_history) > 10:
                price_history.pop(0)
                
            print(f"🏷️ Current Price of {asset}: ${current_price:,.2f} | Saved points: {len(price_history)}/10")
            
            # We need a minimum of 3 tracking points to establish an average trend line
            if len(price_history) >= 3:
                average_price = sum(price_history) / len(price_history)
                print(f"📈 Trend Line (Average Price): ${average_price:,.2f}")
                
                # Check your current open balance directly from Alpaca
                current_qty = get_current_position(base_url, asset)
                
                # --- STRATEGY CONDITIONS ---
                # 1. Price jumps above average and we don't own any -> BUY
                if current_price > average_price and current_qty == 0:
                    print("🚦 STRATEGY SIGNAL: Price breaking upward! Placing BUY order...")
                    qty = 0.001 if "BTC" in asset else 1
                    place_alpaca_order(base_url, asset, "buy", qty)
                    
                # 2. Price drops below average and we hold a balance -> SELL
                elif current_price < average_price and current_qty > 0:
                    print("🚦 STRATEGY SIGNAL: Price breaking downward! Placing SELL order...")
                    place_alpaca_order(base_url, asset, "sell", current_qty)
                else:
                    print("⏳ Strategy Status: Position Balanced. Waiting for market movement.")
        
        print("--------------------------------------------------")
        time.sleep(60) # Re-analyze the market every 60 seconds

if __name__ == "__main__":
    try:
        os.chdir('/app')
    except Exception:
        pass
    main()
