import streamlit as st
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import requests
import json

st.title("🎯 Uitjes in je Omgeving")

location = st.text_input("Voer je stad in:", "Amsterdam")
activity_type = st.selectbox(
    "Wat zoek je?",
    ["restaurant", "museum", "park", "cafe", "library"]
)
radius = st.slider("Zoekradius (km)", 1, 50, 10)

if location:
    try:
        # Geocodeer locatie
        geolocator = Nominatim(user_agent="activities_finder")
        loc = geolocator.geocode(location)
        
        if loc:
            st.success(f"📍 Gezocht in: {location}")
            
            # Overpass API query voor OSM data
            overpass_url = "http://overpass-api.de/api/interpreter"
            
            # Map activity types to OSM tags
            osm_tags = {
                "restaurant": "amenity=restaurant",
                "museum": "tourism=museum",
                "park": "leisure=park",
                "cafe": "amenity=cafe",
                "library": "amenity=library"
            }
            
            query = f"""
            [bbox:{loc.latitude-radius/111},{loc.longitude-radius/111},{loc.latitude+radius/111},{loc.longitude+radius/111}];
            (
              node[{osm_tags.get(activity_type, "tourism=attraction")}];
              way[{osm_tags.get(activity_type, "tourism=attraction")}];
            );
            out center;
            """
            
            response = requests.get(overpass_url, params={'data': query}, timeout=10)
            
            if response.status_code == 200:
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
                
                places = sorted(places, key=lambda x: x['distance'])[:20]
                
                if places:
                    st.write(f"✅ **{len(places)} {activity_type}s gevonden!**")
                    
                    for place in places:
                        with st.container(border=True):
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.subheader(place['name'])
                                st.write(f"📍 {place['lat']:.4f}, {place['lng']:.4f}")
                                if 'phone' in place['tags']:
                                    st.write(f"📞 {place['tags']['phone']}")
                                if 'website' in place['tags']:
                                    st.markdown(f"[Website →]({place['tags']['website']})")
                            with col2:
                                st.metric("Afstand", f"{place['distance']} km")
                else:
                    st.info("Geen resultaten gevonden")
            else:
                st.error("API fout bij ophalen gegevens")
                
    except Exception as e:
        st.error(f"Fout: {str(e)}")
