import os
import time
import json
import urllib.request
import random

# Core Watchlist including Google and Take-Two (GTA 6 parent company)
WATCHLIST = ["GOOGL", "TTWO", "AAPL", "MSFT", "NVDA"]

# Global adaptive configuration optimized across the entire portfolio
CONFIG = {
    "short_window": 5,
    "long_window": 20,
    "stop_loss_pct": 0.02,   # 2% maximum allowed loss per trade
    "take_profit_pct": 0.04  # 4% target profit target per trade
}

def get_alpaca_headers():
    api_key = os.environ.get("APCA_API_KEY_ID")
    api_secret = os.environ.get("APCA_API_SECRET_KEY")
    return {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": api_secret,
        "Content-Type": "application/json"
    }

def get_stock_bars(symbols, limit=100):
    symbols_str = ",".join(symbols)
    url = f"https://data.alpaca.markets/v2/stocks/bars?symbols={symbols_str}&timeframe=1Min&limit={limit}"
    headers = get_alpaca_headers()
    try:
        req = urllib.request.Request(url, headers=headers, method='GET')
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data.get("bars", {})
    except Exception as e:
        print(f"⚠️ Stock Market Data Fetch Error: {e}")
        return {}

def calculate_ema(prices, window):
    if len(prices) < window:
        return prices[-1] if prices else 0
    alpha = 2 / (window + 1)
    ema = prices[0]
    for price in prices[1:]:
        ema = (price * alpha) + (ema * (1 - alpha))
    return ema

def get_alpaca_position(base_url, symbol):
    url = f"{base_url}/v2/positions/{symbol}"
    headers = get_alpaca_headers()
    try:
        req = urllib.request.Request(url, headers=headers, method='GET')
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return {
                "qty": float(res_data["qty"]),
                "entry_price": float(res_data["avg_entry_price"])
            }
    except Exception:
        return {"qty": 0.0, "entry_price": 0.0}

def place_stock_order(base_url, symbol, side, qty):
    url = f"{base_url}/v2/orders"
    headers = get_alpaca_headers()
    data = {
        "symbol": symbol,
        "qty": str(qty),
        "side": side,
        "type": "market",
        "time_in_force": "day"
    }
    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req) as response:
            print(f"✅ [TRADE EXECUTED] {side.upper()} order filled for {qty} shares of {symbol}!")
            return True
    except Exception as e:
        print(f"❌ [ORDER ERROR] Failed to execute {side} order for {symbol}: {e}")
        return False

def simulate_portfolio_strategy(all_bars, short_w, long_w, sl_pct, tp_pct):
    total_simulated_profit = 0.0
    
    for symbol in WATCHLIST:
        bars = all_bars.get(symbol, [])
        prices = [float(b['c']) for b in bars]
        if len(prices) < long_w:
            continue
            
        balance = 2000.0
        shares = 0.0
        entry_p = 0.0
        
        for i in range(long_w, len(prices)):
            sub_prices = prices[:i+1]
            cur_p = sub_prices[-1]
            s_ema = calculate_ema(sub_prices, short_w)
            l_ema = calculate_ema(sub_prices, long_w)
            
            # Risk Mitigation evaluation inside backtests
            if shares > 0:
                if cur_p <= entry_p * (1 - sl_pct) or cur_p >= entry_p * (1 + tp_pct):
                    balance = shares * cur_p
                    shares = 0.0
                    continue
            
            if s_ema > l_ema and balance > 0:
                shares = balance / cur_p
                entry_p = cur_p
                balance = 0.0
            elif s_ema < l_ema and shares > 0:
                balance = shares * cur_p
                shares = 0.0
                
        profit = balance + (shares * prices[-1]) - 2000.0
        total_simulated_profit += profit
        
    return total_simulated_profit

