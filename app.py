
import hashlib
import json
import uuid
from pathlib import Path

import streamlit as st

from ai_engine import generate_answer
from database import (
    initialize_database,
    save_message,
    get_chat_history,
    save_note,
    get_saved_notes,
    add_study_task,
    get_study_tasks,
    update_task_status,
)
from study_tools import generate_short_notes
from pdf_qa import (
    extract_pdf_chunks,
    retrieve_relevant_chunks,
    build_pdf_prompt,
)


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="StudyMate AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==================================================
# LOAD PROFESSIONAL CSS
# ==================================================

def load_css():
    css_path = Path(__file__).parent / "styles.css"

    try:
        css = css_path.read_text(encoding="utf-8")
        st.markdown(
            f"<style>{css}</style>",
            unsafe_allow_html=True,
        )
    except OSError:
        st.warning(
            "Custom stylesheet not found. "
            "Please ensure styles.css is in the same folder as app.py."
        )


load_css()


# ==================================================
# INITIALIZE DATABASE
# ==================================================

initialize_database()


# ==================================================
# SESSION STATE INITIALIZATION
# ==================================================

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None

if "quiz_topic" not in st.session_state:
    st.session_state.quiz_topic = ""

if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False

if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = {}

if "generated_notes" not in st.session_state:
    st.session_state.generated_notes = None

if "generated_notes_title" not in st.session_state:
    st.session_state.generated_notes_title = ""

if "pdf_fingerprint" not in st.session_state:
    st.session_state.pdf_fingerprint = None


# ==================================================
# HELPER FUNCTIONS
# ==================================================

def show_ai_error(answer):
    return (
        isinstance(answer, str)
        and answer.startswith("ERROR:")
    )


def create_quiz(topic, level, language, number):
    prompt = f"""
You are an educational quiz generator.

Create exactly {number} multiple-choice questions about:
{topic}

Student level: {level}
Question language: {language}

Return ONLY a valid JSON object without Markdown fences.

Required structure:
{{
  "questions": [
    {{
      "question": "Question text",
      "options": {{
        "A": "Option A",
        "B": "Option B",
        "C": "Option C",
        "D": "Option D"
      }},
      "answer": "A",
      "explanation": "Explanation of the correct answer"
    }}
  ]
}}

Rules:
- Return exactly {number} questions.
- Every question must contain four options.
- The answer must be A, B, C, or D.
- Make questions factually accurate.
- Follow the requested language.
- Return valid JSON only.
"""

    raw = generate_answer(prompt)

    if show_ai_error(raw):
        return None, raw

    try:
        cleaned = raw.strip()

        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            cleaned = cleaned.rsplit("```", 1)[0].strip()

        data = json.loads(cleaned)
        questions = data.get("questions", [])

        if not isinstance(questions, list):
            return None, "Invalid quiz format. Please try again."

        valid_questions = []

        for question in questions:
            if not isinstance(question, dict):
                continue

            options = question.get("options", {})
            answer = str(
                question.get("answer", "")
            ).upper().strip()

            if (
                isinstance(options, dict)
                and question.get("question")
                and all(
                    key in options
                    for key in ["A", "B", "C", "D"]
                )
                and answer in ["A", "B", "C", "D"]
            ):
                valid_questions.append(question)

        if not valid_questions:
            return None, (
                "The AI did not return valid quiz questions. "
                "Please try again."
            )

        return valid_questions[:number], None

    except (ValueError, TypeError, AttributeError, IndexError):
        return None, (
            "The AI returned an invalid quiz format. "
            "Please generate the quiz again."
        )


def update_task_from_checkbox(task_id, widget_key):
    update_task_status(
        task_id,
        st.session_state[widget_key],
    )


# ==================================================
# SIDEBAR NAVIGATION
# ==================================================

pages = [
    "Dashboard",
    "AI Tutor",
    "PDF Q&A",
    "Notes Generator",
    "MCQ Quiz",
    "Study Planner",
    "Saved Notes",
    "Chat History",
]

