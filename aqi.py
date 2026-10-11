
"""
Approximate Indian AQI calculations using PM2.5 and PM10.

These values are derived from Open-Meteo model data, not
official CPCB monitoring-station readings.
"""

# Approximate concentration breakpoints and corresponding
# Indian AQI sub-index ranges.
#
# Each tuple is:
# (concentration_low, concentration_high, aqi_low, aqi_high)

PM25_BREAKPOINTS = [
    (0, 30, 0, 50),
    (31, 60, 51, 100),
    (61, 90, 101, 200),
    (91, 120, 201, 300),
    (121, 250, 301, 400),
    (251, 500, 401, 500),
]

PM10_BREAKPOINTS = [
    (0, 50, 0, 50),
    (51, 100, 51, 100),
    (101, 250, 101, 200),
    (251, 350, 201, 300),
    (351, 430, 301, 400),
    (431, 600, 401, 500),
]

AQI_CATEGORIES = [
    (50, "Good", "#00B050"),
    (100, "Satisfactory", "#92D050"),
    (200, "Moderate", "#FFFF00"),
    (300, "Poor", "#FF9900"),
    (400, "Very Poor", "#FF0000"),
    (500, "Severe", "#99004C"),
]



def calculate_sub_index(concentration, breakpoints):
    """
    Calculate a pollutant sub-index using linear interpolation.

    Concentrations between integer breakpoint boundaries are assigned
    to the next applicable band. Values above the final band receive
    the maximum AQI of 500.
    """

    if concentration is None:
        return None

    if concentration < 0:
        raise ValueError("Pollutant concentration cannot be negative.")

    # Find the first band whose upper concentration limit contains
    # this value. Clamp to the band's lower limit to handle gaps such
    # as 30.5 between the 0-30 and 31-60 bands.
    for c_low, c_high, i_low, i_high in breakpoints:
        if concentration <= c_high:
            adjusted = max(concentration, c_low)

            sub_index = (
                (i_high - i_low)
                / (c_high - c_low)
            ) * (adjusted - c_low) + i_low

            return round(sub_index)

    # Concentrations beyond the highest defined band are capped.
    return 500



def get_aqi_category(aqi):
    """Return the Indian AQI category for a calculated index."""

    if aqi is None:
        return "Unavailable"

    for upper_limit, category, _color in AQI_CATEGORIES:
        if aqi <= upper_limit:
            return category

    return "Beyond supported range"


def get_aqi_color(aqi):
    """Return a colour for the AQI display."""

    if aqi is None:
        return "#808080"

    for upper_limit, _category, color in AQI_CATEGORIES:
        if aqi <= upper_limit:
            return color

    return "#808080"


def calculate_aqi(pm25=None, pm10=None):
    """
    Return approximate AQI, category and pollutant sub-indices.

    At least one supported pollutant measurement is required.
    If both are available, the overall index is their maximum.
    """

    if pm25 is None and pm10 is None:
        raise ValueError("At least one pollutant value is required.")

    pm25_index = calculate_sub_index(pm25, PM25_BREAKPOINTS)
    pm10_index = calculate_sub_index(pm10, PM10_BREAKPOINTS)

    available_indices = [
        index
        for index in (pm25_index, pm10_index)
        if index is not None
    ]

    if not available_indices:
        return {
            "aqi": None,
            "category": "Unavailable",
            "color": "#808080",
            "pm25_sub_index": pm25_index,
            "pm10_sub_index": pm10_index,
            "is_approximate": True,
            "source": "Open-Meteo model data",
        }

    overall_aqi = max(available_indices)

    return {
        "aqi": overall_aqi,
        "category": get_aqi_category(overall_aqi),
        "color": get_aqi_color(overall_aqi),
        "pm25_sub_index": pm25_index,
        "pm10_sub_index": pm10_index,
        "is_approximate": True,
        "source": "Open-Meteo model data",
    }
