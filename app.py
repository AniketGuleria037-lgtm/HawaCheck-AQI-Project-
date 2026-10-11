"""School AQI Advisor Streamlit app."""
from datetime import datetime, timedelta
import os
from zoneinfo import ZoneInfo
import requests
import streamlit as st
from dotenv import load_dotenv
from aqi import calculate_aqi
from data import fetch_air_quality
from forecast import add_hourly_aqi, fetch_forecast, find_safest_two_hour_window, is_in_window
from i18n import get_text,translate_activity,translate_category,translate_verdict
from locations import search_indian_locations
from parent_alert import generate_parent_alert
from verdicts import ACTIVITY_RULES,get_activity_verdict
load_dotenv(); IST=ZoneInfo("Asia/Kolkata")
CITIES={"Delhi":(28.6139,77.2090),"Mumbai":(19.0760,72.8777),"Bengaluru":(12.9716,77.5946),"Chennai":(13.0827,80.2707),"Kolkata":(22.5726,88.3639)}
ACTIVITIES=list(ACTIVITY_RULES); st.set_page_config(page_title="School AQI Advisor",page_icon="🌿",layout="wide")

def text_color(color):
    """Use dark text on light yellow/green cards for readability."""
    r,g,b=(int(color[i:i+2],16) for i in (1,3,5)); return "#000" if (r*299+g*587+b*114)/1000>160 else "#fff"
@st.cache_data(ttl=600,show_spinner=False)
def get_ai_advice(city,measurements,activity,verdict,language):
    from strands import Agent
    from strands.models.gemini import GeminiModel
    from google.genai import types
    key=os.getenv("GEMINI_API_KEY")
    if not key:raise ValueError("GEMINI_API_KEY is missing from .env.")
    prompt=f"""Reply in {'Hindi' if language=='हिन्दी' else 'English'}. LOCATION: {city}; model estimates: PM2.5 {measurements['pm2_5']}, PM10 {measurements['pm10']}, NO2 {measurements['nitrogen_dioxide']} µg/m³. Activity: {activity}. AUTHORITATIVE PYTHON VERDICT: {verdict['verdict']}. Explain it; never change the verdict, invent AQI values, or declare a school open or closed. Mention model-data limitations and official advisories."""
    model=GeminiModel(client_args={"api_key":key,"http_options":types.HttpOptions(timeout=30000)},model_id="gemini-2.5-flash")
    return str(Agent(model=model)(prompt))
def ask_advisor(question,place,activity,vulnerable,language):
    from strands import Agent
    from strands.models.gemini import GeminiModel
    from agent_tools import TOOLS
    key=os.getenv("GEMINI_API_KEY")
    if not key:raise ValueError("GEMINI_API_KEY is missing from .env.")
    prompt=f"""Current India time: {datetime.now(IST):%A %d %B %Y %H:%M}. Answer in {'Hindi' if language=='हिन्दी' else 'English'} in under 120 words. User question: {question}. Coordinates: {place['latitude']}, {place['longitude']}; selected activity {activity}; vulnerable children {vulnerable}. You MUST call tools before answering, use only tool-returned AQI values, and quote get_activity_verdict's verdict unchanged. Valid activities: {', '.join(ACTIVITIES)}. Valid categories: Good, Satisfactory, Moderate, Poor, Very Poor, Severe. Map cricket/football/PT/games to Sports period; morning prayer/assembly to Outdoor assembly; bus/walking to school to School commute; class/lab to Classroom activities. Politely decline unrelated questions. Give one short safety caveat; never declare a school open or closed."""
    return str(Agent(model=GeminiModel(client_args={"api_key":key},model_id="gemini-2.5-flash"),tools=TOOLS)(prompt))
def fallback(value):
    return ["Continue to follow applicable official advisories.","Watch for symptoms and reduce exposure if needed."] if value=="Go ahead" else ["Reduce outdoor activity duration or intensity.","Consider an indoor alternative where appropriate."] if value=="Modify" else ["Avoid or relocate the planned outdoor activity.","Check official local air-quality and school guidance."]

language=st.sidebar.selectbox(get_text("English","language"),["English","हिन्दी"])
st.title(get_text(language,"title"));st.write(get_text(language,"hero"));st.info(get_text(language,"disclaimer"));st.subheader(get_text(language,"location"))
if "location_query" not in st.session_state:st.session_state.location_query=""
quick=st.radio(get_text(language,"quick_select"),list(CITIES),horizontal=True,index=0)
query=st.text_input(get_text(language,"search"),key="location_query")
def clear_search():
    """Reset the search box. Runs as a button callback, before the next rerun draws the widget."""
    st.session_state.location_query=""
if query:st.button(get_text(language,"clear_search"),on_click=clear_search)
matches=[]
if query.strip():
    try:matches=search_indian_locations(query)
    except requests.RequestException as error:st.warning(str(error))
    if not matches:st.info(get_text(language,"no_results"))
if matches:
    choice=st.selectbox(get_text(language,"matching_locations"),matches,format_func=lambda x:", ".join(part for part in (x["name"],x["admin2"],x["admin1"]) if part))
    place={"name":", ".join(part for part in (choice["name"],choice["admin2"],choice["admin1"]) if part),"latitude":choice["latitude"],"longitude":choice["longitude"]};st.caption(get_text(language,"using_search",place=place["name"]))
else:
    lat,lon=CITIES[quick];place={"name":quick,"latitude":lat,"longitude":lon};st.caption(get_text(language,"using_quick",place=quick))
try:
    with st.spinner(get_text(language,"fetching")):measurements=fetch_air_quality(place["latitude"],place["longitude"])
except (requests.RequestException,ValueError) as error:
    st.error(f"Could not retrieve usable data: {error}");st.stop()
