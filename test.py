import google.generativeai as genai
import os
 
genai.configure(api_key="AIzaSyCJyw6yG29DS6D0gUcIK2ah3Ji14rVMCS4")
 
models = genai.list_models()
for model in models:
    print(model.name)
