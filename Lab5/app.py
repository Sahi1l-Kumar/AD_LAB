from flask import Flask, render_template, request, jsonify
from bs4 import BeautifulSoup
import requests
from langchain_community.llms import Ollama
import validators

app = Flask(__name__, static_folder='styles', template_folder='.')

def scrape_webpage(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        

        content = []
        for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'article']):
            if tag.text.strip():
                content.append(tag.text.strip())
        
        return ' '.join(content)
    except Exception as e:
        return f"Error scraping webpage: {str(e)}"

def process_with_llm(text):
    llm = Ollama(model="deepseek-r1:1.5b")
    prompt = f"""Summarize the following text in a clear and concise way, focusing on the main points:

    {text[:3000]}

    Provide the summary in the following format:
    - Main topic
    - Key points (3-5 bullets)
    - Brief conclusion"""
    
    return llm.invoke(prompt)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.get_json()
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    if not validators.url(url):
        return jsonify({'error': 'Invalid URL'}), 400
    
    scraped_content = scrape_webpage(url)
    
    try:
        summary = process_with_llm(scraped_content)
        return jsonify({
            'scraped_content': scraped_content[:500] + '...',
            'summary': summary
        })
    except Exception as e:
        return jsonify({'error': f'Error processing with LLM: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)