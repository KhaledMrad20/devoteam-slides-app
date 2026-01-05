import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import os

# --- CONNECT TO YOUR LOGIC ---
from generator_logic import generate_presentation_outline, create_presentation_file

# --- PAGE CONFIG ---
st.set_page_config(page_title="Devoteam Slide Gen", page_icon="📊", layout="centered")

# --- 1. LOAD YOUR CUSTOM CSS (styles.css) ---
# This looks for the file 'styles.css' in your GitHub folder
css_file = "styles.css"
if os.path.exists(css_file):
    with open(css_file) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
else:
    # If styles.css is missing, use this default basic styling
    st.markdown("""
    <style>
        .stApp { background-color: #F5F5F5; }
        .stButton>button { background-color: #E63312; color: white; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- AUTHENTICATION SETUP ---
auth_file = "auth_config.yaml"
try:
    with open(auth_file) as file:
        config = yaml.load(file, Loader=SafeLoader)
except FileNotFoundError:
    st.error(f"⚠️ Error: {auth_file} not found.")
    st.stop()

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# --- LOGIN SCREEN ---
name, auth_status, username = authenticator.login('main')

if auth_status is False:
    st.error("Username/password is incorrect")
elif auth_status is None:
    st.warning("Please enter your Devoteam credentials.")
elif auth_status:
    authenticator.logout('Logout', 'sidebar')
    
    # --- 2. SHOW YOUR IMAGE (devoteam.png) ---
    # I updated this line to match your file name exactly
    image_name = "devoteam.png" 
    
    col1, col2, col3 = st.columns([1,2,1]) # Use columns to center the logo
    with col2:
        if os.path.exists(image_name):
            st.image(image_name, use_container_width=True)
        else:
            st.warning(f"⚠️ Image '{image_name}' not found. Check GitHub filename.")
    
    # Header
    st.title("Devoteam AI Generator")
    st.write(f"**Welcome, {name}!**")
    st.divider()

    # Input Section
    topic = st.text_area("Presentation Topic", height=100)
    
    # Generate Button
    if st.button("Generate Slides 🚀", type="primary"):
        if not topic:
            st.warning("Please enter a topic first.")
        else:
            with st.spinner("AI is working..."):
                data = generate_presentation_outline(topic)
                
                if data.get("presentation_title") == "Error":
                    st.error(f"Error: {data.get('subtitle')}")
                else:
                    output_path = "/tmp/devoteam_slides.pptx"
                    template = "my_brand_template.pptx"
                    
                    if not os.path.exists(template):
                        final_file = create_presentation_file(data, output_filename=output_path)
                    else:
                        final_file = create_presentation_file(data, template_path=template, output_filename=output_path)
                    
                    st.success("✅ Success!")
                    
                    with open(final_file, "rb") as file:
                        st.download_button(
                            label="📥 Download PPTX",
                            data=file,
                            file_name="Presentation.pptx",
                            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
                        )
