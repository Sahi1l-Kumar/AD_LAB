from flask import Flask, render_template, request, jsonify
from bs4 import BeautifulSoup
import requests
import validators
from dotenv import load_dotenv
import os
import google.generativeai as genai
from groq import Groq
import re
from urllib.parse import quote_plus

load_dotenv('.env.local')

app = Flask(__name__, static_folder='styles', template_folder='.')


def init_gemini():
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    genai.configure(api_key=gemini_api_key)
    return genai.GenerativeModel('gemini-2.0-flash')


def init_groq():
    groq_api_key = os.getenv('GROQ_API_KEY')
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables")
    return Groq(api_key=groq_api_key)


OLLAMA_API_URL = "http://localhost:11434/api/generate"


def get_ollama_response(prompt):
    payload = {
        "model": "deepseek-r1:1.5b",
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        return response.json()["response"]
    except requests.exceptions.ConnectionError:
        raise Exception(
            "Could not connect to Ollama. Make sure it's running (ollama run deepseek-r1:1.5b)")
    except Exception as e:
        raise Exception(f"Ollama API error: {str(e)}")


try:
    gemini_model = init_gemini()
    groq_client = init_groq()
except Exception as e:
    print(f"Error initializing AI models: {str(e)}")


def scrape_webpage(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        content = []
        for tag in soup.find_all(['p', 'h1', 'h2', 'h3', 'article']):
            if tag.text.strip():
                content.append(tag.text.strip())

        return ' '.join(content)
    except Exception as e:
        return f"Error scraping webpage: {str(e)}"


def duckduckgo_search(query):
    try:
        search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()

        print(f"DuckDuckGo search status code: {response.status_code}")

        soup = BeautifulSoup(response.text, 'html.parser')

        results = soup.select('.results_links_deep:not(.results-sponsored)')

        valid_links = []
        for result in results:
            link = result.select_one('.result__title .result__a')
            snippet = result.select_one('.result__snippet')

            if link and snippet:
                href = link.get('href', '')
                title = link.get_text()
                snippet_text = snippet.get_text()

                if any(ad_indicator in href.lower() for ad_indicator in [
                    'ad_provider', 'sponsored', 'advertisement', 'pdffiller',
                    'click_metadata', 'utm_source=bing'
                ]):
                    continue

                if href.startswith('http'):
                    url = href
                elif href.startswith('/'):
                    try:
                        url = requests.utils.unquote(
                            href.split('?uddg=')[1].split('&')[0])
                    except:
                        continue
                else:
                    continue

                valid_links.append({
                    'url': url,
                    'title': title,
                    'snippet': snippet_text
                })
                print(f"Found DuckDuckGo result: {url}")

                if len(valid_links) >= 5:
                    break

        if valid_links:
            news_domains = ['news', 'times', 'bbc', 'cnn',
                            'reuters', 'theweek', 'firstpost', 'ndtv', 'msn']
            for link in valid_links:
                if any(domain in link['url'].lower() for domain in news_domains):
                    return link['url']

            return valid_links[0]['url']

        print("No valid links found in DuckDuckGo search results.")
        return None

    except Exception as e:
        print(f"Error during DuckDuckGo search: {str(e)}")
        return None


def create_prompt(text, topic=None):
    if topic:
        prompt = f"""TASK: Extract and summarize ONLY information about '{topic}' from the provided text.

        TEXT: {text[:3000]}

        INSTRUCTIONS:
        1. Focus exclusively on '{topic}' - ignore all unrelated content
        2. If '{topic}' is mentioned, provide:
           - A brief overview of how '{topic}' is discussed
           - 3-5 key points specifically about '{topic}'
           - A short conclusion about '{topic}'
        3. If '{topic}' is not mentioned at all, simply respond: "The topic '{topic}' was not found in the content."
        4. Do not include any information unrelated to '{topic}'
        5. Do not mention or summarize other topics or the general content

        FORMAT YOUR RESPONSE AS FOLLOWS (only if the topic is found):
        # Summary of '{topic}'
        
        ## Overview
        [Brief overview of how '{topic}' appears in the text]
        
        ## Key Points
        - [Point 1 about '{topic}']
        - [Point 2 about '{topic}']
        - [Point 3 about '{topic}']
        
        ## Conclusion
        [Brief conclusion specifically about '{topic}']"""
    else:
        prompt = f"""TASK: Provide a comprehensive summary of the entire text.

        TEXT: {text[:3000]}

        INSTRUCTIONS:
        1. Identify the main topic or themes
        2. Extract the most important information
        3. Organize the summary in a clear structure
        4. Focus on substance over style
        
        FORMAT YOUR RESPONSE AS FOLLOWS:
        # Summary
        
        ## Main Topic
        [Brief description of what the text is primarily about]
        
        ## Key Points
        - [Most important point 1]
        - [Most important point 2]
        - [Most important point 3]
        - [Most important point 4]
        - [Most important point 5]
        
        ## Conclusion
        [Overall takeaway or significance of the content]"""

    return prompt


def check_if_topic_not_found(result, topic):
    if not topic:
        return False

    if re.search(rf"(?:topic|'{topic}'|the topic '{topic}')\s+(?:was|is)\s+not\s+found", result, re.IGNORECASE):
        return True

    if "therefore, i should respond accordingly without mentioning other topics." in result.lower():
        return True

    if re.search(rf"no\s+information\s+(?:about|on|regarding)\s+(?:the topic\s+)?['\"]?{topic}['\"]?", result, re.IGNORECASE):
        return True

    if not (re.search(r"## Overview", result, re.IGNORECASE) and re.search(r"## Key Points", result, re.IGNORECASE)):
        if re.search(rf"(?:couldn't|could not|didn't|did not|no|none)\s+find", result, re.IGNORECASE):
            return True

    return False


def process_with_llm(text, topic=None, model="deepseek"):
    prompt = create_prompt(text, topic)

    try:
        if model == "deepseek":
            result = get_ollama_response(prompt)

        elif model == "gemini":
            response = gemini_model.generate_content(prompt)
            result = response.text

        elif model == "groq":
            completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that analyzes web content and provides well-structured summaries."},
                    {"role": "user", "content": prompt}
                ],
                model="llama3-8b-8192",
            )
            result = completion.choices[0].message.content

        else:
            raise ValueError(f"Unsupported model: {model}")

        return result

    except Exception as e:
        raise Exception(f"Error processing with {model}: {str(e)}")


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.get_json()
    url = data.get('url')
    topic = data.get('topic')
    model = data.get('model', 'deepseek')

    if not url:
        if not topic:
            return jsonify({'error': 'Either a URL or a topic must be provided'}), 400

        print(f"No URL provided, searching DuckDuckGo for: {topic}")
        url = duckduckgo_search(topic)

        if not url:
            return jsonify({'error': 'No relevant webpage found for the topic'}), 404

        print(f"Using found URL: {url}")

    if not validators.url(url):
        return jsonify({'error': 'Invalid URL'}), 400

    scraped_content = scrape_webpage(url)

    try:
        print(f"Processing URL: {url} for topic: {topic} using model: {model}")
        summary = process_with_llm(scraped_content, topic, model)
        print(f"Initial summary result: {summary[:200]}...")

        if topic and check_if_topic_not_found(summary, topic):
            print(
                f"Topic '{topic}' not found, attempting DuckDuckGo search...")
            search_query = f"{topic} information"
            new_url = duckduckgo_search(search_query)
            print(f"DuckDuckGo search returned URL: {new_url}")

            if new_url:
                print(f"Scraping new URL: {new_url}")
                new_content = scrape_webpage(new_url)
                new_summary = process_with_llm(new_content, topic, model)
                print(f"New summary result: {new_summary[:200]}...")

                if not check_if_topic_not_found(new_summary, topic):
                    print(f"Topic found in new URL. Returning combined summary.")
                    search_info = f"*Original website didn't contain information about '{topic}'. This summary is from: {new_url}*\n\n"
                    return jsonify({
                        'summary': search_info + new_summary,
                        'fallback_url': new_url
                    })
                else:
                    print(
                        f"Topic not found in new URL either. Returning original summary.")

        return jsonify({
            'summary': summary
        })
    except ValueError as e:
        print(f"ValueError: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Exception: {str(e)}")
        return jsonify({'error': f'Error processing with LLM: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True)
