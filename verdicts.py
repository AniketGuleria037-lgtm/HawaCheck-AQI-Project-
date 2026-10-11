"""Rule-based school activity recommendations.

These are conservative project rules, not official CPCB or medical guidance.
"""

AQI_LEVELS = {"Good": 0, "Satisfactory": 1, "Moderate": 2, "Poor": 3,
              "Very Poor": 4, "Severe": 5}

# Outdoor assembly / commute: modify from Moderate, indoors from Very Poor.
# Sport: modify from Moderate, indoors from Poor because exertion is high.
# Classroom: modify from Poor, indoors from Severe as it is already indoors.
ACTIVITY_RULES = {
    "Outdoor assembly": {"modify_at": 2, "indoors_at": 4},
    "Sports period": {"modify_at": 2, "indoors_at": 3},
    "Classroom activities": {"modify_at": 3, "indoors_at": 5},
    "School commute": {"modify_at": 2, "indoors_at": 4},
}
VERDICT_DETAILS = {
    "Go ahead": {"color": "#218838", "icon": "✅"},
    "Modify": {"color": "#e0a800", "icon": "⚠️"},
    "Move indoors": {"color": "#c82333", "icon": "🏠"},
}


def get_activity_verdict(category, activity, vulnerable_children=False):
    """Return a fixed project verdict for the supplied AQI category."""
    if category not in AQI_LEVELS:
        raise ValueError(f"Unknown AQI category: {category}")
    if activity not in ACTIVITY_RULES:
        raise ValueError(f"Unknown activity: {activity}")
    level, rules = AQI_LEVELS[category], ACTIVITY_RULES[activity]
    if level >= rules["indoors_at"]:
        verdict = "Move indoors"
    elif level >= rules["modify_at"]:
        verdict = "Modify"
    else:
        verdict = "Go ahead"
    if vulnerable_children:
        verdict = {"Go ahead": "Modify", "Modify": "Move indoors",
                   "Move indoors": "Move indoors"}[verdict]
    return {"activity": activity, "verdict": verdict,
            "color": VERDICT_DETAILS[verdict]["color"],
            "icon": VERDICT_DETAILS[verdict]["icon"], "category": category,
            "vulnerable_children": vulnerable_children}
