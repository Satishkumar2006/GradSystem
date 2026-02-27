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

def get_stars(avg_score):
    if avg_score >= 8.5: return 5
    if avg_score >= 7.0: return 4
    if avg_score >= 5.0: return 3
    return 1

async def process_pending_submissions():
    print("\n🔎 Scanning for 'pending' work...", end="", flush=True)
    query = db.collection('submissions').where(filter=FieldFilter("status", "==", "pending"))
    docs = query.get()
    
    if not docs:
        print(" (0).", end="", flush=True)
        return

    for doc in docs:
        sub = doc.to_dict()
        sub_id = doc.id
        print(f"\n🎯 Processing: {sub_id}...", flush=True)

        try:
            assign_doc = db.collection('assignments').document(sub['assignment_id']).get()
            answer_key = assign_doc.to_dict().get('answer_key', 'No key provided.')

            img_data = requests.get(sub['image_url']).content
            img = Image.open(io.BytesIO(img_data))

            # UPDATED PROMPT: Added 'Improvement Tip' mandate
            response = await client.aio.models.generate_content(
                model="gemini-2.0-flash",
                config=types.GenerateContentConfig(
                    system_instruction=(
                        f"You are a strict academic tutor. KEY: {answer_key}. "
                        "FEEDBACK RULE: Start with a brief critique, then add a section: 'TO GET REMAINING MARKS: [Actionable Tip]'. "
                        "Identify exactly what fact from the KEY is missing. "
                        "Return ONLY JSON. Heatmap 1-10. Scores 1-10 (clarity, logic). feedback < 40 words."
                    ),
                    response_mime_type="application/json"
                ),
                contents=["Analyze the work and provide a path to a 10/10 score.", img]
            )
            
            ai_data = json.loads(response.text)
            s = ai_data.get('scores', {"clarity": 0, "logic": 0})
            avg = (s['clarity'] + s['logic']) / 2
            stars = get_stars(avg)

            # Update Firestore
            db.collection('submissions').document(sub_id).update({
                "ai_score": round(avg, 1),
                "ai_feedback": ai_data.get('feedback', "Analysis complete."),
                "ai_full_json": ai_data, 
                "stars": stars,
                "status": "graded_by_ai", 
                "processed_at": firestore.SERVER_TIMESTAMP
            })
            print(f"✅ Success: {sub_id} graded {round(avg, 1)}/10", flush=True)

        except Exception as e:
            print(f"❌ Error: {e}", flush=True)

async def main():
    while True:
        await process_pending_submissions()
        await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())