import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Error: Could not find GEMINI_API_KEY in the .env file!")
else:
    client = genai.Client(api_key=api_key)

    print("--- Listing All Available Models ---")
    try:
        # This asks Google for a list of all models you can use
        for model in client.models.list():
            # We only care about models that can 'generateContent'
            if 'generateContent' in model.supported_actions:
                print(f"✅ Model Name: {model.name}")
    except Exception as e:
        print(f"❌ Error listing models: {e}")