with st.sidebar:
    st.title("📚 StudyMate AI")
    st.caption("Your personal AI study companion")
    st.divider()

    if st.session_state.page not in pages:
        st.session_state.page = "Dashboard"

    current_page = st.radio(
        "Navigation",
        pages,
        index=pages.index(st.session_state.page),
        key="navigation",
    )

    st.session_state.page = current_page

    st.divider()

    st.caption("🤖 AI Model: Qwen 2.5 (3B)")
    st.caption("⚡ Powered locally by Ollama")
    st.caption("🔒 Local AI processing")


# ==================================================
# DASHBOARD
# ==================================================

if current_page == "Dashboard":
    st.title("Welcome to StudyMate AI 👋")

    st.write(
        "Learn smarter with your personal AI-powered "
        "study assistant."
    )

    st.caption(
        "Your learning workspace for explanations, "
        "study notes, quizzes and PDF-based learning."
    )

    history = get_chat_history(st.session_state.session_id)
    notes = get_saved_notes()
    tasks = get_study_tasks()

    completed_tasks = sum(
        1 for task in tasks if task["completed"]
    )

    st.divider()

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "💬 Chat Messages",
        len(history),
    )

    c2.metric(
        "📝 Saved Notes",
        len(notes),
    )

    c3.metric(
        "✅ Completed Tasks",
        f"{completed_tasks}/{len(tasks)}",
    )

    st.divider()

    st.subheader("What would you like to do today?")

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "💬 Ask AI Tutor",
            use_container_width=True,
        ):
            st.session_state.page = "AI Tutor"
            st.rerun()

        if st.button(
            "📄 Ask Questions From PDF",
            use_container_width=True,
        ):
            st.session_state.page = "PDF Q&A"
            st.rerun()

        if st.button(
            "📝 Generate Study Notes",
            use_container_width=True,
        ):
            st.session_state.page = "Notes Generator"
            st.rerun()

    with col2:
        if st.button(
            "🧠 Take a Quiz",
            use_container_width=True,
        ):
            st.session_state.page = "MCQ Quiz"
            st.rerun()

        if st.button(
            "📅 Plan My Study",
            use_container_width=True,
        ):
            st.session_state.page = "Study Planner"
            st.rerun()

        if st.button(
            "📚 View Saved Notes",
            use_container_width=True,
        ):
            st.session_state.page = "Saved Notes"
            st.rerun()

    st.divider()

    st.info(
        "Study tip: Upload your study PDF, ask questions, "
        "generate revision notes and test your knowledge "
        "with a quiz."
    )


# ==================================================
# AI TUTOR
# ==================================================

elif current_page == "AI Tutor":
    st.title("💬 AI Tutor")

    st.write(
        "Ask questions and learn concepts with your personal AI tutor."
    )

    col1, col2 = st.columns(2)

    with col1:
        level = st.selectbox(
            "Your learning level",
            ["Beginner", "College Student", "Advanced"],
            key="tutor_level",
        )

    with col2:
        language = st.selectbox(
            "Answer language",
            ["Simple English", "Marathi", "Hinglish"],
            key="tutor_language",
        )

    history = get_chat_history(st.session_state.session_id)

    for message in history:
        role = message["role"]

        if role in ["user", "assistant"]:
            with st.chat_message(role):
                st.markdown(message["content"])

    question = st.chat_input(
        "Ask StudyMate AI a question..."
    )

    if question:
        prior_messages = [
            {
                "role": message["role"],
                "content": message["content"],
            }
            for message in history
            if message["role"] in ["user", "assistant"]
        ]

        prompt = f"""
You are StudyMate AI, a helpful educational tutor.

Student level: {level}
Preferred response language: {language}

Instructions:
- Explain concepts clearly and accurately.
- Use simple language appropriate for the student's level.
- Use headings, examples and bullet points when useful.
- For programming questions, include code examples when appropriate.
- If the student asks a follow-up, consider the conversation context.
- Be honest if you are unsure of a fact.

Student message:
{question}
"""

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("StudyMate is thinking..."):
                answer = generate_answer(
                    prompt,
                    chat_history=prior_messages,
                )

            if show_ai_error(answer):
                st.error(answer)
            else:
                st.markdown(answer)

        save_message(
            st.session_state.session_id,
            "user",
            question,
        )

        save_message(
            st.session_state.session_id,
            "assistant",
            answer,
        )


# ==================================================
# PDF QUESTION ANSWERING
# ==================================================

