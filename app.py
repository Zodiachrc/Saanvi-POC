import os
import PyPDF2
import docx
import pandas as pd
from flask import Flask, request, jsonify, render_template_string, send_file
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

app = Flask(__name__)
#abcd



# Initialized LangChain with OpenAI 
llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo", openai_api_key=API_KEY)


prompt_template = """
From the following resume, extract and return the following fields as a JSON object:
- Candidate Name
- Highest Qualification
- Experience (in Years)
- Company you have worked in
- Skills
- Location
- Certification
- Official notice period

If any information is missing, return 'N/A' or an empty string.

Resume:
{resume_text}
"""

# LangChain prompt and chain setup
template = PromptTemplate(input_variables=["resume_text"], template=prompt_template)
chain = LLMChain(llm=llm, prompt=template)

resume_text = ""

def extract_text(file):
    print(f"Extracting text from {file.filename}")
    if file.filename.endswith(".pdf"):
        reader = PyPDF2.PdfReader(file)
        return "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
    elif file.filename.endswith(".docx"):
        doc = docx.Document(file)
        return "\n".join(paragraph.text for paragraph in doc.paragraphs)
    elif file.filename.endswith(".txt"):
        return file.read().decode("utf-8")
    return ""

@app.route("/", methods=["GET", "POST"])
def index():
    global resume_text
    extracted_data = None
    message = ""
    if request.method == "POST":
        file = request.files.get("resume")
        if file:
            resume_text = extract_text(file)
            message = "Resume uploaded successfully!"
            # Extract data using LangChain
            extracted_data = chain.run(resume_text)
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Resume Reader Bot</title>
    </head>
    <body>
        <h2>Resume Reader Bot</h2>
        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="resume" required>
            <button type="submit">Upload Resume</button>
        </form>
        <p>{{ message }}</p>
        {% if extracted_data %}
        <h3>Extracted Resume Information:</h3>
        <pre>{{ extracted_data }}</pre>
        {% endif %}
    </body>
    </html>
    """, message=message, extracted_data=extracted_data)

@app.route("/save", methods=["GET"])
def save():
    """Save the extracted data as Excel."""
    global resume_text
    if not resume_text:
        return jsonify({"error": "No resume uploaded!"})

    # Run LangChain to extract structured fields
    extracted_data = chain.run(resume_text)
    
    # Convert extracted data into a dictionary and save it as Excel
    df = pd.DataFrame([extracted_data])
    filename = "resume_extracted_data.xlsx"
    df.to_excel(filename, index=False)

    return send_file(filename, as_attachment=True)

if __name__ == "__main__":
    print("✅ App is starting... Visit http://127.0.0.1:5000")
    app.run(debug=True)
