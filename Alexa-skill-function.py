import json
import os
import urllib.request
import urllib.error

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

SYSTEM_PROMPT = (
    "You are Jarvis, a smart and concise voice assistant. "
    "Keep all responses under 3 sentences. Never use markdown, bullet points, or special characters. "
    "Speak naturally as if talking to a person."
)


def ask_gemini(user_message: str) -> str:
    url = f"{GEMINI_URL}?key={GEMINI_API_KEY}"
    payload = json.dumps({
        "contents": [
            {"role": "user", "parts": [{"text": SYSTEM_PROMPT + "\n\n" + user_message}]}
        ]
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body["candidates"][0]["content"]["parts"][0]["text"].strip()
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        return f"Gemini error {e.code}: {error_body[:200]}"
    except Exception as e:
        return f"Exception: {str(e)[:200]}"


def build_response(speech_text: str, end_session: bool = False) -> dict:
    return {
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": speech_text,
            },
            "shouldEndSession": end_session,
        },
    }


def lambda_handler(event, context):
    request_type = event.get("request", {}).get("type", "")

    if request_type == "LaunchRequest":
        return build_response("Jarvis online. How can I help?", end_session=False)

    if request_type == "IntentRequest":
        intent_name = event["request"]["intent"]["name"]

        if intent_name == "AskJarvisIntent":
            slots = event["request"]["intent"].get("slots", {})
            query = slots.get("query", {}).get("value", "")
            if not query:
                return build_response("I didn't catch that. Could you repeat?", end_session=False)
            answer = ask_gemini(query)
            return build_response(answer, end_session=False)

        if intent_name in ("AMAZON.StopIntent", "AMAZON.CancelIntent"):
            return build_response("Goodbye.", end_session=True)

        if intent_name == "AMAZON.HelpIntent":
            return build_response("Just ask me anything.", end_session=False)

    if request_type == "SessionEndedRequest":
        return build_response("", end_session=True)

    return build_response("I'm not sure how to handle that.", end_session=True)