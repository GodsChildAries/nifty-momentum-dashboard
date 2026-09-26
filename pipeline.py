import yfinance as yf
import pandas as pd
from NSE_list import nse_500
from datetime import datetime

def run_daily_calculations():
    print(f"[{datetime.now()}] Starting EOD data pipeline for Nifty 500...")
    data = yf.download(nse_500, period="1y")['Close']
    
    analysis_list = []
    
    for ticker in nse_500:
        if ticker not in data.columns: continue
        price_series = data[ticker].dropna()
        if len(price_series) < 210: continue 
            
        dma_50 = price_series.rolling(window=50).mean()
        dma_200 = price_series.rolling(window=200).mean()
        ema_9 = price_series.ewm(span=9, adjust=False).mean()
        
        current_price = price_series.iloc[-1]
        curr_ema_9 = ema_9.iloc[-1]
        if current_price <= curr_ema_9: continue  # Strict 9 EMA filter
        
        curr_dma_50, curr_dma_200 = dma_50.iloc[-1], dma_200.iloc[-1]
        dist_50_pct = ((current_price - curr_dma_50) / curr_dma_50) * 100
        dist_200_pct = ((current_price - curr_dma_200) / curr_dma_200) * 100
        dma_cross_pct = ((curr_dma_50 - curr_dma_200) / curr_dma_200) * 100
        
        score = int((dma_50.diff().iloc[-10:] > 0).sum() * 2) + \
                int((dma_200.diff().iloc[-10:] > 0).sum() * 2) + \
                int(min(20, max(0, 10 + (dist_50_pct * 2)))) + \
                int(min(20, max(0, 10 + (dist_200_pct * 2)))) + \
                int(min(20, max(0, 10 + (dma_cross_pct * 2))))
                
        analysis_list.append({
            'Ticker': ticker.replace('.NS', ''),
            'Price': round(current_price, 2),
            '9 EMA': round(curr_ema_9, 2),
            '50 DMA': round(curr_dma_50, 2),
            '200 DMA': round(curr_dma_200, 2),
            'Bullish Score': score,
            'Dist 50 DMA (%)': round(dist_50_pct, 2),
            'Dist 200 DMA (%)': round(dist_200_pct, 2),
            'Near DMA Zone': '50 DMA' if abs(dist_50_pct) <= 5.0 else ('200 DMA' if abs(dist_200_pct) <= 5.0 else 'No')
        })

    # Save the final processed data to a CSV
    final_df = pd.DataFrame(analysis_list)
    final_df.to_csv("master_dashboard_data.csv", index=False)
    print("Pipeline complete. CSV exported successfully.")

if __name__ == "__main__":
    run_daily_calculations()