
import os
import requests

GEMINI_MODEL = "gemini-flash-lite-latest"
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/"
    f"models/{GEMINI_MODEL}:generateContent"
)


def get_api_key():
    """Read the API key from environment variables or Streamlit Secrets."""
    api_key = os.getenv("GEMINI_API_KEY")

    if api_key:
        return api_key

    try:
        import streamlit as st
        return st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        return ""


def generate_answer(prompt, chat_history=None):
    """Generate a response using the Gemini API."""
    api_key = get_api_key()

    if not api_key:
        return (
            "ERROR: Gemini API key is missing. "
            "Configure GEMINI_API_KEY in your environment "
            "or Streamlit Secrets."
        )

    contents = []

    if chat_history:
        for message in chat_history:
            role = message.get("role", "")
            content = message.get("content", "")

            if not content or role not in ("user", "assistant", "model"):
                continue

            gemini_role = "model" if role in ("assistant", "model") else "user"

            contents.append({
                "role": gemini_role,
                "parts": [{"text": str(content)}]
            })

    contents.append({
        "role": "user",
        "parts": [{"text": str(prompt)}]
    })

    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2048
        }
    }

    try:
        response = requests.post(
            GEMINI_URL,
            params={"key": api_key},
            json=payload,
            timeout=90
        )

        if response.status_code == 429:
            return (
                "ERROR: Gemini API usage limit reached. "
                "Please wait and try again, or check your API quota."
            )

        if response.status_code in (401, 403):
            return (
                "ERROR: Gemini API authentication failed. "
                "Check your API key and permissions."
            )

        response.raise_for_status()
        data = response.json()

        candidates = data.get("candidates", [])
        if not candidates:
            return "ERROR: Gemini did not return a response. Please try again."

        parts = candidates[0].get("content", {}).get("parts", [])
        answer = "\n".join(
            part["text"] for part in parts if "text" in part
        ).strip()

        return answer or "ERROR: Gemini returned an empty response."

    except requests.exceptions.Timeout:
        return "ERROR: Gemini response timed out. Please try again."

    except requests.exceptions.ConnectionError:
        return "ERROR: Could not connect to Gemini. Check your internet connection."

    except requests.exceptions.HTTPError as error:
        status = error.response.status_code if error.response is not None else "unknown"
        return f"ERROR: Gemini API request failed (HTTP {status})."

    except (ValueError, KeyError, TypeError):
        return "ERROR: Could not read the Gemini response."

    except requests.exceptions.RequestException:
        return "ERROR: Gemini API request failed. Please try again."
