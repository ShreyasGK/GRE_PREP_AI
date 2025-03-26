import json
from fastapi import FastAPI
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI()

class QuestionRequest(BaseModel):
    topic: str  
    difficulty: str  

class AnswerRequest(BaseModel):
    question: str
    choices: list[str]
    correct_answer: str
    user_answer: str
    topic: str


@app.post("/generate-question")
def generate_question(request: QuestionRequest):
    prompt = (
        f"Generate a GRE-style {request.difficulty} level question on {request.topic}. "
        "The output should be in the following JSON format:\n"
        "{\n"
        '"question": "Your question here",\n'
        '"choices": ["A. Choice1", "B. Choice2", "C. Choice3", "D. Choice4", "E. Choice5"],\n'
        '"correct_answer": "A"\n'
        "}"
    )

    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(prompt)

    try:
        # Extract the text response and convert it to JSON
        response_text = response.text.strip("```json").strip("```").strip()  # Remove formatting
        question_data = json.loads(response_text)  # Safe parsing

        return question_data
    except json.JSONDecodeError:
        return {"error": "Failed to parse AI response", "raw_response": response.text}
    
@app.post("/evaluate-answer")
def evaluate_answer(request: AnswerRequest):
    if request.user_answer == request.correct_answer:
        return {"result": "Correct!", "explanation": "Well done! Your answer is correct."}

    # If incorrect, ask Gemini for an explanation
    prompt = (
        f"The user got the following GRE {request.topic} question wrong:\n\n"
        f"Question: {request.question}\n"
        f"Choices: {request.choices}\n"
        f"Correct Answer: {request.correct_answer}\n"
        f"User's Answer: {request.user_answer}\n\n"
        "Provide a detailed explanation for why the correct answer is right and a step-by-step solution if it's a math problem. "
        "Ensure the response is clear, concise, and easy to understand."
    )

    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(prompt)

    return {
        "result": "Incorrect",
        "explanation": response.text
    }

@app.get("/")
def home():
    return {"message": "GRE Prep AI Backend is up and running!!!!"}