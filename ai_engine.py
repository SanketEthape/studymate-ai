
import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5:3b"


def generate_answer(prompt, chat_history=None):
    """
    Generate a response using the local Ollama model.
    """
    messages = []

    if chat_history:
        messages.extend(chat_history)

    messages.append({
        "role": "user",
        "content": prompt
    })

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=300
        )
        response.raise_for_status()

        data = response.json()
        return data["message"]["content"].strip()

    except requests.exceptions.ConnectionError:
        return (
            "ERROR: Cannot connect to Ollama. "
            "Please make sure Ollama is running."
        )

    except requests.exceptions.Timeout:
        return "ERROR: The AI response timed out. Please try again."

    except requests.exceptions.RequestException as error:
        return f"ERROR: AI service request failed: {error}"

    except (KeyError, ValueError):
        return "ERROR: Could not read the AI response."
