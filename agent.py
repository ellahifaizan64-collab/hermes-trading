import os
import time
import json
import urllib.request
import random
import math

# Watchlist featuring Google and Take-Two (GTA 6 parent company)
WATCHLIST = ["GOOGL", "TTWO", "AAPL", "MSFT", "NVDA"]

# Upgraded configuration focusing on 5-Minute and 15-Minute macroscopic stability
CONFIG = {
    "short_window": 5,
    "long_window": 20,
    "base_stop_loss": 0.02,   # Baseline 2% stop loss
    "base_take_profit": 0.04, # Baseline 4% profit target
    "volume_filter_period": 10
}

def get_alpaca_headers():
    api_key = os.environ.get("APCA_API_KEY_ID")
    api_secret = os.environ.get("APCA_API_SECRET_KEY")
    return {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": api_secret,
        "Content-Type": "application/json"
    }

def get_stock_bars(symbols, timeframe="5Min", limit=100):
    symbols_str = ",".join(symbols)
    url = f"https://data.alpaca.markets/v2/stocks/bars?symbols={symbols_str}&timeframe={timeframe}&limit={limit}"
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

def calculate_volatility_multiplier(prices, period=14):
    """Chaos Meter: Returns a multiplier based on recent price bounces"""
    if len(prices) < period:
        return 1.0
    sub_set = prices[-period:]
    mean = sum(sub_set) / len(sub_set)
    variance = sum((x - mean) ** 2 for x in sub_set) / len(sub_set)
    std_dev = math.sqrt(variance)
    percentage_volatility = std_dev / mean
    
    # Adjust multiplier smoothly based on historical asset movement waves
    if percentage_volatility > 0.01:
        return 1.5  # Wild market: give the trade extra room to breathe
    elif percentage_volatility < 0.002:
        return 0.8  # Very calm market: tighten up defenses
    return 1.0

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
            print(f"✅ [TRADE EXECUTED] {side.upper()} order processed for {qty} shares of {symbol}!")
            return True
    except Exception as e:
        print(f"❌ [ORDER ERROR] Execution blocked for {symbol}: {e}")
        return False

def simulate_smart_strategy(all_bars, short_w, long_w, sl_base, tp_base):
    total_simulated_profit = 0.0
    for symbol in WATCHLIST:
        bars = all_bars.get(symbol, [])
        prices = [float(b['c']) for b in bars]
        volumes = [float(b['v']) for b in bars]
        if len(prices) < long_w:
            continue
            
        balance = 2000.0
        shares = 0.0
        entry_p = 0.0
        
        for i in range(long_w, len(prices)):
            sub_prices = prices[:i+1]
            sub_volumes = volumes[:i+1]
            cur_p = sub_prices[-1]
            
            s_ema = calculate_ema(sub_prices, short_w)
            l_ema = calculate_ema(sub_prices, long_w)
            
            # Smart Volume Filter
            avg_volume = sum(sub_volumes[-10:]) / 10
            high_volume = sub_volumes[-1] > avg_volume
            
            # Dynamic Volatility adjustments
            vol_mult = calculate_volatility_multiplier(sub_prices)
            sl_dynamic = sl_base * vol_mult
            tp_dynamic = tp_base * vol_mult
            
            if shares > 0:
                if cur_p <= entry_p * (1 - sl_dynamic) or cur_p >= entry_p * (1 + tp_dynamic):
                    balance = shares * cur_p
                    shares = 0.0
                    continue
            
            if s_ema > l_ema and high_volume and balance > 0:
                shares = balance / cur_p
                entry_p = cur_p
                balance = 0.0
            elif s_ema < l_ema and shares > 0:
                balance = shares * cur_p
                shares = 0.0
                
        profit = balance + (shares * prices[-1]) - 2000.0
        total_simulated_profit += profit
    return total_simulated_profit

