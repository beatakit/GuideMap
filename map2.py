import streamlit as st
import requests
import sqlite3
import pandas as pd
import folium
from streamlit_folium import st_folium
# from requests_html import HTMLSession
# s = HTMLSession()
# response = s.get(url)
# response.html.render()

st.set_page_config(page_title="Vilnius Old Town Map", layout="wide", page_icon="🦈")
VILNIUS = (54.6870458, 25.2829111)
senamiestis = {"lat_min": 54.673, "lat_max": 54.695, "lon_min": 25.265, "lon_max": 25.295}

# Database setup
@st.cache_resource
def get_db():
    conn = sqlite3.connect('MyDB.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS city_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            description TEXT
        )
    """)
    conn.commit()
    return conn

DB = get_db()
c = DB.cursor()

# Load existing points
df = pd.read_sql_query("SELECT * FROM city_points", DB)

# Sidebar: Search by name
st.sidebar.header("🔍 Ieškok")
search_text = st.sidebar.text_input("Ko ieškai?")

selected_lat, selected_lon = VILNIUS  # default

if search_text:
    # Call Nominatim API
    url = "https://nominatim.openstreetmap.org/search?q={}&format=jsonv2"
    # params = {"q": search_text, "format": "json", "limit": 1, "addressdetails": 1, "countrycodes": "lt"}
    headers = {"User-Agent": "GuideMap/1.0"}
    response = requests.get(url.format(search_text), headers=headers) # timeout=1,
    count = len(response)
    if count > 1:
        st.write("Found {count} objects")

    # st.write(response)
    # st.write(response.text)
    rsp = response.json() # json pakeitem i python koda

    if rsp:
        selected_lat = float(rsp[0]["lat"])
        selected_lon = float(rsp[0]["lon"])
        st.sidebar.success(f"Coordinates found: {selected_lat:.6f}, {selected_lon:.6f}")
    else:
        st.sidebar.warning("Place not found!")

# Sidebar: Add a Place
st.sidebar.header("➕ Add a Place")
with st.sidebar.form("add_point_form"):
    name = st.text_input("Name")
    category = st.text_input("Category")
    lat = st.number_input("Latitude", value=float(selected_lat), format="%.6f")
    lon = st.number_input("Longitude", value=float(selected_lon), format="%.6f")
    desc = st.text_area("Description")
    submitted = st.form_submit_button("Add Point")

    if submitted:
        if not name:
            st.sidebar.error("Name is required!")
        elif not (
            senamiestis["lat_min"] <= lat <= senamiestis["lat_max"]
            and senamiestis["lon_min"] <= lon <= senamiestis["lon_max"]
        ):
            st.sidebar.error("Point must be inside Vilnius Old Town!")
            # st.sidebar.write(senamiestis["lat_min"],lat, senamiestis["lat_max"])
            # st.sidebar.write(senamiestis["lon_min"],lat, senamiestis["lon_max"])
            # st.sidebar.write(senamiestis["lat_min"] <= lat <= senamiestis["lat_max"])
            # st.sidebar.write(senamiestis["lon_min"] <= lon <= senamiestis["lon_max"])
        else:
            c.execute("""
                INSERT INTO city_points
                (name, category, latitude, longitude, description)
                VALUES (?, ?, ?, ?, ?)
            """, (name, category, lat, lon, desc))
            DB.commit()
            st.sidebar.success(f"Added: {name}")
            

# Streamlit map
st.title("🗺️ Vilnius Map App")
m = folium.Map(location=VILNIUS, zoom_start=15, min_zoom=14, max_zoom=18)
m.fit_bounds([
    [senamiestis["lat_min"], senamiestis["lon_min"]],
    [senamiestis["lat_max"], senamiestis["lon_max"]],
])

# Add markers
for _, row in df.iterrows():
    popup_html = f"""
    <b>{row['name']}</b><br>
    <i>{row['category']}</i><br><br>
    {row['description']}
    """
    folium.Marker(
        location=[row["latitude"], row["longitude"]],
        popup=popup_html,
        icon=folium.Icon(icon="info-sign")
    ).add_to(m)

st_folium(m, width=1100, height=600)
