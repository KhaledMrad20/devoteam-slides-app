import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import os

# --- CONNECT TO YOUR LOGIC ---
from generator_logic import generate_presentation_outline, create_presentation_file

# --- PAGE CONFIG ---
st.set_page_config(page_title="Devoteam Slide Gen", page_icon="📊", layout="centered")

# --- CUSTOM CSS FOR DEVOTEAM BRANDING ---
st.markdown("""
<style>
    /* 1. Main Background Color (Light Grey) */
    .stApp {
        background-color: #F5F5F5;
    }
    
    /* 2. Style the Buttons (Devoteam Red color) */
    .stButton>button {
        color: white;
        background-color: #E63312; /* Devoteam Red */
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #B3240B; /* Darker Red on hover */
        color: white;
        border: none;
    }

    /* 3. Customize Input Box */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: white;
        border: 1px solid #ddd;
        border-radius: 8px;
    }

    /* 4. Hide Streamlit Default Menu & Footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- AUTHENTICATION SETUP ---
auth_file = "auth_config.yaml"
try:
    with open(auth_file) as file:
        config = yaml.load(file, Loader=SafeLoader)
except FileNotFoundError:
    st.error(f"⚠️ Error: {auth_file} not found. Please create it in Step 3.")
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
    # =========================================================
    #  LOGGED IN AREA - THIS IS THE APP CONSULTANTS SEE
    # =========================================================
    authenticator.logout('Logout', 'sidebar')
    
    # Header
    st.title("Devoteam AI Generator")
    st.markdown(f"**Welcome, {name}!** Create professional slides in seconds.")
    st.divider()

    # Input Section
    topic = st.text_area(
        "Presentation Topic", 
        height=100, 
        placeholder="e.g. Cloud Migration Strategy for a Banking Client in France..."
    )
    
    # Generate Button
    if st.button("Generate Slides 🚀", type="primary"):
        if not topic:
            st.warning("Please enter a topic first.")
        else:
            with st.spinner("Consulting AI is thinking... (This usually takes 20-40 seconds)"):
                
                # 1. Call the Brain (generator_logic.py)
                data = generate_presentation_outline(topic)
                
                # Check for errors in the logic
                if data.get("presentation_title") == "Error":
                    st.error(f"Generation Failed: {data.get('subtitle')}")
                else:
                    # 2. Create the File
                    # We use /tmp/ because Cloud Run is read-only elsewhere
                    output_path = "/tmp/devoteam_slides.pptx"
                    
                    # Ensure template exists, or it will use blank
                    template = "my_brand_template.pptx"
                    if not os.path.exists(template):
                        st.warning("⚠️ Template file not found. Using blank style.")
                    
                    final_file = create_presentation_file(data, template_path=template, output_filename=output_path)
                    
                    # 3. Success & Download
                    st.success("✅ Slides generated successfully!")
                    
                    with open(final_file, "rb") as file:
                        st.download_button(
                            label="📥 Download PowerPoint (.pptx)",
                            data=file,
                            file_name="Devoteam_Presentation.pptx",
                            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
                        )
                    
                    # 4. Preview (Optional: Show the plan)
                    with st.expander("View Generated Plan"):
                        st.json(data)
