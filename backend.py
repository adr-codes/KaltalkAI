from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY = "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"  # Replace this with your actual OpenRouter API key
SYSTEM_PROMPT = f"You are KaltalkAI,a virtual ai companion. Be cheerful, kind, and positive in every conversation. Your main goal is to lift the user’s spirits and engage them in friendly, lighthearted chat. Always offer a warm greeting, ask about their day, and keep the mood upbeat. You can tell jokes, share fun facts, or offer a listening ear to help them feel comfortable. But remember, every conversation is a fresh start, so don’t recall any previous chats."

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}
MODEL_NAME = "sophosympatheia/rogue-rose-103b-v0.2:free"  # Free model you're using


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"response": "I'm here to help. What would you like to ask?"})

    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                     {"role": "user", "content": user_message}]
    }

    try:
        response = requests.post(OPENROUTER_API_URL, json=payload, headers=HEADERS)
        response_data = response.json()

        if "choices" in response_data and len(response_data["choices"]) > 0:
            ai_reply = response_data["choices"][0]["message"]["content"]
        else:
            ai_reply = "Sorry, I couldn't process that."

    except requests.exceptions.RequestException:
        ai_reply = "Error: Could not connect to AI service."

    return jsonify({"response": ai_reply})


if __name__ == "__main__":
    app.run(debug=True)
