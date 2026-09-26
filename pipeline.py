import yfinance as yf
import pandas as pd
from NSE_list import nse_500
from datetime import datetime

def run_master_pipeline():
    print(f"[{datetime.now()}] Downloading Nifty 500 EOD data...")
    data = yf.download(nse_500, period="1y")['Close']
    
    bullish_mom_list, bearish_mom_list = [], []
    uptrend_trans_list, downtrend_trans_list = [], []
    
    for ticker in nse_500:
        if ticker not in data.columns: continue
        price_series = data[ticker].dropna()
        if len(price_series) < 210: continue 
            
        # Moving Averages
        dma_50 = price_series.rolling(window=50).mean()
        dma_200 = price_series.rolling(window=200).mean()
        ema_9 = price_series.ewm(span=9, adjust=False).mean()
        ema_21 = price_series.ewm(span=21, adjust=False).mean()
        
        current_price = price_series.iloc[-1]
        curr_ema_9, curr_ema_21 = ema_9.iloc[-1], ema_21.iloc[-1]
        curr_dma_50, curr_dma_200 = dma_50.iloc[-1], dma_200.iloc[-1]
        
        # --- MACRO MOMENTUM LOGIC (50 & 200 DMA) ---
        dist_50_pct = ((current_price - curr_dma_50) / curr_dma_50) * 100
        dist_200_pct = ((current_price - curr_dma_200) / curr_dma_200) * 100
        dma_cross_pct = ((curr_dma_50 - curr_dma_200) / curr_dma_200) * 100
        
        # 1. Bullish Momentum (Price > 9 EMA)
        if current_price > curr_ema_9:
            score_bull = int((dma_50.diff().iloc[-10:] > 0).sum() * 2) + \
                         int((dma_200.diff().iloc[-10:] > 0).sum() * 2) + \
                         int(min(20, max(0, 10 + (dist_50_pct * 2)))) + \
                         int(min(20, max(0, 10 + (dist_200_pct * 2)))) + \
                         int(min(20, max(0, 10 + (dma_cross_pct * 2))))
            bullish_mom_list.append({
                'Ticker': ticker.replace('.NS', ''), 'Price': round(current_price, 2),
                '9 EMA': round(curr_ema_9, 2), '50 DMA': round(curr_dma_50, 2), '200 DMA': round(curr_dma_200, 2),
                'Score': score_bull, 'Dist 50 DMA (%)': round(dist_50_pct, 2), 'Dist 200 DMA (%)': round(dist_200_pct, 2),
                'Action Zone': '50 DMA' if abs(dist_50_pct) <= 5.0 else ('200 DMA' if abs(dist_200_pct) <= 5.0 else 'No')
            })
            
        # 2. Bearish Momentum (Price < 9 EMA)
        elif current_price < curr_ema_9:
            score_bear = int((dma_50.diff().iloc[-10:] < 0).sum() * 2) + \
                         int((dma_200.diff().iloc[-10:] < 0).sum() * 2) + \
                         int(min(20, max(0, 10 - (dist_50_pct * 2)))) + \
                         int(min(20, max(0, 10 - (dist_200_pct * 2)))) + \
                         int(min(20, max(0, 10 - (dma_cross_pct * 2))))
            bearish_mom_list.append({
                'Ticker': ticker.replace('.NS', ''), 'Price': round(current_price, 2),
                '9 EMA': round(curr_ema_9, 2), '50 DMA': round(curr_dma_50, 2), '200 DMA': round(curr_dma_200, 2),
                'Score': score_bear, 'Dist 50 DMA (%)': round(dist_50_pct, 2), 'Dist 200 DMA (%)': round(dist_200_pct, 2),
                'Action Zone': '50 DMA' if abs(dist_50_pct) <= 5.0 else ('200 DMA' if abs(dist_200_pct) <= 5.0 else 'No')
            })

        # --- MICRO TRANSITION LOGIC (9 & 21 EMA Slopes) ---
        ema_9_slope = ema_9.diff()
        ema_21_slope = ema_21.diff()
        dist_9_pct = ((current_price - curr_ema_9) / curr_ema_9) * 100
        dist_21_pct = ((current_price - curr_ema_21) / curr_ema_21) * 100
        ema_cross_pct = ((curr_ema_9 - curr_ema_21) / curr_ema_21) * 100
        
        # 3. Uptrend Transition (Both Slopes Positive)
        if ema_9_slope.iloc[-1] > 0 and ema_21_slope.iloc[-1] > 0:
            score_up_trans = int((ema_9_slope.iloc[-10:] > 0).sum() * 2) + \
                             int((ema_21_slope.iloc[-10:] > 0).sum() * 2) + \
                             int(min(20, max(0, 10 + (ema_cross_pct * 2)))) + \
                             int(min(20, max(0, 10 + (dist_9_pct * 2)))) + \
                             int(min(20, max(0, 10 + (dist_21_pct * 2))))
            uptrend_trans_list.append({
                'Ticker': ticker.replace('.NS', ''), 'Price': round(current_price, 2),
                '9 EMA': round(curr_ema_9, 2), '21 EMA': round(curr_ema_21, 2),
                'Score': score_up_trans, '9 EMA Slope': round(ema_9_slope.iloc[-1], 2), '21 EMA Slope': round(ema_21_slope.iloc[-1], 2),
                'Dist 9 EMA (%)': round(dist_9_pct, 2), 'Dist 21 EMA (%)': round(dist_21_pct, 2),
                'Action Zone': '9 EMA' if abs(dist_9_pct) <= 3.0 else ('21 EMA' if abs(dist_21_pct) <= 3.0 else 'No')
            })
            
        # 4. Downtrend Transition (Both Slopes Negative)
        elif ema_9_slope.iloc[-1] < 0 and ema_21_slope.iloc[-1] < 0:
            score_down_trans = int((ema_9_slope.iloc[-10:] < 0).sum() * 2) + \
                               int((ema_21_slope.iloc[-10:] < 0).sum() * 2) + \
                               int(min(20, max(0, 10 - (ema_cross_pct * 2)))) + \
                               int(min(20, max(0, 10 - (dist_9_pct * 2)))) + \
                               int(min(20, max(0, 10 - (dist_21_pct * 2))))
            downtrend_trans_list.append({
                'Ticker': ticker.replace('.NS', ''), 'Price': round(current_price, 2),
                '9 EMA': round(curr_ema_9, 2), '21 EMA': round(curr_ema_21, 2),
                'Score': score_down_trans, '9 EMA Slope': round(ema_9_slope.iloc[-1], 2), '21 EMA Slope': round(ema_21_slope.iloc[-1], 2),
                'Dist 9 EMA (%)': round(dist_9_pct, 2), 'Dist 21 EMA (%)': round(dist_21_pct, 2),
                'Action Zone': '9 EMA' if abs(dist_9_pct) <= 3.0 else ('21 EMA' if abs(dist_21_pct) <= 3.0 else 'No')
            })

    pd.DataFrame(bullish_mom_list).to_csv("bull_mom.csv", index=False)
    pd.DataFrame(bearish_mom_list).to_csv("bear_mom.csv", index=False)
    pd.DataFrame(uptrend_trans_list).to_csv("up_trans.csv", index=False)
    pd.DataFrame(downtrend_trans_list).to_csv("down_trans.csv", index=False)
    print("Pipeline Complete! Exported 4 CSV files.")

if __name__ == "__main__":
    run_master_pipeline()