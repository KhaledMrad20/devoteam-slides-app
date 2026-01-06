import json
import re
import os
import streamlit as st
import google.generativeai as genai # <--- ANCIENNE LIBRAIRIE (PLUS STABLE)
from pptx import Presentation
from pptx.util import Inches, Pt

# --- CONFIGURATION DE LA CLÉ ---
try:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = os.environ.get("GEMINI_API_KEY")
except:
    api_key = os.environ.get("GEMINI_API_KEY")

# Configuration globale de l'API
if api_key:
    genai.configure(api_key=api_key)

# --- CHOIX DU MODÈLE (VERSION STABLE) ---
MODEL_NAME = "gemini-1.5-flash"

LAYOUT_MAP = { 
    "COVER": 0,      
    "SOMMAIRE": 1,   
    "SECTION": 2,    
    "CONTENT": 1,    
    "THANK_YOU": 2   
}

def clean_json_response(text):
    text = text.strip()
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if match: return match.group(1)
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1: return text[start:end+1]
    return text

def safe_add_slide(prs, layout_index):
    try:
        idx = layout_index if layout_index < len(prs.slide_layouts) else 1
        return prs.slides.add_slide(prs.slide_layouts[idx])
    except:
        return prs.slides.add_slide(prs.slide_layouts[0])

def generate_presentation_outline(content):
    print(f"--- CALLING GEMINI AI (LEGACY LIB) ---")
    
    if not api_key:
        return {"presentation_title": "Error", "subtitle": "API Key Missing", "slides": []}

    json_structure = """
    {
        "presentation_title": "Title",
        "subtitle": "Subtitle",
        "slides": [
            { "title": "Slide Title", "content": ["Point 1", "Point 2"] }
        ]
    }
    """
    
    prompt = f"""
    You are a Devoteam Presentation Expert.
    TOPIC: "{content}"
    OUTPUT JSON STRUCTURE: {json_structure}
    INSTRUCTIONS: Create a structured presentation with 4-6 slides in French.
    """

    try:
        # Initialisation du modèle version 'GenerativeModel'
        model = genai.GenerativeModel(MODEL_NAME)
        
        # Appel API
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json"
            )
        )
        
        data = json.loads(clean_json_response(response.text))
        return data

    except Exception as e:
        print(f"ERROR: {e}")
        # Fallback si le modèle JSON natif échoue (parfois le cas sur les vieux comptes)
        return { "presentation_title": "Error", "subtitle": str(e), "slides": [] }

def create_presentation_file(data, template_path="my_brand_template.pptx", output_filename="/tmp/output.pptx"):
    try: prs = Presentation(template_path)
    except: prs = Presentation() 
    
    # 1. Slide Titre
    slide = safe_add_slide(prs, LAYOUT_MAP["COVER"])
    if slide.shapes.title: slide.shapes.title.text = data.get('presentation_title', 'Devoteam AI')
    
    # 2. Slides Contenu
    for slide_data in data.get('slides', []):
        slide = safe_add_slide(prs, LAYOUT_MAP["CONTENT"])
        if slide.shapes.title: slide.shapes.title.text = slide_data.get('title', 'Slide')
        
        if len(slide.placeholders) > 1:
            tf = slide.placeholders[1].text_frame
            tf.clear()
            for point in slide_data.get('content', []):
                p = tf.add_paragraph()
                p.text = str(point)

    prs.save(output_filename)
    return output_filename
