import os, json, time, io, requests, asyncio
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from google import genai
from google.genai import types
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()
print(f"✅ CONNECTED TO: {firebase_admin.get_app().project_id}", flush=True)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

async def process_submissions():
    print("\n🔎 Scanning for 'pending' documents...", end="", flush=True)
    query = db.collection('submissions').where(filter=FieldFilter("status", "==", "pending"))
    docs = query.get()
    
    if not docs:
        print(" (Found 0).", end="", flush=True)
        return

    print(f"\n🎯 Found {len(docs)} document(s).")

    for doc in docs:
        sub_id = doc.id
        sub = doc.to_dict()
        # PRINTING THE PENDING TASK ID
        print(f"📝 STARTING SUBMISSION ID: {sub_id}", flush=True)

        try:
            # 1. Fetch Assignment Data
            assign_doc = db.collection('assignments').document(sub['assignment_id']).get()
            a_data = assign_doc.to_dict()
            
            text_key = a_data.get('answer_key', '').strip()
            pdf_url = a_data.get('reference_url', '').strip()
            
            # THE GROUNDING LOGIC: Prioritize PDF if text key is missing
            grading_context = f"TEXT KEY: {text_key if text_key else 'NONE'}. "
            if pdf_url:
                grading_context += f"MANDATORY QUESTION BANK (PDF): {pdf_url}"

            img_data = requests.get(sub['image_url']).content
            img = Image.open(io.BytesIO(img_data))

            # 2. THE STRICTOR PROMPT
            response = await client.aio.models.generate_content(
                model="gemini-flash-latest",
                config=types.GenerateContentConfig(
                    system_instruction=(
                        f"You are a Senior Academic Examiner. CONTEXT: {grading_context}. "
                        "ZERO-TOLERANCE RELEVANCE RULES: "
                        "1. Does this handwriting answer a question found in the provided CONTEXT (PDF or Text Key)? "
                        "2. IF NO (Irrelevant topic): You MUST award 0/10 for all scores and explain the mismatch. "
                        "3. IF YES: Grade technical accuracy against the context. "
                        "4. RETURN ONLY VALID JSON: scores{{clarity, logic}}, heatmap{{top, middle, bottom}}, feedback."
                    ),
                    response_mime_type="application/json"
                ),
                contents=["Evaluate this work strictly against the Question Bank and context provided.", img]
            )
            
            raw = json.loads(response.text)
            
            # --- TYPE GUARD: FIXES 'list' has no attribute 'get' ---
            scores = raw.get('scores', {})
            if isinstance(scores, list):
                print(f"   ⚠️ Warning: Gemini returned scores as a list. Converting...")
                scores = {
                    "clarity": scores[0] if len(scores) > 0 else 0,
                    "logic": scores[1] if len(scores) > 1 else 0
                }
            
            heatmap = raw.get('heatmap', {})
            if isinstance(heatmap, list):
                print(f"   ⚠️ Warning: Gemini returned heatmap as a list. Converting...")
                heatmap = {
                    "top": heatmap[0] if len(heatmap) > 0 else 0,
                    "middle": heatmap[1] if len(heatmap) > 1 else 0,
                    "bottom": heatmap[2] if len(heatmap) > 2 else 0
                }
            # -------------------------------------------------------

            avg = (scores.get('clarity', 0) + scores.get('logic', 0)) / 2
            
            db.collection('submissions').document(sub_id).update({
                "ai_score": round(avg, 1),
                "ai_feedback": raw.get('feedback', "Analysis complete."),
                "ai_full_json": {
                    "scores": scores,
                    "heatmap": heatmap,
                    "feedback": raw.get('feedback', "")
                }, 
                "stars": 5 if avg >= 8.5 else (4 if avg >= 7 else (3 if avg >= 1 else 1)),
                "status": "graded_by_ai", 
                "processed_at": firestore.SERVER_TIMESTAMP
            })
            print(f"   ✅ SUCCESS: {sub_id} graded {round(avg, 1)}/10", flush=True)

        except Exception as e:
            print(f"   ❌ ERROR for {sub_id}: {e}", flush=True)

async def main():
    while True:
        await process_submissions()
        await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())