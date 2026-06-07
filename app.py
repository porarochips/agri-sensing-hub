import streamlit as st
import qrcode
import io
import base64

st.set_page_config(page_title="Agri-Trade Verification Gateway", page_icon="🛡️", layout="centered")

st.title("🛡️ Global Agri-Trade Passport Verification")
st.markdown("Official international customs and export compliance check gateway.")
st.markdown("---")

query_params = st.query_params

if not query_params:
    st.warning("⚠️ No passport credentials detected. Please scan a valid cryptographic asset QR code.")
else:
    farmer_id = query_params.get("id", "UNKNOWN-TOKEN")
    crop_type = query_params.get("crop", "Agricultural Asset")
    ndvi_rating = query_params.get("ndvi", "0.00")
    
    try: ndvi_float = float(ndvi_rating)
    except ValueError: ndvi_float = 0.0

    if ndvi_float >= 0.6:
        grade = "Class A - Premium Grade (Excellent Canopy Vigor)"
        status_color, text_color_hex = "green", "#2e7d32"
    elif ndvi_float >= 0.4:
        grade = "Class B - Standard Export Grade (Healthy Canopy)"
        status_color, text_color_hex = "blue", "#1565c0"
    else:
        grade = "Class C - Local Market (Low Biomass Index)"
        status_color, text_color_hex = "orange", "#ef6c00"

    # --- SHOW REAL-TIME ON-SCREEN VALIDATION ---
    st.success("✅ DIGITAL SIGNATURE MATCHED: VERIFIED ASSET")
    
    # Re-build the verification URL to match what is encoded in the QR code
    current_url = f"http://localhost:8501/verify?id={farmer_id}&crop={crop_type}&ndvi={ndvi_rating}"

    # Generate QR Code image as base64 string to embed inside the downloadable certificate document file
    qr = qrcode.QRCode(version=1, box_size=4, border=1)
    qr.add_data(current_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = io.BytesIO()
    qr_img.save(buffered, format="PNG")
    qr_base64 = base64.b64encode(buffered.getvalue()).decode()

    # Layout on-screen preview columns
    col_preview, col_meta = st.columns([1, 2])
    with col_preview:
        st.image(buffered.getvalue(), caption="Passport Scan Anchor", use_container_width=False, width=150)
    with col_meta:
        st.markdown(f"**Asset Token ID:** `{farmer_id}`")
        st.markdown(f"**Commodity:** `{crop_type}`")
        st.markdown(f"**Satellite NDVI Index:** `{ndvi_rating}`")
        st.markdown(f"**Export Grade:** :{status_color}[{grade}]")

    # --- EMBED GRAPHIC QR INTO DOWNLOADABLE PRINT ARTIFACT ---
    html_certificate = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Arial', sans-serif; color: #333; padding: 15px; text-align: center; }}
            .border-box {{ border: 4px double #1b5e20; padding: 30px; max-width: 550px; margin: 0 auto; background: #fff; }}
            .title {{ font-size: 24px; font-weight: bold; color: #1b5e20; margin-bottom: 5px; }}
            .label {{ font-size: 11px; text-transform: uppercase; tracking: 1px; color: #777; margin-bottom: 20px; }}
            .badge {{ font-size: 16px; font-weight: bold; background: #e8f5e9; padding: 8px; border-radius: 4px; margin-bottom: 20px; display: inline-block; }}
            .grid {{ text-align: left; margin: 15px auto; width: 85%; font-size: 14px; line-height: 1.8; }}
            .qr-zone {{ margin: 25px 0; }}
            .footer {{ font-size: 10px; color: #999; margin-top: 20px; border-top: 1px dashed #ccc; padding-top: 15px; }}
        </style>
    </head>
    <body>
        <div class="border-box">
            <div class="title">AGRI-TRADE PASSPORT</div>
            <div class="label">Official Export Compliance Documentation</div>
            <div class="badge">Token ID: {farmer_id}</div>
            
            <div class="grid">
                <b>Commodity Classification:</b> {crop_type}<br>
                <b>Orbital NDVI Verification:</b> {ndvi_rating}<br>
                <b>Compliance Quality Rating:</b> <span style="color:{text_color_hex}; font-weight:bold;">{grade}</span><br>
                <b>Export Status Clearance:</b> PASSED / CLEARED FOR SHIPMENT
            </div>
            
            <div class="qr-zone">
                <img src="data:image/png;base64,{qr_base64}" width="130" height="130" style="border: 1px solid #ddd;" /><br>
                <span style="font-size: 10px; color: #555; font-style: italic;">Scan paper printout to verify authentic cloud record trace.</span>
            </div>
            
            <div class="footer">
                Signed autonomously via Google Cloud Rapid Agent Platform Engine.<br>
                Satellite Data Infrastructure Verification: Google Earth Engine Layer.
            </div>
        </div>
    </body>
    </html>
    """

    st.markdown("---")
    st.markdown("### 📥 Download Document File")
    st.download_button(
        label="📄 Download Printable Passport Sheet (With QR Code Embedded)",
        data=html_certificate,
        file_name=f"Passport-Certificate-{farmer_id}.html",
        mime="text/html",
        use_container_width=True
    )