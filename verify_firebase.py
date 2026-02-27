import firebase_admin
from firebase_admin import credentials, firestore

# 1. Setup credentials using the key you downloaded
try:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("✅ SUCCESS: Firebase Admin SDK Initialized.")

    # 2. Test Write to Firestore
    test_ref = db.collection('system_check').document('status')
    test_ref.set({
        'connection': 'active',
        'message': 'Hello from Python Backend!'
    })
    print("✅ SUCCESS: Test document written to Firestore.")

    # 3. Test Read from Firestore
    doc = test_ref.get()
    print(f"✅ SUCCESS: Data read from Firebase: {doc.to_dict()}")

except Exception as e:
    print(f"❌ ERROR: Could not connect to Firebase. Details: {e}")