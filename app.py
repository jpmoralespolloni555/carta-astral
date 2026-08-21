import datetime
import math
import swisseph as swe
import streamlit as st
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

# Configuración inicial de Swiss Ephemeris
swe.set_ephe_path('')

ZODIAC_SIGNS = [
    "Aries", "Tauro", "Géminis", "Cáncer", "Leo", "Virgo",
    "Libra", "Escorpio", "Sagitario", "Capricornio", "Acuario", "Piscis"
]

PLANETS = {
    swe.SUN: "Sol",
    swe.MOON: "Luna",
    swe.MERCURY: "Mercurio",
    swe.VENUS: "Venus",
    swe.MARS: "Marte",
    swe.JUPITER: "Júpiter",
    swe.SATURN: "Saturno",
    swe.URANUS: "Urano",
    swe.NEPTUNE: "Neptuno",
    swe.PLUTO: "Plutón"
}

ELEMENT_COLORS = {
    "Fuego": {"main": "Rojo vibrante o Naranja", "avoid": "Azul oscuro o Gris apagado"},
    "Tierra": {"main": "Verde oliva, Terracota o Marrón", "avoid": "Tonos neón o Colores sintéticos"},
    "Aire": {"main": "Amarillo claro, Blanco o Azul cielo", "avoid": "Negro pesado o Marrón oscuro"},
    "Agua": {"main": "Azul marino, Turquesa o Violeta", "avoid": "Rojo chillón o Naranja fuego"}
}

PLANET_COLORS = {
    "Sol": "Dorado, Amarillo o Naranja",
    "Luna": "Blanco, Plata o Perla",
    "Mercurio": "Verde claro, Amarillo o Gris claro",
    "Venus": "Rosa, Verde esmeralda o Pasteles",
    "Marte": "Rojo, Granate o Coral",
    "Júpiter": "Azul real, Púrpura o Turquesa",
    "Saturno": "Negro, Gris marengo o Azul noche",
    "Urano": "Azul eléctrico o Tonos metalizados",
    "Neptuno": "Azul marino, Verde agua o Violeta",
    "Plutón": "Tinto, Borgoña o Negro"
}

def get_julian_day(dt_utc):
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0)

