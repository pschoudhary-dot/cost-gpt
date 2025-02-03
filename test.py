import google.generativeai as genai
import os
 
genai.configure(api_key="yourapi")
 
models = genai.list_models()
for model in models:
    print(model.name)
