import json
import os
import re
import requests
from http.server import BaseHTTPRequestHandler

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")


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
    messages = [
        {
            "role": "system",
            "content": "You are Jarvis, a concise and helpful AI assistant. Keep responses short and clear.",
        }
    ]
    for line in chat_history.strip().split("\n"):
        if line.startswith("User: "):
            messages.append({"role": "user", "content": line[6:]})
        elif line.startswith("Jarvis: "):
            messages.append({"role": "assistant", "content": line[8:]})
    messages.append({"role": "user", "content": query})
    return messages


def get_reply(chat_history: str, query: str) -> str:
    if not OPENROUTER_API_KEY:
        return "Error: OPENROUTER_API_KEY environment variable is not set."
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": OPENROUTER_MODEL,
                "messages": build_messages(chat_history, query),
            },
            timeout=60,
        )
        result = response.json()
        reply = result["choices"][0]["message"]["content"]
        return clean_text(reply)
    except Exception as e:
        return f"Error reaching OpenRouter: {str(e)}"


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors()
        self.end_headers()

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            query = body.get("query", "").strip()
            chat_history = body.get("chatHistory", "")

            if not query:
                self._respond(400, {"error": "query is required"})
                return

            reply = get_reply(chat_history, query)
            updated_history = chat_history + f"User: {query}\nJarvis: {reply}\n"

            self._respond(200, {"reply": reply, "chatHistory": updated_history})
        except Exception as e:
            self._respond(500, {"error": str(e)})

    def _set_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _respond(self, status: int, data: dict):
        self.send_response(status)
        self._set_cors()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
