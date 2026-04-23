import streamlit as st
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import requests
import time

st.set_page_config(page_title="Uitjes Finder", layout="wide")
st.title("🎯 Uitjes in je Omgeving")

location = st.text_input("Voer je stad in:", "Amsterdam")
activity_type = st.selectbox(
    "Wat zoek je?",
    ["restaurant", "museum", "park", "cafe", "library", "playground", "swimming_pool"]
)
radius = st.slider("Zoekradius (km)", 1, 50, 10)

if st.button("🔍 Zoeken"):
    with st.spinner("Even geduld, aan het zoeken..."):
        try:
            # Geocodeer locatie
            geolocator = Nominatim(user_agent="activities_finder_v1")
            loc = geolocator.geocode(location, timeout=10)
            
            if not loc:
                st.error(f"Locatie '{location}' niet gevonden")
                st.stop()
            
            st.success(f"📍 Gezocht rond: **{location}**")
            
            # OSM tags mapping
            osm_tags = {
                "restaurant": "amenity=restaurant",
                "museum": "tourism=museum",
                "park": "leisure=park",
                "cafe": "amenity=cafe",
                "library": "amenity=library",
                "playground": "leisure=playground",
                "swimming_pool": "leisure=swimming_pool"
            }
            
            tag = osm_tags.get(activity_type, "tourism=attraction")
            
            # Maak Overpass query
            query = f"""
            [bbox:{loc.latitude - radius/111},{loc.longitude - radius/111},{loc.latitude + radius/111},{loc.longitude + radius/111}];
            (
              node[{tag}];
              way[{tag}];
            );
            out center;
            """
            
            # Overpass API call met retry
            overpass_url = "https://overpass-api.de/api/interpreter"
            max_retries = 3
            response = None
            
            for attempt in range(max_retries):
                try:
                    response = requests.get(
                        overpass_url, 
                        params={'data': query}, 
                        timeout=15
                    )
                    if response.status_code == 200:
                        break
                    elif response.status_code == 429:  # Rate limit
                        st.warning(f"API overbelast, poging {attempt + 1}/{max_retries}...")
                        time.sleep(2)
                    else:
                        st.warning(f"API fout {response.status_code}, poging {attempt + 1}/{max_retries}...")
                        time.sleep(2)
                except requests.exceptions.Timeout:
                    st.warning(f"Timeout, poging {attempt + 1}/{max_retries}...")
                    time.sleep(2)
            
            if not response or response.status_code != 200:
                st.error(f"❌ Overpass API is momenteel niet beschikbaar. Probeer het later opnieuw.")
                st.info("💡 Tip: Probeer een kleinere zoekradius of een ander moment")
                st.stop()
            
            # Parse resultaten
            data = response.json()
            places = []
            
            for element in data.get('elements', []):
                if 'lat' in element and 'lon' in element:
                    name = element['tags'].get('name', 'Onbekend')
                    lat = element['lat']
                    lng = element['lon']
                    distance = geodesic((loc.latitude, loc.longitude), (lat, lng)).kilometers
                    
                    places.append({
                        'name': name,
                        'lat': lat,
                        'lng': lng,
                        'distance': round(distance, 1),
                        'tags': element.get('tags', {})
                    })
            
            # Sorteer op afstand
            places = sorted(places, key=lambda x: x['distance'])[:30]
            
            if places:
                st.subheader(f"✅ {len(places)} {activity_type}s gevonden!")
                
                # Toon in kolommen
                for place in places:
                    with st.container(border=True):
                        col1, col2 = st.columns([4, 1])
                        
                        with col1:
                            st.subheader(place['name'])
                            
                            # Adres/coördinaten
                            st.write(f"📍 {place['lat']:.4f}, {place['lng']:.4f}")
                            
                            # Contact info
                            tags = place['tags']
                            if 'phone' in tags:
                                st.write(f"📞 {tags['phone']}")
                            if 'website' in tags:
                                st.markdown(f"[🌐 Website]({tags['website']})")
                            if 'opening_hours' in tags:
                                st.write(f"🕐 {tags['opening_hours']}")
                            if 'description' in tags:
                                st.write(f"ℹ️ {tags['description']}")
                        
                        with col2:
                            st.metric("Afstand", f"{place['distance']} km")
            else:
                st.info(f"Geen {activity_type}s gevonden in deze omgeving")
        
        except Exception as e:
            st.error(f"❌ Fout: {str(e)}")
            st.info("💡 Probeer het later opnieuw of gebruik een ander zoekwoord")
