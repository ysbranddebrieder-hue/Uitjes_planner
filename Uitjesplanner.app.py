import streamlit as st
import json
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

st.set_page_config(page_title="Uitjes Finder", layout="wide")
st.title("🎯 Uitjes in je Omgeving")

# Laad activiteiten data
with open('activities.json', 'r', encoding='utf-8') as f:
    activities = json.load(f)

# Gebruiker voert locatie in
col1, col2 = st.columns(2)
with col1:
    user_location = st.text_input("Voer je stad/adres in:")
with col2:
    radius = st.slider("Zoekradius (km)", 1, 50, 10)

# Functie om coördinaten op te halen
@st.cache_data
def get_coordinates(location):
    geolocator = Nominatim(user_agent="activities_finder")
    try:
        loc = geolocator.geocode(location)
        return (loc.latitude, loc.longitude)
    except:
        st.error("Locatie niet gevonden")
        return None

if user_location:
    user_coords = get_coordinates(user_location)
    
    if user_coords:
        # Filter activiteiten op afstand
        nearby_activities = []
        for activity in activities:
            activity_coords = (activity['lat'], activity['lon'])
            distance = geodesic(user_coords, activity_coords).kilometers
            
            if distance <= radius:
                activity['distance'] = round(distance, 1)
                nearby_activities.append(activity)
        
        # Toon resultaten
        if nearby_activities:
            st.success(f"✅ {len(nearby_activities)} activiteiten gevonden!")
            
            for activity in sorted(nearby_activities, key=lambda x: x['distance']):
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.subheader(activity['name'])
                        st.write(f"📍 {activity['address']}")
                        st.write(f"📝 {activity['description']}")
                        if activity.get('url'):
                            st.markdown(f"[Meer info →]({activity['url']})")
                    with col2:
                        st.metric("Afstand", f"{activity['distance']} km")
        else:
            st.info("Geen activiteiten gevonden binnen deze radius")