elif current_page == "PDF Q&A":
    st.title("📄 Ask Questions From Your PDF")

    st.write(
        "Upload a textbook or study material PDF and ask "
        "questions based on its content."
    )

    st.caption(
        "Maximum file size: 20 MB. "
        "PDFs should contain selectable text."
    )

    uploaded_pdf = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        key="study_pdf_uploader",
        help="Scanned image-only PDFs may require OCR.",
    )

    if uploaded_pdf is None:
        st.info("Upload a PDF to start asking questions.")

        for key in [
            "pdf_fingerprint",
            "pdf_chunks",
            "pdf_error",
            "pdf_last_answer",
        ]:
            st.session_state.pop(key, None)

    else:
        pdf_bytes = uploaded_pdf.getvalue()

        if len(pdf_bytes) > 20 * 1024 * 1024:
            st.error(
                "This PDF is larger than 20 MB. "
                "Please upload a smaller PDF."
            )

        else:
            fingerprint = hashlib.sha256(
                pdf_bytes
            ).hexdigest()

            if (
                st.session_state.get("pdf_fingerprint")
                != fingerprint
            ):
                for key in [
                    "pdf_chunks",
                    "pdf_error",
                    "pdf_last_answer",
                ]:
                    st.session_state.pop(key, None)

                try:
                    with st.spinner("Reading your PDF..."):
                        chunks = extract_pdf_chunks(pdf_bytes)

                    if not chunks:
                        st.session_state.pdf_error = (
                            "No readable text was found. "
                            "This PDF may contain scanned pages only."
                        )
                    else:
                        st.session_state.pdf_chunks = chunks

                    st.session_state.pdf_fingerprint = fingerprint

                except Exception:
                    st.session_state.pdf_error = (
                        "Unable to read this PDF. "
                        "Please check that the file is valid and try again."
                    )
                    st.session_state.pdf_fingerprint = fingerprint

            if "pdf_error" in st.session_state:
                st.error(st.session_state.pdf_error)

            elif "pdf_chunks" in st.session_state:
                chunks = st.session_state.pdf_chunks

                pages_found = sorted({
                    chunk["page"] for chunk in chunks
                })

                st.success(
                    f"PDF ready! Readable text found on "
                    f"{len(pages_found)} page(s)."
                )

                with st.expander("📖 Preview extracted PDF text"):
                    preview = "\n\n".join(
                        f"Page {chunk['page']}: "
                        f"{chunk['text'][:500]}"
                        for chunk in chunks[:3]
                    )
                    st.write(preview)

                with st.form("pdf_question_form"):
                    question = st.text_input(
                        "Your question",
                        placeholder=(
                            "Example: Explain MapReduce "
                            "using this PDF."
                        ),
                    )

                    answer_language = st.selectbox(
                        "Answer language",
                        ["Simple English", "Marathi", "Hinglish"],
                        key="pdf_answer_language",
                    )

                    ask_question = st.form_submit_button(
                        "🔍 Ask PDF",
                        use_container_width=True,
                    )

                if ask_question:
                    if not question.strip():
                        st.warning("Please enter a question.")

                    else:
                        relevant_chunks = retrieve_relevant_chunks(
                            question.strip(),
                            chunks,
                            top_k=4,
                        )

                        if not relevant_chunks:
                            st.warning(
                                "I couldn't find a clear keyword match "
                                "in this PDF. Try using specific terms "
                                "from the document."
                            )

                            st.session_state.pop(
                                "pdf_last_answer", None
                            )

                        else:
                            prompt = build_pdf_prompt(
                                question.strip(),
                                relevant_chunks,
                            )

                            prompt += f"""

Answer language: {answer_language}

Additional instructions:
- Answer using the supplied PDF excerpts.
- Explain concepts in a student-friendly way.
- If the excerpts do not contain the answer, say so.
- Refer to the page numbers provided in the excerpts.
"""

                            with st.spinner(
                                "StudyMate AI is preparing your answer..."
                            ):
                                answer = generate_answer(prompt)

                            if show_ai_error(answer):
                                st.error(answer)

                            else:
                                st.session_state.pdf_last_answer = {
                                    "question": question.strip(),
                                    "answer": answer,
                                    "pages": sorted({
                                        chunk["page"]
                                        for chunk in relevant_chunks
                                    }),
                                    "fingerprint": fingerprint,
                                }

                last_answer = st.session_state.get(
                    "pdf_last_answer"
                )

                if (
                    last_answer
                    and last_answer.get("fingerprint")
                    == fingerprint
                ):
                    st.divider()
                    st.subheader("💡 Answer")

                    st.markdown(last_answer["answer"])

                    page_labels = ", ".join(
                        str(page)
                        for page in last_answer["pages"]
                    )

                    st.caption(
                        f"Relevant PDF pages: {page_labels}"
                    )


