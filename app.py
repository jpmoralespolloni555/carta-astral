import datetime
import math
import ephem
import streamlit as st
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

ZODIAC_SIGNS = [
    "Aries", "Tauro", "Géminis", "Cáncer", "Leo", "Virgo",
    "Libra", "Escorpio", "Sagitario", "Capricornio", "Acuario", "Piscis"
]

ASCENDANT_DESCRIPTIONS = {
    "Aries": "Tu filtro de vida es la acción directa, la iniciativa y el dinamismo. Te proyectas con determinación y liderazgo natural.",
    "Tauro": "Proyectas estabilidad, paciencia y contacto con lo sensorial. Buscas construir bases sólidas y sostener procesos a largo plazo.",
    "Géminis": "Tu enfoque vital se basa en la curiosidad, el aprendizaje y la comunicación. Te adaptas rápido a la diversidad de ideas.",
    "Cáncer": "Muestras una coraza receptiva y protectora. Tu percepción del entorno es fuertemente intuitiva y enfocada en el resguardo emocional.",
    "Leo": "Proyectas vitalidad, magnetismo y expresión personal. Buscas compartir tu luz de forma genuina y asumir un rol central.",
    "Virgo": "Tu filtro es analítico, observador y funcional. Buscas el orden, el discernimiento y el perfeccionamiento de tus entornos.",
    "Libra": "Muestras una inclinación hacia la armonía, la estética y la mediación. Evalúas las situaciones desde la perspectiva del vínculo.",
    "Escorpio": "Proyectas intensidad, perspicacia y profundidad. Tu lectura del entorno va más allá de la superficie, buscando transformaciones reales.",
    "Sagitario": "Tu actitud vital es expansiva, optimista y orientada a la búsqueda de sentido, horizontes amplios y aprendizaje.",
    "Capricornio": "Proyectas estructura, pragmatismo y disciplina. Abordas tus metas con sobriedad y foco en la maestría a largo plazo.",
    "Acuario": "Tu visión es original, independiente y enfocada en la innovación. Aportas una perspectiva diferenciada a lo colectivo.",
    "Piscis": "Proyectas sensibilidad, empatía y apertura simbólica. Tu conexión con el entorno se da a través de la percepción sutil."
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

# --- CÁLCULOS NUMEROLÓGICOS ---

def reduce_number(n):
    while n > 9 and n not in [11, 22]:
        n = sum(int(digit) for digit in str(n))
    return n

def calculate_life_path(date_obj):
    total = date_obj.day + date_obj.month + sum(int(d) for d in str(date_obj.year))
    return reduce_number(total)

def calculate_personal_day(birth_date, query_date):
    day_month_birth = reduce_number(birth_date.day + birth_date.month)
    universal_day = reduce_number(query_date.day + query_date.month + sum(int(d) for d in str(query_date.year)))
    return reduce_number(day_month_birth + universal_day)

NUMEROLOGY_MEANINGS = {
    1: "Inicios, toma de decisiones individuales, autonomía e impulso para arrancar proyectos.",
    2: "Cooperación, alianzas, diplomacia y observación de detalles en acuerdos.",
    3: "Autoexpresión, creatividad, comunicación fluida y dinamismo social.",
    4: "Organización, estructura pragmática, trabajo enfocado y consolidación de bases.",
    5: "Movimiento, versatilidad, cambios de ritmo y adaptabilidad ante lo imprevisto.",
    6: "Responsabilidad, balance en los vínculos, contención y enfoque en la armonía.",
    7: "Introspección, análisis estratégico, estudio y discernimiento profundo.",
    8: "Eficiencia, gestión de recursos, visión de poder personal y concreción.",
    9: "Cierres de ciclo, integración de aprendizajes, balance general y generosidad.",
    11: "Visión intuitiva, inspiración elevada y sensibilidad para conectar ideas complejas.",
    22: "Construcción a gran escala, materialización de visiones y maestría práctica."
}

# --- CÁLCULOS ASTRONÓMICOS ---

def get_zodiac_position_from_deg(raw_deg):
    raw_deg = raw_deg % 360
    sign_num = int(raw_deg // 30)
    deg_in_sign = raw_deg % 30
    return {
        "sign": ZODIAC_SIGNS[sign_num],
        "degree": int(deg_in_sign),
        "minute": int((deg_in_sign - int(deg_in_sign)) * 60),
        "raw_deg": raw_deg
    }

def get_zodiac_position(equatorial_body):
    ecl = ephem.Ecliptic(equatorial_body)
    raw_deg = math.degrees(ecl.lon) % 360
    return get_zodiac_position_from_deg(raw_deg)

def calculate_exact_ascendant(dt_utc, lat, lon):
    """Cálculo trigonométrico exacto del Ascendente usando la oblicuidad real de la fecha."""
    observer = ephem.Observer()
    observer.date = dt_utc
    observer.lat = math.radians(lat)
    observer.lon = math.radians(lon)
    
    # Tiempo Sideral Local (LST) en radianes
    lst = float(observer.sidereal_time())
    
    # Oblicuidad verdadera de la eclíptica (IAU)
    julian_days = float(ephem.julian_date(dt_utc)) - 2451545.0
    eps_deg = 23.4392911 - (0.0000004 * julian_days)
    eps = math.radians(eps_deg)
    
    # Fórmula trigonométrica para la intersección de la eclíptica con el horizonte este
    y = -math.cos(lst)
    x = math.sin(lst) * math.cos(eps) + math.tan(observer.lat) * math.sin(eps)
    
    asc_deg = math.degrees(math.atan2(y, x)) % 360
    return get_zodiac_position_from_deg(asc_deg)

def calculate_chart(dt_utc, lat, lon):
    observer = ephem.Observer()
    observer.date = dt_utc
    observer.lat = str(lat)
    observer.lon = str(lon)
    
    bodies = {
        "Sol": ephem.Sun(observer),
        "Luna": ephem.Moon(observer),
        "Mercurio": ephem.Mercury(observer),
        "Venus": ephem.Venus(observer),
        "Marte": ephem.Mars(observer),
        "Júpiter": ephem.Jupiter(observer),
        "Saturno": ephem.Saturn(observer),
        "Urano": ephem.Uranus(observer),
        "Neptuno": ephem.Neptune(observer),
        "Plutón": ephem.Pluto(observer)
    }
    
    positions = {}
    for name, body in bodies.items():
        positions[name] = get_zodiac_position(body)
        
    positions["Ascendente"] = calculate_exact_ascendant(dt_utc, lat, lon)
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

def generate_daily_synthesis(natal, transits, aspects, life_path, personal_day):
    asc_sign = natal["Ascendente"]["sign"]
    sun_transit = transits["Sol"]["sign"]
    moon_transit = transits["Luna"]["sign"]
    
    tension_count = sum(1 for a in aspects if a["type"] == "Tensión")
    harmonic_count = sum(1 for a in aspects if a["type"] == "Armónico")
    
    text = f"""
    * **Integración Astrológica:** Con tu **Ascendente natal en {asc_sign}**, abordas las experiencias mediante {ASCENDANT_DESCRIPTIONS[asc_sign].lower()} El tránsito actual del **Sol en {sun_transit}** y la **Luna en {moon_transit}** inclina la atmósfera general hacia este terreno temático.
    * **Dinamismo de Aspectos:** En el mapa de hoy destacan **{harmonic_count} aspectos armónicos** y **{tension_count} de tensión** activos sobre tus posiciones natales.
    * **Conexión Numerológica:** Tu **Camino de Vida natal ({life_path})** sintoniza hoy con la energía del **Día Personal {personal_day}**, caracterizado por: _{NUMEROLOGY_MEANINGS.get(personal_day, '')}_
    """
    
    if tension_count > harmonic_count:
        guidance = f"La combinación entre la exigencia de los tránsitos y la vibración del Día Personal {personal_day} sugiere actuar con cautela. Utiliza la fortaleza pragmática de tu Ascendente en {asc_sign} para evitar sobre-reacciones."
    else:
        guidance = f"La fluidez de los aspectos astrológicos apoya los objetivos marcados por la energía del Día Personal {personal_day}. Es una jornada oportuna para canalizar la iniciativa alineada con tu esencia en {asc_sign}."
        
    return text, guidance

def calculate_color_recommendation(natal, transits, aspects):
    element_weights = {"Fuego": 0, "Tierra": 0, "Aire": 0, "Agua": 0}
    element_weights[get_element(natal["Sol"]["sign"])] += 3
    element_weights[get_element(natal["Luna"]["sign"])] += 2
    element_weights[get_element(natal["Ascendente"]["sign"])] += 3
    
    t_moon_element = get_element(transits["Luna"]["sign"])
    t_sun_element = get_element(transits["Sol"]["sign"])
    element_weights[t_moon_element] += 3
    element_weights[t_sun_element] += 2
    
    dominant_element = max(element_weights, key=element_weights.get)
    
    active_planets = [a["transit"] for a in aspects]
    if "Venus" in active_planets: comp_colors = f"{PLANET_COLORS['Venus']} y tonologías pastel"
    elif "Marte" in active_planets: comp_colors = "Gris Acero, Neutros fríos o Azul"
    else: comp_colors = f"{PLANET_COLORS['Sol']} y matices de {t_moon_element}"

    return {
        "main_color": ELEMENT_COLORS[dominant_element]["main"],
        "comp_colors": comp_colors,
        "avoid_color": ELEMENT_COLORS[dominant_element]["avoid"]
    }

# --- INTERFAZ STREAMLIT ---

st.set_page_config(page_title="Astrología y Numerología de Precisión", layout="wide")
st.title("🌌 Astrología & Numerología Integrada: Carta Natal, Tránsitos y Guía del Día")

st.sidebar.header("1. Datos de Nacimiento")
birth_date = st.sidebar.date_input("Fecha de nacimiento", datetime.date(1992, 5, 15), min_value=datetime.date(1900, 1, 1))
birth_time = st.sidebar.time_input("Hora exacta de nacimiento", datetime.time(14, 30))
city_name = st.sidebar.text_input("Ciudad y País de Nacimiento", "Santiago, Chile")

# Resolución de Zona Horaria Local para la Hora Actual de Consulta
tf = TimezoneFinder()
geolocator = Nominatim(user_agent="astro_num_app_tz_v3")
loc_default = geolocator.geocode(city_name)

if loc_default:
    tz_name = tf.timezone_at(lat=loc_default.latitude, lng=loc_default.longitude)
    tz_obj = pytz.timezone(tz_name)
    now_local = datetime.datetime.now(tz_obj)
else:
    now_local = datetime.datetime.now()

st.sidebar.header("2. Consulta de Tránsitos")
query_date = st.sidebar.date_input("Fecha de Consulta", now_local.date())
query_time = st.sidebar.time_input("Hora de Consulta (Auto-detectada Local)", now_local.time())

if st.sidebar.button("Calcular Carta, Tránsitos y Numerología"):
    location = geolocator.geocode(city_name)
    if location:
        lat, lon = location.latitude, location.longitude
        tz_str = tf.timezone_at(lat=lat, lng=lon)
        local_tz = pytz.timezone(tz_str)
        
        utc_birth = local_tz.localize(datetime.datetime.combine(birth_date, birth_time)).astimezone(pytz.utc)
        utc_query = local_tz.localize(datetime.datetime.combine(query_date, query_time)).astimezone(pytz.utc)
        
        natal_chart = calculate_chart(utc_birth, lat, lon)
        transit_chart = calculate_chart(utc_query, lat, lon)
        aspects = calculate_aspects(natal_chart, transit_chart)
        
        life_path = calculate_life_path(birth_date)
        personal_day = calculate_personal_day(birth_date, query_date)
        
        synthesis_text, guidance_text = generate_daily_synthesis(natal_chart, transit_chart, aspects, life_path, personal_day)
        rec = calculate_color_recommendation(natal_chart, transit_chart, aspects)
        
        st.success(f"Ubicación: **{location.address}** | Huso Horario Local: **{tz_str} (UTC{utc_query.strftime('%z')})**")
        
        # --- SECCIÓN 1: VÍNCULO ASTROLOGÍA + NUMEROLOGÍA + GUÍA DEL DÍA ---
        st.subheader("📜 Sincronía del Día: Astrología & Numerología")
        
        col_num1, col_num2 = st.columns(2)
        with col_num1:
            st.info(f"**Camino de Vida Natal:** Número **{life_path}**")
        with col_num2:
            st.success(f"**Día Personal de Consulta:** Número **{personal_day}**")
            
        st.markdown(synthesis_text)
        st.warning(f"**Guía & Consejo:** {guidance_text}")
        
        st.markdown("---")
        
        # --- SECCIÓN 2: PALETA DE COLORIMETRÍA ---
        st.subheader("🎨 Recomendación Energetizada de Color")
        c1, c2, c3 = st.columns(3)
        c1.info(f"**Principal:** {rec['main_color']}")
        c2.success(f"**Complementarios:** {rec['comp_colors']}")
        c3.error(f"**Evitar:** {rec['avoid_color']}")
        
        st.markdown("---")
        
        # --- SECCIÓN 3: ASCENDENTE Y CARTA NATAL vs TRÁNSITOS ---
        asc_info = natal_chart["Ascendente"]
        st.subheader(f"✨ Ascendente Natal: {asc_info['sign']} a {asc_info['degree']}° {asc_info['minute']}'")
        st.write(ASCENDANT_DESCRIPTIONS[asc_info["sign"]])
        
        col_nat, col_tra = st.columns(2)
        with col_nat:
            st.subheader("Planetas Natales")
            st.table([{"Planeta": p, "Signo": v["sign"], "Grados": f"{v['degree']}° {v['minute']}'"} for p, v in natal_chart.items() if p != "Ascendente"])
        with col_tra:
            st.subheader("Tránsitos de la Consulta")
            st.table([{"Planeta": p, "Signo": v["sign"], "Grados": f"{v['degree']}° {v['minute']}'"} for p, v in transit_chart.items() if p != "Ascendente"])
        
        st.subheader("⚡ Aspectos del Día (Tránsitos ➔ Natal)")
        st.dataframe([{"Tránsito": a["transit"], "Aspecto": a["aspect"], "Natal": a["natal"], "Órbita": f"{a['orb']}°", "Tipo": a["type"]} for a in aspects] if aspects else "Sin aspectos mayores registrados hoy.")