def run_portfolio_reflection_cycle():
    global CONFIG
    print("\n🧠 [HERMES PORTFOLIO REFLECTION CYCLE] Optimizing thresholds across all target stock assets...")
    all_bars = get_stock_bars(WATCHLIST, limit=100)
    if not all_bars:
        print("⚠️ Insufficient multi-asset market data. Delaying reflection cycle.")
        return
        
    best_profit = -99999.0
    best_cfg = CONFIG.copy()
    
    # 35-pass Machine Learning hyperparameter mutation block
    for _ in range(35):
        t_short = random.randint(3, 10)
        t_long = random.randint(15, 35)
        t_sl = random.choice([0.01, 0.015, 0.02, 0.025, 0.03])
        t_tp = random.choice([0.03, 0.04, 0.05, 0.06, 0.08])
        
        sim_profit = simulate_portfolio_strategy(all_bars, t_short, t_long, t_sl, t_tp)
        if sim_profit > best_profit:
            best_profit = sim_profit
            best_cfg = {
                "short_window": t_short,
                "long_window": t_long,
                "stop_loss_pct": t_sl,
                "take_profit_pct": t_tp
            }
            
    print(f"📋 Portfolio Evaluation Complete. Best multi-stock optimization payout: ${best_profit:,.2f}")
    if best_cfg != CONFIG:
        print(f"⚙️ Adapting execution parameters globally across all tracking systems:")
        print(f"   • EMA Fast/Slow: {CONFIG['short_window']}/{CONFIG['long_window']} -> {best_cfg['short_window']}/{best_cfg['long_window']}")
        print(f"   • Stop-Loss: {CONFIG['stop_loss_pct']*100}% -> {best_cfg['stop_loss_pct']*100}%")
        print(f"   • Take-Profit: {CONFIG['take_profit_pct']*100}% -> {best_cfg['take_profit_pct']*100}%")
        CONFIG = best_cfg
    else:
        print("📊 Current portfolio settings are performing optimally.")
    print("--------------------------------------------------\n")

def main():
    base_url = os.environ.get("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")
    print("🚀 Real Autonomous Multi-Asset Stock Optimization Engine Online!")
    print(f"📊 Live Watchlist Scanning: {', '.join(WATCHLIST)}")
    print("--------------------------------------------------")
    
    loop_count = 0
    while True:
        loop_count += 1
        all_bars = get_stock_bars(WATCHLIST, limit=50)
        
        for symbol in WATCHLIST:
            bars = all_bars.get(symbol, [])
            if not bars:
                continue
                
            prices = [float(b['c']) for b in bars]
            current_price = prices[-1]
            
            short_ema = calculate_ema(prices, CONFIG["short_window"])
            long_ema = calculate_ema(prices, CONFIG["long_window"])
            
            # Fetch dynamic position state directly from Alpaca exchange infrastructure
            position = get_alpaca_position(base_url, symbol)
            qty = position["qty"]
            entry_price = position["entry_price"]
            
            print(f"🏷️ {symbol}: ${current_price:,.2f} | Short/Long EMA: {short_ema:.2f}/{long_ema:.2f}")
            
            # --- RISK MANAGEMENT LAYER ---
            if qty > 0:
                stop_price = entry_price * (1 - CONFIG["stop_loss_pct"])
                profit_price = entry_price * (1 + CONFIG["take_profit_pct"])
                
                if current_price <= stop_price:
                    print(f"🚨 [STOP LOSS TRIGGERED] {symbol} dropped below safety limit (${stop_price:,.2f}). Liquidation active...")
                    place_stock_order(base_url, symbol, "sell", qty)
                    continue
                elif current_price >= profit_price:
                    print(f"💰 [TAKE PROFIT TRIGGERED] {symbol} hit profit goal (${profit_price:,.2f}). Locking rewards...")
                    place_stock_order(base_url, symbol, "sell", qty)
                    continue
            
            # --- MOMENTUM SCANNER LAYER ---
            if short_ema > long_ema and qty == 0:
                print(f"🚦 MOMENTUM SIGNAL: {symbol} breaking out upward. Initiating buy routine...")
                place_stock_order(base_url, symbol, "buy", 1)  # Buys 1 baseline share of stock
            elif short_ema < long_ema and qty > 0:
                print(f"🚦 MOMENTUM SIGNAL: {symbol} trend reversing downward. Releasing holdings...")
                place_stock_order(base_url, symbol, "sell", qty)
                
        if loop_count % 15 == 0:
            run_portfolio_reflection_cycle()
            
        print("--------------------------------------------------")
        time.sleep(60)

if __name__ == "__main__":
    try:
        os.chdir('/app')
    except Exception:
        pass
    main()

