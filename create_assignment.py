import firebase_admin
from firebase_admin import credentials, firestore

if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

def create_task():
    assignment_id = "hist_task_001"
    
    task_data = {
        "assignment_id": assignment_id,
        "teacher_id": "teacher_01", # Prof. Smith
        "title": "Ancient Indian Art & Cave Paintings",
        "instructions": "Discuss the aesthetic features of Bhimbetka and Ajanta caves.",
        # The AI will use this text to verify facts
        "answer_key": """
            Key points to check:
            1. Bhimbetka: Located in Madhya Pradesh, Upper Paleolithic era. 
            2. Aesthetics: Use of white and red pigments, stick figures, hunting scenes.
            3. Ajanta: Located in Maharashtra, Buddhist themes, Jataka tales.
            4. Techniques: Fresco-secco, natural dyes, sense of movement.
        """,
        "created_at": firestore.SERVER_TIMESTAMP
    }

    print(f"📡 Uploading Assignment: {task_data['title']}...")
    db.collection('assignments').document(assignment_id).set(task_data)
    print(f"✅ SUCCESS: Assignment '{assignment_id}' created in Firestore.")

if __name__ == "__main__":
    create_task()