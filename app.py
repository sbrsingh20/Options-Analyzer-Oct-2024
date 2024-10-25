import streamlit as st
import pandas as pd
import requests

# Load data function (example, replace with actual data fetching method)
def load_option_chain(symbol, expiry_date):
    url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    data = response.json()
    return pd.DataFrame(data['records']['data'])

# Fetch strike prices with 100-point gap
def get_strike_prices(option_chain_df):
    strike_prices = option_chain_df['strikePrice'].unique()
    return sorted(strike_prices[::100])  # Select every 100-point gap

# Streamlit UI
st.title("NSE Option Chain Analyzer")

# Select stock symbol
symbol = st.selectbox("Select Symbol", ["NIFTY", "BANKNIFTY", "RELIANCE", "TCS"])  # Add symbols as required
expiry_date = st.date_input("Select Expiry Date")

# Load option chain data
option_chain_df = load_option_chain(symbol, expiry_date)

# Generate strike price dropdown with 100 points gap
strike_prices = get_strike_prices(option_chain_df)
selected_strike_price = st.selectbox("Select Strike Price", strike_prices)

# Display filtered data based on selected strike price
filtered_df = option_chain_df[option_chain_df['strikePrice'] == selected_strike_price]
st.write(f"Options Chain for {symbol} at Strike Price {selected_strike_price}", filtered_df)
