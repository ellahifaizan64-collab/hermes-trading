import os
import time
import json
import urllib.request
import random

# Core Watchlist - Separate playground from your trend bot
WATCHLIST = ["TTWO", "NVDA", "TSLA"]

# Markov Probability configurations optimized for 5-Minute intervals
CONFIG = {
    "stop_loss_pct": 0.02,
    "take_profit_pct": 0.04,
    "state_threshold": 0.0006,  # Slightly wider threshold for 5-minute moves
    "lookback_bars": 100         # Uses last 100 5-minute bars for the matrix
}

def get_alpaca_headers():
    api_key = os.environ.get("APCA_API_KEY_ID")
    api_secret = os.environ.get("APCA_API_SECRET_KEY")
    return {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": api_secret,
        "Content-Type": "application/json"
    }

def get_stock_bars(symbols, limit=120):
    symbols_str = ",".join(symbols)
    url = f"https://data.alpaca.markets/v2/stocks/bars?symbols={symbols_str}&timeframe=5Min&limit={limit}"
    headers = get_alpaca_headers()
    try:
        req = urllib.request.Request(url, headers=headers, method='GET')
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data.get("bars", {})
    except Exception as e:
        print(f"⚠️ Market Stream Error: {e}")
        return {}

def get_alpaca_position(base_url, symbol):
    """Upgraded to safely extract the actual live market price directly from your portfolio"""
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
    """Safety Shield: Checks if there are already unexecuted orders waiting in the queue"""
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
            print(f"✅ [MARKOV TRADE EXECUTED] {side.upper()} order processed for {qty} shares of {symbol}!")
            return True
    except Exception as e:
        print(f"❌ [MARKOV ERROR] Order rejected for {symbol}: {e}")
        return False

def compute_markov_signals(bars):
    """Calculates state transitions and returns the probability of an upward move"""
    prices = [float(b['c']) for b in bars]
    if len(prices) < 2:
        return 1  
        
    states = []
    for i in range(1, len(prices)):
        change = (prices[i] - prices[i-1]) / prices[i-1]
        if change > CONFIG["state_threshold"]:
            states.append(2)
        elif change < -CONFIG["state_threshold"]:
            states.append(0)
        else:
            states.append(1)
            
    if len(states) < 10:
        return 1
        
    matrix = {0: {0:0, 1:0, 2:0}, 1: {0:0, 1:0, 2:0}, 2: {0:0, 1:0, 2:0}}
    for i in range(len(states) - 1):
        current_s = states[i]
        next_s = states[i+1]
        matrix[current_s][next_s] += 1
        
    last_state = states[-1]
    total_transitions_from_last = sum(matrix[last_state].values())
    
    if total_transitions_from_last == 0:
        return 1  
        
    prob_of_upward_move = matrix[last_state][2] / total_transitions_from_last
    return prob_of_upward_move

def main():
    base_url = os.environ.get("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")
    print("🚀 Upgraded Markov 3.0 Position-First Engine Active!")
    print(f"📊 Tracking Matrix Shifts For: {', '.join(WATCHLIST)}")
    print("--------------------------------------------------")
    
    while True:
        all_bars = get_stock_bars(WATCHLIST, limit=CONFIG["lookback_bars"])
        
        for symbol in WATCHLIST:
            # STEP 1: Always check your live account positions and raw prices first
            position = get_alpaca_position(base_url, symbol)
            qty = position["qty"]
            entry_price = position["entry_price"]
            live_price = position["current_price"]
            
            # STEP 2: RUN PROTECTIVE RISK LAYER FIRST (Independent of data stream availability)
            if qty > 0 and live_price > 0:
                stop_price = entry_price * (1 - CONFIG["stop_loss_pct"])
                profit_price = entry_price * (1 + CONFIG["take_profit_pct"])
                
                if live_price <= stop_price:
                    print(f"🚨 [MARKOV STOP] Liquidation triggered for {symbol} at ${live_price:,.2f} (Entry: ${entry_price:.2f})")
                    place_stock_order(base_url, symbol, "sell", qty)
                    continue
                elif live_price >= profit_price:
                    print(f"💰 [MARKOV PROFIT] Milestone hit for {symbol} at ${live_price:,.2f} (Entry: ${entry_price:.2f})")
                    place_stock_order(base_url, symbol, "sell", qty)
                    continue
            
            # STEP 3: Now look at chart data for building the prediction matrix
            bars = all_bars.get(symbol, [])
            if not bars:
                # If we don't own it and there's no data, skip calculation safely
                if qty == 0:
                    print(f"⏳ Waiting for sufficient IEX volume data to calculate matrix for {symbol}...")
                continue
                
            display_price = live_price if live_price > 0 else float(bars[-1]['c'])
            upward_probability = compute_markov_signals(bars)
            
            print(f"🔮 {symbol}: ${display_price:,.2f} | Next-Bar Bullish Probability: {upward_probability*100:.1f}%")
            
            # --- MARKOV PROBABILITY EXECUTION CORE ---
            if upward_probability > 0.45 and qty == 0 and not has_pending_orders(base_url, symbol):
                print(f"🚦 PROBABILITY SIGNAL: High likelihood of upward breakout on {symbol}. Buying 2 shares...")
                place_stock_order(base_url, symbol, "buy", 2)
            elif upward_probability < 0.20 and qty > 0 and not has_pending_orders(base_url, symbol):
                print(f"🚦 PROBABILITY SIGNAL: Directional edge decayed for {symbol}. Releasing holdings...")
                place_stock_order(base_url, symbol, "sell", qty)
                
        print("--------------------------------------------------")
        time.sleep(300)  # Re-evaluate every 5 minutes

if __name__ == "__main__":
    try:
        os.chdir('/app')
    except Exception:
        pass
    main()