def get_zodiac_position(longitude):
    sign_num = int(longitude // 30)
    deg_in_sign = longitude % 30
    return {
        "sign": ZODIAC_SIGNS[sign_num],
        "degree": int(deg_in_sign),
        "minute": int((deg_in_sign - int(deg_in_sign)) * 60),
        "raw_deg": longitude
    }

def calculate_chart(dt_utc, lat, lon):
    jd = get_julian_day(dt_utc)
    positions = {}
    for p_id, p_name in PLANETS.items():
        res, _ = swe.calc_ut(jd, p_id)
        positions[p_name] = get_zodiac_position(res[0])
        positions[p_name]["speed"] = res[3]
    cusps, ascmc = swe.houses(jd, lat, lon, b'P')
    positions["Ascendente"] = get_zodiac_position(ascmc[0])
    return positions

def get_element(sign_name):
    elements = {
        "Aries": "Fuego", "Leo": "Fuego", "Sagitario": "Fuego",
        "Tauro": "Tierra", "Virgo": "Tierra", "Capricornio": "Tierra",
        "Géminis": "Aire", "Libra": "Aire", "Acuario": "Aire",
        "Cáncer": "Agua", "Escorpio": "Agua", "Piscis": "Agua"
    }
    return elements.get(sign_name, "Desconocido")

def calculate_aspects(natal, transits):
    aspects_def = [("Conjunción", 0, 8), ("Oposición", 180, 8), ("Trígono", 120, 7), ("Cuadratura", 90, 7), ("Sextil", 60, 5)]
    found = []
    for t_name, t_pos in transits.items():
        if t_name == "Ascendente": continue
        for n_name, n_pos in natal.items():
            diff = abs(t_pos["raw_deg"] - n_pos["raw_deg"])
            if diff > 180: diff = 360 - diff
            for asp_name, asp_deg, orb in aspects_def:
                if abs(diff - asp_deg) <= orb:
                    found.append({
                        "transit": t_name,
                        "natal": n_name,
                        "aspect": asp_name,
                        "orb": round(abs(diff - asp_deg), 2),
                        "type": "Tensión" if asp_name in ["Cuadratura", "Oposición"] else "Armónico"
                    })
    return found

def calculate_color_recommendation(natal, transits, aspects):
    element_weights = {"Fuego": 0, "Tierra": 0, "Aire": 0, "Agua": 0}
    element_weights[get_element(natal["Sol"]["sign"])] += 3
    element_weights[get_element(natal["Luna"]["sign"])] += 2
    element_weights[get_element(natal["Ascendente"]["sign"])] += 3
    
    t_moon_element = get_element(transits["Luna"]["sign"])
    t_sun_element = get_element(transits["Sol"]["sign"])
    element_weights[t_moon_element] += 3
    element_weights[t_sun_element] += 2
    
    tension_count = sum(1 for a in aspects if a["type"] == "Tensión")
    harmonic_count = sum(1 for a in aspects if a["type"] == "Armónico")
    dominant_element = max(element_weights, key=element_weights.get)
    
    active_planets = [a["transit"] for a in aspects]
    if "Venus" in active_planets: comp_colors = f"{PLANET_COLORS['Venus']} y pasteles suaves"
    elif "Marte" in active_planets: comp_colors = "Gris Acero, Neutros fríos o Azul"
    else: comp_colors = f"{PLANET_COLORS['Sol']} y tonos de {t_moon_element}"

    return {
        "main_color": ELEMENT_COLORS[dominant_element]["main"],
        "comp_colors": comp_colors,
        "avoid_color": ELEMENT_COLORS[dominant_element]["avoid"],
        "explanation": f"* **Elemento Predominante hoy:** {dominant_element}.\n* **Aspectos activos:** {harmonic_count} armónicos y {tension_count} de tensión.",
        "advice": "Día con fricción planetaria. Mantén la calma e integra tonos neutros." if tension_count > harmonic_count else "Tránsitos en armonía. Excelente día para concretar metas e iniciativas."
    }

st.set_page_config(page_title="Astrología de Precisión", layout="wide")
st.title("🌌 Astrología de Precisión: Carta Natal, Tránsitos y Colorimetría")

st.sidebar.header("1. Datos de Nacimiento")
birth_date = st.sidebar.date_input("Fecha de nacimiento", datetime.date(1992, 5, 15), min_value=datetime.date(1900, 1, 1))
birth_time = st.sidebar.time_input("Hora exacta de nacimiento", datetime.time(14, 30))
city_name = st.sidebar.text_input("Ciudad y País de Nacimiento", "Santiago, Chile")

st.sidebar.header("2. Consulta de Tránsitos")
query_date = st.sidebar.date_input("Fecha de Consulta", datetime.date.today())
query_time = st.sidebar.time_input("Hora de Consulta", datetime.datetime.now().time())

if st.sidebar.button("Calcular Carta y Tránsitos"):
    geolocator = Nominatim(user_agent="astro_app_cloud")
    location = geolocator.geocode(city_name)
    if location:
        lat, lon = location.latitude, location.longitude
        tf = TimezoneFinder()
        tz_str = tf.timezone_at(lat=lat, lng=lon)
        local_tz = pytz.timezone(tz_str)
        utc_birth = local_tz.localize(datetime.datetime.combine(birth_date, birth_time)).astimezone(pytz.utc)
        utc_query = local_tz.localize(datetime.datetime.combine(query_date, query_time)).astimezone(pytz.utc)
        
        natal_chart = calculate_chart(utc_birth, lat, lon)
        transit_chart = calculate_chart(utc_query, lat, lon)
        aspects = calculate_aspects(natal_chart, transit_chart)
        rec = calculate_color_recommendation(natal_chart, transit_chart, aspects)
        
        st.success(f"Ubicación: **{location.address}** | Huso Horario: **{tz_str}**")
        st.subheader("🎨 Recomendación de Color del Día")
        c1, c2, c3 = st.columns(3)
        c1.info(f"**Principal:** {rec['main_color']}")
        c2.success(f"**Complementarios:** {rec['comp_colors']}")
        c3.error(f"**Evitar:** {rec['avoid_color']}")
        st.markdown(rec["explanation"])
        st.warning(rec["advice"])
        st.markdown("---")
        
        col_nat, col_tra = st.columns(2)
        with col_nat:
            st.subheader("📜 Carta Natal")
            st.write(f"**Ascendente:** {natal_chart['Ascendente']['sign']} a {natal_chart['Ascendente']['degree']}° {natal_chart['Ascendente']['minute']}'")
            st.table([{"Planeta": p, "Signo": v["sign"], "Grados": f"{v['degree']}° {v['minute']}'"} for p, v in natal_chart.items() if p != "Ascendente"])
        with col_tra:
            st.subheader("🌌 Tránsitos del Día")
            st.table([{"Planeta": p, "Signo": v["sign"], "Grados": f"{v['degree']}° {v['minute']}'"} for p, v in transit_chart.items() if p != "Ascendente"])
        
        st.subheader("⚡ Aspectos del Día")
        st.dataframe([{"Tránsito": a["transit"], "Aspecto": a["aspect"], "Natal": a["natal"], "Órbita": f"{a['orb']}°", "Tipo": a["type"]} for a in aspects] if aspects else "Sin aspectos mayores hoy.")
