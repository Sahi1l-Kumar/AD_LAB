from flask import Flask, request, jsonify, render_template
import os
from werkzeug.utils import secure_filename
import pandas as pd
import PyPDF2
import google.generativeai as genai
from groq import Groq
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv('.env.local')

app = Flask(__name__, static_folder='styles', template_folder='.')
CORS(app)


UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'csv'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def init_gemini():
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    genai.configure(api_key=gemini_api_key)
    return genai.GenerativeModel('gemini-pro')

def init_groq():
    groq_api_key = os.getenv('GROQ_API_KEY')
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables")
    return Groq(api_key=groq_api_key)

try:
    gemini_model = init_gemini()
    groq_client = init_groq()
except Exception as e:
    print(f"Error initializing AI models: {str(e)}")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text(file_path):
    file_extension = file_path.rsplit('.', 1)[1].lower()
    
    if file_extension == 'txt':
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
            
    elif file_extension == 'pdf':
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text
        
    elif file_extension == 'csv':
        df = pd.read_csv(file_path)
        return df.to_string()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            text_content = extract_text(filepath)
            return jsonify({'success': True, 'text': text_content})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    if not data or 'question' not in data or 'context' not in data or 'model' not in data:
        return jsonify({'error': 'Missing required fields'}), 400

    question = data['question']
    context = data['context']
    model_choice = data['model']
    
    prompt = f"""Context: {context}\n\nQuestion: {question}\n\nPlease answer the question based on the context provided."""
    
    try:
        if model_choice == 'gemini':
            response = gemini_model.generate_content(prompt)
            answer = response.text
        else: 
            completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided context."},
                    {"role": "user", "content": prompt}
                ],
                model="mixtral-8x7b-32768",
            )
            answer = completion.choices[0].message.content
            
        return jsonify({'response': answer})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)