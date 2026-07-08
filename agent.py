import os
import time
import json
import urllib.request

# Core Watchlist - Separate playground from your markov bot
WATCHLIST = ["GOOGL", "AAPL", "MSFT"]

# Trend Bot Configuration
CONFIG = {
    "stop_loss_pct": 0.03,
    "take_profit_pct": 0.05,
    "lookback_bars": 20
}

def get_alpaca_headers():
    api_key = os.environ.get("APCA_API_KEY_ID")
    api_secret = os.environ.get("APCA_API_SECRET_KEY")
    return {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": api_secret,
        "Content-Type": "application/json"
    }

def get_stock_bars(symbols, limit=50):
    symbols_str = ",".join(symbols)
    url = f"https://data.alpaca.markets/v2/stocks/bars?symbols={symbols_str}&timeframe=5Min&limit={limit}"
    headers = get_alpaca_headers()
    try:
        req = urllib.request.Request(url, headers=headers, method='GET')
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data.get("bars", {})
    except Exception as e:
        print(f"⚠️ Trend Market Data Error: {e}")
        return {}

def get_alpaca_position(base_url, symbol):
    url = f"{base_url}/v2/positions/{symbol}"
    headers = get_alpaca_headers()
    try:
        req = urllib.request.Request(url, headers=headers, method='GET')
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return {
                "qty": float(res_data["qty"]), 
                "entry_price": float(res_data["avg_entry_price"]),
                "current_price": float(res_data["current_price"])
            }
    except Exception:
        return {"qty": 0.0, "entry_price": 0.0, "current_price": 0.0}

def has_pending_orders(base_url, symbol):
    """Safety Shield: Prevents duplicate pre-market order spamming when market is closed"""
    url = f"{base_url}/v2/orders?status=open&symbols={symbol}"
    headers = get_alpaca_headers()
    try:
        req = urllib.request.Request(url, headers=headers, method='GET')
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return len(res_data) > 0
    except Exception:
        return False

def place_stock_order(base_url, symbol, side, qty):
    url = f"{base_url}/v2/orders"
    headers = get_alpaca_headers()
    data = {"symbol": symbol, "qty": str(qty), "side": side, "type": "market", "time_in_force": "day"}
    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req) as response:
            print(f"✅ [TREND TRADE EXECUTED] {side.upper()} order processed for {qty} share of {symbol}!")
            return True
    except Exception as e:
        print(f"❌ [TREND ERROR] Order rejected for {symbol}: {e}")
        return False

def check_trend_signal(bars):
    """Calculates heavy-volume breakout momentum changes across historical bars"""
    if len(bars) < 10:
        return "neutral"
        
    closes = [float(b['c']) for b in bars]
    volumes = [float(b['v']) for b in bars]
    
    current_price = closes[-1]
    avg_price = sum(closes[:-1]) / len(closes[:-1])
    avg_volume = sum(volumes[:-1]) / len(volumes[:-1])
    current_volume = volumes[-1]
    
    # Signal triggers if price breaks above average on higher than average volume
    if current_price > avg_price and current_volume > (avg_volume * 1.2):
        return "buy"
    elif current_price < avg_price:
        return "sell"
    return "neutral"

def main():
    base_url = os.environ.get("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")
    print("🚀 Protected Trend Bot 2.0 Engine Active!")
    print(f"📊 Monitoring Outbreaks For: {', '.join(WATCHLIST)}")
    print("--------------------------------------------------")
    
    while True:
        all_bars = get_stock_bars(WATCHLIST, limit=CONFIG["lookback_bars"])
        
        for symbol in WATCHLIST:
            # Check positions and active prices first
            position = get_alpaca_position(base_url, symbol)
            qty = position["qty"]
            entry_price = position["entry_price"]
            live_price = position["current_price"]
            
            # PROTECTIVE RISK LAYER FIRST 
            if qty > 0 and live_price > 0:
                stop_price = entry_price * (1 - CONFIG["stop_loss_pct"])
                profit_price = entry_price * (1 + CONFIG["take_profit_pct"])
                
                if live_price <= stop_price:
                    print(f"🚨 [TREND STOP] Stop-loss triggered for {symbol} at ${live_price:,.2f}")
                    place_stock_order(base_url, symbol, "sell", qty)
                    continue
                elif live_price >= profit_price:
                    print(f"💰 [TREND PROFIT] Profit milestone hit for {symbol} at ${live_price:,.2f}")
                    place_stock_order(base_url, symbol, "sell", qty)
                    continue
            
            bars = all_bars.get(symbol, [])
            if not bars:
                continue
                
            signal = check_trend_signal(bars)
            display_price = live_price if live_price > 0 else float(bars[-1]['c'])
            print(f"📈 {symbol}: ${display_price:,.2f} | Current Signal State: {signal.upper()}")
            
            # CORE EXECUTION LAYER (with Pending Order Shield applied)
            if signal == "buy" and qty == 0 and not has_pending_orders(base_url, symbol):
                print(f"🚦 TREND SIGNAL: Volume breakout detected on {symbol}. Ordering 1 share...")
                place_stock_order(base_url, symbol, "buy", 1)
            elif signal == "sell" and qty > 0 and not has_pending_orders(base_url, symbol):
                print(f"🚦 TREND SIGNAL: Momentum reversal detected on {symbol}. Clearing holdings...")
                place_stock_order(base_url, symbol, "sell", qty)
                
        print("--------------------------------------------------")
        time.sleep(300)  # Check trend frames every 5 minutes

if __name__ == "__main__":
    try:
        os.chdir('/app')
    except Exception:
        pass
    main()

