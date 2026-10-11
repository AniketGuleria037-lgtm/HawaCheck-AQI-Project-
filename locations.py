"""Search Indian places with Open-Meteo geocoding."""
import requests
try: import streamlit as st
except ModuleNotFoundError:
 class _Fallback:
  @staticmethod
  def cache_data(*_args,**_kwargs): return lambda function:function
 st=_Fallback()
GEOCODING_URL="https://geocoding-api.open-meteo.com/v1/search"
@st.cache_data(ttl=600)
def search_indian_locations(query):
    """Return Indian matches, including district to distinguish duplicate names."""
    if len(query.strip())<2: return []
    response=requests.get(GEOCODING_URL,params={"name":query.strip(),"count":10,"language":"en","format":"json"},timeout=15)
    response.raise_for_status()
    return [
        {"name": item.get("name", "Unknown"), "admin1": item.get("admin1", ""),
         "admin2": item.get("admin2", ""), "latitude": item["latitude"],
         "longitude": item["longitude"]}
        for item in response.json().get("results", [])
        if item.get("country_code") == "IN"
    ]
