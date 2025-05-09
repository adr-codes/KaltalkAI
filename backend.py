from flask import Flask, request, jsonify
import requests
import os

sessions = {}

app = Flask(__name__)

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY = os.environ.get("OPENROUTER_API_KEY")  # your key here
MODEL_NAME = "mistralai/mistral-7b-instruct:free"

SYSTEM_PROMPT = """
            Your name is KaltalkAI, a virtual AI companion,
            Remember, every converstation is a fresh start.
            Always inntroduce your self first every new conversation starts.
            Be cheerful, kind, and positive in every conversation.
            Use casual and friendly language, not robotic or overly formal.
            Your main goal is to lift the user’s spirits and engage them in friendly, lighthearted chat.
            Always offer a warm greeting, ask about their day, and keep the mood upbeat.
            You can tell jokes, share fun facts, or offer a listening ear to help them feel comfortable.
            Try to use tagalog language if necessary. If the user chats in tagalog, respond in tagalog.
            if the user chats in english, respond in english.
                """

HEADERS = {

    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Keeps history per session ID
chat_sessions = {}

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "").strip()
    session_id = data.get("session_id", "default")  # Use "default" if none provided

    if not user_message:
        return jsonify({"response": "I'm here to help. What would you like to ask?"})

    # Initialize session if it doesn't exist yet
    if session_id not in sessions:
        sessions[session_id] = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Add user message to session
    sessions[session_id].append({"role": "user", "content": user_message})

    payload = {
        "model": MODEL_NAME,
        "messages": sessions[session_id]  # Full history
    }

    try:
        response = requests.post(OPENROUTER_API_URL, json=payload, headers=HEADERS)
        print(response.status_code)
        print(response.text)

        response_data = response.json()

        if "choices" in response_data and len(response_data["choices"]) > 0:
            ai_reply = response_data["choices"][0]["message"]["content"]
            # Add AI reply to the session history
            sessions[session_id].append({"role": "assistant", "content": ai_reply})
        else:
            ai_reply = "Sorry, I couldn't process that."

    except requests.exceptions.RequestException:
        ai_reply = "Error: Could not connect to AI service."

    return jsonify({"response": ai_reply})

#if __name__ == "__main__":
#    app.run(debug=True)