# ==================================================
# NOTES GENERATOR
# ==================================================

elif current_page == "Notes Generator":
    st.title("📝 Smart Notes Generator")

    st.write(
        "Generate concise, exam-oriented notes for your topic."
    )

    with st.form("notes_form"):
        topic = st.text_input(
            "Enter topic",
            placeholder="Example: Cloud Computing",
        )

        level = st.selectbox(
            "Student level",
            ["Beginner", "College Student", "Advanced"],
        )

        language = st.selectbox(
            "Notes language",
            ["Simple English", "Marathi", "Hinglish"],
        )

        generate = st.form_submit_button(
            "✨ Generate Notes",
            use_container_width=True,
        )

    if generate:
        if not topic.strip():
            st.warning("Please enter a topic.")

        else:
            with st.spinner("Preparing your notes..."):
                notes_text = generate_short_notes(
                    topic.strip(),
                    level,
                    language,
                )

            if show_ai_error(notes_text):
                st.error(notes_text)

            else:
                st.session_state.generated_notes = notes_text
                st.session_state.generated_notes_title = topic.strip()

    if st.session_state.generated_notes:
        st.divider()

        st.subheader(
            st.session_state.generated_notes_title
        )

        st.markdown(
            st.session_state.generated_notes
        )

        if st.button(
            "💾 Save These Notes",
            use_container_width=False,
        ):
            save_note(
                st.session_state.generated_notes_title,
                st.session_state.generated_notes,
            )

            st.success("Notes saved successfully!")


# ==================================================
# MCQ QUIZ
# ==================================================

elif current_page == "MCQ Quiz":
    st.title("🧠 MCQ Quiz")

    st.write(
        "Generate multiple-choice questions and test your knowledge."
    )

    with st.form("quiz_form"):
        topic = st.text_input(
            "Quiz topic",
            placeholder="Example: Python Programming",
        )

        level = st.selectbox(
            "Student level",
            ["Beginner", "College Student", "Advanced"],
        )

        language = st.selectbox(
            "Question language",
            ["Simple English", "Marathi", "Hinglish"],
        )

        number = st.slider(
            "Number of questions",
            min_value=3,
            max_value=10,
            value=5,
        )

        create = st.form_submit_button(
            "🚀 Generate Quiz",
            use_container_width=True,
        )

    if create:
        if not topic.strip():
            st.warning("Please enter a topic.")

        else:
            with st.spinner("Creating your quiz..."):
                questions, error = create_quiz(
                    topic.strip(),
                    level,
                    language,
                    number,
                )

            if error:
                st.error(error)

            else:
                st.session_state.quiz_data = questions
                st.session_state.quiz_topic = topic.strip()
                st.session_state.quiz_submitted = False
                st.session_state.quiz_answers = {}

                for i in range(len(questions)):
                    st.session_state.pop(
                        f"quiz_answer_{i}", None
                    )

                st.rerun()

    questions = st.session_state.quiz_data

    if questions:
        st.divider()

        st.subheader(
            f"Quiz: {st.session_state.quiz_topic}"
        )

        if not st.session_state.quiz_submitted:
            with st.form("answer_quiz_form"):
                selected_answers = {}

                for i, question in enumerate(questions):
                    st.markdown(
                        f"**Q{i + 1}. {question['question']}**"
                    )

                    options = question["options"]

                    choice = st.radio(
                        f"Select your answer for Q{i + 1}",
                        ["Not answered", "A", "B", "C", "D"],
                        format_func=lambda key, opts=options: (
                            "Choose an answer"
                            if key == "Not answered"
                            else f"{key}. {opts[key]}"
                        ),
                        key=f"quiz_answer_{i}",
                    )

                    selected_answers[i] = choice

                submitted = st.form_submit_button(
                    "Submit Quiz",
                    use_container_width=True,
                )

            if submitted:
                st.session_state.quiz_answers = selected_answers
                st.session_state.quiz_submitted = True
                st.rerun()

        else:
            score = 0

            for i, question in enumerate(questions):
                chosen = st.session_state.quiz_answers.get(
                    i,
                    "Not answered",
                )

                correct = str(
                    question["answer"]
                ).upper()

                if chosen == correct:
                    score += 1
                    st.success(
                        f"Q{i + 1}: Correct!"
                    )

                else:
                    st.error(
                        f"Q{i + 1}: Incorrect or unanswered. "
                        f"Correct answer: {correct}."
                    )

                explanation = question.get("explanation", "")

                if explanation:
                    st.markdown(
                        f"**Explanation:** {explanation}"
                    )

            total = len(questions)

            st.subheader(
                f"Your score: {score}/{total}"
            )

            st.progress(score / total if total else 0)

            if total:
                percentage = round(score / total * 100)
                st.caption(f"Score percentage: {percentage}%")

            if st.button(
                "🔄 Try Another Quiz",
                use_container_width=True,
            ):
                st.session_state.quiz_data = None
                st.session_state.quiz_topic = ""
                st.session_state.quiz_submitted = False
                st.session_state.quiz_answers = {}

                for i in range(10):
                    st.session_state.pop(
                        f"quiz_answer_{i}", None
                    )

                st.rerun()


