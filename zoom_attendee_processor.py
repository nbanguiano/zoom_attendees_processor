import os
import pandas as pd
import streamlit as st
import chardet as cd
from datetime import datetime

def process_zoom_attendees(file_path, timestamp_threshold, skip_rows=0):

    with open(file_path, 'rb') as f:
        result = cd.detect(f.read(100000)) # Read the first 100KB
        detected_encoding = result['encoding']

    df = pd.read_csv(file_path, skiprows=skip_rows, encoding=detected_encoding)
    df['Leave Time'] = pd.to_datetime(df['Leave Time'], errors='coerce')
    df = df.sort_values('Leave Time').drop_duplicates(subset=['Email'], keep='last')
    df = df[df['Is Guest'] == 'Yes']
    threshold = pd.to_datetime(timestamp_threshold)
    df = df[df['Leave Time'] >= threshold]
    digested_df = df[['First Name', 'Last Name', 'Email']]
    return digested_df

# Streamlit app
st.title("Zoom Attendee CSV Helper")

st.markdown("""
This little tool processes Zoom webinar attendee reports, and filters attendees past a given time threshold (normally used to filter those who stayed after the pitch).

Upload your file, define the pitch timestamp on your left, and you’ll get a cleaned-up file with names and emails of those "pitched" ready to download!
""")

with st.sidebar:
    st.header("Settings")
    
    st.subheader("Timestamp Threshold")
    date = st.date_input("Select date", value=datetime(2025, 2, 8))
    time = st.time_input("Select time", value=datetime(2025, 2, 8, 13, 0).time())
    timestamp = datetime.combine(date, time)
    
    skip_rows = st.slider("Rows to skip", min_value=0, max_value=50, value=16, step=1)

uploaded_file = st.file_uploader("Upload Zoom Attendee Report (.csv) — No personal data is saved, anywhere, ever.", type="csv")

if uploaded_file is not None:
    if st.button("Process File"):
        with st.spinner("Processing..."):
            temp_path = os.path.join("temp", uploaded_file.name)
            os.makedirs("temp", exist_ok=True)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            digested_df = process_zoom_attendees(temp_path, timestamp, skip_rows)

            st.write("Processed Data Preview:")
            st.dataframe(digested_df)

            output_file = uploaded_file.name.replace(".csv", "-digested.csv")
            digested_df.to_csv(output_file, index=False)

            with open(output_file, "rb") as f:
                st.download_button(
                    label="Download Digested File",
                    data=f,
                    file_name=output_file,
                    mime="text/csv"
                )

            os.remove(temp_path)
else:
    st.write("Please upload a file to begin.")

if 'output_file' in locals() and os.path.exists(output_file):
    os.remove(output_file)