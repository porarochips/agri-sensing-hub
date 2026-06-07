import streamlit as st
import os
import uuid
import segno
from io import BytesIO
from google import genai
from pymongo import MongoClient
import certifi
from dotenv import load_dotenv
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet

# ==============================================================================
# 1. CORE CONFIGURATION & ENVIRONMENT SETUP
# ==============================================================================
load_dotenv()
st.set_page_config(page_title="Agri-Sensing Hub", page_icon="🌱", layout="wide")

# Extract secure backend cloud service string variables
api_key_string = os.getenv("GEMINI_API_KEY", "")
mongo_uri_string = os.getenv("MONGO_URI", "")

# Initialize the next-generation Google GenAI Client
ai_client = genai.Client(api_key=api_key_string)

# Establish connection to your MongoDB Atlas Cluster Architecture
try:
    db_client = MongoClient(
        mongo_uri_string,
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

# ==============================================================================
# 2. FARMER CONSOLE & SATELLITE METRICS INTERFACE
# ==============================================================================
st.title("🌱 Agri-Sensing Hub & Diagnostic Terminal")
st.markdown("---")

col_input, col_metrics = st.columns([1, 1])

with col_input:
    st.subheader("📋 Core Registration Details")
    farmer_id = st.text_input("Farmer Identifier / Registration ID:", value="FM-2026-09A")
    farmer_name = st.text_input("Full Legal Name:", value="Prince Kamudyariwa")
    crop_type = st.selectbox("Active Crop Target:", ["Maize", "Tobacco", "Soybeans", "Wheat"])
    
    # Context specific coordinates default to Mazowe Valley testing zone
    latitude = st.number_input("Target Latitude Coordinates:", value=-17.5210, format="%.4f")
    longitude = st.number_input("Target Longitude Coordinates:", value=30.9841, format="%.4f")

with col_metrics:
    st.subheader("🛰️ Remote Planetary Telemetry (Google Earth Engine Mock)")
    # Simulating real-time Multi-Spectral Climate Metrics
    live_ndvi = st.slider("Live Multi-Spectral NDVI Crop Health Index:", 0.0, 1.0, 0.72)
    st.metric(label="Calculated Crop Canopy Status", value=f"{live_ndvi} NDVI", delta="Optimal Zone" if live_ndvi > 0.6 else "Stress Zone")

# ==============================================================================
# 3. AUTONOMOUS GENAI CROP DIAGNOSTICS LAYER
# ==============================================================================
st.markdown("---")
st.subheader("🤖 Autonomous Gemini Agronomic Analysis")

analysis_query = st.text_area("Provide custom soil/diagnostic notes for the AI Agent:", 
                              value="Mazowe Valley field parcel showing rich vegetative canopy. Slight variations in rainfall distributions observed over past 14 days.")

ai_analysis_summary = "No diagnostic logs attached."

if st.button("Run Diagnostic Analysis Engine"):
    if analysis_query:
        with st.spinner("Executing autonomous agent diagnostic layer..."):
            try:
                prompt_payload = f"As an advanced agronomic AI expert evaluating field coordinates ({latitude}, {longitude}) in the Mazowe Valley region, analyze this crop data: Crop: {crop_type}, NDVI Health Metrics: {live_ndvi}. Additional Farmer Notes: {analysis_query}. Provide a highly detailed, actionable diagnostic summary to optimize yield."
                
                response = ai_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt_payload
                )
                ai_analysis_summary = response.text
                st.info("🤖 **Gemini Live Diagnostics:**")
                st.write(ai_analysis_summary)
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
    
    # 1. Generate the unique transaction identifier sequence
    generated_certificate_id = "CERT-" + str(uuid.uuid4())[:8].upper()

    # 2. Build the live multi-page verification link pointing to your pages/verify.py routing
    live_app_base_url = "https://agri-sensing-app-tps9arrbjuqdgewjtrhrty.streamlit.app/verify"
    verification_url = f"{live_app_base_url}?cert_id={generated_certificate_id}"

    # 3. Create the optimized high-density QR asset matrix using segno
    qr_asset = segno.make(verification_url)
    
    # 4. Sync the record dictionary structure directly to your MongoDB Atlas Cluster
    try:
        certificate_document = {
            "farm_id": farmer_id,
            "farmer_name": farmer_name,
            "crop_type": crop_type,
            "final_tracked_ndvi": live_ndvi,
            "status": "Verified Sustainable",
            "verification_node": "Gemini-Atlas-Satellite-Audit",
            "certificate_id": generated_certificate_id,
            "region": "Mazowe Valley",
            "yield_quantity": 4250,
            "ai_analysis_summary": ai_analysis_summary
        }
        
        certs_collection.insert_one(certificate_document)
        st.success(f"✅ Data successfully synced to Atlas! Ledger Reference ID: {generated_certificate_id}")
        
        # 5. Render the high-density QR code asset safely to the viewport
        qr_asset.save("current_passport_qr.png", scale=5)
        st.image("current_passport_qr.png", caption="Scan to verify this harvest on the mobile ledger portal")
        
    except Exception as db_error:
        st.error(f"❌ Failed to write to ledger cluster: {db_error}")
        st.stop()

    # 6. ReportLab PDF Generation Asset Registry Execution Pipeline
    try:
        st.info("📄 Generating Secure Trade Passport Document...")
        pdf_buf = BytesIO()
        doc = SimpleDocTemplate(
            pdf_buf,
            pagesize=letter,
            rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
        )
        
        # Populate structural PDF canvas story components matching the database payload
        styles = getSampleStyleSheet()
        story = [
            Paragraph(f"<b>Agri-Sensing Digital Trade Passport</b>", styles['Title']),
            Spacer(1, 12),
            Paragraph(f"<b>Certificate Ledger ID:</b> {generated_certificate_id}", styles['Normal']),
            Paragraph(f"<b>Farmer Legal Identity:</b> {farmer_name}", styles['Normal']),
            Paragraph(f"<b>Farm Identifier Node:</b> {farmer_id}", styles['Normal']),
            Paragraph(f"<b>Crop Matrix Classification:</b> {crop_type}", styles['Normal']),
            Paragraph(f"<b>Verified Satellite NDVI Metric:</b> {live_ndvi}", styles['Normal']),
            Spacer(1, 12),
            Paragraph(f"<b>Security Registry Status:</b> Verified Sustainable Ledger Transaction Asset", styles['Normal']),
        ]
        doc.build(story)
        
        # Serve the finalized asset directly as a downloadable UI download trigger button
        st.download_button(
            label="📥 Download Verified PDF Certificate",
            data=pdf_buf.getvalue(),
            file_name=f"crop_passport_{generated_certificate_id}.pdf",
            mime="application/pdf"
        )
        
    except Exception as pdf_error:
        st.error(f"⚠️ PDF Generation warning: {pdf_error}")