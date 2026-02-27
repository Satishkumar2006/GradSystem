import os, time, io, json, asyncio
from dotenv import load_dotenv
from google import genai
from google.genai import types 
from PIL import Image

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# 1. ATOMIC CONFIG: Minimal text for maximum generation speed
MODEL_CONFIG = types.GenerateContentConfig(
    system_instruction="""
    Analyze handwriting. Return ONLY JSON. feedback < 10 words.
    Keys: 
    - 'scores': { 'clarity': 1-10, 'argumentation': 1-10, 'evidence': 1-10 }
    - 'feedback': 'Actionable critique'
    - 'fluff': 'Filler location'
    - 'bias_check': 'Pass'
    - 'heatmap': { 'top': 1-10, 'middle': 1-10, 'bottom': 1-10 }
    """,
    response_mime_type="application/json"
)

def get_optimized_image(path):
    img = Image.open(path)
    if img.mode in ("RGBA", "P"): img = img.convert("RGB")
    img.thumbnail((500, 500)) 
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG', quality=40) 
    return Image.open(img_byte_arr)

async def grade_page_async(page_data):
    page_num, path = page_data
    try:
        img = get_optimized_image(path)
        response = await client.aio.models.generate_content(
            model="gemini-flash-latest", 
            config=MODEL_CONFIG,
            contents=[img]
        )
        return { "page": page_num, "data": json.loads(response.text) }
    except Exception as e:
        return { "page": page_num, "error": str(e) }

async def main():
    pages = [ (1, "page1.jpg"), (2, "page2.jpg"), (3, "page3.jpg") ] 
    print(f"🚀 FIRING ENGINE...", flush=True)
    start_time = time.time()
    
    # Process all pages simultaneously
    results = await asyncio.gather(*(grade_page_async(p) for p in pages))
    
    # --- INSTANT SUMMARY OUTPUT ---
    report_output = "\n--- ASYNC DEMO REPORT ---\n" + json.dumps(results, indent=2)
    report_output += "\n\n" + "="*40 + "\n🏆 FINAL AGGREGATED REPORT\n"
    
    total_score, count = 0, 0
    for res in results:
        if "data" in res:
            data = res["data"]
            scores = data.get("scores", {})
            vals = [float(str(v).split('/')[0]) for v in scores.values() if isinstance(scores, dict)]
            if vals:
                avg = sum(vals)/len(vals)
                total_score += avg
                count += 1
                report_output += f"Page {res['page']} Average: {avg:.1f}/10\n"

    if count > 0:
        report_output += "-" * 40 + f"\nOVERALL EXAM GRADE: {total_score / count:.1f}/10\n" + "="*40

    # Dump the entire result to terminal at once
    print(report_output, flush=True)
    print(f"\n✅ TRUE TOTAL TIME: {time.time() - start_time:.2f} seconds", flush=True)

if __name__ == "__main__":
    asyncio.run(main())