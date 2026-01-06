import json
import re
import os
import streamlit as st
import google.generativeai as genai
from pptx import Presentation
from pptx.util import Inches, Pt

# --- CONFIGURATION CLÉ API ---
try:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = os.environ.get("GEMINI_API_KEY")
except:
    api_key = os.environ.get("GEMINI_API_KEY")

if api_key:
    genai.configure(api_key=api_key)

# --- CHANGEMENT ICI : ON UTILISE LE MODÈLE "PRO" (LE PLUS STABLE) ---
MODEL_NAME = "gemini-pro"

LAYOUT_MAP = { 
    "COVER": 0,      
    "SOMMAIRE": 1,   
    "SECTION": 2,    
    "CONTENT": 1,    
    "THANK_YOU": 2   
}

def clean_json_response(text):
    text = text.strip()
    # Nettoyage agressif pour trouver le JSON
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
    print(f"--- CALLING GEMINI PRO ---")
    
    if not api_key:
        return {"presentation_title": "Error", "subtitle": "API Key Missing", "slides": []}

    # Structure simplifiée pour Gemini Pro qui est parfois têtu
    json_structure = """
    {
        "presentation_title": "Titre",
        "subtitle": "Sous-titre",
        "slides": [
            { "title": "Titre Slide", "content": ["Point 1", "Point 2"] }
        ]
    }
    """
    
    prompt = f"""
    Rôle: Expert Devoteam.
    Sujet: "{content}"
    Tâche: Créer une présentation de 5 slides en Français.
    Format OBLIGATOIRE: JSON pur respectant cette structure: {json_structure}
    Important: Ne rien écrire avant ou après le JSON.
    """

    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)
        
        # On tente de nettoyer la réponse
        cleaned_text = clean_json_response(response.text)
        data = json.loads(cleaned_text)
        return data

    except Exception as e:
        print(f"ERROR: {e}")
        return { "presentation_title": "Error", "subtitle": f"Erreur IA: {str(e)}", "slides": [] }

def create_presentation_file(data, template_path="my_brand_template.pptx", output_filename="/tmp/output.pptx"):
    try: prs = Presentation(template_path)
    except: prs = Presentation() 
    
    # 1. Slide Titre
    slide = safe_add_slide(prs, LAYOUT_MAP["COVER"])
    if slide.shapes.title: slide.shapes.title.text = data.get('presentation_title', 'Devoteam AI')
    
    # 2. Slides
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
