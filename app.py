import html as htmllib
import io
import json
import math
import re
import urllib.parse
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import streamlit as st
from packaging.version import Version

APP_NAME = "AgriSense"
APP_TAGLINE = "Crop recommendation based on soil nutrition"

st.set_page_config(
    page_title=f"{APP_NAME} | {APP_TAGLINE}",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

STRETCH = (
    {"width": "stretch"}
    if Version(st.__version__) >= Version("1.50.0")
    else {"use_container_width": True}
)

# ============================================================
# THEME: SOIL STRATA (topsoil, subsoil, clay, sand + leaf green)
# ============================================================
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Inter:wght@400;500;600;700&family=Noto+Sans+Tamil:wght@400;600;700&display=swap');
:root{
  --top:#2e2016; --sub:#5a3d27; --clay:#9a6b43; --sand:#e9dbbd; --cream:#fbf6ea;
  --leaf:#3f7d3a; --sprout:#8bc34a; --harvest:#d9962b; --ink:#2b2118; --muted:#6b5c4b;
  --forest:#14391f; --forest2:#1f5a2c;
  --p1:#4fa356; --p2:#3b8d46; --p3:#2c7a3a; --p4:#1b5429;
  --edge:#b9d99a; --fborder:#7fae5a; --stepper:#e3f0d3; --side2:#0c2814;
  --b1:#5a3d27; --b2:#7a5435; --b3:#9a6b43; --b4:#c29a6b;
}
html, body, [class*="css"]{ font-family:'Inter','Noto Sans Tamil',sans-serif; }
.stApp{ color:var(--ink);
  background:
    repeating-linear-gradient(90deg, rgba(255,255,255,.045) 0 3px, transparent 3px 54px),
    radial-gradient(circle at 12% 8%, var(--p1) 0, transparent 38%),
    radial-gradient(circle at 90% 92%, var(--p2) 0, transparent 40%),
    linear-gradient(180deg,var(--p3) 0%, var(--p4) 100%);
  background-attachment:fixed; }
[data-testid="stMainBlockContainer"]{ background:var(--cream); border-radius:26px;
  padding:1.8rem 2.2rem 2.6rem 2.2rem !important; margin:1.2rem auto 2rem auto;
  max-width:1280px; box-shadow:0 22px 60px rgba(8,40,18,.45); border:2px solid var(--edge); }
[data-testid="stHeader"]{ background:transparent; }
[data-testid="stSidebar"]{ background:linear-gradient(180deg,var(--forest) 0%,var(--side2) 100%); }
[data-testid="stSidebar"] *{ color:#f1e6d0 !important; }
#MainMenu, footer{ visibility:hidden; }

.strata{ border-radius:22px; overflow:hidden; margin:.2rem 0 1.2rem 0;
  box-shadow:0 14px 34px rgba(46,32,22,.18); }
.strata-top{ background:var(--top); padding:1.7rem 2rem 1.3rem 2rem; }
.kicker{ color:var(--sprout); text-transform:uppercase; letter-spacing:.2em;
  font-size:.72rem; font-weight:700; }
.strata h1{ font-family:'Fraunces',serif; color:#fff; font-size:clamp(1.8rem,3.6vw,2.8rem);
  line-height:1.1; margin:.5rem 0 .4rem 0; }
.strata p{ color:#e5d6b8; margin:0; max-width:680px; }
.band{ height:15px; }
.b1{ background:var(--b1); } .b2{ background:var(--b2); }
.b3{ background:var(--b3); } .b4{ background:var(--b4); }
.band-label{ font-size:.68rem; letter-spacing:.14em; color:#f1e6d0; padding:0 2rem;
  line-height:15px; text-transform:uppercase; }

.h2{ font-family:'Fraunces',serif; font-size:1.4rem; font-weight:700; color:var(--sub);
  margin:.3rem 0 .1rem 0; }
.sub{ color:var(--muted); font-size:.88rem; margin-bottom:.7rem; }

.card{ background:#fff; border:1px solid #eadfc7; border-radius:18px; padding:1rem 1.2rem;
  box-shadow:0 6px 18px rgba(90,61,39,.06); }
.stat-label{ color:var(--muted); font-size:.74rem; font-weight:600; letter-spacing:.06em;
  text-transform:uppercase; }
.stat-value{ font-family:'Fraunces',serif; color:var(--sub); font-size:1.6rem; font-weight:700; }

.lvl{ margin:.55rem 0 .9rem 0; }
.lvl-head{ display:flex; justify-content:space-between; font-size:.84rem; font-weight:600; }
.lvl-badge{ font-size:.72rem; font-weight:700; padding:.1rem .55rem; border-radius:999px; }
.low{ background:#fbe7c2; color:#8a5a0b; } .med{ background:#d9efc9; color:#2d6a2a; }
.high{ background:#e8d3bd; color:#5a3d27; }
.track{ position:relative; height:12px; border-radius:999px; overflow:hidden; display:flex;
  margin-top:.35rem; }
.track > div{ height:100%; }
.marker{ position:absolute; top:-3px; width:4px; height:18px; background:var(--top);
  border-radius:2px; border:1px solid #fff; transform:translateX(-50%); }

.result{ background:linear-gradient(135deg,var(--forest),var(--forest2)); border-radius:22px; padding:1.4rem 1.6rem; color:#fff;
  box-shadow:0 14px 34px rgba(46,32,22,.2); border-bottom:10px solid var(--harvest); }
.result .kicker{ color:var(--sprout); }
.result .name{ font-family:'Fraunces',serif; font-size:clamp(2rem,4vw,3rem); font-weight:700;
  text-transform:capitalize; margin:.3rem 0 .2rem 0; }
.result .meta{ color:#e5d6b8; font-size:.9rem; }
.match{ display:inline-block; margin-top:.6rem; background:var(--leaf); color:#fff;
  font-weight:700; font-size:.82rem; padding:.3rem .8rem; border-radius:999px; }

.rank{ display:flex; align-items:center; gap:.7rem; margin:.5rem 0; }
.rank .n{ width:26px; height:26px; border-radius:50%; background:var(--sand); color:var(--sub);
  display:flex; align-items:center; justify-content:center; font-weight:700; font-size:.8rem; }
.rank .nm{ width:150px; font-weight:600; text-transform:capitalize; font-size:.9rem; }
.rank .bar{ flex:1; height:10px; background:#f0e6d0; border-radius:999px; overflow:hidden; }
.rank .bar > div{ height:100%; background:linear-gradient(90deg,var(--leaf),var(--sprout)); }
.rank .pc{ width:56px; text-align:right; font-size:.85rem; color:var(--muted); font-weight:600; }

.legend{ display:flex; gap:1rem; font-size:.78rem; color:var(--muted); margin-top:.2rem; }
.dot{ display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:.3rem; }

.stButton > button, .stFormSubmitButton > button{
  background:var(--forest2); color:#fff; border:0; border-radius:12px; font-weight:700;
  min-height:2.9rem; padding:.6rem 1.2rem; }
.stButton > button:hover{ background:var(--leaf); color:#fff; border:0; }
button[kind="secondary"]{ background:var(--sand) !important; color:var(--sub) !important; }
.stTabs [data-baseweb="tab"]{ font-weight:600; color:var(--muted); }
.stTabs [aria-selected="true"]{ color:var(--sub); }

[data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label, .stNumberInput label, .stSelectbox label{
  color:var(--forest) !important; font-weight:700 !important; font-size:.92rem !important; }
div[data-baseweb="input"] > div, div[data-baseweb="select"] > div{
  background:#ffffff !important; border:2px solid var(--fborder) !important; border-radius:10px !important; }
div[data-baseweb="input"] input, [data-testid="stNumberInput"] input{
  color:#14391f !important; -webkit-text-fill-color:#14391f !important;
  font-weight:700 !important; font-size:1.02rem !important; background:#ffffff !important; }
div[data-baseweb="select"] *{ color:#14391f !important; -webkit-text-fill-color:#14391f !important;
  font-weight:600 !important; }
[data-testid="stNumberInput"] button{ background:var(--stepper) !important; color:#14391f !important; }
[data-testid="stNumberInput"] button svg{ fill:#14391f !important; }
div[data-baseweb="input"] > div:focus-within, div[data-baseweb="select"] > div:focus-within{
  border-color:var(--harvest) !important; box-shadow:0 0 0 3px rgba(217,150,43,.25) !important; }
.stTabs [data-baseweb="tab"]{ color:#4a5a46 !important; }
.stTabs [aria-selected="true"]{ color:var(--forest) !important; }
[data-testid="stMainBlockContainer"] [data-testid="stMarkdownContainer"] p{ color:var(--ink); }
.strata p{ color:#e5d6b8 !important; }

.calwrap{ display:grid; grid-template-columns:repeat(12,1fr); gap:4px; margin:.4rem 0 .3rem 0; }
.cal{ border-radius:8px; text-align:center; padding:.35rem 0; font-size:.72rem; font-weight:700; }
.cal span{ display:block; font-size:.62rem; height:.8rem; }
.cal-on{ background:var(--leaf); color:#fff; } .cal-off{ background:#efe6d0; color:#8a7a66; }
.cal-note{ font-size:.75rem; color:var(--muted); margin-bottom:.6rem; }
.wmsg-ok{ background:#d9efc9; color:#2d6a2a; padding:.4rem .7rem; border-radius:8px; font-size:.82rem; font-weight:600; }
.wmsg-err{ background:#fbe1d6; color:#8a3b17; padding:.4rem .7rem; border-radius:8px; font-size:.82rem; font-weight:600; }
.fert{ background:#fff; border:1px solid #eadfc7; border-left:6px solid var(--harvest);
  border-radius:12px; padding:.6rem .9rem; margin:.45rem 0; font-size:.9rem; color:var(--ink); }
.fert b{ color:var(--forest); }
.fert-ok{ border-left-color:var(--leaf); }
.why{ display:flex; align-items:center; gap:.6rem; margin:.4rem 0; }
.why .wl{ width:150px; font-size:.85rem; font-weight:600; color:var(--forest); }
.why .wbar{ flex:1; height:10px; background:#f0e6d0; border-radius:999px; overflow:hidden; }
.why .wfill{ height:100%; }
.why .pos{ background:linear-gradient(90deg,var(--leaf),var(--sprout)); }
.why .neg{ background:linear-gradient(90deg,#d9962b,#e8a87c); }
.why .wv{ width:64px; text-align:right; font-size:.82rem; color:var(--muted); font-weight:700; }
[data-testid="stImage"] img{ border-radius:18px; box-shadow:0 10px 26px rgba(20,57,31,.28);
  border:3px solid var(--edge); object-fit:cover; }
</style>
""",
    unsafe_allow_html=True,
)



# ============================================================
# DESIGN THEMES (only colours change, the layout stays the same)
# ============================================================
THEMES = {
    "Soil Strata": {
        "--top": "#2e2016", "--sub": "#5a3d27", "--clay": "#9a6b43", "--sand": "#e9dbbd",
        "--cream": "#fbf6ea", "--leaf": "#3f7d3a", "--sprout": "#8bc34a", "--harvest": "#d9962b",
        "--ink": "#2b2118", "--muted": "#6b5c4b", "--forest": "#14391f", "--forest2": "#1f5a2c",
        "--p1": "#4fa356", "--p2": "#3b8d46", "--p3": "#2c7a3a", "--p4": "#1b5429",
        "--edge": "#b9d99a", "--fborder": "#7fae5a", "--stepper": "#e3f0d3", "--side2": "#0c2814",
        "--b1": "#5a3d27", "--b2": "#7a5435", "--b3": "#9a6b43", "--b4": "#c29a6b",
    },
    "Paddy Field": {
        "--top": "#0d4f3c", "--sub": "#1f5a3a", "--clay": "#5aa469", "--sand": "#dff1d2",
        "--cream": "#f7fbf2", "--leaf": "#267a42", "--sprout": "#9ad35a", "--harvest": "#e8a317",
        "--ink": "#1f2d24", "--muted": "#4f6355", "--forest": "#0f4c3a", "--forest2": "#1b7a52",
        "--p1": "#b6e3f7", "--p2": "#a5dc86", "--p3": "#7ec8e3", "--p4": "#3f9a4a",
        "--edge": "#b8e0a0", "--fborder": "#5fb36f", "--stepper": "#e0f3e3", "--side2": "#082e22",
        "--b1": "#1f7a4d", "--b2": "#3fa55f", "--b3": "#7cc96a", "--b4": "#b9e08a",
    },
    "Sunrise Harvest": {
        "--top": "#4a2f0e", "--sub": "#6b4210", "--clay": "#b07a22", "--sand": "#f6e3b8",
        "--cream": "#fffaf0", "--leaf": "#4f7a22", "--sprout": "#a8c94a", "--harvest": "#e8892b",
        "--ink": "#33250f", "--muted": "#6e5a3b", "--forest": "#5a3a0e", "--forest2": "#9a5b12",
        "--p1": "#ffe3a0", "--p2": "#f6b85a", "--p3": "#f5a742", "--p4": "#b8651a",
        "--edge": "#f0cf8a", "--fborder": "#d9a13b", "--stepper": "#fbe9c3", "--side2": "#3b2408",
        "--b1": "#8a5a1a", "--b2": "#b07a22", "--b3": "#d49b34", "--b4": "#ecc16a",
    },
    "Monsoon Blue": {
        "--top": "#0b3a5a", "--sub": "#14506f", "--clay": "#5aa7cf", "--sand": "#d9eaf4",
        "--cream": "#f5fafd", "--leaf": "#1a7a6e", "--sprout": "#7fd1c1", "--harvest": "#f4a259",
        "--ink": "#172a38", "--muted": "#4b6475", "--forest": "#0b3a5a", "--forest2": "#17678f",
        "--p1": "#8cc3e6", "--p2": "#5fa8d3", "--p3": "#2f7fb0", "--p4": "#164f78",
        "--edge": "#a9d3ea", "--fborder": "#4f9cc4", "--stepper": "#dcebf5", "--side2": "#082a41",
        "--b1": "#145a85", "--b2": "#2a7fae", "--b3": "#5aa7cf", "--b4": "#9cc9e3",
    },
}
DEFAULT_THEME = "Soil Strata"


def theme_css(name: str) -> str:
    values = THEMES.get(name, THEMES[DEFAULT_THEME])
    return "<style>:root{" + "".join(f"{k}:{v};" for k, v in values.items()) + "}</style>"


# The theme widget lives in the sidebar, but its value is already in session_state when the script starts.
st.markdown(theme_css(st.session_state.get("theme", DEFAULT_THEME)), unsafe_allow_html=True)


def html(markup: str):
    """Render HTML safely: strip indentation so markdown never treats it as a code block."""
    cleaned = "\n".join(line.strip() for line in markup.splitlines() if line.strip())
    st.markdown(cleaned, unsafe_allow_html=True)


# ============================================================
# PATHS AND CONSTANTS
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "saved_models"
IMAGE_DIR = BASE_DIR / "crop_images"
DATASET_CANDIDATES = [
    BASE_DIR / "Crop_recommendation_dataset.xls",
    BASE_DIR / "Crop_recommendation_dataset.csv",
    BASE_DIR / "Crop recommendation dataset.csv",
    BASE_DIR / "Crop recommendation dataset.xls",
]

NUM_COLS = ["N", "P", "K", "SOIL_PH", "TEMP", "RELATIVE_HUMIDITY", "WATERREQUIRED"]
INPUT_COLS = NUM_COLS + ["SOIL", "SEASON"]
SHORT = {
    "N": "Nitrogen", "P": "Phosphorus", "K": "Potassium", "SOIL_PH": "Soil pH",
    "TEMP": "Temp", "RELATIVE_HUMIDITY": "Humidity", "WATERREQUIRED": "Water",
}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# ============================================================
# LANGUAGE (English / Tamil)
# ============================================================
TEXT = {
    "en": {
        "tagline": "Crop recommendation based on soil nutrition",
        "kicker": "Soil nutrition intelligence",
        "hero": "Tell us what is in your soil. We find the crop that grows best in it.",
        "tab_rec": "🌾 Recommend a crop", "tab_explore": "📚 Crop explorer",
        "tab_compare": "⚖️ Compare crops", "tab_batch": "📁 Batch prediction",
        "tab_model": "📊 Model insights",
        "sample": "🎲 Load a sample field", "reset": "↺ Reset",
        "h_soil": "Soil nutrients", "s_soil": "Macro-nutrients and acidity",
        "h_field": "Field conditions", "s_field": "Weather, water and soil type",
        "h_health": "Soil health snapshot", "s_health": "Compared with the training data",
        "n": "Nitrogen (N)", "p": "Phosphorus (P)", "k": "Potassium (K)", "ph": "Soil pH",
        "temp": "Temperature (°C)", "hum": "Relative humidity (%)",
        "water": "Water required (dataset units)", "soil": "Soil type", "season": "Season",
        "city": "Type a city and press Enter (live weather)", "fetch": "📡 Refresh live weather",
        "city_pick": "Select the matching place", "weather_nf": "City not found. Try another spelling.",
        "types": "Only show these crop types (optional)",
        "go": "🌱 Recommend the best crop",
        "low": "Low", "medium": "Medium", "high": "High",
        "acidic": "Acidic", "neutral": "Neutral", "alkaline": "Alkaline",
        "best": "Best crop for your soil", "predicted_by": "Predicted by",
        "match": "Soil match", "top": "Top matches",
        "radar_h": "Your soil vs the ideal profile", "typical_for": "Typical for",
        "your_field": "Your field", "adjust_h": "What to adjust",
        "adjust_s": "Your value against the average field for this crop",
        "on_target": "On target", "higher": "Higher than ideal", "lower": "Lower than ideal",
        "factor": "Factor", "typical": "Typical", "status": "Status",
        "cal_h": "Crop calendar", "sow": "Sowing", "harvest": "Harvest",
        "duration": "Duration", "days": "days", "ctype": "Crop type",
        "wsource": "Water source", "bseason": "Best season", "csoil": "Common soil",
        "cal_note": "S = sowing month, H = harvest month",
        "whatif_h": "What-if: change one nutrient",
        "whatif_pick": "Nutrient to vary", "value": "Value", "crop": "Crop", "conf": "Confidence (%)",
        "download": "⬇️ Download report (HTML, print to PDF)",
        "history_h": "My previous checks", "history_dl": "⬇️ Download history (CSV)",
        "history_clear": "Clear history",
        "disclaimer": "This is a machine-learning prediction from the training dataset, not a guarantee of yield or profit. Confirm with local agricultural guidance before planting.",
        "outside": "Some values are outside the range the model was trained on, so treat this result with care: ",
        "no_type_match": "No crops matched the selected types, so all crops are shown.",
        "weather_ok": "Live weather loaded", "weather_err": "Could not fetch weather. Check the city name and your internet.",
        "explore_h": "Explore any crop", "explore_s": "What soil and weather the dataset says each crop likes",
        "choose_crop": "Choose a crop", "profile_h": "Typical profile",
        "all_avg": "Average of all crops",
        "cmp_h": "Compare two crops", "cmp_s": "See how their soil and weather needs differ",
        "crop_a": "First crop", "crop_b": "Second crop",
        "batch_h": "Predict for many fields at once",
        "batch_s": "Upload a CSV or Excel file with one row per field",
        "template": "⬇️ Download template (CSV)", "upload": "Upload file",
        "batch_done": "Predictions ready", "batch_dl": "⬇️ Download results (CSV)",
        "batch_missing": "Missing columns: ",
        "model_h": "Model comparison", "model_s": "All trained algorithms, best first",
        "model_note": "The dataset is clean and well separated, so accuracy is very high. Real field soil can be noisier, so use the result as guidance.",
        "how": "How it works",
        "how_body": "1. Enter your soil nutrients and field conditions.\n2. The model matches them to the crops.\n3. See the best crop and how well your soil fits it.",
        "crops_cov": "Crops covered", "model": "Model", "acc": "Test accuracy",
        "no_image": "No image yet", "save_photo": "Save the photo as",
        "photo_credit": "Photo credit",
        "s_zaid": "Summer (Zaid)", "s_kharif": "Monsoon (Kharif)", "s_rabi": "Winter (Rabi)",
        "tab_sow": "🗓️ Sow this month",
        "sow_h": "What can I sow this month?",
        "sow_s": "Crops that are usually sown in the chosen month, ranked by how well your soil and weather suit them",
        "sow_month": "Sowing month",
        "sow_note": "Uses the soil and weather values you entered in the first tab.",
        "sow_none": "No crop in the dataset is usually sown in this month.",
        "sow_fit": "Soil match (%)",
        "fert_h": "Fertilizer guidance",
        "fert_s": "General guidance from the gap between your soil and this crop's typical soil",
        "fert_ok": "Your N, P, K and pH are close to what this crop needs. No big correction is suggested.",
        "fert_n_low": "Nitrogen is lower than this crop usually needs. Urea, ammonium sulphate, or organic sources such as farmyard manure, compost and green manure can help.",
        "fert_n_high": "Nitrogen is higher than usual for this crop. Skip extra nitrogen fertilizer this season.",
        "fert_p_low": "Phosphorus is lower than this crop usually needs. Single super phosphate (SSP) or DAP can help.",
        "fert_p_high": "Phosphorus is higher than usual. Extra phosphorus fertilizer is not needed.",
        "fert_k_low": "Potassium is lower than this crop usually needs. Muriate of potash (MOP) or wood ash can help.",
        "fert_k_high": "Potassium is higher than usual. Extra potash is not needed.",
        "fert_ph_low": "Soil pH is lower (more acidic) than ideal. Agricultural lime or dolomite is commonly used to raise it.",
        "fert_ph_high": "Soil pH is higher (more alkaline) than ideal. Compost or elemental sulphur can help lower it.",
        "fert_note": "This is general guidance with no quantities. Get a soil test and follow the dose advised by your local agriculture officer.",
        "download_pdf": "⬇️ Download report (PDF)",
        "pdf_missing": "PDF download needs the reportlab package. Run: pip install reportlab",
        "why_h": "Why this crop?",
        "why_s": "How much each input pushes the model towards this crop (percentage points)",
        "why_legend": "Green = pushes towards this crop, orange = pushes away from it",
        "rot_h": "Crop rotation tip",
        "rot_text": "After {crop}, consider following with {nxt}. Growing a different crop type next helps break pest and disease cycles.",
        "rot_legume": " Pulses also add nitrogen to the soil.",
        "rot_n_pulses": "pulses", "rot_n_cereals": "cereals or millets", "rot_n_mix": "pulses or cereals",
        "rot_note": "General farming tip, not taken from the dataset.",
        "fields_h": "My saved fields",
        "field_name": "Field name (for example: North plot)",
        "field_save": "💾 Save current values", "field_pick": "Saved fields",
        "field_load": "Load", "field_delete": "Delete",
        "field_saved": "Saved", "field_need_name": "Type a name first.",
        "field_loaded": "Loaded", "field_deleted": "Deleted", "field_fail": "Could not save the file.",
        "share_wa": "📲 Share on WhatsApp",
        "theme_label": "🎨 Design theme",
        "low_conf": "The model is not very sure (top match below 50%). Look at the top matches before deciding.",
    },
    "ta": {
        "tagline": "மண் ஊட்டச்சத்து அடிப்படையில் பயிர் பரிந்துரை",
        "kicker": "மண் ஊட்டச்சத்து நுண்ணறிவு",
        "hero": "உங்கள் மண்ணில் என்ன உள்ளது என்று சொல்லுங்கள். அதில் சிறப்பாக வளரும் பயிரை நாங்கள் கண்டறிவோம்.",
        "tab_rec": "🌾 பயிர் பரிந்துரை", "tab_explore": "📚 பயிர் தகவல்",
        "tab_compare": "⚖️ பயிர் ஒப்பீடு", "tab_batch": "📁 தொகுப்பு கணிப்பு",
        "tab_model": "📊 மாதிரி விவரம்",
        "sample": "🎲 மாதிரி வயல்", "reset": "↺ மீட்டமை",
        "h_soil": "மண் ஊட்டச்சத்துகள்", "s_soil": "முக்கிய ஊட்டச்சத்துகள் மற்றும் அமிலத்தன்மை",
        "h_field": "வயல் நிலைமைகள்", "s_field": "வானிலை, தண்ணீர் மற்றும் மண் வகை",
        "h_health": "மண் ஆரோக்கிய நிலை", "s_health": "பயிற்சி தரவுடன் ஒப்பீடு",
        "n": "நைட்ரஜன் (N)", "p": "பாஸ்பரஸ் (P)", "k": "பொட்டாசியம் (K)", "ph": "மண் pH",
        "temp": "வெப்பநிலை (°C)", "hum": "ஈரப்பதம் (%)",
        "water": "தண்ணீர் தேவை", "soil": "மண் வகை", "season": "பருவம்",
        "city": "ஊர் பெயரை தட்டச்சு செய்து Enter அழுத்தவும் (நேரடி வானிலை)", "fetch": "📡 வானிலையை புதுப்பி",
        "city_pick": "பொருத்தமான இடத்தை தேர்வு செய்க", "weather_nf": "ஊர் கிடைக்கவில்லை. வேறு எழுத்துப்பிழையுடன் முயற்சிக்கவும்.",
        "types": "இந்த பயிர் வகைகள் மட்டும் (விருப்பம்)",
        "go": "🌱 சிறந்த பயிரைப் பரிந்துரை செய்",
        "low": "குறைவு", "medium": "நடுத்தரம்", "high": "அதிகம்",
        "acidic": "அமிலத்தன்மை", "neutral": "நடுநிலை", "alkaline": "காரத்தன்மை",
        "best": "உங்கள் மண்ணுக்கு ஏற்ற சிறந்த பயிர்", "predicted_by": "கணித்தது",
        "match": "மண் பொருத்தம்", "top": "சிறந்த பொருத்தங்கள்",
        "radar_h": "உங்கள் மண் vs சிறந்த நிலை", "typical_for": "வழக்கமான நிலை",
        "your_field": "உங்கள் வயல்", "adjust_h": "என்ன சரிசெய்ய வேண்டும்",
        "adjust_s": "இந்த பயிரின் சராசரி வயலுடன் உங்கள் மதிப்பு",
        "on_target": "சரியாக உள்ளது", "higher": "தேவையை விட அதிகம்", "lower": "தேவையை விட குறைவு",
        "factor": "காரணி", "typical": "வழக்கமான", "status": "நிலை",
        "cal_h": "பயிர் நாட்காட்டி", "sow": "விதைப்பு", "harvest": "அறுவடை",
        "duration": "காலம்", "days": "நாட்கள்", "ctype": "பயிர் வகை",
        "wsource": "நீர் ஆதாரம்", "bseason": "சிறந்த பருவம்", "csoil": "பொதுவான மண்",
        "cal_note": "S = விதைப்பு மாதம், H = அறுவடை மாதம்",
        "whatif_h": "ஒரு ஊட்டச்சத்தை மாற்றினால் என்ன ஆகும்?",
        "whatif_pick": "மாற்ற வேண்டிய ஊட்டச்சத்து", "value": "மதிப்பு", "crop": "பயிர்", "conf": "நம்பிக்கை (%)",
        "download": "⬇️ அறிக்கையை பதிவிறக்கு (HTML)",
        "history_h": "முந்தைய சோதனைகள்", "history_dl": "⬇️ வரலாறு பதிவிறக்கு (CSV)",
        "history_clear": "வரலாற்றை அழி",
        "disclaimer": "இது பயிற்சி தரவை அடிப்படையாகக் கொண்ட இயந்திரக் கற்றல் கணிப்பு. மகசூல் அல்லது லாபத்திற்கு உத்தரவாதம் அல்ல. விதைப்பதற்கு முன் உள்ளூர் வேளாண் அலுவலரிடம் உறுதிப்படுத்துங்கள்.",
        "outside": "சில மதிப்புகள் மாதிரி கற்ற வரம்புக்கு வெளியே உள்ளன, எனவே கவனமாக பயன்படுத்துங்கள்: ",
        "no_type_match": "தேர்ந்தெடுத்த வகையில் பயிர் இல்லை, எனவே அனைத்து பயிர்களும் காட்டப்படுகின்றன.",
        "weather_ok": "நேரடி வானிலை ஏற்றப்பட்டது", "weather_err": "வானிலையை பெற முடியவில்லை. ஊர் பெயர் மற்றும் இணைய இணைப்பை சரிபார்க்கவும்.",
        "explore_h": "எந்த பயிரையும் அறிந்து கொள்ளுங்கள்", "explore_s": "ஒவ்வொரு பயிரும் விரும்பும் மண் மற்றும் வானிலை",
        "choose_crop": "பயிரை தேர்வு செய்க", "profile_h": "வழக்கமான நிலை",
        "all_avg": "அனைத்து பயிர்களின் சராசரி",
        "cmp_h": "இரண்டு பயிர்களை ஒப்பிடுக", "cmp_s": "அவற்றின் மண் மற்றும் வானிலை தேவைகளின் வேறுபாடு",
        "crop_a": "முதல் பயிர்", "crop_b": "இரண்டாம் பயிர்",
        "batch_h": "பல வயல்களுக்கு ஒரே நேரத்தில் கணிக்க",
        "batch_s": "ஒரு வயலுக்கு ஒரு வரியுடன் CSV அல்லது Excel கோப்பை பதிவேற்றவும்",
        "template": "⬇️ மாதிரி கோப்பு (CSV)", "upload": "கோப்பை பதிவேற்றுக",
        "batch_done": "கணிப்புகள் தயார்", "batch_dl": "⬇️ முடிவுகளை பதிவிறக்கு (CSV)",
        "batch_missing": "இல்லாத நெடுவரிசைகள்: ",
        "model_h": "மாதிரி ஒப்பீடு", "model_s": "பயிற்சி செய்த அனைத்து அல்காரிதம்கள்",
        "model_note": "தரவு சுத்தமாக இருப்பதால் துல்லியம் மிக அதிகம். உண்மையான வயல் மண் மாறுபடலாம், எனவே வழிகாட்டியாக மட்டும் பயன்படுத்துங்கள்.",
        "how": "எப்படி செயல்படுகிறது",
        "how_body": "1. உங்கள் மண் ஊட்டச்சத்து மற்றும் வயல் நிலைமையை உள்ளிடுங்கள்.\n2. மாதிரி அவற்றை பயிர்களுடன் பொருத்தும்.\n3. சிறந்த பயிரையும் பொருத்தத்தையும் பாருங்கள்.",
        "crops_cov": "பயிர்கள்", "model": "மாதிரி", "acc": "துல்லியம்",
        "no_image": "படம் இல்லை", "save_photo": "படத்தை இப்படி சேமிக்கவும்",
        "photo_credit": "புகைப்பட உரிமை",
        "s_zaid": "கோடை (Zaid)", "s_kharif": "பருவமழை (Kharif)", "s_rabi": "குளிர்காலம் (Rabi)",
        "tab_sow": "🗓️ இந்த மாதம் விதைக்க",
        "sow_h": "இந்த மாதம் எதை விதைக்கலாம்?",
        "sow_s": "தேர்ந்தெடுத்த மாதத்தில் வழக்கமாக விதைக்கப்படும் பயிர்கள், உங்கள் மண் மற்றும் வானிலைக்கு ஏற்ற வரிசையில்",
        "sow_month": "விதைப்பு மாதம்",
        "sow_note": "முதல் தாவலில் நீங்கள் உள்ளிட்ட மண் மற்றும் வானிலை மதிப்புகளைப் பயன்படுத்துகிறது.",
        "sow_none": "இந்த மாதத்தில் வழக்கமாக விதைக்கப்படும் பயிர் தரவில் இல்லை.",
        "sow_fit": "மண் பொருத்தம் (%)",
        "fert_h": "உர வழிகாட்டுதல்",
        "fert_s": "உங்கள் மண்ணுக்கும் இந்த பயிரின் வழக்கமான மண்ணுக்கும் உள்ள வேறுபாட்டின் அடிப்படையில் பொது வழிகாட்டுதல்",
        "fert_ok": "உங்கள் N, P, K மற்றும் pH இந்த பயிருக்கு ஏற்ற அளவில் உள்ளன. பெரிய திருத்தம் தேவையில்லை.",
        "fert_n_low": "நைட்ரஜன் இந்த பயிருக்குத் தேவையானதை விடக் குறைவு. யூரியா, அம்மோனியம் சல்பேட் அல்லது தொழுவுரம், கம்போஸ்ட், பசுந்தாள் உரம் உதவும்.",
        "fert_n_high": "நைட்ரஜன் வழக்கத்தை விட அதிகம். இந்த பருவத்தில் கூடுதல் நைட்ரஜன் உரம் தவிர்க்கவும்.",
        "fert_p_low": "பாஸ்பரஸ் குறைவு. சூப்பர் பாஸ்பேட் (SSP) அல்லது DAP உதவும்.",
        "fert_p_high": "பாஸ்பரஸ் அதிகம். கூடுதல் பாஸ்பரஸ் உரம் தேவையில்லை.",
        "fert_k_low": "பொட்டாசியம் குறைவு. மியூரேட் ஆஃப் பொட்டாஷ் (MOP) அல்லது சாம்பல் உதவும்.",
        "fert_k_high": "பொட்டாசியம் அதிகம். கூடுதல் பொட்டாஷ் தேவையில்லை.",
        "fert_ph_low": "மண் pH குறைவு (அமிலத்தன்மை). சுண்ணாம்பு அல்லது டோலோமைட் pH ஐ உயர்த்த உதவும்.",
        "fert_ph_high": "மண் pH அதிகம் (காரத்தன்மை). கம்போஸ்ட் அல்லது கந்தகம் pH ஐ குறைக்க உதவும்.",
        "fert_note": "இவை பொதுவான வழிகாட்டுதல்கள், அளவு குறிப்பிடப்படவில்லை. மண் பரிசோதனை செய்து, வேளாண் அலுவலர் கூறும் அளவைப் பின்பற்றவும்.",
        "download_pdf": "⬇️ அறிக்கையை பதிவிறக்கு (PDF)",
        "pdf_missing": "PDF பதிவிறக்க reportlab தேவை. இயக்கவும்: pip install reportlab",
        "why_h": "ஏன் இந்த பயிர்?",
        "why_s": "ஒவ்வொரு உள்ளீடும் மாதிரியை இந்த பயிரை நோக்கி எவ்வளவு தள்ளுகிறது (சதவீத புள்ளிகள்)",
        "why_legend": "பச்சை = இந்த பயிரை நோக்கி, ஆரஞ்சு = இந்த பயிரிலிருந்து விலகி",
        "rot_h": "பயிர் சுழற்சி குறிப்பு",
        "rot_text": "{crop} பயிருக்குப் பிறகு {nxt} பயிரிடலாம். வேறு வகை பயிரைச் சுழற்சி செய்வது பூச்சி, நோய் சுழற்சியை உடைக்க உதவும்.",
        "rot_legume": " பயறு வகைகள் மண்ணில் நைட்ரஜனையும் சேர்க்கும்.",
        "rot_n_pulses": "பயறு வகைகள்", "rot_n_cereals": "தானியங்கள் அல்லது சிறுதானியங்கள்",
        "rot_n_mix": "பயறு வகைகள் அல்லது தானியங்கள்",
        "rot_note": "இது பொதுவான விவசாய குறிப்பு, தரவிலிருந்து எடுக்கப்பட்டது அல்ல.",
        "fields_h": "சேமித்த வயல்கள்",
        "field_name": "வயல் பெயர் (எ.கா. வடக்கு வயல்)",
        "field_save": "💾 தற்போதைய மதிப்புகளை சேமி", "field_pick": "சேமித்த வயல்கள்",
        "field_load": "ஏற்று", "field_delete": "அழி",
        "field_saved": "சேமிக்கப்பட்டது", "field_need_name": "முதலில் ஒரு பெயரை தட்டச்சு செய்யவும்.",
        "field_loaded": "ஏற்றப்பட்டது", "field_deleted": "அழிக்கப்பட்டது", "field_fail": "கோப்பை சேமிக்க முடியவில்லை.",
        "share_wa": "📲 வாட்ஸ்அப்பில் பகிர்",
        "theme_label": "🎨 வடிவமைப்பு தீம்",
        "low_conf": "மாதிரிக்கு உறுதி குறைவு (முதல் பொருத்தம் 50%க்கும் கீழ்). முடிவெடுக்கும் முன் சிறந்த பொருத்தங்களைப் பாருங்கள்.",
    },
}
LANG_CODE = "en"


def t(key: str) -> str:
    return TEXT.get(LANG_CODE, {}).get(key) or TEXT["en"].get(key, key)


# Icons shown on screen next to headings and field labels (the PDF/HTML reports stay plain text)
ICONS = {
    "h_soil": "🧪", "h_field": "🌤️", "h_health": "🩺",
    "n": "🍃", "p": "🌸", "k": "🍎", "ph": "⚗️",
    "city": "📍", "temp": "🌡️", "hum": "💧", "water": "🚰", "soil": "🟤", "season": "📅",
}


def lbl(key: str) -> str:
    return f"{ICONS.get(key, '')} {t(key)}".strip()


# Season values stay exactly as in the dataset (Zaid / kharif / rabi) because the model was
# trained on them. Only the NAME SHOWN to the user is changed here.
SEASON_KEYS = {"zaid": "s_zaid", "kharif": "s_kharif", "rabi": "s_rabi"}
# Names a user may type in a batch file -> the real dataset value
SEASON_ALIASES = {
    "summer": "Zaid", "zaid": "Zaid",
    "monsoon": "kharif", "rainy": "kharif", "kharif": "kharif",
    "winter": "rabi", "rabi": "rabi",
}


def season_label(value) -> str:
    key = SEASON_KEYS.get(str(value).strip().lower())
    return t(key) if key else str(value)


CROP_TA = {
    "annual moringa": "முருங்கை", "ash gourd": "வெண்பூசணி", "beetroot": "பீட்ரூட்",
    "bengalgram": "கொண்டைக்கடலை", "bhendi": "வெண்டைக்காய்", "bitter gourd": "பாகற்காய்",
    "blackgram": "உளுந்து", "bottle gourd": "சுரைக்காய்", "brinjal": "கத்தரிக்காய்",
    "cabbage": "முட்டைகோஸ்", "capsicum": "குடைமிளகாய்", "carrot": "கேரட்",
    "castor": "ஆமணக்கு", "cauliflower": "காலிஃபிளவர்", "chillies": "மிளகாய்",
    "chowchow": "சௌ சௌ", "cluster bean": "கொத்தவரை", "cotton": "பருத்தி",
    "cowpea": "காராமணி", "cucumber": "வெள்ளரிக்காய்", "elephant foot yam": "சேனைக்கிழங்கு",
    "french bean": "பீன்ஸ்", "gingely": "எள்", "greengram": "பாசிப்பயறு",
    "groundnut": "நிலக்கடலை", "horsegram": "கொள்ளு", "jute": "சணல்",
    "kudiraivali": "குதிரைவாலி", "maize": "மக்காச்சோளம்", "muskmelon": "முலாம்பழம்",
    "onion": "பெரிய வெங்காயம்", "panivaragu": "பனிவரகு", "pearl millet": "கம்பு",
    "peas": "பட்டாணி", "pumpkin": "பூசணிக்காய்", "radish": "முள்ளங்கி",
    "ragi": "கேழ்வரகு", "redgram": "துவரை", "ribbed gourd": "பீர்க்கங்காய்",
    "rice": "நெல்", "samai": "சாமை", "small onion": "சின்ன வெங்காயம்",
    "snake gourd": "புடலங்காய்", "sorghum": "சோளம்", "soyabean": "சோயா பீன்ஸ்",
    "sugarbeet": "சர்க்கரை பீட்", "sugarcane": "கரும்பு", "sunflower": "சூரியகாந்தி",
    "sweet potato": "சர்க்கரைவள்ளிக்கிழங்கு", "tapoica": "மரவள்ளிக்கிழங்கு",
    "thinai": "தினை", "tinda": "டிண்டா", "tomato": "தக்காளி", "varagu": "வரகு",
    "vegetable cowpea": "காய்கறி காராமணி", "watermelon": "தர்பூசணி", "wheat": "கோதுமை",
}


def crop_label(crop) -> str:
    """English name, or 'Tamil name (English)' when Tamil mode is on."""
    name = str(crop).strip().lower()
    if LANG_CODE == "ta" and name in CROP_TA:
        return f"{CROP_TA[name]} ({name.title()})"
    return name.title()


def season_label_en(value) -> str:
    return TEXT["en"].get(SEASON_KEYS.get(str(value).strip().lower(), ""), str(value))


def slugify(name) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(name).strip().lower()).strip("_")


# ============================================================
# LOADERS
# ============================================================
@st.cache_resource
def load_model():
    comparison_path = MODEL_DIR / "model_comparison.csv"
    encoder_path = MODEL_DIR / "label_encoder.pkl"
    if not comparison_path.exists():
        raise FileNotFoundError(f"Missing file: {comparison_path}")
    if not encoder_path.exists():
        raise FileNotFoundError(f"Missing file: {encoder_path}")

    results = pd.read_csv(comparison_path).dropna(subset=["Algorithm", "Accuracy (%)"])
    results = results.sort_values("Accuracy (%)", ascending=False).reset_index(drop=True)
    if results.empty:
        raise ValueError("model_comparison.csv has no valid rows.")

    best = str(results.loc[0, "Algorithm"]).strip()
    model_path = MODEL_DIR / (best.lower().replace(" ", "_") + ".pkl")
    if not model_path.exists():
        raise FileNotFoundError(f"Best model file not found: {model_path}")

    return (
        joblib.load(model_path),
        joblib.load(encoder_path),
        best,
        float(results.loc[0, "Accuracy (%)"]),
        results,
    )


@st.cache_data
def load_dataset():
    for path in DATASET_CANDIDATES:
        if path.exists():
            data = pd.read_csv(path)
            data["SOIL"] = data["SOIL"].astype(str).str.strip().str.lower()
            data["CROPS"] = data["CROPS"].astype(str).str.strip().str.lower()
            for col in ("TYPE_OF_CROP", "SOWN", "HARVESTED", "WATER_SOURCE"):
                if col in data.columns:
                    data[col] = data[col].astype(str).str.strip()
            return data
    return None


@st.cache_data
def load_image_credits():
    path = IMAGE_DIR / "image_sources.csv"
    if not path.exists():
        return {}
    df_ = pd.read_csv(path).fillna("")
    out = {}
    for r in df_.itertuples():
        artist = re.sub(r"<[^>]+>", "", str(r.artist)).strip()
        lic = str(r.license)
        parts = [artist, lic, "Pexels" if "pexels" in lic.lower() else "Wikimedia Commons"]
        out[slugify(r.crop_name)] = " · ".join(x for x in parts if x)
    return out


def crop_image_path(crop):
    slug = slugify(crop)
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        p = IMAGE_DIR / f"{slug}{ext}"
        if p.exists():
            return p
    return None


# ============================================================
# VISUAL HELPERS
# ============================================================
def level_bar(label, value, lo, hi, cuts, unit_names, colors):
    span = hi - lo
    pos = min(max((value - lo) / span, 0), 1) * 100
    c1 = min(max((cuts[0] - lo) / span, 0), 1) * 100
    c2 = min(max((cuts[1] - lo) / span, 0), 1) * 100
    idx = 0 if value < cuts[0] else (1 if value <= cuts[1] else 2)
    badge = ["low", "med", "high"][idx]
    html(
        f"""
        <div class="lvl">
          <div class="lvl-head"><span>{label}: {value:g}</span>
            <span class="lvl-badge {badge}">{unit_names[idx]}</span></div>
          <div class="track">
            <div style="width:{c1}%;background:{colors[0]}"></div>
            <div style="width:{c2 - c1}%;background:{colors[1]}"></div>
            <div style="width:{100 - c2}%;background:{colors[2]}"></div>
            <div class="marker" style="left:{pos}%"></div>
          </div>
        </div>
        """
    )


def radar_svg(series, norm, size=330):
    cx = cy = size / 2
    radius = size / 2 - 52
    n = len(NUM_COLS)

    def point(i, frac):
        ang = -math.pi / 2 + 2 * math.pi * i / n
        return cx + radius * frac * math.cos(ang), cy + radius * frac * math.sin(ang)

    parts = [f'<svg viewBox="0 0 {size} {size}" width="100%" style="max-width:{size}px">']
    for ring in (0.25, 0.5, 0.75, 1.0):
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in (point(i, ring) for i in range(n)))
        parts.append(f'<polygon points="{pts}" fill="none" stroke="#e2d3b3" stroke-width="1"/>')
    for i, col in enumerate(NUM_COLS):
        x, y = point(i, 1)
        parts.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="#eadfc7"/>')
        lx, ly = point(i, 1.2)
        anchor = "middle" if abs(lx - cx) < 8 else ("start" if lx > cx else "end")
        parts.append(
            f'<text x="{lx:.1f}" y="{ly + 4:.1f}" font-size="11" fill="#7a6a58" '
            f'text-anchor="{anchor}">{SHORT[col]}</text>'
        )
    for _name, values, colour in series:
        fr = []
        for col in NUM_COLS:
            lo, hi = norm[col]
            fr.append(min(max((values[col] - lo) / (hi - lo), 0), 1))
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in (point(i, f) for i, f in enumerate(fr)))
        parts.append(
            f'<polygon points="{pts}" fill="{colour}" fill-opacity="0.22" '
            f'stroke="{colour}" stroke-width="2.2"/>'
        )
    parts.append("</svg>")
    return "".join(parts)


def similarity_score(values, profile, norm):
    diffs = [abs(values[c] - profile[c]) / (norm[c][1] - norm[c][0]) for c in NUM_COLS]
    return max(0.0, 100 * (1 - float(np.mean(diffs)) * 2))


def rank_html(pairs):
    rows = ""
    for i, (name, pct) in enumerate(pairs, 1):
        rows += (
            f'<div class="rank"><div class="n">{i}</div><div class="nm">{crop_label(name)}</div>'
            f'<div class="bar"><div style="width:{min(pct, 100):.1f}%"></div></div>'
            f'<div class="pc">{pct:.1f}%</div></div>'
        )
    return rows


def calendar_html(sown, harvest):
    s_name, h_name = str(sown).strip()[:3].title(), str(harvest).strip()[:3].title()
    if s_name not in MONTHS or h_name not in MONTHS:
        return ""
    s_i, h_i = MONTHS.index(s_name), MONTHS.index(h_name)
    active, i = set(), s_i
    for _ in range(12):
        active.add(i)
        if i == h_i:
            break
        i = (i + 1) % 12
    cells = ""
    for m, name in enumerate(MONTHS):
        mark = "S" if m == s_i else ("H" if m == h_i else "&nbsp;")
        cells += f'<div class="cal {"cal-on" if m in active else "cal-off"}">{name}<span>{mark}</span></div>'
    return f'<div class="calwrap">{cells}</div><div class="cal-note">{t("cal_note")}</div>'


# ============================================================
# MODEL HELPERS
# ============================================================
def class_names():
    ids = getattr(model, "classes_", None)
    if ids is None:
        ids = np.arange(len(encoder.classes_))
    return encoder.inverse_transform(np.asarray(ids).astype(int))


def predict_batch(X):
    """Return (list of crop names, list of confidence %) for a DataFrame."""
    try:
        proba = np.asarray(model.predict_proba(X))
        names = class_names()
        idx = proba.argmax(axis=1)
        return [str(names[i]) for i in idx], [float(proba[r, i]) * 100 for r, i in enumerate(idx)]
    except Exception:
        pred = np.asarray(model.predict(X)).reshape(-1).astype(int)
        return [str(c) for c in encoder.inverse_transform(pred)], [100.0] * len(pred)


def rank_crops(frame, allowed=None, top_n=5):
    try:
        proba = np.asarray(model.predict_proba(frame)[0]) * 100
        pairs = sorted(zip(class_names(), proba), key=lambda x: -x[1])
        pairs = [(str(a), float(b)) for a, b in pairs]
    except Exception:
        names, conf = predict_batch(frame)
        pairs = [(names[0], conf[0])]
    if allowed:
        filtered = [p for p in pairs if p[0] in allowed]
        if filtered:
            total = sum(p for _, p in filtered)
            if total >= 0.5:
                pairs = [(n, p / total * 100) for n, p in filtered]   # renormalise inside the filter
            else:
                # model gives these types almost no probability: rank them by soil-profile closeness
                vals = frame.iloc[0]
                sims = {n: similarity_score(vals, PROFILES.loc[n], NORM)
                        for n, _ in filtered if n in PROFILES.index}
                tot = sum(sims.values()) or 1.0
                pairs = sorted(((n, v / tot * 100) for n, v in sims.items()), key=lambda x: -x[1])
        else:
            st.info(t("no_type_match"))
    return pairs[:top_n]


def crop_facts(crop):
    sub = df[df["CROPS"] == crop]

    def mode(col):
        return str(sub[col].mode().iat[0]) if col in sub and not sub.empty else "-"

    return {
        "type": mode("TYPE_OF_CROP").title(),
        "sown": mode("SOWN"),
        "harvest": mode("HARVESTED"),
        "duration": float(sub["CROPDURATION"].mean()) if "CROPDURATION" in sub else 0.0,
        "season": season_label(mode("SEASON")),
        "soil": mode("SOIL").title(),
        "water": mode("WATER_SOURCE").title(),
    }


GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


def _place_label(item):
    parts = [item.get("name", ""), item.get("admin1", ""), item.get("country", "")]
    seen, clean = set(), []
    for part in parts:
        if part and part not in seen:
            seen.add(part)
            clean.append(part)
    return ", ".join(clean)


def _load_weather(place):
    """Fill temperature and humidity from live weather for one place."""
    import requests

    cur = requests.get(
        WEATHER_URL,
        params={"latitude": place["lat"], "longitude": place["lon"],
                "current": "temperature_2m,relative_humidity_2m"},
        timeout=10,
    ).json()["current"]
    st.session_state["temp"] = float(cur["temperature_2m"])
    st.session_state["hum"] = float(cur["relative_humidity_2m"])
    st.session_state["weather_msg"] = (
        "ok", f'{place["label"]}: {cur["temperature_2m"]}°C, {cur["relative_humidity_2m"]}%'
    )


def search_city():
    """Runs when the user types a city and presses Enter: list matches, pick the first, load weather."""
    query = str(st.session_state.get("city_query", "")).strip()
    st.session_state["city_results"] = []
    if len(query) < 2:
        st.session_state["weather_msg"] = ("nf", "")
        return
    try:
        import requests

        found = requests.get(
            GEO_URL, params={"name": query, "count": 8, "language": "en", "format": "json"}, timeout=10
        ).json().get("results", [])
        places, seen_labels = [], set()
        for x in found:
            label = _place_label(x)
            if label in seen_labels:          # same place listed twice: keep the first
                continue
            seen_labels.add(label)
            places.append({"label": label, "lat": x["latitude"], "lon": x["longitude"]})
        if not places:
            st.session_state["weather_msg"] = ("nf", "")
            return
        st.session_state["city_results"] = places
        st.session_state["city_pick"] = places[0]["label"]
        _load_weather(places[0])
    except Exception:
        st.session_state["weather_msg"] = ("err", "")


def pick_city():
    """Runs when the user chooses another match in the dropdown."""
    label = st.session_state.get("city_pick")
    for place in st.session_state.get("city_results", []):
        if place["label"] == label:
            try:
                _load_weather(place)
            except Exception:
                st.session_state["weather_msg"] = ("err", "")
            return


def refresh_weather():
    if st.session_state.get("city_results"):
        pick_city()
    else:
        search_city()


FACTOR_KEY = {
    "N": "n", "P": "p", "K": "k", "SOIL_PH": "ph", "TEMP": "temp",
    "RELATIVE_HUMIDITY": "hum", "WATERREQUIRED": "water", "SOIL": "soil", "SEASON": "season",
}


def factor_influence(frame, crop):
    """Percentage points of probability for `crop` lost when one input is replaced by the dataset's
    typical value. Positive = that input pushes towards the crop, negative = pushes away."""
    try:
        idx = [str(x) for x in class_names()].index(crop)
        base_row = frame.iloc[0].to_dict()
        alts = []
        for col in INPUT_COLS:
            row = dict(base_row)
            row[col] = TYPICAL[col]
            alts.append(row)
        base = float(np.asarray(model.predict_proba(frame[INPUT_COLS]))[0][idx]) * 100
        alt_p = np.asarray(model.predict_proba(pd.DataFrame(alts)[INPUT_COLS]))[:, idx] * 100
        return sorted(((c, base - float(p)) for c, p in zip(INPUT_COLS, alt_p)), key=lambda x: -abs(x[1]))
    except Exception:
        return []


def why_html(items, limit=6):
    items = [(c, v) for c, v in items if abs(v) >= 0.05][:limit]
    if not items or max(abs(v) for _, v in items) < 0.5:
        return ""
    top_abs = max(abs(v) for _, v in items)
    rows = ""
    for col, val in items:
        cls = "pos" if val >= 0 else "neg"
        sign = "+" if val >= 0 else "−"
        rows += (
            f'<div class="why"><div class="wl">{lbl(FACTOR_KEY[col])}</div>'
            f'<div class="wbar"><div class="wfill {cls}" style="width:{abs(val) / top_abs * 100:.0f}%"></div></div>'
            f'<div class="wv">{sign}{abs(val):.1f}</div></div>'
        )
    return rows


ROTATION = {
    "cereals": "pulses", "millets": "pulses", "pulses": "cereals", "oil seeds": "cereals",
    "fibre crop": "pulses", "sugar crops": "pulses",
    "vegetables": "mix", "colecrops": "mix", "bulbvegetables": "mix", "root&tuber": "mix",
}


def rotation_tip(crop):
    kind = ROTATION.get(str(CROP_TYPE.get(crop, "")).strip().lower())
    if not kind:
        return ""
    nxt = t({"pulses": "rot_n_pulses", "cereals": "rot_n_cereals", "mix": "rot_n_mix"}[kind])
    text = t("rot_text").format(crop=crop_label(crop), nxt=nxt)
    if kind in ("pulses", "mix"):
        text += t("rot_legume")
    return text


FIELD_KEYS = ["n", "p", "k", "ph", "temp", "hum", "water", "soil", "season"]


def read_fields():
    return db_read_fields()


def save_field():
    name = str(st.session_state.get("field_name", "")).strip()
    if not name:
        st.session_state["field_msg"] = ("err", t("field_need_name"))
        return
    data = {k_: st.session_state[k_] for k_ in FIELD_KEYS}
    ok = db_save_field(name, data)
    st.session_state["field_msg"] = ("ok", f'{t("field_saved")}: {name}') if ok else ("err", t("field_fail"))


def load_field():
    name = st.session_state.get("field_pick")
    data = read_fields().get(name)
    if not data:
        return
    for k_ in FIELD_KEYS:
        if k_ not in data:
            continue
        if k_ == "soil" and data[k_] not in SOILS:
            continue
        if k_ == "season" and data[k_] not in SEASONS:
            continue
        st.session_state[k_] = data[k_]
    st.session_state.pop("result", None)
    st.session_state["field_msg"] = ("ok", f'{t("field_loaded")}: {name}')


def delete_field():
    name = st.session_state.get("field_pick")
    if name and db_delete_field(name):
        st.session_state["field_msg"] = ("ok", f'{t("field_deleted")}: {name}')
    st.session_state.pop("field_pick", None)


ADVICE_COLS = (("N", "n"), ("P", "p"), ("K", "k"), ("SOIL_PH", "ph"))


def fertilizer_advice(crop, used, lang=None):
    """List of (nutrient label, advice text). Empty list = soil is close to this crop's typical soil."""
    code = lang or LANG_CODE
    tx = lambda key: TEXT[code].get(key) or TEXT["en"][key]
    if crop not in PROFILES.index:
        return []
    items = []
    for col, key in ADVICE_COLS:
        ideal = float(PROFILES.loc[crop, col])
        span = NORM[col][1] - NORM[col][0]
        diff = used[col] - ideal
        if abs(diff) / span < 0.08:
            continue
        items.append((tx(key), tx(f"fert_{key}_{'high' if diff > 0 else 'low'}")))
    return items


def advice_html(items):
    if not items:
        return f'<div class="fert fert-ok">✅ {t("fert_ok")}</div>'
    return "".join(f'<div class="fert"><b>{a}:</b> {b}</div>' for a, b in items)


def build_pdf(crop, top, used, soil_, season_, fit, facts, advice, image_path):
    """Real PDF report (English, because the standard PDF fonts have no Tamil glyphs)."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.lib.utils import ImageReader
    from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    esc = htmllib.escape
    green, brown, line = colors.HexColor("#14391f"), colors.HexColor("#5a3d27"), colors.HexColor("#d8c9a8")
    base = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=base["Title"], textColor=green, fontSize=19, alignment=0)
    h2 = ParagraphStyle("h2", parent=base["Heading2"], textColor=brown, fontSize=12, spaceBefore=8, spaceAfter=3)
    body = ParagraphStyle("body", parent=base["BodyText"], fontSize=10, leading=14)
    small = ParagraphStyle("small", parent=body, fontSize=8, textColor=colors.HexColor("#6b5c4b"))

    def grid(rows, widths, header=True):
        table = Table(rows, colWidths=widths)
        style = [("GRID", (0, 0), (-1, -1), 0.5, line), ("FONTSIZE", (0, 0), (-1, -1), 9),
                 ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
        if header:
            style += [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef3e2")),
                      ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")]
        table.setStyle(TableStyle(style))
        return table

    fit_txt = f"{fit:.0f}%" if fit is not None else "-"
    label_style = ParagraphStyle("lbl", parent=body, fontSize=9, leading=13, textColor=colors.HexColor("#8bc34a"))
    name_style = ParagraphStyle("nm", parent=body, fontSize=26, leading=32, textColor=colors.white,
                                fontName="Helvetica-Bold")
    fit_style = ParagraphStyle("fit", parent=body, fontSize=11, leading=15, textColor=colors.HexColor("#e5d6b8"))
    banner_text = [
        Paragraph("BEST CROP FOR YOUR SOIL", label_style),
        Paragraph(esc(crop.title()), name_style),
        Paragraph(f"Soil match: {fit_txt}", fit_style),
    ]
    photo = ""
    if image_path:
        try:
            iw, ih = ImageReader(str(image_path)).getSize()
            photo = Image(str(image_path), width=6.2 * cm, height=6.2 * cm * ih / iw)
        except Exception:
            photo = ""
    banner = Table([[photo, banner_text]], colWidths=[6.6 * cm, 10.4 * cm])
    banner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), green), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 12), ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))

    values = [["Factor", "Your value"]] + [[SHORT[c], f"{used[c]:g}"] for c in NUM_COLS]
    values += [["Soil type", str(soil_).title()], ["Season", season_label_en(season_)]]
    matches = [["#", "Crop", "Confidence"]] + [[str(i), n.title(), f"{p:.1f}%"] for i, (n, p) in enumerate(top, 1)]
    calendar = [
        ["Crop type", facts["type"]], ["Usually sown", facts["sown"]],
        ["Usually harvested", facts["harvest"]], ["Duration", f'{facts["duration"]:.0f} days'],
        ["Water source", facts["water"]],
    ]

    story = [
        Paragraph(f"{APP_NAME}: {esc(TEXT['en']['tagline'])}", h1),
        Paragraph(datetime.now().strftime("Generated on %d %b %Y, %H:%M"), small),
        Spacer(1, 8), banner,
        Paragraph("Your soil and field values", h2), grid(values, [8.5 * cm, 8.5 * cm]),
        Paragraph("Top matches", h2), grid(matches, [1.5 * cm, 10 * cm, 5.5 * cm]),
        Paragraph("Crop calendar", h2), grid(calendar, [8.5 * cm, 8.5 * cm], header=False),
        Paragraph("Fertilizer guidance", h2),
    ]
    if advice:
        for label, text in advice:
            story.append(Paragraph(f"<b>{esc(label)}:</b> {esc(text)}", body))
            story.append(Spacer(1, 4))
    else:
        story.append(Paragraph(esc(TEXT["en"]["fert_ok"]), body))
    story += [Spacer(1, 6), Paragraph(esc(TEXT["en"]["fert_note"]), small),
              Spacer(1, 6), Paragraph(esc(TEXT["en"]["disclaimer"]), small)]

    buf = io.BytesIO()
    SimpleDocTemplate(buf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                      topMargin=1.8 * cm, bottomMargin=1.8 * cm, title=f"{APP_NAME} report").build(story)
    return buf.getvalue()


def build_report(crop, top, used, soil_, season_, fit, facts, advice=()):
    e = htmllib.escape
    rows = "".join(
        f"<tr><td>{e(SHORT[c])}</td><td>{used[c]:g}</td></tr>" for c in NUM_COLS
    )
    rows += f"<tr><td>Soil type</td><td>{e(str(soil_))}</td></tr>"
    rows += f"<tr><td>Season</td><td>{e(season_label_en(season_))}</td></tr>"
    ranks = "".join(
        f"<tr><td>{i}</td><td>{e(n.title())}</td><td>{p:.1f}%</td></tr>"
        for i, (n, p) in enumerate(top, 1)
    )
    fit_txt = f"{fit:.0f}%" if fit is not None else "-"
    if advice:
        advice_block = "".join(f"<p><b>{e(a)}:</b> {e(b)}</p>" for a, b in advice)
    else:
        advice_block = f"<p>{e(TEXT['en']['fert_ok'])}</p>"
    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>{APP_NAME} report</title>
<style>body{{font-family:Arial,sans-serif;max-width:760px;margin:2rem auto;color:#2b2118}}
h1{{color:#14391f}} h2{{color:#5a3d27;border-bottom:2px solid #8bc34a;padding-bottom:4px}}
table{{border-collapse:collapse;width:100%;margin:.5rem 0 1rem}}
td,th{{border:1px solid #d8c9a8;padding:6px 10px;text-align:left}} th{{background:#eef3e2}}
.best{{background:#14391f;color:#fff;padding:1rem 1.4rem;border-radius:12px}}
.best b{{font-size:1.8rem;text-transform:capitalize}}</style></head><body>
<h1>{APP_NAME}: {e(TEXT['en']['tagline'])}</h1>
<p>Generated on {datetime.now().strftime('%d %b %Y, %H:%M')}</p>
<div class="best">Best crop for your soil<br><b>{e(crop)}</b><br>Soil match: {fit_txt}</div>
<h2>Your soil and field values</h2><table><tr><th>Factor</th><th>Value</th></tr>{rows}</table>
<h2>Top matches</h2><table><tr><th>#</th><th>Crop</th><th>Confidence</th></tr>{ranks}</table>
<h2>Crop calendar</h2>
<table><tr><td>Crop type</td><td>{e(facts['type'])}</td></tr>
<tr><td>Usually sown</td><td>{e(facts['sown'])}</td></tr>
<tr><td>Usually harvested</td><td>{e(facts['harvest'])}</td></tr>
<tr><td>Duration</td><td>{facts['duration']:.0f} days</td></tr>
<tr><td>Water source</td><td>{e(facts['water'])}</td></tr></table>
<h2>Fertilizer guidance</h2>{advice_block}
<p style="font-size:.8rem;color:#6b5c4b">{e(TEXT['en']['fert_note'])}</p>
<p style="font-size:.85rem;color:#6b5c4b">{e(TEXT['en']['disclaimer'])}</p>
</body></html>"""


# ============================================================
# SUPABASE AUTHENTICATION AND USER DATA
# ============================================================
def _get_supabase_client():
    try:
        from supabase import create_client
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as exc:
        st.error("Supabase configuration is missing. Add SUPABASE_URL and SUPABASE_KEY in Streamlit secrets.")
        st.caption("Do not put your Supabase service_role/secret key here. Use the publishable (anon) key.")
        st.stop()

supabase = _get_supabase_client()

# Restore a signed-in session after Streamlit reruns.
if st.session_state.get("agri_access_token") and st.session_state.get("agri_refresh_token"):
    try:
        supabase.auth.set_session(st.session_state["agri_access_token"], st.session_state["agri_refresh_token"])
    except Exception:
        for _k in ("agri_access_token", "agri_refresh_token", "agri_user", "agri_role"):
            st.session_state.pop(_k, None)


def _store_auth_session(auth_response):
    session = getattr(auth_response, "session", None)
    user = getattr(auth_response, "user", None)
    if session is None or user is None:
        return False
    st.session_state["agri_access_token"] = session.access_token
    st.session_state["agri_refresh_token"] = session.refresh_token
    st.session_state["agri_user"] = {"id": str(user.id), "email": user.email or ""}
    return True


def _load_profile_role(user_id):
    try:
        result = supabase.table("profiles").select("role").eq("id", user_id).limit(1).execute()
        if result.data:
            return str(result.data[0].get("role", "user")).lower()
    except Exception:
        pass
    return "user"


def _auth_screen():
    st.title("🌱 AgriSense")
    st.subheader("Sign in to your account")
    login_tab, signup_tab = st.tabs(["Login", "Sign up"])
    with login_tab:
        with st.form("agri_login_form"):
            email = st.text_input("Email", key="agri_login_email")
            password = st.text_input("Password", type="password", key="agri_login_password")
            submitted = st.form_submit_button("Login", use_container_width=True)
        if submitted:
            try:
                response = supabase.auth.sign_in_with_password({"email": email.strip(), "password": password})
                if _store_auth_session(response):
                    st.session_state["agri_role"] = _load_profile_role(st.session_state["agri_user"]["id"])
                    st.rerun()
                st.error("Login did not return a valid session. Check your email confirmation status.")
            except Exception as exc:
                st.error(f"Login failed: {exc}")
    with signup_tab:
        with st.form("agri_signup_form"):
            new_email = st.text_input("Email address", key="agri_signup_email")
            new_password = st.text_input("Create password", type="password", key="agri_signup_password")
            confirm = st.text_input("Confirm password", type="password", key="agri_signup_confirm")
            submitted_signup = st.form_submit_button("Create account", use_container_width=True)
        if submitted_signup:
            if not new_email.strip() or len(new_password) < 6:
                st.warning("Enter an email and a password with at least 6 characters.")
            elif new_password != confirm:
                st.warning("The passwords do not match.")
            else:
                try:
                    response = supabase.auth.sign_up({"email": new_email.strip(), "password": new_password})
                    if _store_auth_session(response):
                        st.session_state["agri_role"] = _load_profile_role(st.session_state["agri_user"]["id"])
                        st.success("Account created.")
                        st.rerun()
                    else:
                        st.success("Signup submitted. Check your email to confirm the account, then log in.")
                except Exception as exc:
                    st.error(f"Signup failed: {exc}")

if not st.session_state.get("agri_user"):
    _auth_screen()
    st.stop()

CURRENT_USER = st.session_state["agri_user"]
CURRENT_USER_ID = CURRENT_USER["id"]
CURRENT_ROLE = st.session_state.get("agri_role") or _load_profile_role(CURRENT_USER_ID)
st.session_state["agri_role"] = CURRENT_ROLE

with st.sidebar:
    st.caption(f"Signed in: {CURRENT_USER.get('email', '')}")
    if st.button("Logout", key="agri_logout", use_container_width=True):
        try:
            supabase.auth.sign_out()
        except Exception:
            pass
        for _k in list(st.session_state.keys()):
            if _k.startswith("agri_") or _k in ("result", "history", "field_msg", "field_pick"):
                st.session_state.pop(_k, None)
        st.rerun()


def db_read_fields():
    try:
        response = supabase.table("saved_fields").select("field_name,field_data").eq("user_id", CURRENT_USER_ID).execute()
        return {row["field_name"]: row["field_data"] for row in (response.data or [])}
    except Exception as exc:
        st.error(f"Could not load saved fields: {exc}")
        return {}


def db_save_field(name, data):
    try:
        supabase.table("saved_fields").upsert(
            {"user_id": CURRENT_USER_ID, "field_name": name, "field_data": data},
            on_conflict="user_id,field_name",
        ).execute()
        return True
    except Exception as exc:
        st.error(f"Could not save field: {exc}")
        return False


def db_delete_field(name):
    try:
        supabase.table("saved_fields").delete().eq("user_id", CURRENT_USER_ID).eq("field_name", name).execute()
        return True
    except Exception as exc:
        st.error(f"Could not delete field: {exc}")
        return False


def db_load_history():
    try:
        response = supabase.table("prediction_history").select("prediction_data,created_at").eq("user_id", CURRENT_USER_ID).order("created_at", desc=True).limit(100).execute()
        items = []
        for row in (response.data or []):
            payload = row.get("prediction_data") or {}
            if isinstance(payload, dict):
                items.append(payload)
        return items
    except Exception as exc:
        st.warning(f"Could not load prediction history: {exc}")
        return []


def db_save_prediction(payload):
    try:
        supabase.table("prediction_history").insert({"user_id": CURRENT_USER_ID, "prediction_data": payload}).execute()
    except Exception as exc:
        st.warning(f"Prediction was made, but history could not be saved: {exc}")


def db_clear_history():
    try:
        supabase.table("prediction_history").delete().eq("user_id", CURRENT_USER_ID).execute()
        return True
    except Exception as exc:
        st.error(f"Could not clear history: {exc}")
        return False

# ============================================================
# LOAD EVERYTHING
# ============================================================
try:
    model, encoder, model_name, accuracy, comparison = load_model()
except Exception as err:
    st.error("Model files could not be loaded. Check the saved_models folder.")
    st.exception(err)
    st.stop()

df = load_dataset()
if df is None:
    st.error(
        "Dataset not found. Keep Crop_recommendation_dataset.xls (or .csv) "
        "in the same folder as this app."
    )
    st.stop()

NORM = {c: (float(df[c].min()), float(df[c].max())) for c in NUM_COLS}
Q = {c: (float(df[c].quantile(0.33)), float(df[c].quantile(0.66))) for c in ("N", "P", "K")}
PROFILES = df.groupby("CROPS")[NUM_COLS].mean()
SOILS = sorted(df["SOIL"].unique().tolist())
SEASONS = sorted(df["SEASON"].astype(str).unique().tolist())
CROPS = sorted(df["CROPS"].unique().tolist())
CROP_TYPE = (
    df.groupby("CROPS")["TYPE_OF_CROP"].agg(lambda s: s.mode().iat[0]).to_dict()
    if "TYPE_OF_CROP" in df.columns else {}
)
TYPE_OPTIONS = sorted(set(CROP_TYPE.values()))
TYPICAL = {
    **{c: float(df[c].median()) for c in NUM_COLS},
    "SOIL": str(df["SOIL"].mode().iat[0]), "SEASON": str(df["SEASON"].mode().iat[0]),
}
SOWN_MONTHS = (
    df.groupby("CROPS")["SOWN"].agg(lambda x: {str(m).strip()[:3].title() for m in x}).to_dict()
    if "SOWN" in df.columns else {}
)

# ============================================================
# SESSION DEFAULTS AND CALLBACKS
# ============================================================
DEFAULTS = {
    "n": 90.0, "p": 48.0, "k": 55.0, "ph": 6.5, "temp": 25.0,
    "hum": 70.0, "water": 900.0,
    "soil": "loamy soil" if "loamy soil" in SOILS else SOILS[0],
    "season": SEASONS[0],
    "city_query": "Coimbatore",
}
for key, val in DEFAULTS.items():
    st.session_state.setdefault(key, val)
st.session_state.setdefault("history", db_load_history())


def load_random_field():
    row = df.sample(1).iloc[0]
    st.session_state.update(
        n=float(row["N"]), p=float(row["P"]), k=float(row["K"]),
        ph=float(row["SOIL_PH"]), temp=float(row["TEMP"]),
        hum=float(row["RELATIVE_HUMIDITY"]), water=float(row["WATERREQUIRED"]),
        soil=str(row["SOIL"]), season=str(row["SEASON"]),
    )
    st.session_state.pop("result", None)


def reset_inputs():
    st.session_state.update(DEFAULTS)
    st.session_state.pop("result", None)
    for k_ in ("weather_msg", "city_results", "city_pick"):
        st.session_state.pop(k_, None)


def clear_history():
    if db_clear_history():
        st.session_state["history"] = []


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    choice = st.radio("Language / மொழி", ["English", "தமிழ்"], horizontal=True, key="lang_choice")
    LANG_CODE = "ta" if choice == "தமிழ்" else "en"
    st.selectbox(t("theme_label"), list(THEMES), key="theme")
    html(
        f"""
        <div style="padding:.4rem 0 1rem 0">
          <div style="font-size:1.9rem">🌱</div>
          <div style="font-family:'Fraunces',serif;font-size:1.6rem;font-weight:700">{APP_NAME}</div>
          <div style="color:#8bc34a;font-size:.7rem;letter-spacing:.16em;font-weight:700">
          SOIL-FIRST CROP ADVICE</div>
        </div>
        """
    )
    st.markdown("---")
    st.markdown(f"**{t('how')}**")
    st.write(t("how_body"))
    st.markdown("---")
    st.metric(t("crops_cov"), df["CROPS"].nunique())
    st.metric(t("model"), model_name)
    st.metric(t("acc"), f"{accuracy:.2f}%")

# ============================================================
# ADMIN DASHBOARD (visible only to profiles.role = 'admin')
# ============================================================
if CURRENT_ROLE == "admin":
    with st.expander("🛡️ Admin dashboard", expanded=False):
        st.subheader("Registered users")
        try:
            users = supabase.table("profiles").select("id,email,role,created_at").order("created_at", desc=True).execute().data or []
            st.dataframe(pd.DataFrame(users), hide_index=True, use_container_width=True)
        except Exception as exc:
            st.warning(f"Could not load user list: {exc}")
        st.subheader("Recent prediction records")
        try:
            rows = supabase.table("prediction_history").select("user_id,prediction_data,created_at").order("created_at", desc=True).limit(200).execute().data or []
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        except Exception as exc:
            st.warning(f"Could not load prediction records: {exc}")
        st.subheader("Saved fields")
        try:
            rows = supabase.table("saved_fields").select("user_id,field_name,created_at").order("created_at", desc=True).limit(200).execute().data or []
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        except Exception as exc:
            st.warning(f"Could not load saved fields: {exc}")

# ============================================================
# HEADER
# ============================================================
html(
    f"""
    <div class="strata">
      <div class="strata-top">
        <div class="kicker">{t('kicker')}</div>
        <h1>{t('tagline') if LANG_CODE == 'ta' else t('tagline').capitalize()}</h1>
        <p>{t('hero')}</p>
      </div>
      <div class="band b1"><div class="band-label">Topsoil: N · P · K</div></div>
      <div class="band b2"></div><div class="band b3"></div><div class="band b4"></div>
    </div>
    """
)

tab_rec, tab_sow, tab_explore, tab_compare, tab_batch, tab_model = st.tabs(
    [t("tab_rec"), t("tab_sow"), t("tab_explore"), t("tab_compare"), t("tab_batch"), t("tab_model")]
)

# ============================================================
# TAB 1: RECOMMEND
# ============================================================
with tab_rec:
    top_a, top_b, _ = st.columns([1, 1, 3])
    top_a.button(t("sample"), on_click=load_random_field, **STRETCH)
    top_b.button(t("reset"), on_click=reset_inputs, type="secondary", **STRETCH)

    with st.expander(t("fields_h")):
        fc1, fc2 = st.columns([2, 1])
        fc1.text_input(t("field_name"), key="field_name")
        fc2.markdown("<div style='height:1.75rem'></div>", unsafe_allow_html=True)
        fc2.button(t("field_save"), on_click=save_field, key="save_field_btn")
        saved_fields = read_fields()
        if saved_fields:
            pc1, pc2, pc3 = st.columns([2, 1, 1])
            pc1.selectbox(t("field_pick"), sorted(saved_fields), key="field_pick")
            pc2.markdown("<div style='height:1.75rem'></div>", unsafe_allow_html=True)
            pc2.button(t("field_load"), on_click=load_field, key="load_field_btn")
            pc3.markdown("<div style='height:1.75rem'></div>", unsafe_allow_html=True)
            pc3.button(t("field_delete"), on_click=delete_field, type="secondary", key="del_field_btn")
        fmsg = st.session_state.get("field_msg")
        if fmsg:
            html(f'<div class="{"wmsg-ok" if fmsg[0] == "ok" else "wmsg-err"}">{htmllib.escape(fmsg[1])}</div>')

    left, mid, right = st.columns([1.05, 1.05, 1.1], gap="large")

    with left:
        html(f'<div class="h2">{lbl("h_soil")}</div><div class="sub">{t("s_soil")}</div>')
        n = st.number_input(lbl("n"), min_value=0.0, step=1.0, key="n")
        p = st.number_input(lbl("p"), min_value=0.0, step=1.0, key="p")
        k = st.number_input(lbl("k"), min_value=0.0, step=1.0, key="k")
        ph = st.number_input(lbl("ph"), min_value=0.0, max_value=14.0, step=0.1, key="ph")

    with mid:
        html(f'<div class="h2">{lbl("h_field")}</div><div class="sub">{t("s_field")}</div>')
        st.text_input(lbl("city"), key="city_query", on_change=search_city)
        city_matches = st.session_state.get("city_results", [])
        if city_matches:
            st.selectbox(
                t("city_pick"), [c["label"] for c in city_matches], key="city_pick", on_change=pick_city
            )
        st.button(t("fetch"), on_click=refresh_weather, key="fetch_btn", type="secondary")
        wmsg = st.session_state.get("weather_msg")
        if wmsg:
            if wmsg[0] == "ok":
                html(f'<div class="wmsg-ok">📍 {htmllib.escape(wmsg[1])}</div>')
            elif wmsg[0] == "nf":
                html(f'<div class="wmsg-err">{t("weather_nf")}</div>')
            else:
                html(f'<div class="wmsg-err">{t("weather_err")}</div>')
        temp = st.number_input(lbl("temp"), step=0.1, key="temp")
        hum = st.number_input(lbl("hum"), min_value=0.0, max_value=100.0, step=0.1, key="hum")
        water = st.number_input(lbl("water"), min_value=0.0, step=10.0, key="water")
        soil = st.selectbox(lbl("soil"), SOILS, key="soil")
        season = st.selectbox(lbl("season"), SEASONS, format_func=season_label, key="season")

    with right:
        html(f'<div class="h2">{lbl("h_health")}</div><div class="sub">{t("s_health")}</div>')
        names = [t("low"), t("medium"), t("high")]
        zone = ["#f0c36d", "#8bc34a", "#a67c52"]
        level_bar(lbl("n"), n, NORM["N"][0], NORM["N"][1], Q["N"], names, zone)
        level_bar(lbl("p"), p, NORM["P"][0], NORM["P"][1], Q["P"], names, zone)
        level_bar(lbl("k"), k, NORM["K"][0], NORM["K"][1], Q["K"], names, zone)
        level_bar(
            lbl("ph"), ph, 4.0, 10.0, (6.0, 7.5),
            [t("acidic"), t("neutral"), t("alkaline")], ["#e8a87c", "#8bc34a", "#7aa6c2"],
        )

    chosen_types = st.multiselect(t("types"), TYPE_OPTIONS, format_func=lambda x: x.title(), key="type_filter")
    go = st.button(t("go"), **STRETCH)

    current = {
        "N": n, "P": p, "K": k, "SOIL_PH": ph, "TEMP": temp,
        "RELATIVE_HUMIDITY": hum, "WATERREQUIRED": water,
    }

    if go:
        frame = pd.DataFrame([{**current, "SOIL": soil, "SEASON": season}])
        try:
            allowed = {c for c, ty in CROP_TYPE.items() if ty in chosen_types} if chosen_types else None
            top = rank_crops(frame, allowed=allowed, top_n=5)
            crop = top[0][0]
            st.session_state["result"] = {
                "crop": crop, "top": top, "inputs": dict(current), "soil": soil, "season": season,
            }
            history_item = {
                "Time": datetime.now().strftime("%d %b %H:%M:%S"), "Best crop": crop.title(),
                "Confidence (%)": round(top[0][1], 1),
                **{SHORT[c]: round(current[c], 1) for c in NUM_COLS},
                "Soil": soil, "Season": season_label(season),
            }
            st.session_state["history"].insert(0, history_item)
            db_save_prediction(history_item)
        except Exception as exc:
            st.error("Prediction could not be completed.")
            st.exception(exc)

    res = st.session_state.get("result")
    if res:
        crop, top, used = res["crop"], res["top"], res["inputs"]
        outside = [
            f"{SHORT[c]} ({used[c]:g}, {lo:g}–{hi:g})"
            for c, (lo, hi) in NORM.items() if not (lo <= used[c] <= hi)
        ]
        if outside:
            st.warning(t("outside") + ", ".join(outside))
        if len(top) > 1 and top[0][1] < 50:
            st.warning(t("low_conf"))

        st.markdown("---")
        facts = crop_facts(crop)
        fit = similarity_score(used, PROFILES.loc[crop], NORM) if crop in PROFILES.index else None

        img_col, info_col = st.columns([1, 1.2], gap="large")
        with img_col:
            path = crop_image_path(crop)
            if path:
                st.image(str(path), caption=crop_label(crop), **STRETCH)
                credit = load_image_credits().get(slugify(crop))
                if credit:
                    st.caption(f"{t('photo_credit')}: {credit}")
            else:
                html(
                    f"""
                    <div class="card" style="min-height:240px;display:flex;flex-direction:column;
                    align-items:center;justify-content:center;text-align:center;color:#7a6a58">
                    <div style="font-size:3.5rem">🌿</div>
                    <div>{t('save_photo')}<br><b>crop_images/{slugify(crop)}.jpg</b></div></div>
                    """
                )

        with info_col:
            fit_html = f'<span class="match">{t("match")} {fit:.0f}%</span>' if fit is not None else ""
            html(
                f"""
                <div class="result">
                  <div class="kicker">{t('best')}</div>
                  <div class="name">{crop_label(crop)}</div>
                  <div class="meta">{t('predicted_by')} {model_name}</div>
                  {fit_html}
                </div>
                """
            )
            if len(top) > 1:
                html(f'<div class="h2" style="margin-top:1rem">{t("top")}</div>')
                html(rank_html(top))

        # ---- crop calendar
        st.markdown("")
        html(f'<div class="h2">{t("cal_h")}</div>')
        html(calendar_html(facts["sown"], facts["harvest"]))
        fact_items = [
            (t("ctype"), facts["type"]), (t("sow"), facts["sown"]), (t("harvest"), facts["harvest"]),
            (t("duration"), f'{facts["duration"]:.0f} {t("days")}'),
            (t("wsource"), facts["water"]), (t("bseason"), facts["season"]),
        ]
        cards = "".join(
            f'<div class="card"><div class="stat-label">{a}</div>'
            f'<div class="stat-value" style="font-size:1.1rem">{b}</div></div>'
            for a, b in fact_items
        )
        html(f'<div style="display:grid;grid-template-columns:repeat(6,1fr);gap:.6rem">{cards}</div>')

        # ---- radar + adjust table
        if crop in PROFILES.index:
            st.markdown("")
            c1, c2 = st.columns([1, 1.1], gap="large")
            with c1:
                html(f'<div class="h2">{t("radar_h")}</div>')
                svg = radar_svg(
                    [(crop, PROFILES.loc[crop].to_dict(), "#3f7d3a"), ("Your field", used, "#d9962b")],
                    NORM,
                )
                html(
                    f"""{svg}
                    <div class="legend"><span><span class="dot" style="background:#3f7d3a"></span>
                    {t('typical_for')} {crop}</span>
                    <span><span class="dot" style="background:#d9962b"></span>{t('your_field')}</span></div>"""
                )
            with c2:
                html(f'<div class="h2">{t("adjust_h")}</div><div class="sub">{t("adjust_s")}</div>')
                table = []
                for col in NUM_COLS:
                    ideal = float(PROFILES.loc[crop, col])
                    diff = used[col] - ideal
                    span = NORM[col][1] - NORM[col][0]
                    if abs(diff) / span < 0.08:
                        status = t("on_target")
                    else:
                        status = t("higher") if diff > 0 else t("lower")
                    table.append({
                        t("factor"): SHORT[col], t("your_field"): round(used[col], 1),
                        t("typical"): round(ideal, 1), t("status"): status,
                    })
                st.dataframe(pd.DataFrame(table), hide_index=True, **STRETCH)

        # ---- why this crop + fertilizer + rotation
        st.markdown("")
        why_col, fert_col = st.columns(2, gap="large")
        with why_col:
            html(f'<div class="h2">{t("why_h")}</div><div class="sub">{t("why_s")}</div>')
            frame_used = pd.DataFrame([{**used, "SOIL": res["soil"], "SEASON": res["season"]}])
            why_rows = why_html(factor_influence(frame_used, crop))
            if why_rows:
                html(why_rows)
                st.caption(t("why_legend"))
        with fert_col:
            html(f'<div class="h2">{t("fert_h")}</div><div class="sub">{t("fert_s")}</div>')
            html(advice_html(fertilizer_advice(crop, used)))
            st.caption(t("fert_note"))
            tip = rotation_tip(crop)
            if tip:
                html(f'<div class="h2" style="margin-top:.8rem">{t("rot_h")}</div>')
                html(f'<div class="fert fert-ok">{htmllib.escape(tip)}</div>')
                st.caption(t("rot_note"))

        # ---- what-if analysis
        with st.expander(t("whatif_h")):
            vary = st.selectbox(t("whatif_pick"), ["N", "P", "K", "SOIL_PH"],
                                format_func=lambda c: SHORT[c], key="whatif_col")
            lo_v, hi_v = float(df[vary].quantile(0.05)), float(df[vary].quantile(0.95))
            values = np.linspace(lo_v, hi_v, 9)
            base = {**used, "SOIL": res["soil"], "SEASON": res["season"]}
            frame_w = pd.DataFrame([{**base, vary: float(v)} for v in values])
            names_w, conf_w = predict_batch(frame_w)
            st.dataframe(
                pd.DataFrame({
                    f"{SHORT[vary]} {t('value').lower()}": [round(float(v), 1) for v in values],
                    t("crop"): [crop_label(x) for x in names_w],
                    t("conf"): [round(c, 1) for c in conf_w],
                }),
                hide_index=True, **STRETCH,
            )

        # ---- report downloads
        advice_en = fertilizer_advice(crop, used, "en")
        report = build_report(crop, top, used, res["soil"], res["season"], fit, facts, advice_en)
        pdf_bytes, pdf_ok = None, True
        try:
            pdf_bytes = build_pdf(crop, top, used, res["soil"], res["season"], fit, facts, advice_en, path)
        except ImportError:
            pdf_ok = False
        except Exception:
            pdf_bytes = None
        dl1, dl2, dl3, _ = st.columns([1.5, 1.2, 1.2, 1.2])
        dl1.download_button(
            t("download"), data=report.encode("utf-8"),
            file_name=f"agrisense_report_{slugify(crop)}.html", mime="text/html",
        )
        if pdf_bytes:
            dl2.download_button(
                t("download_pdf"), data=pdf_bytes,
                file_name=f"agrisense_report_{slugify(crop)}.pdf", mime="application/pdf",
            )
        elif not pdf_ok:
            st.caption(t("pdf_missing"))
        share_text = (
            f"AgriSense\n{t('best')}: {crop_label(crop)}\n"
            + (f"{t('match')}: {fit:.0f}%\n" if fit is not None else "")
            + f"N {used['N']:g}, P {used['P']:g}, K {used['K']:g}, pH {used['SOIL_PH']:g}"
        )
        wa_url = "https://wa.me/?text=" + urllib.parse.quote(share_text)
        if hasattr(st, "link_button"):
            dl3.link_button(t("share_wa"), wa_url)
        else:
            dl3.markdown(f"[{t('share_wa')}]({wa_url})")
        st.info(t("disclaimer"))

    # ---- history
    if st.session_state["history"]:
        with st.expander(f'{t("history_h")} ({len(st.session_state["history"])})'):
            hist = pd.DataFrame(st.session_state["history"])
            st.dataframe(hist, hide_index=True, **STRETCH)
            hc1, hc2, _ = st.columns([1, 1, 3])
            hc1.download_button(
                t("history_dl"), data=hist.to_csv(index=False).encode("utf-8"),
                file_name="agrisense_history.csv", mime="text/csv",
            )
            hc2.button(t("history_clear"), on_click=clear_history, type="secondary", key="clr_hist")

# ============================================================
# TAB: SOW THIS MONTH
# ============================================================
with tab_sow:
    html(f'<div class="h2">{t("sow_h")}</div><div class="sub">{t("sow_s")}</div>')
    month = st.selectbox(t("sow_month"), MONTHS, index=datetime.now().month - 1, key="sow_month")
    st.caption(t("sow_note"))
    now_values = {
        "N": st.session_state["n"], "P": st.session_state["p"], "K": st.session_state["k"],
        "SOIL_PH": st.session_state["ph"], "TEMP": st.session_state["temp"],
        "RELATIVE_HUMIDITY": st.session_state["hum"], "WATERREQUIRED": st.session_state["water"],
    }
    sow_rows = []
    for name_ in CROPS:
        if month in SOWN_MONTHS.get(name_, set()) and name_ in PROFILES.index:
            sow_rows.append((name_, similarity_score(now_values, PROFILES.loc[name_], NORM), crop_facts(name_)))
    sow_rows.sort(key=lambda r: -r[1])
    if not sow_rows:
        st.info(t("sow_none"))
    else:
        html(rank_html([(n_, fit_) for n_, fit_, _ in sow_rows[:8]]))
        st.dataframe(
            pd.DataFrame({
                t("crop"): [crop_label(n_) for n_, _, _ in sow_rows],
                t("sow_fit"): [round(f_, 1) for _, f_, _ in sow_rows],
                t("ctype"): [x["type"] for _, _, x in sow_rows],
                t("harvest"): [x["harvest"] for _, _, x in sow_rows],
                t("duration"): [f'{x["duration"]:.0f} {t("days")}' for _, _, x in sow_rows],
            }),
            hide_index=True, **STRETCH,
        )

# ============================================================
# TAB 2: CROP EXPLORER
# ============================================================
with tab_explore:
    html(f'<div class="h2">{t("explore_h")}</div><div class="sub">{t("explore_s")}</div>')
    pick = st.selectbox(t("choose_crop"), CROPS, format_func=crop_label, key="explore_pick")
    sub = df[df["CROPS"] == pick]
    pf = crop_facts(pick)

    e1, e2 = st.columns([1, 1.2], gap="large")
    with e1:
        path = crop_image_path(pick)
        if path:
            st.image(str(path), caption=crop_label(pick), **STRETCH)
        else:
            html(f'<div class="card" style="text-align:center;min-height:200px;padding-top:3rem">🌿<br>{t("no_image")}</div>')
        items = [
            (t("ctype"), pf["type"]), (t("sow"), pf["sown"]), (t("harvest"), pf["harvest"]),
            (t("duration"), f'{pf["duration"]:.0f} {t("days")}'), (t("bseason"), pf["season"]),
            (t("wsource"), pf["water"]), (t("csoil"), pf["soil"]),
        ]
        cards = "".join(
            f'<div class="card"><div class="stat-label">{a}</div><div class="stat-value" '
            f'style="font-size:1.1rem">{b}</div></div>' for a, b in items
        )
        html(f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:.6rem;margin-top:.8rem">{cards}</div>')

    with e2:
        html(f'<div class="h2">{t("cal_h")}</div>')
        html(calendar_html(pf["sown"], pf["harvest"]))
        html(f'<div class="h2">{t("profile_h")}</div>')
        overall = df[NUM_COLS].mean().to_dict()
        svg = radar_svg(
            [("All crops", overall, "#9a6b43"), (pick, PROFILES.loc[pick].to_dict(), "#3f7d3a")], NORM,
        )
        html(
            f"""{svg}
            <div class="legend"><span><span class="dot" style="background:#3f7d3a"></span>{pick}</span>
            <span><span class="dot" style="background:#9a6b43"></span>{t('all_avg')}</span></div>"""
        )
        st.dataframe(
            pd.DataFrame({
                t("factor"): [SHORT[c] for c in NUM_COLS],
                "Min": [round(float(sub[c].min()), 1) for c in NUM_COLS],
                "Avg": [round(float(sub[c].mean()), 1) for c in NUM_COLS],
                "Max": [round(float(sub[c].max()), 1) for c in NUM_COLS],
            }),
            hide_index=True, **STRETCH,
        )

# ============================================================
# TAB 3: COMPARE TWO CROPS
# ============================================================
with tab_compare:
    html(f'<div class="h2">{t("cmp_h")}</div><div class="sub">{t("cmp_s")}</div>')
    ia = CROPS.index("rice") if "rice" in CROPS else 0
    ib = CROPS.index("wheat") if "wheat" in CROPS else min(1, len(CROPS) - 1)
    cc1, cc2 = st.columns(2, gap="large")
    crop_a = cc1.selectbox(t("crop_a"), CROPS, index=ia, format_func=crop_label, key="cmp_a")
    crop_b = cc2.selectbox(t("crop_b"), CROPS, index=ib, format_func=crop_label, key="cmp_b")

    for col_, name_ in ((cc1, crop_a), (cc2, crop_b)):
        with col_:
            ip = crop_image_path(name_)
            if ip:
                st.image(str(ip), caption=crop_label(name_), **STRETCH)

    r1, r2 = st.columns([1, 1.2], gap="large")
    with r1:
        svg = radar_svg(
            [(crop_a, PROFILES.loc[crop_a].to_dict(), "#3f7d3a"),
             (crop_b, PROFILES.loc[crop_b].to_dict(), "#d9962b")], NORM,
        )
        html(
            f"""{svg}
            <div class="legend"><span><span class="dot" style="background:#3f7d3a"></span>{crop_a}</span>
            <span><span class="dot" style="background:#d9962b"></span>{crop_b}</span></div>"""
        )
    with r2:
        fa, fb = crop_facts(crop_a), crop_facts(crop_b)
        rows = [(SHORT[c], round(float(PROFILES.loc[crop_a, c]), 1), round(float(PROFILES.loc[crop_b, c]), 1))
                for c in NUM_COLS]
        rows += [
            (t("ctype"), fa["type"], fb["type"]), (t("sow"), fa["sown"], fb["sown"]),
            (t("harvest"), fa["harvest"], fb["harvest"]),
            (t("duration"), f'{fa["duration"]:.0f} {t("days")}', f'{fb["duration"]:.0f} {t("days")}'),
            (t("bseason"), fa["season"], fb["season"]), (t("wsource"), fa["water"], fb["water"]),
        ]
        st.dataframe(
            pd.DataFrame(
                [(a, str(b), str(c)) for a, b, c in rows],
                columns=[t("factor"), crop_a.title(), crop_b.title()],
            ),
            hide_index=True, **STRETCH,
        )

# ============================================================
# TAB 4: BATCH PREDICTION
# ============================================================
with tab_batch:
    html(f'<div class="h2">{t("batch_h")}</div><div class="sub">{t("batch_s")}</div>')
    template = df[INPUT_COLS].sample(5, random_state=1).reset_index(drop=True)
    st.download_button(
        t("template"), data=template.to_csv(index=False).encode("utf-8"),
        file_name="agrisense_template.csv", mime="text/csv",
    )
    st.caption("Columns: " + ", ".join(INPUT_COLS))
    up = st.file_uploader(t("upload"), type=["csv", "xlsx", "xls"], key="batch_file")
    if up is not None:
        try:
            raw = pd.read_csv(up) if up.name.lower().endswith(".csv") else pd.read_excel(up)
            raw.columns = [str(c).strip().upper() for c in raw.columns]
            missing = [c for c in INPUT_COLS if c not in raw.columns]
            if missing:
                st.error(t("batch_missing") + ", ".join(missing))
            else:
                data_in = raw.copy()
                data_in["SOIL"] = data_in["SOIL"].astype(str).str.strip().str.lower()
                data_in["SEASON"] = (
                    data_in["SEASON"].astype(str).str.strip()
                    .map(lambda x: SEASON_ALIASES.get(x.lower(), x))
                )
                for c in NUM_COLS:
                    data_in[c] = pd.to_numeric(data_in[c], errors="coerce")
                data_in = data_in.dropna(subset=NUM_COLS)
                names_b, conf_b = predict_batch(data_in[INPUT_COLS])
                out = data_in.copy()
                out["RECOMMENDED_CROP"] = [x.title() for x in names_b]
                out["CONFIDENCE_%"] = [round(c, 1) for c in conf_b]
                st.success(f'{t("batch_done")}: {len(out)}')
                st.dataframe(out, hide_index=True, **STRETCH)
                st.download_button(
                    t("batch_dl"), data=out.to_csv(index=False).encode("utf-8"),
                    file_name="agrisense_batch_results.csv", mime="text/csv",
                )
        except Exception as exc:
            st.error("Could not read the file.")
            st.exception(exc)

# ============================================================
# TAB 5: MODEL INSIGHTS
# ============================================================
with tab_model:
    html(f'<div class="h2">{t("model_h")}</div><div class="sub">{t("model_s")}</div>')
    cols = [c for c in ["Algorithm", "Accuracy (%)", "Precision (%)", "Recall (%)",
                        "F1 Score (%)", "Training Time (sec)"] if c in comparison.columns]
    st.dataframe(comparison[cols], hide_index=True, **STRETCH)
    st.bar_chart(comparison.set_index("Algorithm")["Accuracy (%)"])
    st.caption(t("model_note"))
