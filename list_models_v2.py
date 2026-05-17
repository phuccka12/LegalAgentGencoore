import google.generativeai as genai

API_KEY = "AIzaSyDcN9LLYR04McNF-veS3UVsHV-IH6nzV9I" 
genai.configure(api_key=API_KEY)

for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)
