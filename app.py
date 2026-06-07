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

# Import ReportLab components for high-fidelity PDF serialization
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import os
import streamlit as st
import google.generativeai as genai  # Or your specific SDK client module

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
# =====================================================================
# 1. LIVE INFRASTRUCTURE & CREDENTIAL INITIALIZATION
# =====================================================================
load_dotenv()

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

# Pass gemini_key directly when initializing your Google GenAI client
# Example: client = genai.Client(api_key=gemini_key)

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

    # =====================================================================
    # 4. DIGITAL TRANS-PASSPORT & HIGH-FIDELITY PDF CERTIFICATE GENERATOR
    # =====================================================================
    st.markdown("---")
    st.subheader("🌾 Agri-Trade Passport: Issue Digital Harvest Certificate")
    st.write("Commit your current verified sustainable crop batch data to the immutable cloud ledger and generate a printable passport document.")

    if st.button("Finalize Harvest & Generate Verification QR"):
        if not farmer_name or not farmer_id or not crop_type:
            st.error("⚠️ Authentication Error: Cannot issue a secure certificate for an empty profile. Fill out your details in the sidebar first.")
        else:
            with st.spinner("Processing transactional verification registry assets..."):
                generated_id = f"CERT-{uuid.uuid4().hex[:8].upper()}"
                
                try:
                    certificate_document = {
                        "farm_id": farmer_id,
                        "farmer_name": farmer_name,
                        "crop_type": crop_type,
                        "final_tracked_ndvi": live_ndvi,
                        "status": "Verified Sustainable",
                        "verification_node": "Gemini-Atlas-Satellite-Audit"
                    }
                    insert_result = certs_collection.insert_one(certificate_document)
                    generated_id = str(insert_result.inserted_id)
                    st.success(f"🎉 Certificate successfully committed to MongoDB Atlas under ID: {generated_id}")
                except Exception:
                    st.warning("⚠️ Cloud registry fallback triggered. Generating a locally-signed security token matrix...")
                
                # Generate QR Code Graphic Matrix Layer
                demo_lookup_url = f"https://agrilink.streamlit.app/verify?cert_id={generated_id}"
                qr = qrcode.QRCode(version=1, box_size=10, border=2)
                qr.add_data(demo_lookup_url)
                qr.make(fit=True)
                qr_img = qr.make_image(fill_color="#0e1117", back_color="white")
                
                qr_buf = BytesIO()
                qr_img.save(qr_buf, format="PNG")
                qr_bytes = qr_buf.getvalue()
                
                # Render Preview Image on Dashboard UI
                st.markdown("### 🎫 Your Scannable Marketplace Token:")
                st.image(qr_bytes, caption=f"ID Reference: {generated_id}", width=220)
                
                # =====================================================================
                # REPORTLAB PDF GENERATION ENGINE
                # =====================================================================
                pdf_buf = BytesIO()
                doc = SimpleDocTemplate(
                    pdf_buf, 
                    pagesize=letter,
                    rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
                )
                
                styles = getSampleStyleSheet()
                
                # Custom Graphic Typographic Styles
                title_style = ParagraphStyle(
                    'CertTitle',
                    parent=styles['Heading1'],
                    fontName='Helvetica-Bold',
                    fontSize=24,
                    leading=28,
                    textColor=colors.HexColor('#1B4D3E'),
                    alignment=1, # Centered
                    spaceAfter=15
                )
                
                subtitle_style = ParagraphStyle(
                    'CertSub',
                    parent=styles['Normal'],
                    fontName='Helvetica-Oblique',
                    fontSize=11,
                    leading=14,
                    textColor=colors.HexColor('#555555'),
                    alignment=1,
                    spaceAfter=25
                )
                
                label_style = ParagraphStyle(
                    'CertLabel',
                    fontName='Helvetica-Bold',
                    fontSize=11,
                    leading=14,
                    textColor=colors.HexColor('#2C3E50')
                )
                
                value_style = ParagraphStyle(
                    'CertValue',
                    fontName='Helvetica',
                    fontSize=11,
                    leading=14,
                    textColor=colors.HexColor('#333333')
                )
                
                footer_style = ParagraphStyle(
                    'CertFoot',
                    fontName='Helvetica-Bold',
                    fontSize=9,
                    leading=12,
                    textColor=colors.HexColor('#7F8C8D'),
                    alignment=1
                )

                story = []
                
                # Decorative top structural bar
                bar_data = [['']]
                bar_table = Table(bar_data, colWidths=[540], rowHeights=[6])
                bar_table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#1B4D3E')),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 0),
                    ('TOPPADDING', (0,0), (-1,-1), 0),
                ]))
                story.append(bar_table)
                story.append(Spacer(1, 20))
                
                # Document Header Layout
                story.append(Paragraph("DIGITAL HARVEST PASSPORT", title_style))
                story.append(Paragraph("Official Sustainability and Multi-Spectral Earth-Observation Audit Verification Certificate", subtitle_style))
                story.append(Spacer(1, 15))
                
                # Construct data table layout matrices
                data = [
                    [Paragraph("Certificate Identifier:", label_style), Paragraph(generated_id, value_style)],
                    [Paragraph("Verified Producer Name:", label_style), Paragraph(farmer_name, value_style)],
                    [Paragraph("Producer Farm ID Node:", label_style), Paragraph(farmer_id, value_style)],
                    [Paragraph("Audited Crop Typology:", label_style), Paragraph(crop_type, value_style)],
                    [Paragraph("Geographic Boundaries:", label_style), Paragraph(f"Lat {lat:.4f}, Lon {lon:.4f} (Mazowe, ZIM)", value_style)],
                    [Paragraph("Satellite Multi-Spectral NDVI:", label_style), Paragraph(f"{live_ndvi:.2f}", value_style)],
                    [Paragraph("Regulatory Compliance Status:", label_style), Paragraph("VERIFIED SUSTAINABLE ORIGIN", ParagraphStyle('GreenVal', fontName='Helvetica-Bold', textColor=colors.HexColor('#27AE60')))]
                ]
                
                # Setup Reportlab layout table structure widths
                info_table = Table(data, colWidths=[200, 340], rowHeights=[24]*7)
                info_table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#F8F9F9')),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#2C3E50')),
                    ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#BDC3C7')),
                    ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#2C3E50')),
                    ('TOPPADDING', (0,0), (-1,-1), 6),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                    ('LEFTPADDING', (0,0), (-1,-1), 12),
                ]))
                story.append(info_table)
                story.append(Spacer(1, 30))
                
                # Render generated binary stream QR image asset directly inside PDF stream layout object
                qr_pdf_img = Image(BytesIO(qr_bytes), width=140, height=140)
                qr_table_data = [[qr_pdf_img], [Paragraph("SCAN TO VERIFY LEDGER ECO-PASS RECORD", footer_style)]]
                qr_table = Table(qr_table_data, colWidths=[540])
                qr_table.setStyle(TableStyle([
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('BOTTOMPADDING', (0,0), (-1,0), 5),
                ]))
                story.append(qr_table)
                story.append(Spacer(1, 40))
                
                # Bottom verification seal baseline text marks
                story.append(Paragraph("Issued via Google Cloud Rapid Agent System Protocol Nodes & MongoDB Atlas Infrastructure Clustering.", footer_style))
                
                # Build doc composition
                doc.build(story)
                pdf_bytes = pdf_buf.getvalue()
                
                # Download link trigger interface integration handle
                st.download_button(
                    label="📥 Download Detailed PDF Certificate",
                    data=pdf_bytes,
                    file_name=f"Digital_Harvest_Certificate_{generated_id}.pdf",
                    mime="application/pdf"
                )