import os
import time
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from google import genai
from PIL import Image

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# The Professional Prompt (including your improvement ideas)
SYSTEM_PROMPT = """
Analyze this exam page. 
1. Provide a SCORE (1-10) for: Clarity, Argumentation, Evidence.
2. Provide INLINE FEEDBACK for specific sentences.
3. FLUFF CHECK: Flag if the student is repeating words just to fill space.
4. BIAS CHECK: Ensure you aren't docking points for bad handwriting if the logic is sound.
"""

def grade_single_page(image_info):
    page_name, path = image_info
    print(f"🚀 Starting {page_name}...")
    img = Image.open(path)
    
    # We use the Gemini 3 model for speed
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        config={'system_instruction': SYSTEM_PROMPT},
        contents=[img]
    )
    return f"--- {page_name} REPORT ---\n{response.text}"

# List of your images
images_to_grade = [
    ("Page 1", "page1.jpg"),
    ("Page 2", "page2.jpg"),
    ("Page 3", "page3.jpg")
]

start_time = time.time()

# This is the "Magic" part that runs them all at once
with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(grade_single_page, images_to_grade))

end_time = time.time()

for report in results:
    print(report)

print(f"\n✅ TOTAL TIME: {end_time - start_time:.2f} seconds")