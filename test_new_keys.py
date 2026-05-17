import google.generativeai as genai

API_KEY = "AIzaSyDcN9LLYR04McNF-veS3UVsHV-IH6nzV9I" 
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

try:
    response = model.generate_content("Hi")
    print(f"SUCCESS: {response.text}")
except Exception as e:
    print(f"FAILURE: {e}")
