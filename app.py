import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from NSE_list import nse_500

st.set_page_config(page_title="Nifty 4-Pillar Scanner", layout="wide")

st.sidebar.title("Navigation & Filters")
view_mode = st.sidebar.radio(
    "Select Market View:", 
    [
        "🚀 Bullish Momentum (Macro)", 
        "🩸 Bearish Momentum (Macro)", 
        "🌱 Uptrend Transition (Micro)", 
        "🔻 Downtrend Transition (Micro)"
    ]
)

# Clean Nifty 500 list for the UI
all_nifty_tickers = [t.replace('.NS', '') for t in nse_500]

# --- WATCHLIST MEMORY SETUP ---
# --- WATCHLIST MEMORY SETUP ---
if 'user_watchlist' not in st.session_state:
    desired_defaults = ['HAL', 'BEL', 'CGPOWER', 'KAYNES', 'DIXON', 'SUZLON', 'TATAPOWER']
    # Safety check: Only apply defaults that actually exist in your master list
    safe_defaults = [ticker for ticker in desired_defaults if ticker in all_nifty_tickers]
    st.session_state.user_watchlist = safe_defaults

indices = {
    "Nifty 50 (1-50)": all_nifty_tickers[:50],
    "Nifty Next 50 (51-100)": all_nifty_tickers[50:100],
    "Nifty Midcap 150 (101-250)": all_nifty_tickers[100:250],
    "Nifty Smallcap 250 (251-500)": all_nifty_tickers[250:500],
    "⭐ My Custom Watchlist": [] # Placeholder, logic handled below
}

selected_index = st.sidebar.selectbox("Select Market Segment:", list(indices.keys()))

# --- DYNAMIC WATCHLIST LOGIC ---
if selected_index == "⭐ My Custom Watchlist":
    # Show a multiselect box only when the Watchlist is active
    selected_tickers = st.sidebar.multiselect(
        "Add or remove stocks in your Watchlist:",
        options=all_nifty_tickers,
        default=st.session_state.user_watchlist
    )
    # Save any changes the user makes back to memory
    st.session_state.user_watchlist = selected_tickers
    valid_tickers = selected_tickers
else:
    valid_tickers = indices[selected_index]


@st.cache_data
def load_data(file_name):
    try:
        return pd.read_csv(file_name)
    except FileNotFoundError:
        st.error(f"Data file '{file_name}' missing. Run pipeline.py.")
        return pd.DataFrame()

# View Configuration Mapping
view_config = {
    "🚀 Bullish Momentum (Macro)": {"file": "bull_mom.csv", "cmap": "RdYlGn", "y_col_1": "Dist 50 DMA (%)", "y_col_2": "Dist 200 DMA (%)", "zone": 5, "type": "Macro"},
    "🩸 Bearish Momentum (Macro)": {"file": "bear_mom.csv", "cmap": "Reds", "y_col_1": "Dist 50 DMA (%)", "y_col_2": "Dist 200 DMA (%)", "zone": 5, "type": "Macro"},
    "🌱 Uptrend Transition (Micro)": {"file": "up_trans.csv", "cmap": "RdYlGn", "y_col_1": "Dist 9 EMA (%)", "y_col_2": "Dist 21 EMA (%)", "zone": 3, "type": "Micro"},
    "🔻 Downtrend Transition (Micro)": {"file": "down_trans.csv", "cmap": "Reds", "y_col_1": "Dist 9 EMA (%)", "y_col_2": "Dist 21 EMA (%)", "zone": 3, "type": "Micro"}
}

config = view_config[view_mode]
df = load_data(config["file"])

st.title(view_mode)

if not df.empty:
    df_segment = df[df['Ticker'].isin(valid_tickers)].set_index('Ticker').sort_values(by='Score', ascending=False)
    
    if df_segment.empty:
        if selected_index == "⭐ My Custom Watchlist" and not valid_tickers:
            st.info("Your watchlist is empty. Add some stocks from the sidebar!")
        else:
            st.info("No stocks in this segment match the current criteria.")
    else:
        df_display = df_segment.head(40)
        st.write(f"**Found {len(df_segment)} matching stocks. Displaying Top {len(df_display)}.**")

        fig, axes = plt.subplots(2, 1, figsize=(16, 10), gridspec_kw={'height_ratios': [1, 1.5]})
        
        # Heatmap
        sns.heatmap(df_display[['Score']].T, annot=True, fmt="d", cmap=config["cmap"], vmin=0, vmax=100, ax=axes[0], linewidths=0.5)
        axes[0].set_title(f'{view_mode} Score (0-100)', fontsize=14, fontweight='bold')

        # Scatter Plot
        axes[1].plot(df_display.index, df_display[config["y_col_1"]], linestyle='None', marker='o', markersize=8, color='#1f77b4', label=config["y_col_1"])
        axes[1].plot(df_display.index, df_display[config["y_col_2"]], linestyle='None', marker='s', markersize=8, color='#ff7f0e', label=config["y_col_2"])
        axes[1].axhspan(-config["zone"], config["zone"], color='gray', alpha=0.15)
        axes[1].axhline(0, color='black', linestyle='-', alpha=0.7) 
        axes[1].set_ylabel('% Distance from Average')
        axes[1].grid(True, linestyle=':', alpha=0.6)
        axes[1].legend(loc='upper right' if "Bullish" in view_mode or "Uptrend" in view_mode else 'lower right')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        st.pyplot(fig)

        # Action Zone Table
        st.subheader(f"Action Zone: Stocks Pulling Back to Support/Resistance (< {config['zone']}%)")
        action_df = df_segment[df_segment['Action Zone'] != 'No']
        st.dataframe(action_df, width='stretch')