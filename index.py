import os
import re
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL   = os.environ.get("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")


def clean_text(text):
    text = re.sub(r'\*{1,3}', '', text)
    text = re.sub(r'#{1,6}\s?', '', text)
    text = re.sub(r'`{1,3}', '', text)
    text = re.sub(r'_{1,2}', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'^\s*>\s?', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*[-•]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n+', ' ', text).strip()
    return text


def build_messages(chat_history: str, query: str) -> list:
    messages = [{
        "role": "system",
        "content": "You are Jarvis, a concise and helpful AI assistant. Keep responses short and clear.",
    }]
    for line in chat_history.strip().split("\n"):
        if line.startswith("User: "):
            messages.append({"role": "user",      "content": line[6:]})
        elif line.startswith("Jarvis: "):
            messages.append({"role": "assistant", "content": line[8:]})
    messages.append({"role": "user", "content": query})
    return messages


@app.route("/api/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return _cors_response(jsonify({}), 200)

    body        = request.get_json(force=True)
    query       = (body.get("query") or "").strip()
    chat_history = body.get("chatHistory", "")

    if not query:
        return _cors_response(jsonify({"error": "query is required"}), 400)

    if not OPENROUTER_API_KEY:
        return _cors_response(jsonify({"error": "OPENROUTER_API_KEY is not set"}), 500)

    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
            json={"model": OPENROUTER_MODEL, "messages": build_messages(chat_history, query)},
            timeout=60,
        )
        reply = clean_text(resp.json()["choices"][0]["message"]["content"])
    except Exception as e:
        return _cors_response(jsonify({"error": str(e)}), 500)

    updated_history = chat_history + f"User: {query}\nJarvis: {reply}\n"
    return _cors_response(jsonify({"reply": reply, "chatHistory": updated_history}), 200)


def _cors_response(response, status):
    response.status_code = status
    response.headers["Access-Control-Allow-Origin"]  = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response
