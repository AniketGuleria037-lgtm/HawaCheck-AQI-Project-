"""Safe Strands tools for the advisor; invalid user/model values return messages."""
try: from strands import tool
except ModuleNotFoundError:
    def tool(function): return function
from aqi import calculate_aqi as _calculate_aqi
from data import fetch_air_quality
from forecast import add_hourly_aqi, fetch_forecast
from verdicts import ACTIVITY_RULES, AQI_LEVELS, get_activity_verdict as _verdict

def normalise_activity(value):
    """Map a case-insensitive activity value to its valid project name."""
    clean=" ".join(str(value).strip().lower().split())
    aliases={"cricket":"Sports period","football":"Sports period","pt":"Sports period","games":"Sports period","sports":"Sports period","morning prayer":"Outdoor assembly","assembly":"Outdoor assembly","bus":"School commute","walking to school":"School commute","class":"Classroom activities","lab":"Classroom activities"}
    return aliases.get(clean,next((name for name in ACTIVITY_RULES if name.lower()==clean),None))
def normalise_category(value):
    clean=" ".join(str(value).strip().lower().split())
    return next((name for name in AQI_LEVELS if name.lower()==clean),None)

@tool
def get_current_air_quality(latitude:float,longitude:float)->dict:
    """Get current model-based pollutants for coordinates in India."""
    return fetch_air_quality(latitude,longitude)
@tool
def get_forecast(latitude:float,longitude:float,date:str="",hour_range:str="")->list:
    """Get compact {time, aqi, category} forecast records; date YYYY-MM-DD and hour_range HH-HH are optional."""
    items=[{"time":x["time"],"aqi":x["aqi"],"category":x["category"]} for x in add_hourly_aqi(fetch_forecast(latitude,longitude))]
    if date: items=[x for x in items if x["time"].startswith(date)]
    if hour_range and "-" in hour_range:
        start,end=hour_range.split("-",1); items=[x for x in items if start<=x["time"][11:13]<=end]
    return items
@tool
def calculate_aqi(pm25:float,pm10:float)->dict:
    """Calculate the project AQI estimate from supplied PM2.5 and PM10."""
    return _calculate_aqi(pm25,pm10)
@tool
def get_activity_verdict(category:str,activity:str,vulnerable_children:bool=False):
    """Valid activities: Outdoor assembly, Sports period, Classroom activities, School commute. Valid AQI categories: Good, Satisfactory, Moderate, Poor, Very Poor, Severe."""
    category,activity=normalise_category(category),normalise_activity(activity)
    if not category or not activity:
        return f"Invalid values. Activities: {', '.join(ACTIVITY_RULES)}. AQI categories: {', '.join(AQI_LEVELS)}."
    return _verdict(category,activity,vulnerable_children)
TOOLS=[get_current_air_quality,get_forecast,calculate_aqi,get_activity_verdict]
