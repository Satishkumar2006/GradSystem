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
    print("\n🔎 Scanning for 'pending' work...", end="", flush=True)
    query = db.collection('submissions').where(filter=FieldFilter("status", "==", "pending"))
    docs = query.get()
    
    if not docs:
        print(" (0).", end="", flush=True)
        return

    for doc in docs:
        sub_id = doc.id
        print(f"\n🎯 Processing ID: {sub_id}...", flush=True)
        sub = doc.to_dict()

        try:
            assign_doc = db.collection('assignments').document(sub['assignment_id']).get()
            answer_key = assign_doc.to_dict().get('answer_key', 'No key provided.')

            img_data = requests.get(sub['image_url']).content
            img = Image.open(io.BytesIO(img_data))

            response = await client.aio.models.generate_content(
                model="gemini-flash-latest",
                config=types.GenerateContentConfig(
                    system_instruction=(
                        f"Subject Expert. KEY: {answer_key}. "
                        "Return ONLY JSON: scores{{clarity, logic}}, heatmap{{top, middle, bottom}}, feedback."
                    ),
                    response_mime_type="application/json"
                ),
                contents=["Grade this work strictly. Improvement tips in feedback.", img]
            )
            
            # FIXED TYPE CHECKING
            raw = json.loads(response.text)
            
            # Fix for 'list' error
            scores = raw.get('scores', {})
            if isinstance(scores, list):
                scores = {"clarity": scores[0], "logic": scores[1]}
            
            heatmap = raw.get('heatmap', {})
            if isinstance(heatmap, list):
                heatmap = {"top": heatmap[0], "middle": heatmap[1], "bottom": heatmap[2]}

            avg = (scores.get('clarity', 0) + scores.get('logic', 0)) / 2
            
            db.collection('submissions').document(sub_id).update({
                "ai_score": round(avg, 1),
                "ai_feedback": raw.get('feedback', "Processed."),
                "ai_full_json": {"scores": scores, "heatmap": heatmap, "feedback": raw.get('feedback')}, 
                "stars": 5 if avg >= 8.5 else (4 if avg >= 7 else 3),
                "status": "graded_by_ai", 
                "processed_at": firestore.SERVER_TIMESTAMP
            })
            print(f"✅ SUCCESS: {sub_id} graded {round(avg, 1)}/10", flush=True)

        except Exception as e:
            print(f"❌ Error: {e}", flush=True)

async def main():
    while True:
        await process_submissions()
        await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())