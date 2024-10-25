import streamlit as st
import pandas as pd
import requests
import datetime

# Constants and configurations
NSE_API_URL = "https://www.nseindia.com/api/option-chain-indices?symbol={}"
HEADERS = {'User-Agent': 'Mozilla/5.0'}

# Load data function
@st.cache_data
def load_option_chain(symbol, expiry_date):
    url = NSE_API_URL.format(symbol)
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    
    # Flatten and load the option chain data for calls and puts
    option_data = data['records']['data']
    call_data = []
    put_data = []
    
    for item in option_data:
        if item['expiryDate'] == expiry_date.strftime('%d-%b-%Y'):
            if 'CE' in item:
                call_data.append(item['CE'])
            if 'PE' in item:
                put_data.append(item['PE'])
    
    call_df = pd.DataFrame(call_data)
    put_df = pd.DataFrame(put_data)
    return call_df, put_df

# Get unique strike prices with a 100-point gap
def get_strike_prices(option_chain_df):
    strike_prices = option_chain_df['strikePrice'].unique()
    return sorted(strike_prices[::100])  # 100-point interval

# Streamlit app layout
st.title("NSE Option Chain Analyzer")

# User selections for symbol and expiry date
symbol = st.selectbox("Select Symbol", ["NIFTY", "BANKNIFTY", "RELIANCE", "TCS"])  # Add or replace with desired symbols
expiry_date = st.date_input("Select Expiry Date", min_value=datetime.date.today())

# Load option chain data
st.write("Loading data...")
call_df, put_df = load_option_chain(symbol, expiry_date)

# Generate strike price dropdown with 100-point gap
strike_prices = get_strike_prices(call_df)
selected_strike_price = st.selectbox("Select Strike Price", strike_prices)

# Filtered data based on selected strike price
filtered_call_df = call_df[call_df['strikePrice'] == selected_strike_price]
filtered_put_df = put_df[put_df['strikePrice'] == selected_strike_price]

# Display results
st.subheader(f"Options Chain for {symbol} at Strike Price {selected_strike_price}")

# Display Calls Data
st.write("**Call Options**")
st.dataframe(filtered_call_df[['strikePrice', 'openInterest', 'changeinOpenInterest', 'totalTradedVolume', 'impliedVolatility', 'lastPrice', 'change']])

# Display Puts Data
st.write("**Put Options**")
st.dataframe(filtered_put_df[['strikePrice', 'openInterest', 'changeinOpenInterest', 'totalTradedVolume', 'impliedVolatility', 'lastPrice', 'change']])

# Additional Analysis (Optional)
pcr = filtered_put_df['openInterest'].sum() / filtered_call_df['openInterest'].sum() if filtered_call_df['openInterest'].sum() != 0 else "N/A"
st.write(f"**Put-Call Ratio (PCR) at Strike Price {selected_strike_price}:**", pcr)

# Display open interest trends
st.write("**Open Interest Trends**")
st.line_chart(pd.DataFrame({
    'Call OI': filtered_call_df['openInterest'],
    'Put OI': filtered_put_df['openInterest']
}).reset_index(drop=True))

