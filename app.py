import os
import re
import requests
import PyPDF2
import docx
from flask import Flask, request, jsonify, render_template_string
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI

app = Flask(__name__)

# Define the path to the credentials file
CREDENTIALS_PATH = "C:/Users/netal/OneDrive/Desktop/langchain_chatbot/credentials.json"

# Define the Google Sheets URL
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1XwoM8guhtxbSdxLPyOI2Ub_St2z6JgdzQv9BK6YBsWc/edit?usp=sharing"

# Set API key and OpenRouter Base URL
os.environ["OPENAI_API_KEY"] = "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"
os.environ["OPENAI_API_BASE"] = "https://openrouter.ai/api/v1"

# Function to extract text from PDF, DOCX, or TXT files
def extract_text(file):
    print(f"Extracting text from {file.filename}")
    if file.filename.endswith(".pdf"):
        reader = PyPDF2.PdfReader(file)
        text = "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
        return text
    elif file.filename.endswith(".docx"):
        doc = docx.Document(file)
        text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
        return text
    elif file.filename.endswith(".txt"):
        text = file.read().decode("utf-8")
        return text
    return ""

# Function to extract structured information from resume using LangChain
def extract_resume_info(resume_text):
    # Define prompt to instruct GPT
    prompt_template = PromptTemplate(
        input_variables=["resume_text"],
        template="""
You are an AI assistant that extracts structured information from resumes. Given the following resume:

{resume_text}

Extract the following fields in this exact format:
Candidate Name: ...
Highest Qualification: ...
Experience: ... (in years and months if possible)
Companies: ...
Location: ...
Certifications: ...
Skills: ...
Official Notice Period: ...
"""
    )

    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
    chain = LLMChain(llm=llm, prompt=prompt_template)

    response = chain.run(resume_text=resume_text)
    print("Resume Info:\n" + response)
    
    return parse_extracted_info(response)

# Helper to parse GPT response accurately
def parse_extracted_info(response):
    extracted_info = {
        "Name": "Not Found",
        "Qualification": "Not Found",
        "Experience": "Not Found",
        "Companies": "Not Found",
        "Location": "Not Found",
        "Certificates": "Not Found",
        "Skills": "Not Found",
        "Notice Period": "Not Found"
    }

    lines = [line.strip() for line in response.splitlines() if line.strip()]
    
    for line in lines:
        if line.lower().startswith("candidate name:"):
            extracted_info["Name"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("highest qualification:"):
            extracted_info["Qualification"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("experience:"):
            extracted_info["Experience"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("companies:"):
            extracted_info["Companies"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("location:"):
            extracted_info["Location"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("certifications:"):
            extracted_info["Certificates"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("skills:"):
            extracted_info["Skills"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("official notice period:"):
            extracted_info["Notice Period"] = line.split(":", 1)[1].strip()

    return extracted_info

# Save to Google Sheet in correct column order
def save_to_google_sheet(extracted_info):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/spreadsheets']
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_PATH, scope)
    client = gspread.authorize(creds)

    sheet = client.open_by_url(SPREADSHEET_URL).sheet1

    # Match Google Sheet order:
    # Name | Qualification | Experience | Companies | Location | Certificates | Skills | Notice Period
    sheet.append_row([
        extracted_info["Name"],
        extracted_info["Qualification"],
        extracted_info["Experience"],
        extracted_info["Companies"],
        extracted_info["Location"],
        extracted_info["Certificates"],
        extracted_info["Skills"],
        extracted_info["Notice Period"]
    ])
    print("✅ Data saved to Google Sheets successfully.")

# Route for uploading resume
@app.route("/", methods=["GET", "POST"])
def index():
    message = ""
    if request.method == "POST":
        file = request.files.get("resume")
        if file:
            resume_text = extract_text(file)
            print(f"Extracted Resume Text: {resume_text}")
            message = "Resume uploaded successfully!"
            extracted_info = extract_resume_info(resume_text)
            save_to_google_sheet(extracted_info)
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
    </body>
    </html>
    """, message=message)

if __name__ == "__main__":
    print("✅ App is starting... Visit http://127.0.0.1:5000")
    app.run(debug=True)


    app.run(debug=True)
