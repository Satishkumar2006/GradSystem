import os
import time
import io
from dotenv import load_dotenv
from google import genai
from PIL import Image

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def get_optimized_image(path):
    img = Image.open(path)
    
    # FIX: Convert to RGB to remove the 'A' (Alpha/Transparency) channel
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    
    img.thumbnail((1024, 1024))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG', quality=70)
    return Image.open(img_byte_arr)

# Updated CONFIG for 1.5-Flash
# ULTRA-FAST CONFIG for 2-3 pages
CONFIG = {
    'system_instruction': """
    FAST MODE: Analyze this exam page instantly. 
    Return ONLY a JSON object. Keep text under 15 words per field.
    Keys: 
    - 'scores': { 'clarity': 1-10, 'argumentation': 1-10, 'evidence': 1-10 }
    - 'feedback': 'One punchy sentence'
    - 'fluff': 'Yes/No'
    - 'bias_check': 'Pass'
    - 'heatmap': [1, 5, 10] (Strength of top 3 sections)
    """,
    'response_mime_type': 'application/json'
}
def fast_grade(image_path):
    print(f"⚡ Optimizing and sending {image_path}...")
    img = get_optimized_image(image_path)
    
    # Using the exact name from your 'list_models' output
    # This is the most stable version for the Free Tier
    response = client.models.generate_content(
        model="gemini-flash-latest", 
        config=CONFIG,
        contents=[img]
    )
    return response.text

start = time.time()
result = fast_grade("page1.jpg")
print(f"\n✅ REPORT: {result}")
print(f"⏱️ TIME TAKEN: {time.time() - start:.2f} seconds")