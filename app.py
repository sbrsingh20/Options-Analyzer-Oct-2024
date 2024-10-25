import streamlit as st
import pandas as pd
import requests
import datetime

# Constants and configurations
NSE_API_URL = "https://www.nseindia.com/api/option-chain-indices?symbol={}"
HEADERS = {'User-Agent': 'Mozilla/5.0'}

# Load option chain data function
@st.cache_data
def load_option_chain(symbol, expiry_date):
    url = NSE_API_URL.format(symbol)
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

# User selections for symbol and expiry date
symbol = st.selectbox("Select Symbol", ["NIFTY", "BANKNIFTY", "RELIANCE", "TCS"])
expiry_date = st.date_input("Select Expiry Date", min_value=datetime.date.today())

# Load option chain data
call_df, put_df = load_option_chain(symbol, expiry_date)

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

    # Put-Call Ratio (PCR)
    if not filtered_call_df.empty and not filtered_put_df.empty:
        pcr = filtered_put_df['openInterest'].sum() / filtered_call_df['openInterest'].sum() if filtered_call_df['openInterest'].sum() != 0 else "N/A"
        st.write(f"**Put-Call Ratio (PCR) at Strike Price {selected_strike_price}:**", pcr)

    # Open Interest Trends
    st.write("**Open Interest Trends**")
    st.line_chart(pd.DataFrame({
        'Call OI': filtered_call_df['openInterest'],
        'Put OI': filtered_put_df['openInterest']
    }).reset_index(drop=True))

else:
    st.warning("No option chain data available for the selected date.")
