import firebase_admin
from firebase_admin import credentials, firestore

if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

def seed_data():
    # 1. Define Teachers
    teachers = [
        {"uid": "teacher_01", "name": "Prof. Smith", "role": "teacher"},
        {"uid": "teacher_02", "name": "Prof. Jones", "role": "teacher"}
    ]

    # 2. Define Students
    students = [
        {"uid": "student_01", "name": "Alice", "role": "student"},
        {"uid": "student_02", "name": "Bob", "role": "student"},
        {"uid": "student_03", "name": "Charlie", "role": "student"},
        {"uid": "student_04", "name": "David", "role": "student"},
        {"uid": "student_05", "name": "Eve", "role": "student"}
    ]

    print("🚀 Seeding Users...")
    for user in teachers + students:
        db.collection('users').document(user['uid']).set(user)
        print(f"✅ Created {user['role']}: {user['name']}")

if __name__ == "__main__":
    seed_data()