from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from google import genai
from pypdf import PdfReader
import os

app = Flask(__name__)
app.secret_key = "viva_examiner_secret"


client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def load_syllabus_text():
    reader = PdfReader("syllabus.pdf")
    text = ""

    for i, page in enumerate(reader.pages):
        try:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        except Exception as e:
            print(f"Skipping page {i} due to error:", e)

    return text
SYLLABUS_TEXT = load_syllabus_text()

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form.get("username")
        return redirect(url_for("chat", name=name))
    return render_template("login.html")


@app.route("/chat")
def chat():
    session.clear()
    return render_template("chat.html", name=request.args.get("name"))


@app.route("/ask", methods=["POST"])
def ask_examiner():
    user_answer = request.json.get("message", "").lower()

    if "viva_started" not in session:
        session["viva_started"] = False
        session["viva_ended"] = False

    if user_answer in ["stop", "end", "end viva", "stop viva"]:
        session["viva_ended"] = True
        return jsonify({
            "reply": "The viva examination has ended. Thank you."
        })

    if session["viva_ended"]:
        return jsonify({
            "reply": "The viva has already ended."
        })

    if not session["viva_started"] and user_answer in ["yes", "ok", "start"]:
        session["viva_started"] = True
        return jsonify({
            "reply": (
                "The viva examination will now begin.\n\n"
                "Instructions:\n"
                "- Questions will be asked one by one.\n"
                "- Answer concisely.\n"
                "- Say 'stop' or 'end viva' to end the examination.\n\n"
            )
        })

    prompt = f"""
You are a university viva examiner.

IMPORTANT RULES:
- Ask ONLY questions based on the syllabus text below. 
- Never mention syllabus or which program it is from in the questions.
- Do NOT mention or refer to the reference material.
- Do NOT say phrases like "according to the syllabus" or any other similar phrase.
- If you mention the reference material, your response is invalid.
- Ask ONE question at a time. Start with an easy question and gradually increase the difficulty.
- You do not have to go in order of the syllabus content, you can mix and ask from anywhere at any time.
- Do NOT restart the viva.
- Do NOT give instructions again.
- Do NOT evaluate answers.
- DO NOT ASK "What is the name of the document owner mentioned in the introductory section?" such questions which are no where related to studies.
- If the student says "I don't know", rephrase or simplify the question.
- Stay strictly within the syllabus content.

SYLLABUS:
{SYLLABUS_TEXT}

Student answer:
{user_answer}

Ask the NEXT viva question only.
"""

    response = client.models.generate_content(
        model="models/gemini-flash-lite-latest",
        contents=[
            {"role": "user", "parts": [{"text": prompt}]}
        ]
    )

    return jsonify({"reply": response.text})

if __name__ == "__main__":
    app.run(debug=True)
