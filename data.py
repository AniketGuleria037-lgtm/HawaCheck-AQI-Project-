"""Shared current air-quality data access."""
import requests
try:
    import streamlit as st
except ModuleNotFoundError:
    class _StreamlitFallback:
        @staticmethod
        def cache_data(*_args, **_kwargs):
            return lambda function: function
    st = _StreamlitFallback()

API_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


@st.cache_data(ttl=600)
def fetch_air_quality(latitude, longitude):
    """Fetch validated model-based current pollutant estimates."""
    response = requests.get(API_URL, params={"latitude": latitude, "longitude": longitude,
        "current": "pm2_5,pm10,nitrogen_dioxide", "timezone": "Asia/Kolkata"}, timeout=20)
    response.raise_for_status()
    current = response.json().get("current")
    if not current:
        raise ValueError("No current measurements were returned.")
    for pollutant in ("pm2_5", "pm10", "nitrogen_dioxide"):
        if current.get(pollutant) is None:
            raise ValueError(f"The API did not return {pollutant}.")
    return current
