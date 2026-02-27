import firebase_admin
from firebase_admin import credentials, firestore

if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

def add_teacher_feedback(submission_id, teacher_text):
    print(f"👩‍🏫 Teacher Reviewing: {submission_id}...")
    
    sub_ref = db.collection('submissions').document(submission_id)
    sub_doc = sub_ref.get()

    if not sub_doc.exists:
        print("❌ Error: Submission not found.")
        return

    # Update the document with teacher's input
    sub_ref.update({
        "teacher_feedback": teacher_text,
        "status": "completed", # This is the final state
        "finalized_at": firestore.SERVER_TIMESTAMP
    })

    print(f"✅ SUCCESS: Teacher feedback added. Status set to 'completed'.")

if __name__ == "__main__":
    # Simulate teacher reviewing student_01's history task
    sub_id = "hist_task_001_student_01"
    feedback = "Good attempt. Your description of the Bhimbetka stick figures was very accurate."
    add_teacher_feedback(sub_id, feedback)