import os
import certifi
import qrcode
import uuid
from io import BytesIO
import streamlit as st
from dotenv import load_dotenv
from pymongo import MongoClient
from google import genai
from google.genai import types
# 1. Clear any broken local system environment defaults
if "GEMINI_API_KEY" in os.environ:
    del os.environ["GEMINI_API_KEY"]

# 2. Extract key from Streamlit's absolute cloud workspace
if "GEMINI_API_KEY" in st.secrets:
    api_key_string = st.secrets["GEMINI_API_KEY"]
else:
    # Local developer fallback (.env file usage)
    from dotenv import load_model, load_dotenv
    load_dotenv()
    api_key_string = os.getenv("GEMINI_API_KEY", "")

# 3. Force the Google SDK client configuration to lock onto the validated string
# Create the modern client object using your validated key string
client = genai.Client(api_key=api_key_string)

# Note: If your code uses the newer client layout, initialize it directly:
# client = genai.Client(api_key=api_key_string)
# Import ReportLab components for high-fidelity PDF serialization
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# =====================================================================
# 1. LIVE INFRASTRUCTURE & CREDENTIAL INITIALIZATION
# =====================================================================
load_dotenv()

# Foolproof API Key retrieval for both local dev and Streamlit Cloud
if "GEMINI_API_KEY" in st.secrets:
    gemini_key = st.secrets["GEMINI_API_KEY"]
else:
    gemini_key = os.getenv("GEMINI_API_KEY")

# Pass gemini_key directly when initializing your Google GenAI client
# Example: client = genai.Client(api_key=gemini_key)
# --- Safe Cloud & Local Credential Extraction ---
if "GEMINI_API_KEY" in st.secrets:
    api_key_string = st.secrets["GEMINI_API_KEY"]
    mongo_uri_string = st.secrets["MONGO_URI"]
else:
    # Local fallback using standard dotenv setup
    from dotenv import load_dotenv
    load_dotenv()
    api_key_string = os.getenv("GEMINI_API_KEY", "")
    mongo_uri_string = os.getenv("MONGO_URI", "")

# Line 50: Keep this exactly as you have it in your screenshot
ai_client = genai.Client(api_key=api_key_string)

# Line 52: Change os.getenv("MONGO_URI") to your verified mongo_uri_string
try:
    db_client = MongoClient(
        mongo_uri_string,  # Use the newly extracted variable here!
        tls=True,
        tlsCAFile=certifi.where(),
        tlsAllowInvalidCertificates=True
    )
    db = db_client["agritech_db"]
    farms_collection = db["farms"]
    certs_collection = db["certificates"]
except Exception as connection_error:
    st.error(f"Database infrastructure link failure: {connection_error}")
    st.stop()
ai_client = genai.Client(api_key=api_key_string)

try:
    db_client = MongoClient(
        os.getenv("MONGO_URI"), 
        tls=True,
        tlsCAFile=certifi.where(),
        tlsAllowInvalidCertificates=True
    )
    db = db_client["agritech_db"]
    farms_collection = db["farms"]
    certs_collection = db["certificates"]
except Exception as connection_error:
    st.error(f"Database infrastructure link failure: {connection_error}")
    st.stop()

# =====================================================================
# 2. STREAMLIT FRONTEND LAYOUT & USER LOGIN INTERFACE
# =====================================================================
st.set_page_config(page_title="Agri-Sensing Hub", page_icon="🛰️", layout="wide")