def run_macro_reflection_cycle():
    global CONFIG
    print("\n🧠 [HERMES MACRO REFLECTION CYCLE] Studying 15-Minute trends to optimize portfolio filters...")
    # Pulling larger 15-minute trends to eliminate short-term noisy glitches
    all_bars = get_stock_bars(WATCHLIST, timeframe="15Min", limit=100)
    if not all_bars:
        print("⚠️ Insufficient historical data blocks. Delaying optimization.")
        return
        
    best_profit = -99999.0
    best_cfg = CONFIG.copy()
    
    for _ in range(35):
        t_short = random.randint(3, 10)
        t_long = random.randint(15, 35)
        t_sl = random.choice([0.015, 0.02, 0.025, 0.03])
        t_tp = random.choice([0.03, 0.04, 0.05, 0.06])
        
        sim_profit = simulate_smart_strategy(all_bars, t_short, t_long, t_sl, t_tp)
        if sim_profit > best_profit:
            best_profit = sim_profit
            best_cfg = {
                "short_window": t_short,
                "long_window": t_long,
                "base_stop_loss": t_sl,
                "base_take_profit": t_tp,
                "volume_filter_period": 10
            }
            
    print(f"📋 Macro Evaluation Complete. Optimal target yield simulated: ${best_profit:,.2f}")
    if best_cfg != CONFIG:
        print(f"⚙️ Upgrading tracking algorithms globally:")
        print(f"   • Trend EMAs: {CONFIG['short_window']}/{CONFIG['long_window']} -> {best_cfg['short_window']}/{best_cfg['long_window']}")
        print(f"   • Baseline Risk Guard: Stop-Loss {best_cfg['base_stop_loss']*100}% | Take-Profit {best_cfg['base_take_profit']*100}%")
        CONFIG = best_cfg
    else:
        print("📊 Core configurations are operating at maximum market efficiency.")
    print("--------------------------------------------------\n")

def main():
    base_url = os.environ.get("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")
    print("🚀 Real Autonomous Noise-Filtered Stock Optimization Engine Online!")
    print(f"📊 Live Smart Scanning Activated For: {', '.join(WATCHLIST)}")
    print("--------------------------------------------------")
    
    loop_count = 0
    while True:
        loop_count += 1
        # Main loop switched to stable 5-Minute blocks to avoid 1-minute random whipsaws
        all_bars = get_stock_bars(WATCHLIST, timeframe="5Min", limit=60)
        
        for symbol in WATCHLIST:
            bars = all_bars.get(symbol, [])
            if not bars:
                continue
                
            prices = [float(b['c']) for b in bars]
            volumes = [float(b['v']) for b in bars]
            current_price = prices[-1]
            current_volume = volumes[-1]
            
            short_ema = calculate_ema(prices, CONFIG["short_window"])
            long_ema = calculate_ema(prices, CONFIG["long_window"])
            
            # Volume Crowd Filter calculation
            recent_avg_volume = sum(volumes[-CONFIG["volume_filter_period"]:]) / CONFIG["volume_filter_period"]
            volume_confirmed = current_volume > recent_avg_volume
            
            # Volatility Chaos Meter adjustment
            vol_multiplier = calculate_volatility_multiplier(prices)
            current_sl = CONFIG["base_stop_loss"] * vol_multiplier
            current_tp = CONFIG["base_take_profit"] * vol_multiplier
            
            position = get_alpaca_position(base_url, symbol)
            qty = position["qty"]
            entry_price = position["entry_price"]
            
            vol_status = "HIGH ⚠️ (Widening Safety Nets)" if vol_multiplier > 1.0 else "CALM ✅ (Tight Shields)"
            print(f"🏷️ {symbol}: ${current_price:,.2f} | Volatility: {vol_status} | Volume Confirmed: {volume_confirmed}")
            
            # --- RISK MANAGEMENT LAYER ---
            if qty > 0:
                stop_price = entry_price * (1 - current_sl)
                profit_price = entry_price * (1 + current_tp)
                
                if current_price <= stop_price:
                    print(f"🚨 [DYNAMIC STOP LOSS] Liquidating {symbol} at ${current_price:,.2f} to prevent capital leakage.")
                    place_stock_order(base_url, symbol, "sell", qty)
                    continue
                elif current_price >= profit_price:
                    print(f"💰 [DYNAMIC TAKE PROFIT] Claiming rewards for {symbol} at ${current_price:,.2f} before trend drops.")
                    place_stock_order(base_url, symbol, "sell", qty)
                    continue
            
            # --- INTELLIGENT MOMENTUM SCANNER ---
            if short_ema > long_ema and volume_confirmed and qty == 0:
                print(f"🚦 STRATEGY BREAKOUT: {symbol} surging upward with crowd support. Buying 1 share...")
                place_stock_order(base_url, symbol, "buy", 1)
            elif short_ema < long_ema and qty > 0:
                print(f"🚦 STRATEGY REVERSAL: {symbol} momentum exhausting. Selling position...")
                place_stock_order(base_url, symbol, "sell", qty)
                
        # Run reflection every 30 loops (every 2.5 hours on 5-min intervals) to prioritize macro stability
        if loop_count % 30 == 0:
            run_macro_reflection_cycle()
            
        print("--------------------------------------------------")
        time.sleep(300) # Check the market smoothly every 5 minutes

if __name__ == "__main__":
    try:
        os.chdir('/app')
    except Exception:
        pass
    main()

