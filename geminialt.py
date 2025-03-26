import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import uuid

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI()
PERFORMANCE_FILE = "performance.json"

tests = {}  # Store active tests

class TestSession(BaseModel):
    test_id: str
    start_time: datetime
    end_time: datetime
    questions: list

class SubmitTestRequest(BaseModel):
    test_id: str
    answers: dict  # {question_id: chosen_answer}

class AnswerSubmission(BaseModel):
    topic: str
    correct: bool


def load_performance():
    try:
        with open("performance.json", "r") as f:
            data = f.read()
            return json.loads(data) if data else {}  # Handle empty file
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_performance(data):
    with open(PERFORMANCE_FILE, "w") as f:
        json.dump(data, f, indent=4)



@app.post("/start-test")
def start_test():
    test_id = str(uuid.uuid4())
    start_time = datetime.utcnow()
    end_time = start_time + timedelta(minutes=13)  # Set test duration
    
    questions = []
    topics = ["Algebra", "Geometry", "Probability", "Reading Comprehension", "Critical Reasoning"]
    difficulties = ["easy", "medium", "hard"]
    
    for _ in range(10):  # Generate 10 questions
        topic = topics[_ % len(topics)]
        difficulty = difficulties[_ % len(difficulties)]
        prompt = f"Generate a GRE-style {difficulty} level question on {topic}. Include 5 answer choices (A-E) and specify the correct answer."
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        
        questions.append({"id": str(uuid.uuid4()), "question": response.text, "correct_answer": "A"})  # Placeholder correct answer
    
    tests[test_id] = TestSession(test_id=test_id, start_time=start_time, end_time=end_time, questions=questions)
    
    return {"test_id": test_id, "questions": questions, "end_time": end_time}

@app.post("/submit-test")
def submit_test(request: SubmitTestRequest):
    test = tests.get(request.test_id)
    if not test:
        raise HTTPException(status_code=400, detail="Invalid test ID")
    
    if datetime.utcnow() > test.end_time:
        raise HTTPException(status_code=400, detail="Test time expired. Submission not allowed.")
    
    correct_count = 0
    results = {}
    
    for question in test.questions:
        qid = question["id"]
        correct_answer = question["correct_answer"]
        user_answer = request.answers.get(qid, "")
        results[qid] = {"question": question["question"], "user_answer": user_answer, "correct_answer": correct_answer, "is_correct": user_answer == correct_answer}
        if user_answer == correct_answer:
            correct_count += 1
    
    return {"score": correct_count, "total": len(test.questions), "results": results}


# @app.post("/submit-answer")
# def submit_answer(submission: AnswerSubmission):
#     data = load_performance()
#     topic = submission.topic
    
#     if topic not in data:
#         data[topic] = {"attempted": 0, "correct": 0, "accuracy": 0.0}
    
#     data[topic]["attempted"] += 1
#     if submission.correct:
#         data[topic]["correct"] += 1
    
#     # Update accuracy
#     data[topic]["accuracy"] = round((data[topic]["correct"] / data[topic]["attempted"]) * 100, 2)
    
#     save_performance(data)
#     return {"message": "Answer recorded", "updated_stats": data[topic]}



@app.post("/submit-answer")
def submit_answer(answer: dict):
    # Validate input
    if "topic" not in answer or "correct" not in answer:
        raise HTTPException(status_code=400, detail="Missing 'topic' or 'correct' field in request body.")

    topic = answer["topic"]
    correct = answer["correct"]  # Boolean: True if correct, False if wrong

    # Load existing performance data
    data = load_performance()

    # Initialize topic tracking if it doesn't exist
    if topic not in data:
        data[topic] = {"attempted": 0, "correct": 0, "accuracy": 0.0}

    # Update performance stats
    data[topic]["attempted"] += 1
    if correct:
        data[topic]["correct"] += 1

    # Recalculate accuracy
    data[topic]["accuracy"] = round((data[topic]["correct"] / data[topic]["attempted"]) * 100, 2)

    # Save back to JSON
    save_performance(data)

    return {"message": "Answer submitted successfully!", "updated_performance": data}

@app.get("/performance")
def get_performance():
    data = load_performance()
    if not data:
        raise HTTPException(status_code=404, detail="No performance data found")
    return data