try:
    with st.spinner(get_text(language,"loading_forecast")):forecast_data=add_hourly_aqi(fetch_forecast(place["latitude"],place["longitude"]))
except (requests.RequestException,ValueError) as error:
    forecast_data=[];st.warning(get_text(language,"forecast_warning"))
aqi_result=calculate_aqi(measurements["pm2_5"],measurements["pm10"]);st.subheader(f"{get_text(language,'snapshot')}: {place['name']}")
fg=text_color(aqi_result["color"]);st.markdown(f"<div style='background:{aqi_result['color']};color:{fg};padding:20px;border-radius:12px;text-align:center'><b>{get_text(language,'instant_aqi')}</b><div style='font-size:48px'>{aqi_result['aqi']}</div><b>{translate_category(aqi_result['category'],language)}</b></div>",unsafe_allow_html=True);st.caption(get_text(language,"aqi_caption"))
for col,label,field in zip(st.columns(3),("PM2.5","PM10","Nitrogen dioxide"),("pm2_5","pm10","nitrogen_dioxide")):col.metric(label,f"{measurements[field]} µg/m³")
st.subheader(get_text(language,"activity_planner"));vulnerable=st.checkbox(get_text(language,"vulnerable"));activity=st.selectbox(get_text(language,"choose_activity"),ACTIVITIES,format_func=lambda x:translate_activity(x,language));verdict=get_activity_verdict(aqi_result["category"],activity,vulnerable)
fg=text_color(verdict["color"]);st.markdown(f"<div style='background:{verdict['color']};color:{fg};padding:16px;border-radius:12px'><b>{translate_activity(activity,language)}</b><h3>{verdict['icon']} {translate_verdict(verdict['verdict'],language)}</h3>{translate_category(verdict['category'],language)}</div>",unsafe_allow_html=True)
with st.expander(get_text(language,"verdict_rules")):st.write(get_text(language,"verdict_rules_text"))
advice_key=(place["name"],activity,vulnerable,language)
if st.button(get_text(language,"generate")):
    st.session_state.pop("advice",None)
    try:
        with st.spinner(get_text(language,"analysing")):answer=get_ai_advice(place["name"],measurements,activity,verdict,language)
        st.session_state.advice={"text":answer,"key":advice_key};st.session_state.pop("advice_error",None)
    except Exception as error:st.session_state.advice_error={"text":str(error),"key":advice_key}
if st.session_state.get("advice",{}).get("key")==advice_key:st.markdown(st.session_state.advice["text"])
if st.session_state.get("advice_error",{}).get("key")==advice_key:
    st.warning(get_text(language,"ai_unavailable"));st.markdown(f"### {get_text(language,'basic_precautions')}")
    for tip in fallback(verdict["verdict"]):st.write(f"- {tip}")
    with st.expander(get_text(language,"technical")):st.code(st.session_state.advice_error["text"])
now=datetime.now(IST).replace(tzinfo=None);best_window=find_safest_two_hour_window(forecast_data,now.date(),now) if forecast_data else None
if not best_window and forecast_data:best_window=find_safest_two_hour_window(forecast_data,now.date()+timedelta(days=1),now)
st.subheader(get_text(language,"forecast"))
if forecast_data:
    st.line_chart({"Time":[x["time"] for x in forecast_data],"Estimated AQI":[x["aqi"] for x in forecast_data]},x="Time",y="Estimated AQI")
    if best_window:st.success(f"{get_text(language,'best_window')}: {best_window['start'][11:16]}–{best_window['end'][11:16]} (AQI {best_window['average_aqi']})")
    else:st.info(get_text(language,"no_window"))
    day=datetime.fromisoformat(best_window["start"]).date() if best_window else now.date()
    chips=[x for x in forecast_data if datetime.fromisoformat(x["time"]).date()==day and 7<=datetime.fromisoformat(x["time"]).hour<=16]
    if not chips:day=now.date()+timedelta(days=1);chips=[x for x in forecast_data if datetime.fromisoformat(x["time"]).date()==day and 7<=datetime.fromisoformat(x["time"]).hour<=16]
    st.markdown(f"### {get_text(language,'timeline')} — {day.strftime('%A, %d %b')}")
    chip_html=[]  # build every chip first, then render once so they sit in one wrapping strip
    for hour in chips:
        item=get_activity_verdict(hour["category"],activity,vulnerable);border="border:3px solid #111;" if is_in_window(hour["time"],best_window) else ""
        chip_html.append(f"<span style='display:inline-block;margin:3px;padding:7px;border-radius:8px;background:{item['color']};color:{text_color(item['color'])};{border}'>{hour['time'][11:16]} {translate_verdict(item['verdict'],language)}</span>")
    st.markdown("".join(chip_html),unsafe_allow_html=True)
all_verdicts={x:get_activity_verdict(aqi_result["category"],x,vulnerable) for x in ACTIVITIES};st.subheader(get_text(language,"parent_alert"));st.code(generate_parent_alert(place["name"],aqi_result,all_verdicts,best_window,language),language=None)
question=st.text_input(get_text(language,"advisor_question"),placeholder=get_text(language,"advisor_placeholder"));advisor_key=(question,place["name"],activity,vulnerable,language)
if st.button(get_text(language,"ask")) and question:
    try:
        with st.spinner(get_text(language,"analysing")):st.session_state.advisor_answer={"text":ask_advisor(question,place,activity,vulnerable,language),"key":advisor_key}
    except Exception as error:st.error(get_text(language,"advisor_unavailable",error=error))
if st.session_state.get("advisor_answer",{}).get("key")==advisor_key:st.markdown(st.session_state.advisor_answer["text"])