import json
import re
import os
import streamlit as st  # <--- INDISPENSABLE POUR LIRE LES SECRETS
from google import genai
from google.genai import types
from pptx import Presentation
from pptx.util import Inches, Pt

# --- CONFIGURATION DE LA CLÉ ---
# Cette partie cherche la clé directement dans le coffre-fort Streamlit
try:
    if "GEMINI_API_KEY" in st.secrets:
        API_KEY = st.secrets["GEMINI_API_KEY"]
    else:
        # Fallback pour test local si besoin
        API_KEY = os.environ.get("GEMINI_API_KEY")
except FileNotFoundError:
    # Si on n'est pas sur Streamlit Cloud
    API_KEY = os.environ.get("GEMINI_API_KEY")

MODEL_NAME = "gemini-1.5-flash" 

# --- CONFIGURATION DU LAYOUT PPTX ---
LAYOUT_MAP = { 
    "COVER": 0,      
    "SOMMAIRE": 1,   
    "SECTION": 2,    
    "CONTENT": 1,    
    "THANK_YOU": 2   
}

def clean_text(text):
    if not text: return "Untitled"
    # Nettoyage des balises Markdown
    text = re.sub(r'\s*\((SECTION|CONTENT|Section|Content)\)\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^\d+[\.\-\)\s]+\s*', '', text) 
    text = text.replace('**', '').replace('__', '')
    return text.strip()

def clean_json_response(text):
    text = text.strip()
    # Extraction du JSON si l'IA met des balises ```json ... ```
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

# --- FONCTION PRINCIPALE ---
def generate_presentation_outline(content):
    print(f"--- CALLING GEMINI AI ---")
    
    # Vérification ultime de la clé
    if not API_KEY:
        return {
            "presentation_title": "Error", 
            "subtitle": "API Key Missing. Please check Streamlit Secrets.", 
            "slides": []
        }

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
        # On passe la clé explicitement au client
        client = genai.Client(api_key=API_KEY)
        
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        
        raw_text = clean_json_response(response.text)
        data = json.loads(raw_text)
        data['original_text'] = content
        return data

    except Exception as e:
        print(f"ERROR: {e}")
        return { "presentation_title": "Error", "subtitle": str(e), "slides": [] }

def create_presentation_file(data, template_path="my_brand_template.pptx", output_filename="/tmp/output.pptx"):
    print(f"--- GENERATING PPTX ---")
    try: 
        prs = Presentation(template_path)
    except: 
        prs = Presentation() 
    
    # 1. Slide de Titre
    slide = safe_add_slide(prs, LAYOUT_MAP["COVER"])
    if slide.shapes.title: 
        slide.shapes.title.text = data.get('presentation_title', 'Devoteam AI')
    
    # 2. Slides de Contenu
    for slide_data in data.get('slides', []):
        slide = safe_add_slide(prs, LAYOUT_MAP["CONTENT"])
        if slide.shapes.title: 
            slide.shapes.title.text = slide_data.get('title', 'Slide')
        
        # Ajout du texte
        if len(slide.placeholders) > 1:
            tf = slide.placeholders[1].text_frame
            tf.clear()
            for point in slide_data.get('content', []):
                p = tf.add_paragraph()
                p.text = str(point)
                p.level = 0

    prs.save(output_filename)
    return output_filename
