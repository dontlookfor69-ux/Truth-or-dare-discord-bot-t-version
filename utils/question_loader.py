import json
import random
import os

QUESTIONS_FILE = 'questions.json'

def load_questions():
    """
    Loads questions from the JSON file.
    Returns a dictionary with 'truths' and 'dares' lists.
    """
    if not os.path.exists(QUESTIONS_FILE):
        return {"truths": [], "dares": []}
        
    try:
        with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Basic validation to ensure keys exist
        for key in ["truths", "dares", "wyr", "nhie", "paranoia"]:
            if key not in data:
                data[key] = []
            
        return data
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading questions: {e}")
        return {"truths": [], "dares": []}

def get_random_question(question_type, rating=None, data=None, exclude_id=None):
    """
    Gets a random question based on type and optional rating.
    
    Args:
        question_type (str): 'truth' or 'dare'
        rating (str, optional): 'pg', 'pg13', or 'r'. If None, any rating.
        data (dict, optional): The data dictionary. If None, loads from file.
        exclude_id (int, optional): The ID of the question to exclude (prevent repeats).
        
    Returns:
        dict: The question object, or None if no matching question found.
    """
    if data is None:
        data = load_questions()
        
    keyword = "truths"
    if question_type == "dare":
        keyword = "dares"
    elif question_type == "wyr":
        keyword = "wyr"
    elif question_type == "nhie":
        keyword = "nhie"
    elif question_type == "paranoia":
        keyword = "paranoia"
        
    pool = data.get(keyword, [])
    
    if rating:
        pool = [q for q in pool if q.get("rating", "").lower() == rating.lower()]
    
    # Filter out the excluded ID if provided, but only if we have other options
    if exclude_id is not None and len(pool) > 1:
        pool = [q for q in pool if q.get("id") != exclude_id]
    
    if not pool:
        return None
        
    return random.choice(pool)

def validate_question_structure(data):
    """
    Validates the structure of the loaded data.
    Returns True if valid, False otherwise.
    """
    if not isinstance(data, dict):
        return False
    if "truths" not in data or "dares" not in data:
        return False
    if not isinstance(data["truths"], list) or not isinstance(data["dares"], list):
        return False
    return True
