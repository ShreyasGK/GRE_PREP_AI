import json
from fastapi import FastAPI,HTTPException
import requests
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from pydantic import BaseModel
import os

app = FastAPI()
load_dotenv()

API_URL = "https://api-inference.huggingface.co/models/tiiuae/falcon-7b-instruct"
HF_TOKEN = "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"

HEADERS = {
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type": "application/json"
}

class QuestionRequest(BaseModel):
    topic: str
    difficulty: str

@app.post("/generate-question")
def generate_question(request: QuestionRequest):
    """Generates a GRE-style question based on the requested topic."""
    prompt = """Generate a GRE-style multiple-choice question on Probability.
    Strictly output JSON only, with no extra text or explanations.
    Format:
    {
      "question": "What is X?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Option A"
    }"""

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 500,  # Adjust based on model limits
            "temperature": 0.7
        }
    }

    response = requests.post(API_URL, headers=HEADERS, json=payload)

    try:
        data = response.json()
        print("Raw response:", data)  # Debugging
        
        if isinstance(data, list):
            data = data[0]  # Take the first item if it's a list
        
        generated_text = data.get("generated_text", "")

        # Attempt to extract the JSON portion
        json_start = generated_text.find("{")
        json_end = generated_text.rfind("}") + 1
        clean_json = generated_text[json_start:json_end]

        try:
            structured_output = json.loads(clean_json)  # Convert string to dict
            return structured_output  # Return parsed JSON
        except json.JSONDecodeError:
            return {"error": "Failed to parse AI response as JSON", "raw": generated_text}

    except Exception as e:
        return {"error": f"Failed to parse response: {str(e)}"}


    # try:
    #     response = requests.post(API_URL, headers=HEADERS, json=payload)
    #     response_data = response.json()

    #     if response.status_code == 200:
    #         return {"question": response_data.get("generated_text", "No question generated")}
    #     else:
    #         raise HTTPException(status_code=response.status_code, detail=response_data.get("error", "Failed to fetch question"))

    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=str(e))



@app.get("/")
def home():
    return {"message": "GRE Prep AI Backend is up and running!!!!"}