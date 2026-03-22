import streamlit as st
import requests

st.set_page_config(page_title="Trip Duration Predictor")

st.title("Trip Duration Predictor")
st.write("Enter trip details and get an estimated ride time.")

distance_km = st.slider("Distance (km)", min_value=1.0, max_value=20.0, value=10.0, step=0.5)
battery_level = st.slider("Battery Level (%)", min_value=0.0, max_value=100.0, value=50.0, step=1.0)

payload = {
    "distance_km": distance_km,
    "battery_level": battery_level
}

try:
    response = requests.post(
        "http://127.0.0.1:8000/predict/duration",
        json=payload,
        timeout=5
    )

    if response.status_code == 200:
        data = response.json()
        st.metric(label="Estimated Trip Time", value=f"{data['estimated_minutes']} min")
    else:
        st.error(f"Request failed: {response.status_code}")
        try:
            st.json(response.json())
        except Exception:
            st.text(response.text or "No response body")

except requests.exceptions.ConnectionError:
    st.error("Could not connect to FastAPI server. Make sure it is running on http://127.0.0.1:8000")
