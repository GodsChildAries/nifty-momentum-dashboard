import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from NSE_list import nse_500

st.set_page_config(page_title="Trend & DMA Dashboard", layout="wide")
st.title("Momentum & DMA Proximity Dashboard")
st.caption("Data is updated daily after market close (EOD).")

# Segment definitions
indices = {
    "Nifty 50 (1-50)": [t.replace('.NS', '') for t in nse_500[:50]],
    "Nifty Next 50 (51-100)": [t.replace('.NS', '') for t in nse_500[50:100]],
    "Nifty Midcap 150 (101-250)": [t.replace('.NS', '') for t in nse_500[100:250]],
    "Nifty Smallcap 250 (251-500)": [t.replace('.NS', '') for t in nse_500[250:500]]
}

selected_index = st.selectbox("Select Market Segment:", list(indices.keys()))
valid_tickers = indices[selected_index]

# Instantly load the pre-calculated CSV
@st.cache_data
def load_data():
    try:
        return pd.read_csv("master_dashboard_data.csv")
    except FileNotFoundError:
        st.error("Market data is updating. Please refresh in a few minutes.")
        return pd.DataFrame()

df = load_data()

if not df.empty:
    # Filter for the selected segment
    df_segment = df[df['Ticker'].isin(valid_tickers)]
    
    if df_segment.empty:
        st.warning("No stocks in this segment are currently trading above their 9 EMA.")
    else:
        df_segment = df_segment.set_index('Ticker').sort_values(by='Bullish Score', ascending=False)
        df_display = df_segment.head(40)
        
        st.success(f"Found {len(df_segment)} stocks above 9 EMA. Displaying Top {len(df_display)}.")

        # Plotting logic remains exactly the same as before
        fig, axes = plt.subplots(2, 1, figsize=(16, 10), gridspec_kw={'height_ratios': [1, 1.5]})

        score_df = df_display[['Bullish Score']].T
        sns.heatmap(score_df, annot=True, fmt="d", cmap="RdYlGn", vmin=0, vmax=100, ax=axes[0], linewidths=0.5)
        axes[0].set_title(f'Top Bullish Stocks', fontsize=14, fontweight='bold')

        axes[1].plot(df_display.index, df_display['Dist 50 DMA (%)'], linestyle='None', marker='o', markersize=8, color='#1f77b4', label='Distance to 50 DMA')
        axes[1].plot(df_display.index, df_display['Dist 200 DMA (%)'], linestyle='None', marker='s', markersize=8, color='#ff7f0e', label='Distance to 200 DMA')
        axes[1].axhspan(-5, 5, color='gray', alpha=0.15)
        axes[1].axhline(0, color='black', linestyle='-', alpha=0.7) 
        axes[1].set_ylabel('% Distance from DMA')
        axes[1].grid(True, linestyle=':', alpha=0.6)
        axes[1].legend(loc='upper right')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        st.pyplot(fig)

        st.subheader("Action Zone: Stocks near DMA Support/Resistance (< 5%)")
        near_dma_df = df_segment[df_segment['Near DMA Zone'] != 'No']
        st.dataframe(near_dma_df[['Price', '9 EMA', '50 DMA', '200 DMA', 'Dist 50 DMA (%)', 'Dist 200 DMA (%)', 'Near DMA Zone']], width='stretch')