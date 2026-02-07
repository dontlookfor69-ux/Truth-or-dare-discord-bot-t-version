import json
import os
import aiofiles

SUGGESTIONS_FILE = 'data/suggestions.json'
QUESTIONS_FILE = 'questions.json'

def ensure_suggestions_file():
    if not os.path.exists('data'):
        os.makedirs('data')
    if not os.path.exists(SUGGESTIONS_FILE):
        with open(SUGGESTIONS_FILE, 'w') as f:
            json.dump([], f)

def get_suggestions():
    ensure_suggestions_file()
    try:
        with open(SUGGESTIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def save_suggestions(suggestions):
    ensure_suggestions_file()
    with open(SUGGESTIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(suggestions, f, indent=4)

def add_suggestion(text, type_str, rating, user_id, username):
    suggestions = get_suggestions()
    suggestion = {
        "text": text,
        "type": type_str.lower(),
        "rating": rating.lower(),
        "user_id": user_id,
        "username": username,
        "id": len(suggestions) + 1  # Simple ID assignment
    }
    suggestions.append(suggestion)
    save_suggestions(suggestions)
    return suggestion

def remove_suggestion(index):
    suggestions = get_suggestions()
    if 0 <= index < len(suggestions):
        removed = suggestions.pop(index)
        save_suggestions(suggestions)
        return removed
    return None

def approve_suggestion_to_main(suggestion, final_rating):
    # Load main questions
    try:
        with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading questions: {e}")
        return False

    category = "truths" if suggestion['type'] == 'truth' else "dares"
    
    # Calculate new ID
    current_ids = [item['id'] for item in data.get(category, [])]
    new_id = max(current_ids) + 1 if current_ids else 1
    
    new_entry = {
        "id": new_id,
        "rating": final_rating,
        # Use the correct key based on type
        "question" if category == "truths" else "dare": suggestion['text']
    }
    
    if category not in data:
        data[category] = []
        
    data[category].append(new_entry)
    
    # Save back to questions.json
    try:
        with open(QUESTIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving questions: {e}")
        return False
