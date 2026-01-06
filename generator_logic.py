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

# --- 2. LE MEILLEUR MODÈLE UNIQUE ---
# C'est la version stable et rapide standard
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
    print(f"--- CALLING GEMINI 1.5 FLASH (SINGLE) ---")
    
    if not API_KEY:
        return {"presentation_title": "Error", "subtitle": "API Key Missing", "slides": []}

    json_structure = """
    {
        "presentation_title": "Titre Présentation",
        "subtitle": "Sous-titre",
        "slides": [
            { "title": "Titre Slide", "content": ["Point 1", "Point 2", "Point 3"] }
        ]
    }
    """
    
    prompt = f"""
    Rôle: Expert Consultant Devoteam.
    Sujet: "{content}"
    Tâche: Générer une structure de présentation PowerPoint (5-6 slides) en Français.
    Format de sortie: JSON uniquement respectant cette structure: {json_structure}
    """

    try:
        # Initialisation du client avec la nouvelle librairie
        client = genai.Client(api_key=API_KEY)
        
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        
        data = json.loads(clean_json_response(response.text))
        return data

    except Exception as e:
        error_msg = str(e)
        print(f"ERROR: {error_msg}")
        
        # Gestion des messages d'erreur pour vous aider
        if "404" in error_msg:
            subtitle = "Erreur 404: La clé API est valide mais le projet Google n'a pas accès au modèle. Solution: Créez une nouvelle clé dans un 'New Project'."
        elif "429" in error_msg:
            subtitle = "Erreur 429: Quota dépassé. Créez une nouvelle clé API dans un 'New Project' pour remettre le compteur à zéro."
        else:
            subtitle = f"Erreur technique: {error_msg}"
            
        return { "presentation_title": "Error", "subtitle": subtitle, "slides": [] }

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
