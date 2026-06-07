import streamlit as st
import os
from pymongo import MongoClient
import certifi
from dotenv import load_dotenv

# 1. Load environment variables for local testing fallback
load_dotenv()
mongo_uri_string = os.getenv("MONGO_URI", "")

# 2. Establish connection to your MongoDB Cluster
try:
    db_client = MongoClient(
        mongo_uri_string,
        tls=True,
        tlsCAFile=certifi.where(),
        tlsAllowInvalidCertificates=True
    )
    db = db_client["agritech_db"]
    certs_collection = db["certificates"]
except Exception as connection_error:
    st.error(f"Database connection failure: {connection_error}")
    st.stop()

# 3. Intercept the Query Parameter from the QR Code Link
query_params = st.query_params

st.title("🛡️ Agri-Sensing Verification Portal")

if "cert_id" in query_params:
    target_cert_id = query_params["cert_id"]
    st.subheader(f"Ledger Reference: {target_cert_id}")
    st.divider()
    
    # Query MongoDB for this specific batch matching your certificate key
    with st.spinner("Querying immutable secure ledger..."):
        verified_batch = certs_collection.find_one({"certificate_id": target_cert_id})
        
    if verified_batch:
        st.success("✅ Authentic Crop Batch Record Verified")
        
        # Display the metrics beautifully
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Crop Type", verified_batch.get("crop_type", "N/A"))
            st.metric("Farm Identifier", verified_batch.get("farm_id", "N/A"))
        with col2:
            st.metric("Region / Zone", verified_batch.get("region", "Mazowe Valley"))
            st.metric("Harvest Volume", f"{verified_batch.get('yield_quantity', '0')} KG")
            
        st.info("🤖 **Gemini AI Diagnostic Summary:**")
        st.write(verified_batch.get("ai_analysis_summary", "No diagnostic logs attached."))
    else:
        st.error(f"❌ Record Lookup Error: Certificate ID '{target_cert_id}' could not be found.")
else:
    st.info("👋 Welcome to the Verification Gateway. Scan a crop passport QR code to verify inventory metrics live.")