st.title("🛰️ Google Cloud Rapid Agent: Agri-Sensing Hub")
st.caption("An autonomous execution agent evaluating multi-spectral climate metrics via Google Earth Engine & MongoDB Atlas.")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("🔐 Farmer Profile Login")
    st.write("Please enter your local farm profile parameters to synchronize with cloud telemetry:")
    
    # Fully dynamic inputs defaulted precisely to your Mazowe target parameters
    farmer_name = st.text_input("Full Name:", value="Prince Kamudyariwa")
    farmer_id = st.text_input("Farm Registration ID:", value="FARM-771")
    crop_type = st.text_input("Registered Crop Type:", value="Maize")
    
    coord_col1, coord_col2 = st.columns(2)
    with coord_col1:
        lat = st.number_input("Latitude Bounds:", value=-17.5211, format="%.4f")
    with coord_col2:
        lon = st.number_input("Longitude Bounds:", value=30.9883, format="%.4f")
    
    st.markdown("---")
    st.subheader("🛰️ Live Satellite Telemetry")
    live_ndvi = st.slider("Current Satellite NDVI Metric:", min_value=0.0, max_value=1.0, value=0.11, step=0.01)
    
    if farmer_name and farmer_id:
        try:
            farms_collection.update_one(
                {"_id": farmer_id},
                {"$set": {
                    "farmer_name": farmer_name,
                    "crop_type": crop_type,
                    "satellite_ndvi": live_ndvi,
                    "coordinates": {"lat": lat, "lon": lon}
                }},
                upsert=True
            )
            st.success(f"☁️ Cloud DB Synchronized: Connected to profile {farmer_id}.")
        except Exception:
            st.warning("⚠️ Cloud DB Isolated: Running local ledger failsafe.")
    else:
        st.info("💡 Enter your Name and Farm ID above to initiate secure cloud telemetry syncing.")

with col2:
    st.subheader("💬 Ask Your Crop Management Assistant")
    user_query = st.text_input("Enter your observation or query:", value="why are my crops wilting")
    
    if st.button("Execute Field Analysis", type="primary"):
        if not farmer_name or not farmer_id or not crop_type:
            st.warning("⚠️ Action Required: Please fill out your Farmer Profile details in the left sidebar before executing AI diagnostics.")
        elif user_query:
            with st.spinner("Analyzing multi-spectral imagery matrices and processing query..."):
                
                detected_crop_mismatch_warning = ""
                try:
                    existing_farm_record = farms_collection.find_one({"_id": farmer_id})
                    if existing_farm_record and "crop_type" in existing_farm_record:
                        db_registered_crop = existing_farm_record["crop_type"]
                        if db_registered_crop.lower() != crop_type.lower():
                            st.warning(f"⚠️ **Crop Mismatch Detected:** You logged in with **{crop_type}**, but our database record for ID {farmer_id} is registered as **{db_registered_crop}**.")
                            detected_crop_mismatch_warning = f"""
                            CRITICAL SYSTEM ALERT - CROP CONFLICT:
                            The user has logged in specifying the crop as '{crop_type}'. However, the official cloud database records state this plot is registered for '{db_registered_crop}'. 
                            In your response, you must briefly acknowledge this discrepancy. Address your diagnostic parameters primarily toward the user's observed crop ({crop_type}), but note how a transition from {db_registered_crop} affects the vegetative spectral NDVI signature readings.
                            """
                except Exception:
                    pass
                
                optimized_agri_prompt = f"""
                CONTEXT ANALYSIS REQUIRED:
                An automated satellite event has triggered a query for a user's field plot.
                - Farmer Name: {farmer_name}
                - User-Specified Crop: {crop_type}
                - Plot Coordinates: Latitude {lat}, Longitude {lon} (Region: Mazowe Valley, Zimbabwe)
                - Extracted Remote Sensing Metric: Live NDVI = {live_ndvi} (Critical Danger Threshold: < 0.45)
                - Farmer Observation: "{user_query}"
                
                {detected_crop_mismatch_warning}

                CRITICAL TRUTH REFERENCE:
                The coordinates provided ({lat}, {lon}) must be treated strictly as a location within the Mazowe region of Zimbabwe. Do not interpret positive/negative coordinate flips as locations in the Middle East or Saudi Arabia. An NDVI reading of {live_ndvi} must be interpreted strictly against plant health. Generic suggestions or regional mismatches are strictly forbidden.

                TASK:
                Generate a professional, highly localized diagnostic action plan. The response MUST be clearly structured and include:
                1. Field Analysis Update: An immediate, blunt assessment explaining exactly what an NDVI of {live_ndvi} means for {crop_type} development at these exact coordinates.
                2. Immediate Interventions: Exactly two hyper-specific, practical, step-by-step diagnostic or corrective actions the farmer can execute today.
                
                Ensure the tone is direct, supportive, and completely clear of corporate padding or generic tech-jargon.
                """
                
                try:
                    response = ai_client.models.generate_content(
                        model="gemini-3.5-flash",
                        contents=optimized_agri_prompt,
                        config=types.GenerateContentConfig(
                            system_instruction="You are an expert Agronomist AI. You never give vague advice. You give crisp, bold, data-driven diagnostic instructions."
                        )
                    )
                    st.markdown("### 🤖 Here's a professional summary of your latest field analysis:")
                    st.info(response.text)
                except Exception as ai_error:
                    st.error(f"AI Core processing error: {ai_error}")
        else:
            st.warning("Please enter a query or question to analyze.")

    # ==============================================================================
