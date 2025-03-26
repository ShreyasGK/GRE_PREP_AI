from fastapi import FastAPI
from dotenv import load_dotenv
from pydantic import BaseModel
from openai import OpenAI
from typing import Dict
import os

app = FastAPI()

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

class QuestionRequest(BaseModel):
    topic: str  # e.g., "Probability"
    difficulty: str  # e.g., "easy", "medium", "hard"

@app.post("/generate-question")
def generate_question(request: QuestionRequest):
    prompt = f"""
    Generate a GRE-style {request.difficulty} level question on {request.topic}. 
    Provide five answer choices (A-E), the correct answer, and a detailed explanation.
    Format the output as:
    {{
        "question": "Question text here",
        "choices": {{
            "A": "Option A",
            "B": "Option B",
            "C": "Option C",
            "D": "Option D",
            "E": "Option E"
        }},
        "correct_answer": "A",
        "explanation": "Detailed explanation of the correct answer."
    }}
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        store=True,
        messages=[{"role": "system", "content": prompt}]
    )

    question_text = response.choices[0].message
    
    return {"question": question_text}



class AnswerRequest(BaseModel):
    question: str
    choices: Dict[str, str]
    correct_answer: str
    user_answer: str

@app.post("/evaluate-answer")
def evaluate_answer(request: AnswerRequest):
    if request.user_answer.upper() == request.correct_answer:
        return {"correct": True, "message": "Correct! Well done!"}
    else:
        return {
            "correct": False,
            "message": f"Incorrect. The correct answer is {request.correct_answer}.",
            "explanation": request.choices.get(request.correct_answer, "No explanation available.")
        }



@app.get("/")
def home():
    return {"message": "GRE Prep AI Backend is up and running!!!!"}
