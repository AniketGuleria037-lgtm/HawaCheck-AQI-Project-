"""Generate copyable school air-quality alerts for parents."""
from i18n import translate_activity, translate_category, translate_verdict


def generate_parent_alert(city, aqi_result, verdicts, best_window=None, language="English"):
    """Build a WhatsApp-style alert covering every school activity."""
    hindi = language == "हिन्दी"
    title = "🌿 *स्कूल वायु गुणवत्ता सूचना*" if hindi else "🌿 *School Air Quality Alert*"
    location = "स्थान" if hindi else "Location"
    estimate = "तत्काल अनुमानित AQI" if hindi else "Instant estimated AQI"
    activity_label = "गतिविधियाँ" if hindi else "Activities"
    lines = [title, "", f"📍 {location}: {city}",
             f"🌫️ {estimate}: {aqi_result['aqi']} ({translate_category(aqi_result['category'], language)})", "",
             f"🏫 *{activity_label}:*"]
    for activity, verdict in verdicts.items():
        lines.append(f"• {translate_activity(activity, language)}: {translate_verdict(verdict['verdict'], language)}")
    if best_window:
        label = "आज का बेहतर स्कूल-समय" if hindi else "Best school-hours window today"
        lines.extend(["", f"🕒 {label}: {best_window['start'][11:16]}–{best_window['end'][11:16]}"])
    disclaimer = "यह मॉडल डेटा है, CPCB की आधिकारिक रीडिंग या चिकित्सकीय सलाह नहीं।" if hindi else "This uses model data, not an official CPCB reading or medical advice."
    return "\n".join(lines) + f"\n\n{disclaimer}"
