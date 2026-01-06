import json
import re
import os
import streamlit as st
from google import genai
from google.genai import types
from pptx import Presentation

# --- 1. RÉCUPÉRATION DE LA CLÉ ---
try:
    if "GEMINI_API_KEY" in st.secrets:
        API_KEY = st.secrets["GEMINI_API_KEY"]
    else:
        API_KEY = os.environ.get("GEMINI_API_KEY")
except:
    API_KEY = os.environ.get("GEMINI_API_KEY")

# --- 2. MODÈLE UNIQUE (POUR ÉCONOMISER LE QUOTA) ---
# On vise uniquement le modèle Flash standard qui a le plus gros quota gratuit
MODEL_NAME = "gemini-1.5-flash"

LAYOUT_MAP = { 
    "COVER": 0, "SOMMAIRE": 1, "SECTION": 2, "CONTENT": 1, "THANK_YOU": 2   
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
    print(f"--- CALLING GEMINI 1.5 FLASH (SINGLE CALL) ---")
    
    if not API_KEY:
        return {"presentation_title": "Error", "subtitle": "API Key Missing", "slides": []}

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
    Rôle: Expert Devoteam. Sujet: "{content}".
    Tâche: Créer une présentation de 5 slides en Français.
    Format JSON OBLIGATOIRE: {json_structure}
    """

    try:
        client = genai.Client(api_key=API_KEY)
        
        # Appel unique (1 seul crédit utilisé)
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        
        data = json.loads(clean_json_response(response.text))
        return data

    except Exception as e:
        print(f"ERROR: {e}")
        return { 
            "presentation_title": "Error", 
            "subtitle": f"Erreur ou Quota dépassé. Attendez 1 minute. Détail: {str(e)}", 
            "slides": [] 
        }

def create_presentation_file(data, template_path="my_brand_template.pptx", output_filename="/tmp/output.pptx"):
    try: prs = Presentation(template_path)
    except: prs = Presentation() 
    
    slide = safe_add_slide(prs, LAYOUT_MAP["COVER"])
    if slide.shapes.title: slide.shapes.title.text = data.get('presentation_title', 'Devoteam AI')
    
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
