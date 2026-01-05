import json
import re
import os
from google import genai
from google.genai import types
from pptx import Presentation
from pptx.util import Inches, Pt

# --- CONFIGURATION ---
# SECURITY: Get key from Environment Variable (Never hardcode in Cloud)
API_KEY = os.environ.get("GEMINI_API_KEY") 
MODEL_NAME = "gemini-1.5-flash" 

# --- LAYOUT MAP ---
LAYOUT_MAP = { 
    "COVER": 0,      # Usually 0 is Title Slide
    "SOMMAIRE": 1,   # Title and Content
    "SECTION": 2,    # Section Header
    "CONTENT": 1,    # Title and Content
    "THANK_YOU": 2   # Section Header
}

def clean_text(text):
    if not text: return "Untitled"
    text = re.sub(r'\s*\((SECTION|CONTENT|Section|Content)\)\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^\d+[\.\-\)\s]+\s*', '', text) 
    text = text.replace('**', '').replace('__', '')
    return text.strip()

def clean_json_response(text):
    text = text.strip()
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if match: return match.group(1)
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1: return text[start:end+1]
    return text

def extract_strict_sommaire(full_text):
    lines = full_text.split('\n')
    for line in lines:
        match = re.search(r'^(?:Sommaire|Plan)\s*[:\-]\s*(.*)', line, re.IGNORECASE)
        if match:
            raw_items = re.split(r'[,;]', match.group(1))
            return [clean_text(item) for item in raw_items if item.strip()]
    return []

def get_sorted_text_boxes(slide, slide_height):
    shapes = []
    try:
        for shape in slide.shapes:
            if shape.has_text_frame:
                if shape.top > (slide_height * 0.9): continue 
                shapes.append(shape)
        shapes.sort(key=lambda s: s.top)
    except: pass
    return shapes

def safe_add_slide(prs, layout_index):
    try:
        idx = layout_index if layout_index < len(prs.slide_layouts) else 1
        return prs.slides.add_slide(prs.slide_layouts[idx])
    except:
        return prs.slides.add_slide(prs.slide_layouts[0])

# --- CETTE FONCTION MANQUAIT ---
def generate_presentation_outline(content):
    print(f"--- CALLING GEMINI AI ---")
    if not API_KEY:
        return {"presentation_title": "Error", "subtitle": "Missing API Key", "slides": []}

    is_short_topic = len(content.strip()) < 150
    
    json_structure = """
    {
        "presentation_title": "The Title Here",
        "subtitle": "The Subtitle Here",
        "slides": [
            { "title": "Section Name", "content": ["Bullet 1", "Bullet 2"] }
        ]
    }
    """
    
    prompt = f"""
    You are a Devoteam Presentation Expert.
    TOPIC: "{content}"
    OUTPUT JSON STRUCTURE: {json_structure}
    INSTRUCTIONS: Create a structured presentation with 4-5 slides.
    """

    try:
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
    
    # 1. Title Slide
    slide = safe_add_slide(prs, LAYOUT_MAP["COVER"])
    if slide.shapes.title: slide.shapes.title.text = data.get('presentation_title', 'Devoteam AI')
    
    # 2. Content Slides
    for slide_data in data.get('slides', []):
        slide = safe_add_slide(prs, LAYOUT_MAP["CONTENT"])
        if slide.shapes.title: slide.shapes.title.text = slide_data.get('title', 'Slide')
        
        # Add content to body
        if len(slide.placeholders) > 1:
            tf = slide.placeholders[1].text_frame
            tf.clear()
            for point in slide_data.get('content', []):
                p = tf.add_paragraph()
                p.text = str(point)
                p.level = 0

    prs.save(output_filename)
    return output_filename
