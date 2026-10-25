# StudyMate AI — Smart Study Assistant

StudyMate AI is an AI-powered study assistant designed to help students learn, revise, and organize their academic work through a simple and user-friendly interface.

## Features

- **AI Tutor:** Ask study-related questions and receive AI-generated explanations.
- **PDF Question Answering:** Upload a PDF document and ask questions about its content.
- **Notes Generator:** Generate study notes to support revision.
- **MCQ Quiz:** Create multiple-choice quizzes and review answers with explanations.
- **Study Planner:** Organize study tasks and track completion.
- **Saved Notes:** Save and revisit generated study notes.
- **Chat History:** Access previous conversations.

## Technologies Used

- Python
- Streamlit
- Ollama
- Qwen 2.5 3B language model
- SQLite
- HTML/CSS styling

## Requirements

- Python installed on your computer
- Ollama installed and running
- The `qwen2.5:3b` model downloaded through Ollama

## Run Locally

1. Clone this repository:

   ```bash
   git clone https://github.com/SanketEthape/studymate-ai.git
   ```

2. Open the project directory:

   ```bash
   cd studymate-ai
   ```

3. Install the Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Download the language model if it is not already installed:

   ```bash
   ollama pull qwen2.5:3b
   ```

5. Ensure Ollama is running, then start the application:

   ```bash
   python -m streamlit run app.py
   ```

6. Open the local URL displayed in the terminal, usually `http://localhost:8501`.

## Project Status

The application has been developed and tested locally. Online deployment has not yet been completed.

## Future Improvements

- Online deployment with a compatible hosted AI model or inference service.
- Additional study tools and customization options.
- Improved documentation and user guidance.

## Author

Sanket Ethape

GitHub: https://github.com/SanketEthape
