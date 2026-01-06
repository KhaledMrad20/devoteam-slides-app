import streamlit as st
import os
# We don't need streamlit_authenticator anymore for this simple method
# from generator_logic import ... 

# --- CONNECT TO YOUR LOGIC ---
from generator_logic import generate_presentation_outline, create_presentation_file

# --- PAGE CONFIG ---
st.set_page_config(page_title="Devoteam Slide Gen", page_icon="📊", layout="centered")

# --- CUSTOM CSS (Styles) ---
css_file = "styles.css"
if os.path.exists(css_file):
    with open(css_file) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .stApp { background-color: #F5F5F5; }
        .stButton>button { background-color: #E63312; color: white; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_email' not in st.session_state:
    st.session_state['user_email'] = ''

# --- LOGIN FUNCTION ---
def check_login():
    email = st.session_state.email_input.lower().strip()
    if email.endswith("@devoteam.com"):
        st.session_state['logged_in'] = True
        st.session_state['user_email'] = email
    else:
        st.error("🚫 Access Restricted: You must use a @devoteam.com email address.")

# =========================================================
#  LOGIN SCREEN (If not logged in)
# =========================================================
if not st.session_state['logged_in']:
    # Show Logo
    image_name = "devoteam.png"
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if os.path.exists(image_name):
            st.image(image_name, use_container_width=True)
            
    st.markdown("<h2 style='text-align: center;'>Internal Slide Generator</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Please sign in with your corporate email.</p>", unsafe_allow_html=True)

    # Simple Login Form
    st.text_input("Email Address", key="email_input", placeholder="name.surname@devoteam.com")
    st.button("Sign In", on_click=check_login, type="primary")

# =========================================================
#  MAIN APP (If logged in)
# =========================================================
else:
    # Sidebar with Logout
    with st.sidebar:
        if os.path.exists("devoteam.png"):
            st.image("devoteam.png", width=150)
        st.write(f"👤 **{st.session_state['user_email']}**")
        if st.button("Logout"):
            st.session_state['logged_in'] = False
            st.rerun()

    # Header
    st.title("Devoteam AI Generator")
    st.write("Create professional slides in seconds.")
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
