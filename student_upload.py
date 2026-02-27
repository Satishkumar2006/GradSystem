import firebase_admin
from firebase_admin import credentials, storage, firestore
import datetime

# Initialize Firebase with Storage Bucket URL
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    # Replace 'YOUR_PROJECT_ID' with your actual Firebase Project ID
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'grad-system-4a6fe.firebasestorage.app' 
    })

db = firestore.client()
bucket = storage.bucket()

def upload_answer(student_id, assignment_id, file_path):
    # 1. Upload the file to Firebase Storage
    blob_path = f"submissions/{assignment_id}/{student_id}.jpg"
    blob = bucket.blob(blob_path)
    
    print(f"📤 Uploading {file_path} to Cloud Storage...")
    blob.upload_from_filename(file_path)
    
    # 2. Make the file public so Gemini can see it (for hackathon ease)
    blob.make_public()
    image_url = blob.public_url

    # 3. Create a Submission Record in Firestore
    submission_id = f"{assignment_id}_{student_id}"
    submission_data = {
        "submission_id": submission_id,
        "assignment_id": assignment_id,
        "student_id": student_id,
        "image_url": image_url,
        "status": "pending", # AI hasn't graded it yet
        "ai_score": None,
        "ai_feedback": None,
        "teacher_feedback": None,
        "stars": 0,
        "submitted_at": firestore.SERVER_TIMESTAMP
    }

    db.collection('submissions').document(submission_id).set(submission_data)
    print(f"✅ SUCCESS: Submission record created for {student_id}.")
    print(f"🔗 Image URL: {image_url}")

if __name__ == "__main__":
    # Ensure page1.jpg exists in your folder!
    upload_answer("student_01", "hist_task_001", "page1.jpg")