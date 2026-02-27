import firebase_admin
from firebase_admin import credentials, firestore

if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

def view_report(submission_id):
    doc = db.collection('submissions').document(submission_id).get()
    data = doc.to_dict()

    print("\n" + "⭐" * 10 + " FINAL ANALYTICAL REPORT " + "⭐" * 10)
    print(f"Student ID: {data['student_id']}")
    print(f"Overall Grade: {data['ai_score']}/10")
    print(f"Rating: {'★' * data['stars']}{'☆' * (5 - data['stars'])}")
    print("-" * 45)
    print(f"🤖 AI FEEDBACK: {data['ai_feedback']}")
    print(f"👩‍🏫 TEACHER FEEDBACK: {data['teacher_feedback']}")
    print("-" * 45)
    
    # Visualizing the Heatmap from the stored JSON
    heatmap = data['ai_full_json']['heatmap']
    print("📈 CONTENT DENSITY ANALYSIS:")
    print(f"  [Top Section]:    {heatmap['top']}/10")
    print(f"  [Middle Section]: {heatmap['middle']}/10")
    print(f"  [Bottom Section]: {heatmap['bottom']}/10")
    print("=" * 45)

if __name__ == "__main__":
    view_report("hist_task_001_student_01")