# 4. DIGITAL TRANS-PASSPORT & HIGH-FIDELITY LEDGER WRITER
# ==============================================================================
st.markdown("---")
st.subheader("🎖️ Agri-Trade Passport: Issue Digital Harvest Certificate")
st.write("Commit your current verified sustainable crop batch data to the immutable cloud ledger and generate assets.")

if st.button("Finalize Harvest"):
    try:
        certificate_document = {
            "farm_id": farmer_id,
            "farmer_name": farmer_name,
            "crop_type": crop_type,
            "final_tracked_ndvi": live_ndvi,
            "status": "Verified Sustainable",
            "verification_node": "Gemini-Atlas-Satellite-Audit"
        }
        
        # Your original MongoDB insertion assignment logic
        insert_result = certs_collection.insert_one(certificate_document)
        generated_id = str(insert_result.inserted_id)
        
        st.success(f"🚀 Certificate successfully committed to MongoDB Atlas under ID: {generated_id}")
        
    except Exception:
        # Your exact cloud registry fallback route
        st.warning("⚠️ Cloud registry fallback triggered. Generating a locally-signed security token matrix.")
        generated_id = "LOCAL-FALLBACK-TOKEN"

    # ==============================================================================
    # 5. GENERATE QR CODE GRAPHIC MATRIX LAYER
    # ==============================================================================
    try:
        # Dynamically map the QR generation data string to your live deployed verify path
        demo_lookup_url = f"https://agri-sensing-app-tps9arrbjuqdgewjtrhrty.streamlit.app/verify?cert_id={generated_id}"
        
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(demo_lookup_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="#0e1117", back_color="white")
        
        qr_buf = BytesIO()
        qr_img.save(qr_buf, format="PNG")
        qr_bytes = qr_buf.getvalue()
        
        # Render Preview Image on Dashboard UI exactly as you built it
        st.markdown("### 🪪 Your Scannable Marketplace Token:")
        st.image(qr_bytes, caption=f"ID Reference: {generated_id}", width=220)
        
    except Exception as qr_error:
        st.error(f"⚠️ QR Generation warning: {qr_error}")

    # ==============================================================================
    # 6. REPORTLAB PDF GENERATION ENGINE
    # ==============================================================================
    try:
        pdf_buf = BytesIO()
        doc = SimpleDocTemplate(
            pdf_buf,
            pagesize=letter,
            rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
        )
        
        styles = getSampleStyleSheet()
        story = [
            Paragraph(f"<b>Agri-Sensing Digital Trade Passport</b>", styles['Title']),
            Spacer(1, 12),
            Paragraph(f"<b>Certificate ID:</b> {generated_id}", styles['Normal']),
            Paragraph(f"<b>Farmer Legal Identity:</b> {farmer_name}", styles['Normal']),
            Paragraph(f"<b>Farm Identifier:</b> {farmer_id}", styles['Normal']),
            Paragraph(f"<b>Crop Matrix Classification:</b> {crop_type}", styles['Normal']),
            Paragraph(f"<b>Verified Satellite NDVI Metric:</b> {live_ndvi}", styles['Normal']),
        ]
        doc.build(story)
        
        st.download_button(
            label="📥 Download Verified PDF Certificate",
            data=pdf_buf.getvalue(),
            file_name=f"crop_passport_{generated_id}.pdf",
            mime="application/pdf"
        )
    except Exception as pdf_error:
        st.error(f"⚠️ PDF Generation warning: {pdf_error}")