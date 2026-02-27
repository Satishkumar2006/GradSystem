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
    # SCANNING: Instant retrieval of pending docs
    query = db.collection('submissions').where(filter=FieldFilter("status", "==", "pending"))
    docs = query.get()
    
    if not docs:
        return

    print(f"\n⚡ DETECTED {len(docs)} NEW SUBMISSION(S). GRADING NOW...", flush=True)

    for doc in docs:
        sub_id = doc.id
        sub = doc.to_dict()
        print(f"📝 ACTIVE TASK ID: {sub_id}", flush=True)

        try:
            # 1. FETCH CONTEXT: Question Bank & Key
            assign_doc = db.collection('assignments').document(sub['assignment_id']).get()
            a_data = assign_doc.to_dict()
            
            text_key = a_data.get('answer_key', '').strip()
            pdf_url = a_data.get('reference_url', '').strip()
            
            grading_context = f"TEXT KEY: {text_key if text_key else 'NONE'}. "
            if pdf_url:
                grading_context += f"MANDATORY PDF QUESTIONS: {pdf_url}"

            img_data = requests.get(sub['image_url']).content
            img = Image.open(io.BytesIO(img_data))

            # 2. HARD RELEVANCE PROMPT: Fixes the Medical-for-Computer bug
            response = await client.aio.models.generate_content(
                model="gemini-flash-latest",
                config=types.GenerateContentConfig(
                    system_instruction=(
                        f"Subject Expert Examiner. CONTEXT: {grading_context}. "
                        "ZERO-TOLERANCE RULES: "
                        "1. RELEVANCE: Is this work about the topic in the CONTEXT? If it's Medical for a Computer task, you MUST score 0. "
                        "2. RUBRIC (1-100): concept, clarity, argumentation, evidence, relevance. "
                        "3. RETURN JSON ONLY: scores{{concept, clarity, argumentation, evidence, relevance}}, "
                        "heatmap{{top, middle, bottom}} (1-10), feedback."
                    ),
                    response_mime_type="application/json"
                ),
                contents=["Verify relevance and technical accuracy against the context provided.", img]
            )
            
            raw = json.loads(response.text)
            s = raw.get('scores', {})

            # TYPE GUARD: Robust mapping for Pentagon Chart
            if isinstance(s, list):
                s = {"concept": s[0], "clarity": s[1], "argumentation": s[2], "evidence": s[3], "relevance": s[4]}
            
            final_scores = {k: s.get(k, 0) for k in ["concept", "clarity", "argumentation", "evidence", "relevance"]}
            avg_10 = round(sum(final_scores.values()) / 50, 1)

            # Update Firestore
            db.collection('submissions').document(sub_id).update({
                "ai_score": avg_10,
                "ai_feedback": raw.get('feedback', ""),
                "ai_full_json": {"scores": final_scores, "heatmap": raw.get('heatmap'), "feedback": raw.get('feedback')},
                "stars": 5 if avg_10 >= 8.5 else (4 if avg_10 >= 7 else (3 if avg_10 >= 1 else 1)),
                "status": "graded_by_ai",
                "processed_at": firestore.SERVER_TIMESTAMP
            })
            print(f"✅ SUCCESS: Graded {sub_id} as {avg_10}/10\n", flush=True)

        except Exception as e:
            print(f"❌ ERROR for {sub_id}: {e}", flush=True)

async def main():
    while True:
        await process_submissions()
        await asyncio.sleep(0.5) # REDUCED FOR SPEED

if __name__ == "__main__":
    asyncio.run(main())