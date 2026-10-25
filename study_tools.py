
from ai_engine import generate_answer


def generate_short_notes(topic, level="College Student",
                        language="Simple English"):
    prompt = f"""
Create clear, exam-oriented short notes about: {topic}

Student level: {level}
Language: {language}

Include:
1. Definition
2. Important points
3. A simple example
4. A short conclusion

Keep the notes concise and accurate.
"""
    return generate_answer(prompt)


def generate_mcqs(topic, number=5, level="College Student",
                  language="Simple English"):
    number = max(1, min(int(number), 10))

    prompt = f"""
Create exactly {number} multiple-choice questions about: {topic}

Student level: {level}
Language: {language}

For each question:
- Give four options: A, B, C, D
- Identify the correct answer
- Give a one-sentence explanation

Use this format:

Q1. Question text
A. Option
B. Option
C. Option
D. Option
Correct answer: B
Explanation: Short explanation

Make the questions educational and factually accurate.
"""
    return generate_answer(prompt)


def explain_topic(topic, level="College Student",
                  language="Simple English"):
    prompt = f"""
Explain this topic: {topic}

Student level: {level}
Language: {language}

Use simple language, headings and examples.
Explain the key concepts clearly.
"""
    return generate_answer(prompt)


def answer_question(question, level="College Student",
                    language="Simple English"):
    prompt = f"""
Answer this student's question: {question}

Student level: {level}
Language: {language}

Give a clear, accurate and student-friendly answer.
Use examples where helpful.
If the question is ambiguous, explain the assumption you make.
"""
    return generate_answer(prompt)
