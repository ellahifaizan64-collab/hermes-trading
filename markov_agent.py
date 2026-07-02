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
    url = f"{base_url}/v2/positions/{symbol}"
    headers = get_alpaca_headers()
    try:
        req = urllib.request.Request(url, headers=headers, method='GET')
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return {"qty": float(res_data["qty"]), "entry_price": float(res_data["avg_entry_price"])}
    except Exception:
        return {"qty": 0.0, "entry_price": 0.0}

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
    print("🚀 Upgraded Markov 2.0 Probability Engine Active (5-Minute Windows)!")
    print(f"📊 Tracking Matrix Shifts For: {', '.join(WATCHLIST)}")
    print("--------------------------------------------------")
    
    while True:
        all_bars = get_stock_bars(WATCHLIST, limit=CONFIG["lookback_bars"])
        
        for symbol in WATCHLIST:
            bars = all_bars.get(symbol, [])
            if not bars:
                print(f"⏳ Waiting for sufficient IEX volume data for {symbol}...")
                continue
                
            current_price = float(bars[-1]['c'])
            upward_probability = compute_markov_signals(bars)
            
            position = get_alpaca_position(base_url, symbol)
            qty = position["qty"]
            entry_price = position["entry_price"]
            
            print(f"🔮 {symbol}: ${current_price:,.2f} | Next-Bar Bullish Probability: {upward_probability*100:.1f}%")
            
            # --- PROTECTIVE RISK LAYER ---
            if qty > 0:
                stop_price = entry_price * (1 - CONFIG["stop_loss_pct"])
                profit_price = entry_price * (1 + CONFIG["take_profit_pct"])
                
                if current_price <= stop_price:
                    print(f"🚨 [MARKOV STOP] Liquidation triggered for {symbol} at ${current_price:,.2f}")
                    place_stock_order(base_url, symbol, "sell", qty)
                    continue
                elif current_price >= profit_price:
                    print(f"💰 [MARKOV PROFIT] Milestone hit for {symbol} at ${current_price:,.2f}")
                    place_stock_order(base_url, symbol, "sell", qty)
                    continue
            
            # --- MARKOV PROBABILITY EXECUTION CORE ---
            # Safety shield added: 'and not has_pending_orders(...)' prevents duplicate spamming
            if upward_probability > 0.45 and qty == 0 and not has_pending_orders(base_url, symbol):
                print(f"🚦 PROBABILITY SIGNAL: High likelihood of upward breakout on {symbol}. Buying 2 shares...")
                place_stock_order(base_url, symbol, "buy", 2)
            elif upward_probability < 0.20 and qty > 0 and not has_pending_orders(base_url, symbol):
                print(f"🚦 PROBABILITY SIGNAL: Directional edge decayed for {symbol}. Releasing holdings...")
                place_stock_order(base_url, symbol, "sell", qty)
                
        print("--------------------------------------------------")
        time.sleep(300)  # Re-evaluate probability states every 5 minutes

if __name__ == "__main__":
    try:
        os.chdir('/app')
    except Exception:
        pass
    main()
