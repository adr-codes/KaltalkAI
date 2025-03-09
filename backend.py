from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)  # Define the app BEFORE running it
CORS(app)  # Allow cross-origin requests

# Replace with your OpenRouter API key
API_KEY = "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"

def get_ai_response(user_input):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [{"role": "user", "content": user_input}]
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()["choices"][0]["message"]["content"]

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")
    ai_response = get_ai_response(user_message)
    return jsonify({"response": ai_response})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Use Render's assigned port or default to 5000
    
