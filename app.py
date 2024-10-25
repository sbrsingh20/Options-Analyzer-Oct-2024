import streamlit as st
import pandas as pd
import requests
import datetime

# Constants and configurations
NSE_INDEX_URL = "https://www.nseindia.com/api/option-chain-indices?symbol={}"
NSE_STOCK_URL = "https://www.nseindia.com/api/option-chain-equities?symbol={}"
HEADERS = {'User-Agent': 'Mozilla/5.0'}

# Load option chain data function
@st.cache_data
def load_option_chain(symbol, expiry_date, mode):
    url = NSE_INDEX_URL.format(symbol) if mode == "Index" else NSE_STOCK_URL.format(symbol)
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        data = response.json()
        option_data = data['records']['data']
        
        # Separate call and put data, filtering by expiry date
        call_data = [item['CE'] for item in option_data if 'CE' in item and item['expiryDate'] == expiry_date.strftime('%d-%b-%Y')]
        put_data = [item['PE'] for item in option_data if 'PE' in item and item['expiryDate'] == expiry_date.strftime('%d-%b-%Y')]
        
        call_df = pd.DataFrame(call_data) if call_data else pd.DataFrame()
        put_df = pd.DataFrame(put_data) if put_data else pd.DataFrame()
        return call_df, put_df
    else:
        st.error("Failed to load data from NSE. Please try again later.")
        return pd.DataFrame(), pd.DataFrame()

# Get unique strike prices with a 100-point gap
def get_strike_prices(option_chain_df):
    if 'strikePrice' in option_chain_df.columns:
        strike_prices = option_chain_df['strikePrice'].unique()
        return sorted(strike_prices[::100])  # 100-point interval
    else:
        st.warning("Strike Price data unavailable.")
        return []

# Streamlit app layout
st.title("NSE Option Chain Analyzer")

# User inputs for mode, symbol, and expiry date
mode = st.radio("Select Mode", ["Index", "Stock"])
symbol = st.selectbox("Select Symbol", ["NIFTY", "BANKNIFTY", "RELIANCE", "TCS"])
expiry_date = st.date_input("Select Expiry Date", min_value=datetime.date.today())

# Load option chain data
call_df, put_df = load_option_chain(symbol, expiry_date, mode)

# Strike price selection with fallback to user input
strike_prices = get_strike_prices(call_df)
if strike_prices:
    selected_strike_price = st.selectbox("Select Strike Price", strike_prices)
else:
    selected_strike_price = st.number_input("Enter Strike Price", min_value=0, step=50)

# Filtered data based on selected or entered strike price
if not call_df.empty and not put_df.empty:
    filtered_call_df = call_df[call_df['strikePrice'] == selected_strike_price]
    filtered_put_df = put_df[put_df['strikePrice'] == selected_strike_price]

    # Display results
    st.subheader(f"Options Chain for {symbol} at Strike Price {selected_strike_price}")
    
    # Display Server Time and Value
    server_time = call_df['timestamp'].iloc[0] if 'timestamp' in call_df.columns else "N/A"
    value = call_df['underlyingValue'].iloc[0] if 'underlyingValue' in call_df.columns else "N/A"
    st.write(f"**Server Time**: {server_time}")
    st.write(f"**Value**: {value}")

    # Display Calls Data
    if not filtered_call_df.empty:
        st.write("**Call Options**")
        st.dataframe(filtered_call_df[['strikePrice', 'openInterest', 'changeinOpenInterest', 'totalTradedVolume', 'impliedVolatility', 'lastPrice', 'change']])
    else:
        st.write("No data available for the selected strike price in Calls.")

    # Display Puts Data
    if not filtered_put_df.empty:
        st.write("**Put Options**")
        st.dataframe(filtered_put_df[['strikePrice', 'openInterest', 'changeinOpenInterest', 'totalTradedVolume', 'impliedVolatility', 'lastPrice', 'change']])
    else:
        st.write("No data available for the selected strike price in Puts.")

    # Compute additional parameters
    call_sum = filtered_call_df['changeinOpenInterest'].sum() if 'changeinOpenInterest' in filtered_call_df else 0
    put_sum = filtered_put_df['changeinOpenInterest'].sum() if 'changeinOpenInterest' in filtered_put_df else 0
    difference = call_sum - put_sum
    call_boundary = filtered_call_df.iloc[1]['changeinOpenInterest'] if len(filtered_call_df) > 1 else 0
    put_boundary = filtered_put_df.iloc[0]['changeinOpenInterest'] if len(filtered_put_df) > 0 else 0

    # Labels for Open Interest trends
    open_interest_trend = "Bullish" if put_sum > call_sum else "Bearish"
    put_call_ratio = put_sum / call_sum if call_sum != 0 else "N/A"
    
    # Labels for ITM based on thresholds
    call_itm = "Yes" if (put_sum / call_sum) > 1.5 else "No" if call_sum != 0 else "N/A"
    put_itm = "Yes" if (call_sum / put_sum) > 1.5 else "No" if put_sum != 0 else "N/A"
    
    # Display label data
    st.write("### Open Interest Analysis")
    st.write(f"**Call Sum**: {call_sum} (in Thousands for Index / Tens for Stock)")
    st.write(f"**Put Sum**: {put_sum} (in Thousands for Index / Tens for Stock)")
    st.write(f"**Difference**: {difference}")
    st.write(f"**Call Boundary**: {call_boundary} - Indicates {'Bearish' if call_boundary > 0 else 'Bullish'} signal")
    st.write(f"**Put Boundary**: {put_boundary} - Indicates {'Bullish' if put_boundary > 0 else 'Bearish'} signal")
    st.write(f"**Open Interest Trend**: {open_interest_trend}")
    st.write(f"**Put-Call Ratio (PCR)**: {put_call_ratio}")
    st.write(f"**Call In The Money (ITM)**: {call_itm}")
    st.write(f"**Put In The Money (ITM)**: {put_itm}")

else:
    st.warning("No option chain data available for the selected date.")
