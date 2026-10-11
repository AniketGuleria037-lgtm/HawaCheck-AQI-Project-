"""Fetch and evaluate Open-Meteo hourly air-quality forecasts."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import requests
from aqi import calculate_aqi

try:
    import streamlit as st
except ModuleNotFoundError:  # Allows offline calculation tests without the UI dependency.
    class _StreamlitFallback:
        @staticmethod
        def cache_data(*_args, **_kwargs):
            return lambda function: function
    st = _StreamlitFallback()

API_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
IST = ZoneInfo("Asia/Kolkata")


def is_in_window(hour_time, best_window):
    """Return whether an hourly ISO timestamp falls inside a best-window interval."""
    if not best_window:
        return False
    point = datetime.fromisoformat(hour_time)
    return datetime.fromisoformat(best_window["start"]) <= point < datetime.fromisoformat(best_window["end"])


@st.cache_data(ttl=600)
def fetch_forecast(latitude, longitude):
    """Return the next 48 available hourly PM forecasts from the current hour."""
    response = requests.get(API_URL, params={"latitude": latitude, "longitude": longitude,
        "hourly": "pm2_5,pm10", "forecast_days": 3, "timezone": "Asia/Kolkata"}, timeout=20)
    response.raise_for_status()
    hourly = response.json().get("hourly")
    if not hourly:
        raise ValueError("No hourly forecast data was returned.")
    forecast = [{"time": time, "pm2_5": pm25, "pm10": pm10}
                for time, pm25, pm10 in zip(hourly.get("time", []), hourly.get("pm2_5", []), hourly.get("pm10", []))
                if pm25 is not None and pm10 is not None]
    if not forecast:
        raise ValueError("No usable hourly pollutant values were returned.")
    current_hour = datetime.now(IST).replace(tzinfo=None, minute=0, second=0, microsecond=0)
    return [hour for hour in forecast if datetime.fromisoformat(hour["time"]) >= current_hour][:48]


def add_hourly_aqi(forecast):
    """Add estimated AQI/category values to forecast hours."""
    results = []
    for hour in forecast:
        result = calculate_aqi(pm25=hour["pm2_5"], pm10=hour["pm10"])
        results.append({**hour, "aqi": result["aqi"], "category": result["category"], "color": result["color"]})
    return results


def find_safest_two_hour_window(forecast, target_date=None, now=None, school_start=7, school_end=16):
    """Find a lowest-AQI consecutive two-hour window during school hours."""
    now = now or datetime.now(IST).replace(tzinfo=None)
    target_date = target_date or now.date()
    candidates = []
    for first, second in zip(forecast, forecast[1:]):
        if first.get("aqi") is None or second.get("aqi") is None:
            continue
        first_time, second_time = datetime.fromisoformat(first["time"]), datetime.fromisoformat(second["time"])
        if second_time - first_time != timedelta(hours=1):
            continue
        if first_time.date() != target_date or second_time.date() != target_date:
            continue
        if first_time.hour < school_start or second_time.hour > school_end:
            continue
        if target_date == now.date() and first_time < now:
            continue
        candidates.append((first, second, first_time, second_time))
    if not candidates:
        return None
    first, second, first_time, second_time = min(candidates, key=lambda item: (item[0]["aqi"] + item[1]["aqi"]) / 2)
    return {"start": first_time.isoformat(), "end": (second_time + timedelta(hours=1)).isoformat(),
            "average_aqi": round((first["aqi"] + second["aqi"]) / 2, 1),
            "category": first["category"] if first["aqi"] >= second["aqi"] else second["category"]}