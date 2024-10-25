import streamlit as st
import pandas as pd
import requests
import datetime

# Constants and configurations
NSE_INDEX_URL = "https://www.nseindia.com/api/option-chain-indices?symbol={}"
NSE_STOCK_URL = "https://www.nseindia.com/api/option-chain-equities?symbol={}"
HEADERS = {'User-Agent': 'Mozilla/5.0'}

# Predefined strike prices
strike_price_options = [
    22250.00, 22300.00, 22350.00, 22400.00, 22450.00, 22500.00, 22550.00, 22600.00, 22650.00, 22700.00,
    22750.00, 22800.00, 22850.00, 22900.00, 22950.00, 23000.00, 23050.00, 23100.00, 23150.00, 23200.00,
    23250.00, 23300.00, 23350.00, 23400.00, 23450.00, 23500.00, 23550.00, 23600.00, 23650.00, 23700.00,
    23750.00, 23800.00, 23850.00, 23900.00, 23950.00, 24000.00, 24050.00, 24100.00, 24150.00, 24200.00,
    24250.00, 24300.00, 24350.00, 24400.00, 24450.00, 24500.00, 24550.00, 24600.00, 24650.00, 24700.00,
    24750.00, 24800.00, 24850.00, 24900.00, 24950.00, 25000.00, 25050.00, 25100.00, 25150.00, 25200.00,
    25250.00, 25300.00, 25350.00, 25400.00, 25450.00, 25500.00, 25550.00, 25600.00, 25650.00, 25700.00,
    25750.00, 25800.00, 25850.00, 25900.00, 25950.00, 26000.00, 26050.00, 26100.00, 26150.00, 26200.00,
    26250.00, 26300.00, 26350.00, 26400.00, 26450.00, 26500.00, 26550.00, 26600.00, 26650.00, 26700.00,
    26750.00, 26800.00, 26850.00, 26900.00, 26950.00, 27000.00
]

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

# Streamlit app layout
st.title("NSE Option Chain Analyzer")

# User inputs for mode, symbol, and expiry date
mode = st.radio("Select Mode", ["Index", "Stock"])
symbol = st.selectbox("Select Symbol", ["NIFTY", "BANKNIFTY", "RELIANCE", "TCS"])
expiry_date = st.date_input("Select Expiry Date", min_value=datetime.date.today())

# Load option chain data
call_df, put_df = load_option_chain(symbol, expiry_date, mode)

# User selection for predefined strike prices
selected_strike_price = st.selectbox("Select Strike Price", strike_price_options)

# Filtered data based on selected strike price
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
    
    # Display Open Interest Analysis as a table
    st.write("### Open Interest Analysis")
    oi_analysis_data = {
        "Parameter": ["Call Sum", "Put Sum", "Difference", "Call Boundary", "Put Boundary", "Open Interest Trend", "Put-Call Ratio (PCR)", "Call In The Money (ITM)", "Put In The Money (ITM)"],
        "Value": [call_sum, put_sum, difference, call_boundary, put_boundary, open_interest_trend, put_call_ratio, call_itm, put_itm]
    }
    oi_analysis_df = pd.DataFrame(oi_analysis_data)
    st.table(oi_analysis_df)

else:
    st.warning("No option chain data available for the selected date.")