# ==================================================
# STUDY PLANNER
# ==================================================

elif current_page == "Study Planner":
    st.title("📅 Study Planner")

    st.write(
        "Organize your study tasks and track your progress."
    )

    with st.form("add_task_form"):
        task_name = st.text_input(
            "Study task",
            placeholder="Example: Revise SQL JOINs",
        )

        subject = st.text_input(
            "Subject (optional)",
            placeholder="Example: Data Engineering",
        )

        add_task = st.form_submit_button(
            "➕ Add Study Task",
            use_container_width=True,
        )

    if add_task:
        if task_name.strip():
            add_study_task(
                task_name.strip(),
                subject.strip(),
            )

            st.success("Study task added!")
            st.rerun()

        else:
            st.warning("Please enter a task.")

    st.divider()
    st.subheader("Your Study Tasks")

    tasks = get_study_tasks()

    if not tasks:
        st.info(
            "No tasks yet. Add your first study task above."
        )

    else:
        completed = sum(
            1 for task in tasks if task["completed"]
        )

        st.progress(
            completed / len(tasks)
        )

        st.caption(
            f"Completed {completed} of {len(tasks)} tasks."
        )

        for task in tasks:
            widget_key = f"task_done_{task['id']}"

            task_label = task["task"]

            if task["subject"]:
                task_label += f" — {task['subject']}"

            st.checkbox(
                task_label,
                value=bool(task["completed"]),
                key=widget_key,
                on_change=update_task_from_checkbox,
                args=(task["id"], widget_key),
            )


# ==================================================
# SAVED NOTES
# ==================================================

elif current_page == "Saved Notes":
    st.title("📚 Saved Notes")

    st.write(
        "Review the notes you have saved for revision."
    )

    notes = get_saved_notes()

    if not notes:
        st.info(
            "No saved notes yet. Generate and save notes first."
        )

    else:
        st.caption(f"Total saved notes: {len(notes)}")

        for note in notes:
            with st.expander(
                f"📝 {note['title']}"
            ):
                st.caption(
                    f"Created: {note['created_at']}"
                )

                st.markdown(
                    note["content"]
                )


# ==================================================
# CHAT HISTORY
# ==================================================

elif current_page == "Chat History":
    st.title("🗂️ Chat History")

    st.write(
        "Review messages from your current conversation session."
    )

    history = get_chat_history(
        st.session_state.session_id
    )

    if not history:
        st.info(
            "No messages in this session yet. "
            "Start a conversation in AI Tutor."
        )

    else:
        for message in history:
            role = message["role"]

            if role in ["user", "assistant"]:
                with st.chat_message(role):
                    st.markdown(
                        message["content"]
                    )

                    st.caption(
                        message["created_at"]
                    )

        st.divider()

        st.caption(
            f"Total messages in this session: {len(history)}"
        )
